import os
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from assistant import Assistant
from models import CompanyModel
from repositories import CompanyRepository
from utils.functions import generate_uuid

from .search_service import SearchService


class AssistantService:
    _assistants: Dict[int, Assistant] = {}
    _async_client: Optional[AsyncOpenAI] = None

    @classmethod
    def initialize(cls, async_client: AsyncOpenAI) -> None:
        cls._async_client = async_client

    @classmethod
    async def get_assistant(
        cls, company_name: str, company_url: str, company_id: Optional[int] = None
    ) -> Assistant:

        company_data: Optional[CompanyModel] = None

        if company_url is None:

            if company_id is None:
                raise Exception("Can't generate bot, there are not enough information.")

            company_data = await CompanyRepository.get_by_company_id(
                company_id=company_id
            )

            if company_data is None:
                raise Exception("No assistant with such id.")
        else:
            company_data = await CompanyRepository.get_by_company_url(
                company_url=company_url
            )
            if company_data is None:
                await CompanyRepository.insert(
                    company_name=company_name, company_url=company_url
                )
                company_data = CompanyModel(
                    company_name=company_name, company_url=company_url
                )
            else:
                await CompanyRepository.update_by_info(
                    company_data.id, {"company_name": company_name}
                )
                company_data.company_name = company_name

        if (
            company_data.assistant_id is not None
            and company_data.assistant_id in cls._assistants
        ):
            return cls._assistants[company_data.assistant_id]

        raw_data: Optional[List[str]] = None
        if company_data.web_site_raw_data is None:
            raw_data, _ = await SearchService.get_content_from_urls([company_url])
            if len(raw_data) == 0:
                raise Exception(
                    f"Error occured while getting info from company ({company_name})."
                )

        summary_text: Optional[str] = None
        if company_data.web_site_summary_data is None:
            summary_text = company_data.web_site_summary_data = (
                await SearchService.summarize_content(
                    company_url, source_texts=raw_data
                )
            )
            if len(summary_text) == 0:
                raise Exception(
                    f"Error occured while summarizing data from company ({company_name})."
                )

        try:
            file_path: str = f"./temp_files/{generate_uuid()}.txt"
            with open(file_path, "w+") as file:
                file.write(summary_text)

            assistant = Assistant()
            await assistant.initialize(
                async_client=cls._async_client,
                company_name=company_name,
                company_url=company_url,
                data_file_paths=[file_path],
            )
            cls._assistants[await assistant.get_id()] = assistant
            company_data.assistant_id = await assistant.get_id()

            await CompanyRepository.update_by_company(company_instance=company_data)
        finally:
            os.remove(file_path)

        return assistant

    @classmethod
    async def create_thread(cls, user_id: int) -> str:
        thread: Dict[str, Any] = await cls._async_client.beta.threads.create()
        return thread

    @classmethod
    async def request(
        cls, thread_id: str, prompt: str, assistant_id: int
    ) -> Optional[str]:
        if assistant_id is None or assistant_id not in cls._assistants:
            return None

        assistant = cls._assistants[assistant_id]
        ans: Optional[str] = await assistant.request(thread_id=thread_id, prompt=prompt)
        return ans
