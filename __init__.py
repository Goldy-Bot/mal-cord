from __future__ import annotations
from typing import Dict, List, Any

import GoldyBot
from GoldyBot import SlashOptionAutoComplete, SlashOptionChoice
from jikanpy import AioJikan

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
            title = anime["title"]

            if anime["title_english"] is not None:
                title = anime["title_english"]

            choices.append(
                SlashOptionChoice(title, str(anime["mal_id"]))
            )

        return choices

    @GoldyBot.command(
        description = "Search for anime on 🔷MyAnimeList.",
        slash_options = {
            "query": SlashOptionAutoComplete(
                description = "Anime you would like to query.",
                callback = dynamic_anime_query
            )
        }
    )
    async def anime(self, platter: GoldyBot.GoldPlatter, query: str):
        # TODO: Add defer here when it's implemented into goldy bot or else we'll keep on getting errors with this command.
        await platter.wait()

        if query.isdigit():
            search_result = await self.jikan.anime(query, page = 1) # Essentially searching by id. (slash options return anime id as their value)
        else:
            search_result = await self.jikan.search("anime", query, page = 1)
            search_result = search_result["data"][0]

        anime: Dict[str, Any] = search_result["data"]

        embed = GoldyBot.Embed(
            title = f"⛩️ {anime['title_english']}",
            description = anime["background"],
            url = anime["url"],
            image = GoldyBot.EmbedImage(
                url = anime["images"]["jpg"]["large_image_url"]
            )
        )

        await platter.send_message(embeds = [embed])


load = lambda: MALCord()