from __future__ import annotations
from typing import Dict, Any
from dataclasses import dataclass, field

@dataclass
class Anime:
    data: Dict[str, Any] = field(repr=False)

    title: str = field(init=False)
    synopsis: str = field(init=False)
    background: str = field(init=False)
    description: str = field(init=False)
    url: str = field(init=False)

    def __post_init__(self):
        self.title = self.data.get("title")
        self.synopsis = self.data.get("synopsis")
        self.background = self.data.get("background")
        self.url = self.data.get("url")

        self.description = self.background

        if self.description is None:
            self.description = self.synopsis