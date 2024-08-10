import asyncio
from datetime import date, datetime
import random
from urllib.error import HTTPError
import urllib.request

from winner_of_day.bot.callbacks.winner import generate_suno_songs, generate_title
from winner_of_day.bot.data import Winner, PyDoorContext
from telegram import Chat, Message, Update, User
from winner_of_day.bot.utils import get_chat
from winner_of_day.logger import get_logger

from winner_of_day.bot.messages_data import (
    ALREADY_REGISTER_MSG,
    ALREADY_UNREGISTER_MSG,
    DEFAULT_WINNER_MSG,
    MESSAGE_CONTEXT_SIZE,
    SELECTING_PRE_MESSAGES,
    REGISTER_MSG,
    REMIND_TO_RUN_MSG,
    UNREGISTER_MSG,
    get_caption_for_winner_video,
    get_random_song_genre,
    get_song_text_message,
    get_titles_stat,
    get_winner_message,
    NO_ONE_REGISTERED_MSG,
    get_win_stat,
    winner_send_msg,
    remind_winner_of_day,
    winner_title_msg,
)


logger = get_logger(__name__)


async def save_message(update: Update, ctx: PyDoorContext) -> None:
    msg = update.effective_message
    user = update.effective_user
    if msg is None or msg.text is None or msg.text.isspace() or user is None:
        return
    if msg.text is not None and msg.text.startswith("/"):
        return
    chat_data = ctx.check_chat_data()
    if user.id not in chat_data.registered_users:
        return

    msg_ids = chat_data.registered_users[user.id].messages_ids
    while len(msg_ids) > MESSAGE_CONTEXT_SIZE:
        msg_ids.pop(0)
    msg_ids.append(msg.id)


async def register_cmd(update: Update, ctx: PyDoorContext) -> None:
    user = update.effective_user
    chat = get_chat(update)
    chat_data = ctx.check_chat_data()
    if user is None:
        return
    if user.id in chat_data.registered_users:
        await chat.send_message(ALREADY_REGISTER_MSG)
        return
    logger.info(f"User {user.name} with id {user.id} registered")
    chat_data.registered_users[user.id] = Winner(0, [], {})
    await chat.send_message(REGISTER_MSG)


async def unregister_cmd(update: Update, ctx: PyDoorContext) -> None:
    user = update.effective_user
    chat = get_chat(update)
    chat_data = ctx.check_chat_data()
    if user is None:
        return
    if user.id not in chat_data.registered_users:
        await chat.send_message(ALREADY_UNREGISTER_MSG)
        return
    logger.info(f"User {user.name} with id {user.id} unregistered in chat {chat.id}")
    del chat_data.registered_users[user.id]
    await chat.send_message(UNREGISTER_MSG)


async def reset_cmd(update: Update, ctx: PyDoorContext) -> None:
    chat = get_chat(update)
    user = update.effective_user
    if user is None or user.id != ctx.bot_data.admin:
        await chat.send_message("Иш чего захотел")
        return
    ctx.check_chat_data().last_day = date.min

async def regenerate_song_cmd(update: Update, ctx: PyDoorContext) -> None:
    chat = get_chat(update)
    user = update.effective_user
    chat_data = ctx.check_chat_data()
    if user is None or user.id != ctx.bot_data.admin:
        await chat.send_message("Иш чего захотел")
        return
    cur_day = datetime.now().date()
    if cur_day != chat_data.last_day:
        await chat.send_message("Сегодня победителя еще нет")
        return

    await chat.send_message("Ща будет...")
    winner_user = (await chat.get_member(chat_data.winner_of_day)).user
    await generate_and_send_song(
        winner_user, cur_day, chat_data.winner_msg, chat_data.winner_title, chat, ctx
    )

async def regenerate_title_cmd(update: Update, ctx: PyDoorContext) -> None:
    chat = get_chat(update)
    user = update.effective_user
    chat_data = ctx.check_chat_data()
    if user is None or user.id != ctx.bot_data.admin:
        await chat.send_message("Иш чего захотел")
        return
    cur_day = datetime.now().date()
    if cur_day != chat_data.last_day:
        await chat.send_message("Сегодня победителя еще нет")
        return

    await chat.send_message("Ща будет...")
    winner_user = (await chat.get_member(chat_data.winner_of_day)).user
    winner_title = await generate_title(winner_user, chat_data.winner_msg, ctx)
    await chat.send_message(winner_title_msg(winner_user, winner_title))
    chat_data.registered_users[chat_data.winner_of_day].remove_title(chat_data.winner_title)
    chat_data.registered_users[chat_data.winner_of_day].add_title(winner_title)
    chat_data.winner_title = winner_title


