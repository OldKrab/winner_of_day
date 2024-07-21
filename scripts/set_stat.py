import pickle
import sys
from time import sleep
from typing import Any, Dict

from winner_of_day.bot.data import ChatData, Winner

class MigrateUnpickeler(pickle.Unpickler):
    def find_class(self, module_name: str, global_name: str) -> Any:
        if module_name.startswith("pydoor"):
            module_name = module_name.replace("pydoor", "winner_of_day", 1)
            if global_name == "Pidor":
                global_name = "Winner"
        print(f"trying find {global_name} in module {module_name}")
        return super().find_class(module_name, global_name)

def load_storage(storage_path: str) -> Any:
    with open(storage_path, "rb") as file:
        try:
            return MigrateUnpickeler(file).load()
        except EOFError:
            return {}


def save_to_storage(storage_path, active_chats):
    with open(storage_path, "wb") as file:
        pickle.dump(active_chats, file)


storage_path = sys.argv[1]
new_storage_path = sys.argv[2]

storage = load_storage(storage_path)


for chat_data in storage["chat_data"].values():
    chat_data: ChatData
    chat_data.winner_of_day = chat_data.pidor_of_day
    del chat_data.pidor_of_day
    if(hasattr(chat_data, "pidor_msg")):
        chat_data.winner_msg = chat_data.pidor_msg
        del chat_data.pidor_msg
    else:
        chat_data.winner_msg = ""
    chat_data.winner_title = ""
    for winner in chat_data.registered_users.values():
        winner: Winner
        winner.titles = {}
        winner.stat = 0
print(storage)
save_to_storage(new_storage_path, storage)
