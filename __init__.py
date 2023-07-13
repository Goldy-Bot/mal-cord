from __future__ import annotations
from typing import Dict

import GoldyBot
from jikanpy import AioJikan

class MALCord(GoldyBot.Extension):
    def __init__(self):
        super().__init__()

    @GoldyBot.command(
        description = "Search for ⛩️anime on 🔷MyAnimeList.",
        slash_options = {
            "query": GoldyBot.SlashOption(
                description = "Anime you would like to query."
            )
        }
    )
    async def anime(self, platter: GoldyBot.GoldPlatter, query: str):
        jikan = AioJikan()
        search_result = await jikan.search("anime", "one piece", page=1)
        anime: Dict[str, dict|str|list] = search_result["data"][0]

        embed = GoldyBot.Embed(
            title = f"⛩️ {anime['title_english']}",
            description = anime["background"],
            image = GoldyBot.EmbedImage(
                url = anime["images"]["jpg"]["large_image_url"]
            )
        )

        await platter.send_message(embeds = [embed])
        await jikan.close()


def load():
    MALCord()