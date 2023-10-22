from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, List, Any, Literal
    from jikan4snek.client.jikan import JikanResponseFromSearch

import pytz
import GoldyBot
from GoldyBot import (
    SlashOptionAutoComplete, SlashOptionChoice, SlashOption, 
    Button, ButtonStyle, SelectMenu, SelectMenuChoice
)
from enum import Enum
from io import BytesIO
from datetime import datetime
from jikan4snek import Jikan4SNEK
from devgoldyutils import short_str

from .anime import Anime
from .character import Character
from .errors import AnimeNotFound, RestrictedSearch

class SearchTypes(Enum):
    ANIME = 0
    CHARACTERS = 1

    def __init__(self, value: int) -> None:
        ...

class MALCord(GoldyBot.Extension):
    def __init__(self):
        super().__init__()

        self.jikan = Jikan4SNEK(debug = False)

    async def dynamic_anime_query(self, typing_value: str, search_type: int = 0, **_) -> List[SlashOptionChoice]:
        search_results: Dict[str, Any] = None

        search_type: SearchTypes = SearchTypes(search_type)

        if typing_value in ["", " "]: # If typing value is empty return top anime series.
            search_api = self.jikan.search("", page = 1)
            search_results = await self.__get_results(search_api, search_type)

        else:
            search_api = self.jikan.search(typing_value, page = 1)
            search_results = await self.__get_results(search_api, search_type)

        status = search_results.get("status")

        if status == 500:
            return [SlashOptionChoice(f"Search Failed: API Error ({status})", str(None))]

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
                    name += f' ~ "{short_str(text, 50)}"'

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
            search_id = query
        elif query == "None":
            raise RestrictedSearch("uhhh that option is just to notify you that an api error occurred...", platter, self.logger)
        else:
            jikan_response = await self.jikan.search(query, page = 1)
            search_result = self.__get_results(jikan_response, search_type)

            try:
                search_id = search_result["data"][0]["mal_id"]
            except IndexError:
                raise AnimeNotFound(platter, query, search_type, self.logger)

        if search_type == SearchTypes.ANIME:
            await self.send_anime(platter, search_id)
        elif search_type == SearchTypes.CHARACTERS:
            await self.send_character(platter, search_id)


    async def send_anime(self, platter: GoldyBot.GoldPlatter, search_id: int) -> None:
        search_result = await self.jikan.get(search_id).anime()
        characters_result = await self.jikan.get(search_id, "characters").anime()
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

        recipes.append(
            Button(
                ButtonStyle.BLURPLE, 
                label = "Characters", 
                emoji = "🧑", 
                callback = lambda x: x.send_message(
                    "**Which 🧑 character would you like to lookup?**",
                    recipes = [
                        SelectMenu(
                            callback = lambda x, value: self.send_character(x, int(value), True),
                            choices = [
                                SelectMenuChoice(
                                    label = x["character"]["name"], 
                                    value = x["character"]["mal_id"],
                                    description = f"Role: {x['role']} | Favorites: {x['favorites']}"
                                ) for x in sorted(characters_result["data"], key = lambda d: d["favorites"], reverse = True) 
                            ]
                        )
                    ],
                    hide = True
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


    async def send_character(self, platter: GoldyBot.GoldPlatter, character_id: int, hide = False) -> None:
        search_result = await self.jikan.get(character_id).characters()
        print(">>", search_result["data"])
        character = Character(search_result["data"])

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

        await platter.send_message(embeds = [embed], files = [character_image_file], hide = hide)


    def __get_status_icon(self, status: Literal["Not yet aired", "Currently Airing", "Finished Airing"]):
        if status == "Not yet aired":
            return "🟤"
        elif status == "Currently Airing":
            return "🟠"
        elif status == "Finished Airing":
            return "🟢"

    async def __get_results(self, jikan_response: JikanResponseFromSearch, search_type: SearchTypes) -> Dict[str, Any]:
        search_results: Dict[str, Any] = None

        if search_type == SearchTypes.ANIME:
            search_results = await jikan_response.anime()
        else:
            search_results = await jikan_response.characters()

        return search_results


load = lambda: MALCord()