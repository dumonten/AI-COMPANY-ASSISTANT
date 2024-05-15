import json
import os

from loguru import logger
from openai import AsyncOpenAI

from assistant import Assistant
from repositories import UserRepository
from utils import Strings

from .search_service import SearchService


class AssistantService:
    _assistants = []

    @classmethod
    async def get_assistant(cls, company_name: str, company_url: str) -> Assistant:
        summary_data = SearchService.summarize_content(company_url)
        assistant = Assistant()
        await assistant.initialize(
            company_name=company_name, company_url=company_url, data_file_paths=["./"]
        )
        return assistant

    async def create_thread(cls, user_id: int) -> str:
        thread = await cls._async_client.beta.threads.create()
        return thread
