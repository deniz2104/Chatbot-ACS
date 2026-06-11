import streamlit as st
from src.UI.constants import _YEAR_TO_INT

_DEPT_GROUP_COUNT = {"Automatica": 4, "Calculatoare": 5}

_YEAR4_GROUPS: dict[str, list[str]] = {
    "Automatica": ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"],
    "Calculatoare": ["C1", "C2", "C3", "C4", "C5"],
}

def _compose_class(faculty_year: str, department: str) -> list[str]:
    n = _DEPT_GROUP_COUNT.get(department, 3)
    year_int = _YEAR_TO_INT.get(faculty_year, 1)
    return [f"3{year_int}{i}" for i in range(1, n + 1)]

def _set_bachelor_classes(department: str) -> list[str]:
    return {"Automatica": ["AA", "AB", "AC"], "Calculatoare": ["CA", "CB", "CC", "CD"]}.get(department, [])

def _get_year3_specialization(class_name: str, group: str) -> str | None:
    if class_name == "AA" or (class_name == "AB" and group in ["331", "332"]):
        return "A"
    if class_name == "AC" or (class_name == "AB" and group in ["333", "334"]):
        return "B"
    return None

def _decide_year4(department: str) -> tuple[str, str]:
    group = st.selectbox("Group", options=_YEAR4_GROUPS.get(department, []))
    specialization = group[0] if department == "Automatica" and group else ""
    return group, specialization

def _decide_lower_years(faculty_year: str, department: str) -> tuple[str, str]:
    group_prefix = st.selectbox("Group", options=_compose_class(faculty_year, department))
    subgroup = st.selectbox("Subgroup", options=_set_bachelor_classes(department))
    base = group_prefix + subgroup
    specialization = (
        _get_year3_specialization(subgroup, group_prefix)
        if faculty_year == "III" and department == "Automatica"
        else None
    )
    return base, (specialization or "")

def decide_class(faculty_year: str, department: str) -> tuple[str, str]:
    return _decide_year4(department) if faculty_year == "IV" else _decide_lower_years(faculty_year, department)
