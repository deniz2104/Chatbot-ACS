from dataclasses import dataclass
from typing import Literal

from src.categorization.categories import CATEGORY_KEYWORDS_MAPPING

## to do

DepartmentType = Literal[
    "Calculatoare",
    "Automatica Directia A",
    "Automatica Directia B",
    "General",
]

@dataclass
class Website:
    url: str
    main_categories: list[str]
    department: DepartmentType

    def __post_init__(self):
        valid_departments = {"Calculatoare", "Automatica Directia A", "Automatica Directia B", "General"}
        if self.department not in valid_departments:
            raise ValueError(f"Invalid department: {self.department}. Must be one of {valid_departments}")
        
    @property
    def keywords(self) -> dict[str, list[str]]:
        return {cat: CATEGORY_KEYWORDS_MAPPING[cat] for cat in self.main_categories if cat in CATEGORY_KEYWORDS_MAPPING}
    
def load_websites() -> list[Website]:
    return [
    
    ]
