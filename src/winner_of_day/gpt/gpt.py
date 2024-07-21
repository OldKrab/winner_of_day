from abc import ABC
from typing import Protocol
import openai
import requests

from winner_of_day.bot.messages_data import SYSTEM_SONG_PROMPT, SYSTEM_TITLE_PROMPT, get_song_prompt, get_title_prompt
from winner_of_day.logger import get_logger

logger = get_logger(__name__)

class GPTApiProtocol(Protocol):
    async def send_prompt(self, system_msg:str, user_msg:str, max_tokens:int) -> str: 
        ...


class GPT:
    def __init__(self, api: GPTApiProtocol, fallback_api: GPTApiProtocol):
        self.api = api
        self.fallback_api = fallback_api

    async def generate_song(self, winner: str, genre: str, winner_msg: str, title: str) -> str:
        res = await self._generate_song(winner, genre, winner_msg, title, self.api)
        if len(res) < 100:
            logger.warning(f"Api {self.api} return: {res}")
            return await self._generate_song(winner, genre, winner_msg, title, self.fallback_api)
        return res
    
    async def generate_title_of_day(self, winner: str, winner_msg: str) -> str:
        return await self.api.send_prompt(SYSTEM_TITLE_PROMPT, get_title_prompt(winner, winner_msg), 100)

    
    async def _generate_song(self, winner: str, genre: str, winner_msg: str, title: str, api: GPTApiProtocol) -> str:
        return await api.send_prompt(SYSTEM_SONG_PROMPT, get_song_prompt(winner, genre, winner_msg, title), 1024)


class OpenAIApi(GPTApiProtocol):
    def __init__(self, api_key, model="gpt-4o", base_url="https://api.proxyapi.ru/openai/v1/"):
        self.ai_client = openai.AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.base_model = "gpt-4o-mini"

    async def send_prompt(self, system_msg:str, user_msg:str, max_tokens:int) -> str:
        completion = await self.ai_client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": system_msg,
                },
                {
                    "role": "user",
                    "content": user_msg,
                },
            ],
        )
        answer = completion.choices[0].message.content
        assert answer is not None
        return answer


class ClaudeApi(GPTApiProtocol):
    def __init__(self, api_key, model="claude-3-sonnet-20240229"):
        self.url = "https://api.proxyapi.ru/anthropic/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Anthropic-Version": "2023-06-01",
        }
        self.model = model

    async def send_prompt(self, system_msg:str, user_msg:str, max_tokens:int) -> str:
        data = {
            "model": self.model,
            "system": system_msg,
            "messages": [
                {
                    "role": "user",
                    "content": user_msg,
                },
            ],
            "max_tokens": max_tokens,
        }

        response = requests.post(self.url, headers=self.headers, json=data)
        response.raise_for_status()
        json = response.json()
        if "content" not in json or len(json["content"]) == 0 or "text" not in json["content"][0]:
            raise RuntimeError(f"response from gpt not have text. response: {json}")
        answer = response.json()["content"][0]["text"]
        return answer
        
