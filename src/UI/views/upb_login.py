import base64
import hashlib
import secrets
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

REALM_URL = "https://login.upb.ro/auth/realms/UPB/protocol/openid-connect"
CLIENT_ID = "account-console"
REDIRECT_URI = "https://login.upb.ro/auth/realms/UPB/account"


def _pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return verifier, challenge


def _exchange_code(client: httpx.Client, location: str, verifier: str) -> dict:
    parsed = urlparse(location)
    code = parse_qs(parsed.query).get("code", [None])[0]
    if not code:
        raise ValueError("Nu s-a primit codul de autorizare de la UPB.")

    token_resp = client.post(
        f"{REALM_URL}/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "code_verifier": verifier,
        },
        follow_redirects=True,
    )
    token_resp.raise_for_status()
    tokens = token_resp.json()

    userinfo_resp = client.get(
        f"{REALM_URL}/userinfo",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        follow_redirects=True,
    )
    userinfo_resp.raise_for_status()
    return userinfo_resp.json()


def _parse_error(soup: BeautifulSoup) -> str:
    node = soup.select_one(".kc-feedback-text, #input-error, .alert-error")
    return node.get_text(strip=True) if node else "Autentificare eșuată."


def _advance(
    client: httpx.Client, resp: httpx.Response, verifier: str
) -> tuple[httpx.Response | None, dict | None]:
    """Follows Keycloak intermediate redirects. Returns (200_resp, None) or (None, userinfo)."""
    for _ in range(5):
        if resp.status_code == 200:
            return resp, None
        location = resp.headers.get("location", "")
        if location.startswith(REDIRECT_URI):
            return None, _exchange_code(client, location, verifier)
        resp = client.get(location, follow_redirects=False)
    return resp, None


def upb_login(username: str, password: str) -> dict:
    verifier, challenge = _pkce()
    auth_url = (
        f"{REALM_URL}/auth"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid+profile+email"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
    )

    with httpx.Client(follow_redirects=True, timeout=15.0) as client:
        resp = client.get(auth_url)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form", id="kc-form-login")
        if not form:
            raise ValueError("Nu s-a putut contacta serverul UPB. Încearcă mai târziu.")

        resp = client.post(
            form["action"],
            data={"username": username, "password": password},
            follow_redirects=False,
        )

        resp, userinfo = _advance(client, resp, verifier)
        if userinfo:
            return userinfo

        soup = BeautifulSoup(resp.text, "html.parser")

        if soup.find("input", {"name": "otp"}):
            otp_form = soup.find("form")
            return {
                "otp_required": True,
                "action": otp_form["action"] if otp_form else str(resp.url),
                "hidden": {
                    inp["name"]: inp.get("value", "")
                    for inp in soup.find_all("input", type="hidden")
                    if inp.get("name")
                },
                "cookies": dict(client.cookies),
                "verifier": verifier,
            }

        raise ValueError(_parse_error(soup))


def upb_login_otp(otp: str, action: str, hidden: dict, cookies: dict, verifier: str) -> dict:
    with httpx.Client(cookies=cookies, follow_redirects=False, timeout=15.0) as client:
        resp = client.post(action, data={**hidden, "otp": otp}, follow_redirects=False)
        _, userinfo = _advance(client, resp, verifier)
        if userinfo:
            return userinfo
        raise ValueError(_parse_error(BeautifulSoup(resp.text, "html.parser")))
