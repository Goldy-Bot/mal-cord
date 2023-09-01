from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass, field

from io import BytesIO
from PIL import Image, ImageDraw
from GoldyBot import get_goldy_instance

@dataclass
class Anime:
    data: Dict[str, Any] = field(repr=False)

    title: str = field(init=False)
    english_title: str = field(init=False)
    episodes: int = field(init=False)
    synopsis: str = field(init=False)
    background: str = field(init=False)
    description: str = field(init=False)
    type: str = field(init=False)
    status: str = field(init=False)
    aired: dict = field(init=False)
    url: str = field(init=False)
    rank: int = field(init=False)
    popularity: int = field(init=False)
    stars: int = field(init=False)
    genres: List[dict] = field(init=False)
    studios: List[dict] = field(init=False)
    broadcast: dict = field(init=False)

    def __post_init__(self):
        self.title = self.data.get("title")
        self.english_title = self.data.get("title_english")
        self.episodes = self.data.get("episodes")
        self.synopsis = self.data.get("synopsis")
        self.background = self.data.get("background")
        self.type = self.data.get("type")
        self.status = self.data.get("status")
        self.aired = self.data.get("aired")
        self.url = self.data.get("url")
        self.rank = self.data.get("rank")
        self.popularity = self.data.get("popularity")
        self.stars = self.data.get("score")
        self.genres = self.data.get("genres")
        self.studios = self.data.get("studios")
        self.broadcast = self.data.get("broadcast")

        self.description = self.background

        if self.description is None:
            self.description = self.synopsis

    async def generate_banner(self) -> Image.Image:
        """Generates the banner for this anime, returns Pillow Image object."""
        goldy = get_goldy_instance()
        aio_http = goldy.http_client._session

        banner = Image.new("RGB", (1737, 700), color = (51, 51, 51))
        target_height = banner.height

        # Getting cover image.
        cover_image = await aio_http.get(self.data["images"]["jpg"]["large_image_url"])
        cover_image = await cover_image.read()
        cover_image = Image.open(BytesIO(cover_image))

        # Resizing cover image to fit banner.
        height_percent = (target_height/float(cover_image.height))
        width_size = int((float(cover_image.width)*float(height_percent)))
        cover_image = cover_image.resize((width_size, target_height), Image.Resampling.LANCZOS)

        banner.paste(cover_image, (0, 0))

        # Getting trailer image if exits.
        trailer_thumbnail_url = self.data["trailer"].get("images").get("maximum_image_url")
        if trailer_thumbnail_url is not None:
            target_height = target_height + 30 # Solves those weird thumbnails that contain tiny bards at the edge.

            thumbnail = await aio_http.get(trailer_thumbnail_url)
            thumbnail = await thumbnail.read()
            thumbnail = Image.open(BytesIO(thumbnail))

            # Resizing thumbnail image to fit banner.
            height_percent = (target_height/float(thumbnail.height))
            width_size = int((float(thumbnail.width)*float(height_percent)))

            thumbnail = thumbnail.resize((width_size, target_height), Image.Resampling.LANCZOS)

            banner.paste(thumbnail, (cover_image.width, -15))

        banner = add_corners(banner, 40) # Gives the image curvy edges.

        return banner


def add_corners(image: Image.Image, radius: int) -> Image.Image:
    # Totally not stolen from https://stackoverflow.com/questions/11287402/how-to-round-corner-a-logo-without-white-backgroundtransparent-on-it-using-pi
    circle = Image.new("L", (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2 - 1, radius * 2 - 1), fill = 255)
    alpha = Image.new("L", image.size, 255)
    w, h = image.size
    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius))
    image.putalpha(alpha)
    return image