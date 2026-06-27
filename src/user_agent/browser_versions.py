from enum import Enum
from src.user_agent.constants import CHROME_VERSION, FIREFOX_VERSION, EDGE_VERSION, SAFARI_VERSION

class Browser(Enum):
    CHROME = CHROME_VERSION
    FIREFOX = FIREFOX_VERSION
    EDGE = EDGE_VERSION
    SAFARI = SAFARI_VERSION

    @property
    def min_version(self) -> int:
        return self.value

    @property
    def browser_name(self) -> str:
        return self.name.lower()
