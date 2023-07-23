from __future__ import annotations
from typing import Dict, List, Any, Literal

import GoldyBot
from GoldyBot import SlashOptionAutoComplete, SlashOptionChoice
from io import BytesIO
from datetime import datetime
from devgoldyutils import short_str
from jikanpy import AioJikan

from .anime import Anime
from .errors import AnimeNotFound

class MALCord(GoldyBot.Extension):
    def __init__(self):
        super().__init__()
        # We cache the top anime results displayed on auto complete when the member has not entered any character
        # as an attempt to save spamming the jikan API. As top anime results very rarely change we hold this cache for an entire day.
        self.__top_anime_result_cache = (0, {}) # Index 0 = timestamp cache expires, Index 1 = Cached data.

        self.jikan = AioJikan(session = self.goldy.http_client._session)

    async def dynamic_anime_query(self, typing_value: str) -> List[SlashOptionChoice]:
        search_results: Dict[str, Any] = None

        if typing_value in ["", " "]: # If typing value is empty return top anime series.
            current_timestamp = datetime.now().timestamp()
            if current_timestamp > self.__top_anime_result_cache[0]:
                search_results = await self.jikan.top("anime", page = 1)
                self.__top_anime_result_cache = (current_timestamp + 86400, search_results) # Expires in a day.
                self.logger.info(f"Top anime has been cached! Expires at {datetime.fromtimestamp(current_timestamp + 86400)}")
            else:
                search_results = self.__top_anime_result_cache[1]
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
        await platter.wait()

        if query.isdigit(): # Essentially searching by id. (slash options return anime id as their value instead the title)
            search_result = await self.jikan.anime(query, page = 1)
            search_result = search_result["data"]
        else:
            search_result = await self.jikan.search("anime", query, page = 1)

            try:
                search_result = search_result["data"][0]
            except IndexError:
                raise AnimeNotFound(platter, query, self.logger)

        anime = Anime(search_result)
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
            ),
            fields = [
                GoldyBot.EmbedField(
                    "ℹ️ Info:", 
                    f"**- 📺 Type: ``{anime.type}``\n" \
                    f"- 📽️ Episodes: ``{anime.episodes}``\n" \
                    "- 🎙️ Studio: [``{studio}``]({studio_link})\n" \
                    "- 🍬 Genres: ``{genres}``\n" \
                    f"- 🇬🇧 English: ``{short_str(anime.english_title, 50) if anime.english_title is not None else 'None'}``**",
                ),
                GoldyBot.EmbedField(
                    "✈️ Airing Status:", 
                    "**- {status_icon} ``{status}``\n" \
                    "- ⏰ Started: {aired_started}\n" \
                    "- 🏁 Ended: {aired_ended}**",
                    inline = True
                ),
                GoldyBot.EmbedField(
                    "📈 Rating:", 
                    "**- 🏆 Rank: ``{rank}``\n" \
                    "- 🍿 Popularity: ``{popularity}``\n" \
                    "- ⭐ Stars: ``{stars}``**",
                    inline = True
                )
            ]
        )

        airing_start = anime.aired.get("from")
        if airing_start is not None:
            airing_start = datetime.strptime(anime.aired.get("from")[:-6], "%Y-%m-%dT%H:%M:%S") # 2008-04-06T00:00:00+00:00

        airing_end = anime.aired.get("to")
        if airing_end is not None:
            airing_end = datetime.strptime(anime.aired.get("to")[:-6], "%Y-%m-%dT%H:%M:%S")

        embed.format_fields(
            studio = anime.studios[0]["name"] if not anime.studios == [] else "None",
            studio_link = anime.studios[0]["url"] if not anime.studios == [] else anime.url,
            genres = " | ".join([genre["name"] for genre in anime.genres]),
            rank = f"#{anime.rank}" if anime.rank is not None else "None",
            popularity = f"#{anime.popularity}" if anime.popularity is not None else "None",
            stars = f"{anime.stars} / 10" if anime.stars is not None else "None",
            status = anime.status,
            status_icon = self.__get_status_icon(anime.status),
            aired_started = f"<t:{int(airing_start.timestamp())}:D>" if airing_start is not None else "``None``", 
            aired_ended = f"<t:{int(airing_end.timestamp())}:D>" if airing_end is not None else "``None``"
        )

        await platter.send_message(embeds = [embed], files = [banner_file])


    def __get_status_icon(self, status: Literal["Not yet aired", "Currently Airing", "Finished Airing"]):
        if status == "Not yet aired":
            return "🟤"
        elif status == "Currently Airing":
            return "🟠"
        elif status == "Finished Airing":
            return "🟢"


load = lambda: MALCord()