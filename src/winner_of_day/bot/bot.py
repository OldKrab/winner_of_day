from datetime import datetime, timedelta
import html
import json
import random
import signal
from winner_of_day.bot.callbacks.callbacks import (
    check_and_remind_to_run,
    regenerate_title_cmd,
    title_stat_cmd,
    win_stat_cmd,
    regenerate_song_cmd,
    register_cmd,
    reset_cmd,
    save_message,
    unregister_cmd,
)
from winner_of_day.bot.callbacks.callbacks import person_of_day_cmd
from winner_of_day.bot.data import (
    BotData,
    ChatData,
    CianApplication,
    PyDoorContext,
    get_command,
)
from winner_of_day.bot.utils import set_bot_commands
from winner_of_day.logger import get_logger
from telegram import BotCommandScopeChat, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    PicklePersistence,
    PersistenceInput,
)
from telegram.constants import ParseMode
from telegram.ext import MessageHandler
from apscheduler.triggers.base import BaseTrigger

logger = get_logger(__name__)

RESET_CMD = get_command("reset", reset_cmd, "ДЕБАГ ДЕБАГ ДЕБАГ")
REGENERATE_SONG_CMD = get_command("regenerate_song", regenerate_song_cmd, "ДЕБАГ ДЕБАГ ДЕБАГ")
REGENERATE_TITLE_CMD = get_command("regenerate_title", regenerate_title_cmd, "ДЕБАГ ДЕБАГ ДЕБАГ")

PERSON_CMD = get_command("person_of_day", person_of_day_cmd, "Узнать победителя дня")
WIN_STAT_CMD = get_command("win_stat", win_stat_cmd, "Узнать статистику по победителям")
TITLE_STAT_CMD = get_command("title_stat", title_stat_cmd, "Узнать титулы пользователей")
REGISTER_CMD = get_command("reg", register_cmd, "Участвовать в веселом занятии")
UNREGISTER_CMD = get_command("unreg", unregister_cmd, "Прекратить участвовать в веселом занятии")

COMMANDS = [PERSON_CMD, WIN_STAT_CMD, TITLE_STAT_CMD, REGISTER_CMD, UNREGISTER_CMD, RESET_CMD, REGENERATE_SONG_CMD, REGENERATE_TITLE_CMD]


async def error_handler(update: object, ctx: PyDoorContext) -> None:
    logger.error("Exception:", exc_info=ctx.error)
    if ctx.error is None:
        return
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    msg = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n"
        f"<pre>context.chat_data = {html.escape(str(ctx.chat_data))}</pre>\n"
        f"<pre>context.user_data = {html.escape(str(ctx.user_data))}</pre>\n"
        f"Exception: \n<pre>{html.escape(repr(ctx.error))}</pre>\n"
        "See logs for details."
    )
    await ctx.bot.send_message(ctx.bot_data.admin, msg, parse_mode=ParseMode.HTML)


def init_commands_handlers(app: CianApplication):
    app.add_handler(MessageHandler(None, save_message), 0)
    for cmd in COMMANDS:
        app.add_handler(cmd.handler, 1)


class RandomTimeTrigger(BaseTrigger):
    def __init__(self, run_immediately: bool, min_interval_seconds: int, max_interval_seconds: int):
        self.run_immediately = run_immediately
        self.min_interval_seconds = min_interval_seconds
        self.max_interval_seconds = max_interval_seconds

    def get_next_fire_time(self, previous_fire_time: datetime | None, now: datetime) -> datetime:  # type: ignore
        time_from = previous_fire_time
        if time_from is None:
            time_from = now
            if self.run_immediately:
                return now
        random_seconds = random.randint(self.min_interval_seconds, self.max_interval_seconds)
        random_timedelta = timedelta(seconds=random_seconds)
        next_time = time_from + random_timedelta
        return next_time




def set_reminder(app: CianApplication):
    if app.job_queue is None:
        raise RuntimeError("app.job_queue is None")
    time_from = 40000
    time_to = 60000
    app.job_queue.run_custom(
        check_and_remind_to_run,
        job_kwargs={"trigger": RandomTimeTrigger(True, time_from, time_to)},
        name="reminder",
    )
    
   


def run_bot(token: str, admin: int, storage_path: str, gpt_api_key: str, suno_endpoint: str):
    context_types = ContextTypes(context=PyDoorContext, chat_data=ChatData, bot_data=BotData)
    my_persistence = PicklePersistence(
        filepath=storage_path,
        store_data=PersistenceInput(callback_data=False),
        context_types=context_types,
    )

    async def post_init(app: CianApplication):
        app.bot_data.init(admin=admin, gpt_api_key=gpt_api_key, suno_endpoint=suno_endpoint)

        init_commands_handlers(app)

        for chat_id in app.chat_data.keys():
            await set_bot_commands(app.bot, COMMANDS, BotCommandScopeChat(chat_id))

        set_reminder(app)

    async def post_shutdown(app: CianApplication):
        await app.update_persistence()
        logger.info("Shutdown happened. All data is saved.")

    app: CianApplication = (
        ApplicationBuilder()
        .token(token)
        .post_init(post_init)
        .read_timeout(30)
        .write_timeout(30)
        .context_types(context_types)
        .persistence(my_persistence)
        .post_shutdown(post_shutdown)
        .concurrent_updates(True)
        .build()
    )
    app.post_init
    app.add_error_handler(error_handler)
    app.run_polling(stop_signals=[signal.SIGINT])
