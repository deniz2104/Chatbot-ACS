from dataclasses import dataclass, asdict

@dataclass
class Metadata:
    source: str
    url_slug: str
    title: str
    filename: str = ""
    extension: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)