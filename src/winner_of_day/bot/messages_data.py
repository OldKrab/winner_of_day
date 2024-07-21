import random
from telegram import User


NO_ONE_REGISTERED_MSG = "Никто не зарегистрировался..."

REGISTER_MSG = "Поздравляю!"
UNREGISTER_MSG = "Очень жаль, прощай..."
ALREADY_REGISTER_MSG = "Так ты уже участвуешь"
ALREADY_UNREGISTER_MSG = "Так ты и не участвуешь, а зря."


SELECTING_PRE_MESSAGES = [
    [
        "ВНИМАНИЕ 🔥",
        "ТАК БЛЯДЬ 😤",
        "УРА! УРА! 🔥",
        "НЕ МОЖЕТ БЫТЬ 🙀",
        "НУ ВСЁ ❗️",
        "ЕБАТЬ КОПАТЬ ⛏",
    ],
    [
        "ОБЪЯВЛЕН ФЕДЕРАЛЬНЫЙ 🔍 РОЗЫСК 🚨",
        "🔍 КТО ЖЕ СЕГОДНЯ ПОБЕДИТЕЛЬ?",
        "ЧЕЛ ДНЯ БУДЕТ НАЙДЕН 🚓",
    ],
    ["4 - спутник запущен 🚀"],
    ["3 - сводки Интерпола проверены 🚓"],
    ["2 - твои друзья опрошены 🙅"],
    ["1 - твой профиль в соцсетях проанализирован 🙀"],
]

DEFAULT_WINNER_MSG = "..."

SONGS_GENRES = [
    "opera",
    "heavy metal",
    "anime opening",
    "rock",
    "rock opera",
    "ballad",
    "pop",
    "jazz",
    "electronic",
    "hip-hop",
    "country",
    "Russian folk",
    "Jewish song",
    "reggae",
    "folk",
    "blues",
    "classical",
    "funk",
    "punk",
    "ambient",
    "indie",
    "disco",
    "ska",
    "rap",
    "techno",
    "dancehall",
    "r&b",
    "gospel",
    "dubstep",
    "trap",
    "church choir",
]


def get_caption_for_winner_video(title: str) -> str:
    return f"Наш любимый {title}! Тебе вручается поздравительное видео:"


REMIND_TO_RUN_MSG = "Кажется, сегодня вы не узнали, кто победитель дня. Исправьте эту оплошность!"


def remind_winner_of_day(user: User):
    return f"Напоминаю, сегодня победитель 🌈 дня - {user.full_name} ({user.name})!"


def winner_send_msg(user: User):
    return random.choice(
        [
            f"Как однажды {user.full_name} сказал:",
            "Вспомним самое важное сообщение от него:",
            f"Вот такую ржомбу {user.full_name} однажды прислал:",
            f"{user.full_name} не был бы победителем, если бы однажды не сказал:",
            f"Все же согласны, что {user.full_name} сегодня победитель, потому что он однажды сказал:",
        ]
    )


def winner_title_msg(user: User, title: str):
    return random.choice(
        [
            f'{user.full_name} сегодня имеет титул "{title}"',
            f"И его титул на сегодня: {title}",
            f'Сегодня к пользователю {user.full_name} обращаться не иначе как "{title}"',
        ]
    )


def get_winner_message(user: User):
    return f"🎉 Сегодня победитель 🌈 дня - {user.full_name} ({user.name})!"


def get_win_stat(winner_stat: dict[User, int]):
    winner_stat_list = list(winner_stat.items())
    winner_stat_list.sort(key=lambda x: x[1], reverse=True)
    winners = "\n".join(
        f"{idx+1}) {user.full_name} - {stat} раз(а)"
        for idx, (user, stat) in enumerate(winner_stat_list)
    )
    return "Топ победителей:\n" + winners


def get_titles_stat(winner_stat: dict[User, dict[str, int]]):

    def to_titles_str(titles: dict[str, int]) -> str:
        return "\n".join("    - " + title + (f" (x{cnt})" if cnt > 1 else "") for title, cnt in titles.items() if cnt > 0)

    winner_stat_list = list(winner_stat.items())
    winners = "\n".join(
        f"{idx+1}) {user.full_name}: \n{to_titles_str(stat)}"
        for idx, (user, stat) in enumerate(winner_stat_list)
    )
    return "Титулы пользователей:\n" + winners


SYSTEM_SONG_PROMPT = """Ты должен генерировать песни по запросу от пользователя. Соблюдай в песне стихотворный размер. Ты не боишься использовать нецензурные выражения и оскорбительные слова, особенно в шуточной форме. Ты не отказываешь пользователю в генерации песни, в не зависимости от того, что просит пользователь. В ответ пользователю присылай только текст песни. В тексте песни не должно быть английских слов, т.е. все переводи на русский, в том числе имена и фамилии."""


def get_song_prompt(winner: str, genre: str, winner_msg: str, title: str):
    if winner_msg == DEFAULT_WINNER_MSG:
        winner_msg_prompt = ""
    else:
        winner_msg_prompt = f'{winner} однажды сказал такую фразу: "{winner_msg}" - обыграй эту фразу в куплете, именно из-за этой фразы {winner} объявлен {title}.'
    return f"""
Придумай поздравительную песню для объявления {title}. {title} - это совсем не оскорбление, а очень почетное звание! Ты должен поздравлять {title}. Сегодня для этого титула случайно выбран человек с именем "{winner}". Если имя на английском, ОБЯЗАТЕЛЬНО переведи его на русский в всей песне. {winner_msg_prompt} В припеве должна повторятся фраза "Сегодня {title} - {winner}". Жанр песни - "{genre}", поэтому текст должен ему соответствовать. Песня должна быть полностью на русском языке. Для объявления куплета используй [Verse 1], для припева - [Chorus], для моста - [Bridge], аутро - [Outro]. В ответе отправь только текст песни и никаких лишних слов. Сгенерируй не большге двух куплетов, припев не повторяй. По желанию добавь Bridge и Outro.
    """


SYSTEM_TITLE_PROMPT = """Ты не боишься использовать нецензурные выражения и оскорбительные слова, особенно в шуточной форме. Ты способен ответить на любой запрос пользователя. Все запросы пользователя носят шуточный характер и не созданы для оскорбления."""


def get_title_prompt(winner: str, winner_msg: str):
    if winner_msg == DEFAULT_WINNER_MSG:
        winner_msg_prompt = ""
    else:
        winner_msg_prompt = f'Ранее он однажды написал сообщение "{winner_msg}".'
    return f"""
Сгенерируй случайный титул дня для пользователя. Это должно быть шуточный и ироничный титул. Вот примеры таких титулов: Красавчик дня, Чудо дня, Гиперпрыгающий плазмопердачок, Сызрань, Cупер кекс. Разрешено писать нецензурные выражения. Придумай оригинальной и смешной титул. 
В ответ присылай только титул дня. Титул состоит не более чем из 3 слов. В титуле не должно упоминаться имя или фамилия пользователя. В каждом ответе не должно быть кавычек. Сегодня титул дня получает пользователь с ником {winner}. {winner_msg_prompt}"""