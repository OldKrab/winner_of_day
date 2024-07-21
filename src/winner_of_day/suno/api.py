import asyncio
from dataclasses import dataclass
import requests

from winner_of_day.logger import get_logger

logger = get_logger(__name__)


def _get_json_headers() -> dict[str, str]:
    return {"accept": "application/json", "Content-Type": "application/json"}


@dataclass
class SongInfo:
    id: str
    audio_url: str
    video_url: str
    status: str


class SunoApi:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def custom_generate(self, prompt: str, tags: str, title: str) -> list[SongInfo]:
        url = self.endpoint + "/api/custom_generate"
        headers = _get_json_headers()
        data = {
            "prompt": prompt,
            "tags": tags,
            "title": title,
            "make_instrumental": False,
            "wait_audio": False,
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        results = response.json()
        return [
            SongInfo(
                id=result["id"],
                audio_url=result["audio_url"],
                video_url=result["video_url"],
                status=result["status"],
            )
            for result in results
        ]

    def get(self, ids: str) -> list[SongInfo]:
        url = self.endpoint + "/api/get"
        headers = _get_json_headers()
        params = {"ids": ids}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        results = response.json()
        return [
            SongInfo(
                id=result["id"],
                audio_url=result["audio_url"],
                video_url=result["video_url"],
                status=result["status"],
            )
            for result in results
        ]

    async def wait_for_status_complete(self, id: str, interval=10) -> SongInfo:
        while True:
            res = self.get(id)[0]
            logger.info(f"Current status of song with id {id}: {res.status}")
            if res.status == "complete":
                logger.info(f"got song {res}")
                return res
            await asyncio.sleep(interval)
