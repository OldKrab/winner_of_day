from dataclasses import dataclass
from datetime import date

import random
from telegram import Update

from typing import Any, Callable, Coroutine, Optional
from telegram.ext import Application, ExtBot, CallbackContext, BaseHandler, CommandHandler

from winner_of_day.bot.messages_data import DEFAULT_WINNER_MSG
from winner_of_day.gpt.gpt import GPT, OpenAIApi, ClaudeApi
from winner_of_day.suno.api import SunoApi

CallbackType = Callable[[Update, "PyDoorContext"], Coroutine[Any, Any, None]]
ConversationCallbackType = Callable[[Update, "PyDoorContext"], Coroutine[Any, Any, int | None]]


@dataclass(frozen=True)
class Command:
    name: str
    handler: BaseHandler
    desc: str


def get_command(name: str, callback: CallbackType, desc: str) -> Command:
    return Command(name, CommandHandler(name, callback), desc)


@dataclass
class Winner:
    stat: int
    messages_ids: list[int]
    titles: dict[str, int]

    def add_title(self, title):
        if title not in self.titles:
            self.titles[title] = 1
        else:
            self.titles[title] += 1

    def remove_title(self, title):
        if title in self.titles and self.titles[title] > 0:
            self.titles[title] -= 1


class ChatData:
    def __init__(self):
        self.registered_users: dict[int, Winner] = {}
        self.winner_of_day: int = -1
        self.winner_title: str = ""
        self.winner_msg: str = DEFAULT_WINNER_MSG
        self.last_day: date = date.min

    def get_random_registered_user_id(self) -> int:
        stats = [user.stat for user in self.registered_users.values()]
        max_weight = max(stats) * 1.1
        weights = [max_weight - stat + 0.1 for stat in stats]
        return random.choices(list(self.registered_users.keys()), weights=weights, k=1)[0]

    def __repr__(self) -> str:
        return self.__dict__.__str__()


class BotData:
    def __init__(self):
        pass

    def init(self, admin: int, gpt_api_key: str, suno_endpoint: str):
        self.admin = admin
        self.enabled = True
        self.gpt = GPT(OpenAIApi(gpt_api_key, model="gpt-4o"), ClaudeApi(gpt_api_key))
        self.suno = SunoApi(suno_endpoint)

    @dataclass
    class PickleBotData:
        pass

    def __getstate__(self) -> PickleBotData:
        data = BotData.PickleBotData()
        return data

    def __setstate__(self, state: PickleBotData):
        pass


class PyDoorContext(CallbackContext[ExtBot, dict, ChatData, BotData]):
    def __init__(
        self,
        application: Application,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ):
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)

    def check_chat_data(self) -> ChatData:
        if self.chat_data is None:
            raise RuntimeError("chat_data is None")
        return self.chat_data


CianApplication = Application[ExtBot[Any], Any, Any, ChatData, BotData, Any]
