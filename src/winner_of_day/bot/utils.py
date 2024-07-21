import requests
from telegram import BotCommandScope, Chat, Update
from telegram.ext import ExtBot
from winner_of_day.bot.data import Command
from winner_of_day.logger import get_logger

logger = get_logger(__name__)


async def set_bot_commands(bot: ExtBot[None], commands: list[Command], scope: BotCommandScope):
    await bot.set_my_commands([(cmd.name, cmd.desc) for cmd in commands], scope=scope)


def get_chat(update: Update) -> Chat:
    if update.effective_chat is None:
        raise RuntimeError("chat is None")
    return update.effective_chat


def chunks(lst: list, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
