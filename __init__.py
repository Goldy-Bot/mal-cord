from __future__ import annotations
from typing import Dict, List, Any

import GoldyBot
from GoldyBot import SlashOptionAutoComplete, SlashOptionChoice
from io import BytesIO

from devgoldyutils import short_str
from jikanpy import AioJikan

from .anime import Anime

class MALCord(GoldyBot.Extension):
    def __init__(self):
        super().__init__()

        self.jikan = AioJikan(session = self.goldy.http_client._session)

    async def dynamic_anime_query(self, typing_value: str) -> List[SlashOptionChoice]:
        search_results: Dict[str, Any] = None

        if typing_value in ["", " "]: # If typing value is empty return top anime series.
            search_results = await self.jikan.top("anime", page = 1)
        else:
            search_results = await self.jikan.search("anime", typing_value, page = 1)

        anime_list: List[Dict[str, Any]] = search_results["data"]

        choices = []

        for anime in anime_list:
            anime = Anime(anime)

            choices.append(
                SlashOptionChoice(anime.title, str(anime.data["mal_id"]))
            )

        return choices

    @GoldyBot.command(
        description = "✨ Search for anime on 🔷MyAnimeList.",
        slash_options = {
            "query": SlashOptionAutoComplete(
                description = "🌈 Anime you would like to query.",
                callback = dynamic_anime_query
            )
        }
    )
    async def anime(self, platter: GoldyBot.GoldPlatter, query: str):
        # TODO: Add defer here when it's implemented into goldy bot or else we'll keep on getting errors with this command.
        await platter.wait()

        if query.isdigit():
            search_result = await self.jikan.anime(query, page = 1) # Essentially searching by id. (slash options return anime id as their value instead the title)
        else:
            search_result = await self.jikan.search("anime", query, page = 1)
            search_result = search_result["data"][0]

        anime = Anime(search_result["data"])
        banner = await anime.generate_banner()

        memory_buff = BytesIO()
        banner.save(memory_buff, format="png")
        banner_file = GoldyBot.File(memory_buff, "image.png")

        embed = GoldyBot.Embed(
            title = f"⛩️ {anime.title}",
            description = short_str(anime.description, 334) + f"\n[[Read More]]({anime.url})",
            url = anime.url,
            image = GoldyBot.EmbedImage(
                url = banner_file.attachment_url
            )
        )

        await platter.send_message(embeds = [embed], files = [banner_file])


load = lambda: MALCord()