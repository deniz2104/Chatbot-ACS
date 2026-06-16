from datetime import timedelta

DARK_THEME = "<style>.stApp { background-color: #0E5A9C; color: #fff; }</style>"
DARK_BUTTON = "<style>.stButton > button { background-color: #FFFFFF; color: #0E5A9C; }</style>"
_YEAR_TO_INT = {"I": 1, "II": 2, "III": 3, "IV": 4}

_SPECIAL_CHARS = "!@#$%^&*()-_=+[]{}|;:'\",.<>?/"

_CLEAR_DELAY = 1

SESSION_LIFETIME: timedelta = timedelta(hours=1)

_PASSWORD_REQUIREMENTS = [
    ("At least 8 characters",          lambda p: len(p) >= 8),
    ("At least one uppercase letter",   lambda p: any(c.isupper() for c in p)),
    ("At least one lowercase letter",   lambda p: any(c.islower() for c in p)),
    ("At least one digit",              lambda p: any(c.isdigit() for c in p)),
    ("At least one special character",  lambda p: any(c in _SPECIAL_CHARS for c in p)),
]

_USERNAME_REQUIREMENTS = [
    ("Between 6 and 20 characters", lambda u: 6 <= len(u) <= 20),
    ("Only letters and digits",      lambda u: u.isalnum()),
    ("Can contain special characters ._-", lambda u: all(c.isalnum() or c in "._-" for c in u)),
]
