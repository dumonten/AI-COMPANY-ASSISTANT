import json
import os

from loguru import logger
from openai import AsyncOpenAI

from assistant import Assistant
from repositories import CompanyRepository
from utils import Strings

from .search_service import SearchService


class AssistantService:
    _assistants = {}
    _async_client = None

    @classmethod
    def initialize(cls, async_client: AsyncOpenAI):
        cls._async_client = async_client

    @classmethod
    async def get_assistant(
        cls, assistant_id: str, company_name: str, company_url: str
    ) -> Assistant:
        file_path = "./summary.txt"

        """
        if assistant_id in cls._assistants:
            return cls._assistants[assistant_id]

        summary_text, source_urls = SearchService.summarize_content(company_url)

        with open(file_path, "w") as file:
            file.write(summary_text)    
        """

        assistant = Assistant()
        await assistant.initialize(
            async_client=cls._async_client,
            company_name=company_name,
            company_url=company_url,
            data_file_paths=[file_path],
        )
        cls._assistants[await assistant.get_id()] = assistant

        # os.remove(file_path)

        return assistant

    @classmethod
    async def create_thread(cls, user_id: int) -> str:
        thread = await cls._async_client.beta.threads.create()
        return thread

    @classmethod
    async def request(cls, thread_id: str, prompt: str, assistant_id):
        if (assistant_id is None) or (assistant_id not in cls._assistants):
            return

        assistant = cls._assistants[assistant_id]
        ans = await assistant.request(thread_id=thread_id, prompt=prompt)
        return ans
