import json
import os

from loguru import logger
from openai import AsyncOpenAI

from repositories import UserRepository
from utils import Strings


class AssistantService:
    assistants = []

    @classmethod
    async def get_assistant(cls, url: str):
        assistant = 1
        return assistant
