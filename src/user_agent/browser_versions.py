import os

from enum import Enum
from dotenv import load_dotenv

load_dotenv()

class Browser(Enum):
    CHROME = int(os.getenv('CHROME_VERSION','0'))
    FIREFOX = int(os.getenv('FIREFOX_VERSION','0'))
    EDGE = int(os.getenv('EDGE_VERSION','0'))
    SAFARI = int(os.getenv('SAFARI_VERSION','0'))

    @property
    def min_version(self) -> int:
        return self.value

    @property
    def browser_name(self) -> str:
        return self.name.lower()
