from __future__ import annotations
from typing import TYPE_CHECKING

from GoldyBot import nextcore_utils, Embed, Colours

if TYPE_CHECKING:
    import logging as log
    from GoldyBot import objects
    from . import SearchTypes

class AnimeNotFound(nextcore_utils.FrontEndErrors):
    """Raises when an anime query fails."""
    def __init__(self, platter: objects.GoldPlatter, query: str, type: SearchTypes, logger: log.Logger = None):
        super().__init__(
            embed = Embed(
                title = "❤️ Anime not found!", 
                description = f"""
                Umm seems like we couldn't find any {type.name.lower()} with the query ``{query}``.
                Try using the auto complete in the slash command to search, it's much more reliable.
                """,
                colour = Colours.RED
            ),
            message = f"Couldn't find any anime with the query '{query}'.",
            platter = platter, 
            delete_after = 12,
            logger = logger
        )