from __future__ import annotations
from typing import Dict, List, Any, Literal

import pytz
import GoldyBot
from GoldyBot import (
    SlashOptionAutoComplete, SlashOptionChoice, SlashOption, 
    Button, ButtonStyle
)
from enum import Enum
from io import BytesIO
from datetime import datetime
from devgoldyutils import short_str, debug
from jikanpy import AioJikan

from .anime import Anime
from .character import Character
from .errors import AnimeNotFound

class SearchTypes(Enum):
    ANIME = 0
    CHARACTERS = 1

    def __init__(self, value: int) -> None:
        ...

class MALCord(GoldyBot.Extension):
    def __init__(self):
        super().__init__()
        # We cache the top anime results displayed on auto complete when the member has not entered any character
        # as an attempt to save spamming the jikan API. As top anime results very rarely change we hold this cache for an entire day.

        self.__top_results_cache = { # Index 0 = timestamp cache expires, Index 1 = Cached data.
            0: (0, {}),
            1: (0, {})
        }

        self.jikan = AioJikan(session = self.goldy.http_client._session)

    async def dynamic_anime_query(self, typing_value: str, search_type: int = 0, **_) -> List[SlashOptionChoice]:
        search_results: Dict[str, Any] = None

        search_type: SearchTypes = SearchTypes(search_type)

        if typing_value in ["", " "]: # If typing value is empty return top anime series.
            current_timestamp = datetime.now().timestamp()
            top_result_cache = self.__top_results_cache[search_type.value]

            if current_timestamp > top_result_cache[0]:
                search_results = await self.jikan.top(search_type.name.lower(), page = 1)

                self.__top_results_cache[search_type.value] = (current_timestamp + 86400, search_results) # Expires in a day.
                self.logger.info(f"Top anime has been cached! Expires at {datetime.fromtimestamp(current_timestamp + 86400)}")
            else:
                search_results = top_result_cache[1]

        else:
            search_results = await self.jikan.search(search_type.name.lower(), typing_value, page = 1)

        search_result_list: List[Dict[str, Any]] = search_results["data"]

        choices = []

        for search_result in search_result_list:
            name = None

            if search_type == SearchTypes.ANIME:
                name = search_result["title"]

            elif search_type == SearchTypes.CHARACTERS:

                character = Character(search_result)
                name = character.name

                if not character.nicknames == []:
                    name += f" ~ {character.nicknames[0]}"

                elif character.about is not None:
                    text = character.about.replace("\n", " ")
                    name += f' ~ "{short_str(text, 56)}"'

            choices.append(
                SlashOptionChoice(name, str(search_result["mal_id"]))
            )

        return choices


    @GoldyBot.command(
        description = "✨ Search for anime on 🔷MyAnimeList.",
        slash_options = {
            "query": SlashOptionAutoComplete(
                description = "🌈 Anime you would like to query.",
                callback = dynamic_anime_query
            ),
            "search_type": SlashOption(
                name = "type",
                description = "What you would actually like to search, defaults to anime.",
                choices = [
                    SlashOptionChoice("anime", 0),
                    SlashOptionChoice("characters", 1)                    
                ],
                required = False
            )
        },
        wait = True
    )
    async def anime(self, platter: GoldyBot.GoldPlatter, query: str, search_type: int = 0):
        search_type: SearchTypes = SearchTypes(search_type)

        if query.isdigit(): # Essentially searching by id. (slash options return anime id as their value instead the title)
            if search_type == SearchTypes.ANIME:
                search_result = await self.jikan.anime(query, page = 1)
            elif search_type == SearchTypes.CHARACTERS:
                search_result = await self.jikan.characters(query)

            search_result = search_result["data"]
        else:
            search_result = await self.jikan.search(search_type.name.lower(), query, page = 1)

            try:
                search_result = search_result["data"][0]
            except IndexError:
                raise AnimeNotFound(platter, query, search_type, self.logger)


        if search_type == SearchTypes.ANIME:
            await self.send_anime(platter, Anime(search_result))
        elif search_type == SearchTypes.CHARACTERS:
            await self.send_character(platter, Character(search_result))


    async def send_anime(self, platter: GoldyBot.GoldPlatter, anime: Anime) -> None:
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
            status_icon = self.get_status_icon(anime.status),
            aired_started = f"<t:{int(airing_start.timestamp())}:D>" if airing_start is not None else "``None``", 
            aired_ended = f"<t:{int(airing_end.timestamp())}:D>" if airing_end is not None else "``None``"
        )

        recipes = []

        broadcast_timezone = anime.broadcast.get("timezone")
    
        if broadcast_timezone is not None and not anime.status == "Finished Airing":
            timezone = pytz.timezone(broadcast_timezone.lower())

            now = datetime.now()
            broadcast_datetime = datetime(
                year = now.year,
                month = now.month,
                day = now.day,
                hour = int(anime.broadcast_time[0]), 
                minute = int(anime.broadcast_time[1])
            )
            broadcast_datetime = timezone.normalize(timezone.localize(broadcast_datetime, is_dst = True))

            recipes.append(
                Button(
                    ButtonStyle.GREY, 
                    label = "When Air?", 
                    emoji = "✈️", 
                    callback = lambda x: x.send_message(
                        f"✈️ Airing on **{anime.broadcast.get('day')}** at **<t:{int(broadcast_datetime.timestamp())}:t>**", hide = True
                    ),
                    author_only = False
                )
            )

        trailer_url = anime.data["trailer"].get("url")

        if trailer_url is not None:
            recipes.append(
                Button(
                    ButtonStyle.BLURPLE, 
                    label = "Trailer", 
                    emoji = "📽️", 
                    callback = lambda x: x.send_message(
                        f"**[{anime.title} - Trailer]({trailer_url})**", hide = True
                    ),
                    author_only = False
                )
            )


        await platter.send_message(embeds = [embed], files = [banner_file], recipes = recipes)


    async def send_character(self, platter: GoldyBot.GoldPlatter, character: Character) -> None:
        character_image = await character.get_image()

        memory_buff = BytesIO()
        character_image.save(memory_buff, format="png")
        character_image_file = GoldyBot.File(memory_buff, "image.png")

        embed = GoldyBot.Embed(
            title = f"🧑 {character.name}",
            description = (lambda x: short_str(x, 334) + f"\n[[Read More]]({character.url})" if x is not None else "*This character has no description.*")(character.about),
            url = character.url,
            image = GoldyBot.EmbedImage(
                url = character_image_file.attachment_url
            ),
            fields = [
                GoldyBot.EmbedField(
                    "ℹ️ Info:", 
                    f"**- 🇯🇵 Kanji: ``{character.name_kanji}``\n" \
                    "- 💖 Nicknames: ``{nicknames}``**",
                    inline = True
                ),
                GoldyBot.EmbedField(
                    "📈 Rating:", 
                    f"**- 💝 Favorites: ``{character.favorites}``**",
                    inline = True
                )
            ]
        )

        embed.format_fields(
            nicknames = " | ".join(character.nicknames) if not character.nicknames == [] else "None",
        )

        await platter.send_message(embeds = [embed], files = [character_image_file])


    def get_status_icon(self, status: Literal["Not yet aired", "Currently Airing", "Finished Airing"]):
        if status == "Not yet aired":
            return "🟤"
        elif status == "Currently Airing":
            return "🟠"
        elif status == "Finished Airing":
            return "🟢"


load = lambda: MALCord()