import requests
from bs4 import BeautifulSoup

from src.User_Agents.utils import BASE_WEBSITE, BROWSERS, BROWSER_OS_MAP

##TODO: exportam toata asta in cloud. Baza de date redis updatata la o saptamana folosind functie lambda
##TODO: rotim user agentii din redis la fiecare request pe care o sa l facem
##TODO: clasa de Retry
##TODO: clasa de Header Http

def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_user_agents() -> list[tuple[str, str, str]]:
    user_agents: list[tuple[str, str, str]] = []

    for browser in BROWSERS:
        operating_systems = BROWSER_OS_MAP[browser]
        soup = get_soup(f"{BASE_WEBSITE}/{browser}")
        entries = soup.find_all("span", attrs={"class": "code"})

        for os_name, user_agent in zip(operating_systems, entries, strict=False):
            user_agents.append((user_agent.text, browser, os_name))

    return user_agents