async def generate_and_send_song(
    winner_user: User, cur_day: date, winner_msg: str, title: str, chat: Chat, ctx: PyDoorContext
):
    async def load_video(url: str, path: str):
        while True:
            try:
                urllib.request.urlretrieve(url, path)
                break
            except HTTPError as e:
                logger.error(f"got error, try again: {e}")
                await asyncio.sleep(1)


    genre = get_random_song_genre()
    song_text = await ctx.bot_data.gpt.generate_song(winner_user.full_name, genre, winner_msg, title)
    await chat.send_message(get_song_text_message(song_text), parse_mode="MarkdownV2") 
    
    songs = await generate_suno_songs(song_text, genre, winner_user, cur_day, winner_msg, title, ctx)
    async for song in songs:
        logger.info(f"loading file from url '{song.video_url}'")
        await load_video(song.video_url, "temp.mp4")
        await chat.send_video("temp.mp4", caption=get_caption_for_winner_video(title))


async def person_of_day_cmd(update: Update, ctx: PyDoorContext) -> None:
    def get_message_text(msg: Message) -> str:
        text = msg.text
        if text is None:
            return DEFAULT_WINNER_MSG
        return text

    chat = get_chat(update)
    chat_data = ctx.check_chat_data()

    # check if no reg users
    if len(chat_data.registered_users) == 0:
        await chat.send_message(NO_ONE_REGISTERED_MSG)
        return

    cur_day = datetime.now().date()
    # check if today already run
    if chat_data.last_day == cur_day:
        if chat_data.winner_of_day == -1:
            return
        cur_winner = (await chat.get_member(chat_data.winner_of_day)).user
        await chat.send_message(remind_winner_of_day(cur_winner, chat_data.winner_title))
        return
    chat_data.last_day = cur_day
    chat_data.winner_of_day = -1

    # send pre messages
    for i in range(0, len(SELECTING_PRE_MESSAGES)):
        await chat.send_message(random.choice(SELECTING_PRE_MESSAGES[i]))
        await asyncio.sleep(1)

    # select winner
    winner_user_id = chat_data.get_random_registered_user_id()
    winner_user = (await chat.get_member(winner_user_id)).user

    # send winner message
    winner_messages_ids = chat_data.registered_users[winner_user_id].messages_ids
    await chat.send_message(get_winner_message(winner_user))
    if len(winner_messages_ids) != 0:
        await asyncio.sleep(0.5)
        await chat.send_message(winner_send_msg(winner_user))
        msg_id = random.choice(winner_messages_ids)
        winner_msg = get_message_text(await chat.forward_to(chat.id, msg_id))
    else:
        winner_msg = DEFAULT_WINNER_MSG

    # select title
    winner_title = await generate_title(winner_user, winner_msg, ctx)
    await chat.send_message(winner_title_msg(winner_user, winner_title))

    # save values
    chat_data.winner_title = winner_title
    chat_data.winner_of_day = winner_user_id
    chat_data.winner_msg = winner_msg
    chat_data.registered_users[winner_user_id].stat += 1
    chat_data.registered_users[winner_user_id].add_title(winner_title)

    # send song
    await generate_and_send_song(winner_user, cur_day, winner_msg, winner_title, chat, ctx)


async def win_stat_cmd(update: Update, ctx: PyDoorContext) -> None:
    chat = get_chat(update)
    chat_data = ctx.check_chat_data()
    # check if no reg users
    if len(chat_data.registered_users) == 0:
        await chat.send_message(NO_ONE_REGISTERED_MSG)
        return

    winner_stat = {
        (await chat.get_member(user_id)).user: user.stat
        for user_id, user in chat_data.registered_users.items()
    }
    await chat.send_message(get_win_stat(winner_stat))


async def check_and_remind_to_run(ctx: PyDoorContext) -> None:
    cur_day = datetime.now().date()
    bot = ctx.bot
    for chat_id, chat_data in ctx.application.chat_data.items():
        if len(chat_data.registered_users) > 0 and chat_data.last_day != cur_day:
            await bot.send_message(chat_id, REMIND_TO_RUN_MSG)



async def title_stat_cmd(update: Update, ctx: PyDoorContext) -> None:
    chat = get_chat(update)
    chat_data = ctx.check_chat_data()
    # check if no reg users
    if len(chat_data.registered_users) == 0:
        await chat.send_message(NO_ONE_REGISTERED_MSG)
        return

    title_stat = {
        (await chat.get_member(user_id)).user: user.titles
        for user_id, user in chat_data.registered_users.items()
    }
    await chat.send_message(get_titles_stat(title_stat))

