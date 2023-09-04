from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Any, List

from PIL import Image
from io import BytesIO
from GoldyBot import get_goldy_instance
from dataclasses import dataclass, field

@dataclass
class Character:
    data: Dict[str, Any] = field(repr=False)

    name: str = field(init=False)
    name_kanji: str = field(init=False)
    url: str = field(init=False)
    nicknames: List[str] = field(init=False)
    favorites: int = field(init=False)
    about: str | None = field(init=False)

    def __post_init__(self):
        self.name = self.data.get("name")
        self.name_kanji = self.data.get("name_kanji")
        self.url = self.data.get("url")
        self.nicknames = self.data.get("nicknames")
        self.favorites = self.data.get("favorites")
        self.about = self.data.get("about")

    async def get_image(self) -> Image.Image:
        """Get's image of character."""
        goldy = get_goldy_instance()
        aio_http = goldy.http_client._session

        character_image = await aio_http.get(self.data["images"]["jpg"]["image_url"])
        character_image = await character_image.read()
        character_image = Image.open(BytesIO(character_image))

        return character_image