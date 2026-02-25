from enum import Enum

class Browser(Enum):
    CHROME = 145
    FIREFOX = 147
    EDGE = 144
    SAFARI = 26

    @property
    def min_version(self) -> int:
        return self.value

    @property
    def browser_name(self) -> str:
        return self.name.lower()
