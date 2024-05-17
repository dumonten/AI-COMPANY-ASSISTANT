import json
import os

from loguru import logger
from openai import AsyncOpenAI

from assistant import Assistant
from models import CompanyModel
from repositories import CompanyRepository
from utils import Strings
from utils.functions import generate_uuid

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
        # Если нет company_url
        if company_url == None:
            if assistant_id is not None and assistant_id in cls._assistants:
                return cls._assistants[company_data.assistant_id]

        # В данном блоке идет попытка получения данных о компании из БД
        try:
            # Получение по url объекта company_data
            company_data: CompanyModel = await CompanyRepository.get_by_company_url(
                company_url=company_url
            )

            # Если такой компании не было в бд, то ее нужно сохранить
            if company_data == None:
                await CompanyRepository.insert(
                    company_name=company_name, company_url=company_url
                )
                company_data = CompanyModel(
                    company_name=company_name, company_url=company_url
                )
            else:
                # Обновление названия компании, если оно предоставлено и длиннее одного символа
                await CompanyRepository.update_by_info(
                    company_data.id, {"company_name": company_name}
                )
                company_data.company_name = company_name
        except Exception as e:
            raise Exception(
                f"Error occured while accessing to company ({company_name}) data: {e}."
            )

        # Проверка наличия ID помощника в данной компании
        if (
            company_data.assistant_id is not None
            and company_data.assistant_id in cls._assistants
        ):
            return cls._assistants[company_data.assistant_id]

        # Создание нового помощника, если не найден

        # Обновление "сырых" данных сайта
        raw_data = company_data.web_site_raw_data
        if raw_data == None:
            raw_data, search_urls = await SearchService.get_content_from_urls(
                [company_url]
            )
            if len(raw_data) == 0:
                raise Exception(
                    f"Error occured while getting info from company ({company_name}) data: {e}."
                )
            company_data.web_site_raw_data = raw_data[0]

        # Обновление "summary" данных сайта
        summary_text = company_data.web_site_summary_data
        if summary_text == None:
            summary_text = company_data.web_site_summary_data = (
                await SearchService.summarize_content(
                    company_url, source_texts=raw_data
                )
            )

        if len(summary_text) == 0:
            raise Exception(
                f"Error occured while summarizing data from company ({company_name}) data: {e}."
            )

        try:
            file_path = f"./temp_files/{company_name}_{generate_uuid()}.txt"

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
        except Exception as e:
            raise Exception(
                f"Error occured while creating assistant for {company_name}: {e}."
            )

        finally:
            os.remove(file_path)

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
