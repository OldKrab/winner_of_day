from datetime import date
import random
from typing import AsyncIterator, Iterable
from telegram import User
from winner_of_day.bot.data import PyDoorContext
from winner_of_day.logger import get_logger
from winner_of_day.suno.api import SongInfo

logger = get_logger(__name__)


async def generate_title(winner: User, winner_msg: str, ctx: PyDoorContext) -> str:
    title = await ctx.bot_data.gpt.generate_title_of_day(winner.full_name, winner_msg)
    return title


async def generate_suno_songs(
    song_text: str, genre: str, winner: User, today: date, winner_msg: str, title: str, ctx: PyDoorContext
) -> AsyncIterator[SongInfo]:
    songs_infos = ctx.bot_data.suno.custom_generate(song_text, genre, f"{winner.full_name}_{today}")
    logger.info(
        f"Generated songs for genre '{genre}' and winner '{winner.full_name}' and msg '{winner_msg}' and title {title} with ids: {', '.join(s.id for s in songs_infos)}"
    )
    return (
        await ctx.bot_data.suno.wait_for_status_complete(song_info.id) for song_info in songs_infos
    )
