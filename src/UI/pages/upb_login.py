import asyncio
import base64
import hashlib
import secrets
from getpass import getpass

import httpx
from playwright.async_api import async_playwright, BrowserContext, Response

REALM_URL    = "https://login.upb.ro/auth/realms/UPB/protocol/openid-connect"
CLIENT_ID    = "account-console"
REDIRECT_URI = "https://login.upb.ro/auth/realms/UPB/account"


def generate_pkce() -> str:
    code_verifier: str = secrets.token_urlsafe(64)
    code_challenge: str = (
        base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        )
        .rstrip(b"=")
        .decode()
    )
    return code_challenge


async def navigate_sso(
    context: BrowserContext,
    entry_url: str,
    done: callable,
    label: str,
    screenshot_path: str,
    output_path: str,
) -> str:
    """
    Open a new tab, hit entry_url (which triggers the site's own OAuth2 initiation),
    wait until done(url) is True, then save HTML + screenshot.
    Returns the captured HTML.
    """
    page = await context.new_page()
    html = ""
    try:
        print(f"\nNavigating to {label} via SSO...")
        await page.goto(entry_url, wait_until="load", timeout=20000)
        await page.wait_for_url(done, timeout=20000)
        html = await page.content()
        print(f"{label} landed at: {page.url}")
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML saved to {output_path} ({len(html)} chars)")
    except Exception as e:
        print(f"Could not load {label}: {e}")
        html = await page.content()
    return html


async def get_tokens_via_browser(
    username: str,
    password: str,
    code_challenge: str,
) -> tuple[dict, str, str]:
    """Returns (tokens, studenti_html, curs_html)."""
    auth_url = (
        f"{REALM_URL}/auth"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid profile email"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )

    tokens: dict = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        await context.clear_cookies()
        page = await context.new_page()

        async def on_response(response: Response) -> None:
            if "/protocol/openid-connect/token" in response.url:
                try:
                    body = await response.json()
                    if "access_token" in body:
                        tokens.update(body)
                except Exception:
                    pass

        page.on("response", on_response)

        await page.goto(auth_url)
        await page.wait_for_selector('input[name="username"]')
        await page.fill('input[name="username"]', username)
        await page.fill('input[name="password"]', password)
        await page.click('input[type="submit"]')
        await page.wait_for_load_state("load", timeout=15000)

        for _ in range(5):
            if page.url.startswith(REDIRECT_URI):
                break

            error_el = page.locator(".kc-feedback-text, #input-error, .alert-error")
            if await error_el.count() > 0:
                msg = await error_el.first.inner_text()
                raise ValueError(f"Login error from server: {msg.strip()}")

            if await page.locator('input[name="otp"]').count() > 0:
                otp: str = input("Enter OTP code: ")
                await page.fill('input[name="otp"]', otp)
                await page.click('input[type="submit"]')
                await page.wait_for_load_state("load", timeout=15000)
            else:
                screenshot_path = "debug_login.png"
                await page.screenshot(path=screenshot_path)
                print(f"Unexpected intermediate page: {page.url}")
                raise TimeoutError(
                    f"Login flow stuck at unexpected page. See {screenshot_path} for details."
                )

        if not page.url.startswith(REDIRECT_URI):
            await page.screenshot(path="debug_login.png")
            raise TimeoutError(f"Never reached redirect URI. Stuck at: {page.url}")

        await page.wait_for_timeout(3000)

        # studenti.pub.ro — entry point generates its own state/nonce
        studenti_html = await navigate_sso(
            context,
            entry_url="https://studenti.pub.ro/index.php?page=User.UPBLogin&start=1",
            done=lambda url: "studenti.pub.ro" in url and "UPBLogin" not in url,
            label="studenti.pub.ro",
            screenshot_path="studenti_screenshot.png",
            output_path="studenti_page.html",
        )

        # curs.upb.ro — Moodle generates sesskey only after its own session is
        # established. Visit the login page first, then click the OAuth2 link
        # so Moodle's sesskey is already stored server-side when Keycloak redirects back.
        print("\nNavigating to curs.upb.ro via SSO...")
        curs_page = await context.new_page()
        curs_html = ""
        try:
            await curs_page.goto("https://curs.upb.ro/2025/login/index.php", wait_until="load", timeout=20000)
            oauth2_link = curs_page.locator("a[href*='auth/oauth2/login.php']").first
            await oauth2_link.click()
            await curs_page.wait_for_url(
                lambda url: "curs.upb.ro" in url and "oauth2callback" not in url and "login.upb.ro" not in url,
                timeout=20000,
            )
            curs_html = await curs_page.content()
            print(f"curs.upb.ro landed at: {curs_page.url}")
            await curs_page.screenshot(path="curs_screenshot.png")
            print("Screenshot saved to curs_screenshot.png")
            with open("curs_page.html", "w", encoding="utf-8") as f:
                f.write(curs_html)
            print(f"HTML saved to curs_page.html ({len(curs_html)} chars)")
        except Exception as e:
            print(f"Could not load curs.upb.ro: {e}")
            curs_html = await curs_page.content()

        await context.close()
        await browser.close()

    if not tokens:
        raise ValueError("Failed to intercept tokens from browser.")

    return tokens, studenti_html, curs_html


async def get_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{REALM_URL}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def login(username: str, password: str) -> tuple[dict, dict, str, str]:
    code_challenge = generate_pkce()
    tokens, studenti_html, curs_html = await get_tokens_via_browser(username, password, code_challenge)
    userinfo = await get_userinfo(tokens["access_token"])
    return tokens, userinfo, studenti_html, curs_html


async def main() -> None:
    username: str = input("Username: ")
    password: str = getpass("Password: ")

    print("Opening browser for login...")
    tokens, userinfo, studenti_html, curs_html = await login(username, password)

    print("\n--- Tokens ---")
    print(f"Access Token:  {tokens.get('access_token', 'N/A')[:60]}...")
    print(f"Refresh Token: {tokens.get('refresh_token', 'N/A')[:60]}...")
    print(f"ID Token:      {tokens.get('id_token', 'N/A')[:60]}...")
    print(f"Expires in:    {tokens.get('expires_in')} seconds")

    print("\n--- User Info ---")
    for key, value in userinfo.items():
        print(f"{key}: {value}")

    print("\n--- studenti.pub.ro ---")
    print(f"HTML length: {len(studenti_html)} chars" if studenti_html else "No HTML captured.")

    print("\n--- curs.upb.ro ---")
    print(f"HTML length: {len(curs_html)} chars" if curs_html else "No HTML captured.")


if __name__ == "__main__":
    asyncio.run(main())
