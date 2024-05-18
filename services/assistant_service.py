import os
import time
from typing import Optional

from openai import AsyncOpenAI

from assistant import Assistant
from repositories import CompanyRepository
from utils.functions import generate_uuid

from .search_service import SearchService


class AssistantService:
    """
    AssistantService manages the lifecycle of assistants associated with companies,
    facilitating their creation, retrieval, and interaction.
    """

    # A dictionary mapping assistant IDs to Assistant objects.
    _assistants = {}
    # An OpenAI client for making requests to the speech service.
    _async_client = None

    @classmethod
    def initialize(cls, async_client: AsyncOpenAI) -> None:
        """
        Initializes the AssistantService with an instance of AsyncOpenAI for making API calls.

        Parameters:
        - async_client (AsyncOpenAI): The asynchronous OpenAI client for API interactions.

        Returns:
        None
        """

        cls._async_client = async_client

    @classmethod
    async def get_assistant(
        cls, company_name: str, company_url: str, company_id: Optional[int] = None
    ) -> Assistant:
        """
        Retrieves or creates an assistant associated with a company based on the company's name or URL.

        This method first attempts to retrieve an existing assistant for the company. If none exists, it creates a new one.

        Parameters:
        - company_name (str): The name of the company.
        - company_url (str): The URL of the company.
        - company_id (Optional[int], optional): The ID of the company. Defaults to None.

        Returns:
        Assistant: An instance of Assistant associated with the company.

        Raises:
        - Exception: If insufficient information is provided to generate an assistant.
        """

        company_repository = CompanyRepository()
        company_data = None

        if company_url is None:
            if company_id is None:
                raise Exception("Can't generate bot, there are not enough information.")

            company_data = await company_repository.get_by_company_id(
                company_id=company_id
            )

            if company_data is None:
                raise Exception("No assistant with such id.")
        else:
            company_data = await company_repository.get_by_company_url(
                company_url=company_url
            )

            if company_data is None:
                company_data = await company_repository.insert(
                    {"company_name": company_name, "company_url": company_url}
                )
        if (
            company_data.assistant_id is not None
            and company_data.assistant_id in cls._assistants
        ):
            return cls._assistants[company_data.assistant_id]

        raw_data = None
        if company_data.web_site_raw_data is None:
            company_data.web_site_summary_data = None
            raw_data, _ = await SearchService.get_content_from_urls([company_url])

            if raw_data is None or len(raw_data) == 0:
                time.sleep(90)
                raw_data, _ = await SearchService.get_content_from_urls([company_url])
                if raw_data is None or len(raw_data) == 0:
                    raise Exception(
                        f"Error occured while getting info from company ({company_name})."
                    )
            company_data.web_site_raw_data = raw_data[0]

            await company_repository.update_by_info(
                company_data.id,
                {"web_site_raw_data": str(company_data.web_site_raw_data)},
            )
        else:
            raw_data = [company_data.web_site_raw_data]

        summary_text = None
        if company_data.web_site_summary_data is None:
            summary_text = company_data.web_site_summary_data = (
                await SearchService.summarize_content(
                    company_url, source_texts=raw_data
                )
            )
            if summary_text is None or len(summary_text) == 0:
                raise Exception(
                    f"Error occured while summarizing data from company ({company_name})."
                )
            await company_repository.update_by_info(
                company_data.id,
                {"web_site_summary_data": str(company_data.web_site_summary_data)},
            )
        else:
            summary_text = company_data.web_site_summary_data

        try:
            file_path = f"./temp_files/{generate_uuid()}.txt"
            with open(file_path, "w+") as file:
                file.write(summary_text)

            assistant = Assistant()
            await assistant.initialize(
                async_client=cls._async_client,
                company_name=company_data.company_name,
                company_url=company_data.company_url,
                data_file_paths=[file_path],
            )
            cls._assistants[await assistant.get_id()] = assistant
            company_data.assistant_id = await assistant.get_id()

            await company_repository.update_by_info(
                company_data.id,
                company_data.to_dict(),
            )
        finally:
            os.remove(file_path)

        return assistant

    @classmethod
    async def create_thread(cls, user_id: int) -> str:
        """
        Creates a new thread for user interaction with the assistant.

        Parameters:
        - user_id (int): The ID of the user initiating the thread.

        Returns:
        str: The ID of the newly created thread.
        """

        thread = await cls._async_client.beta.threads.create()
        return thread

    @classmethod
    async def request(
        cls, thread_id: str, prompt: str, assistant_id: int
    ) -> Optional[str]:
        """
        Sends a request to the specified assistant within a given thread and returns the assistant's response.

        Parameters:
        - thread_id (str): The ID of the thread where the request should be sent.
        - prompt (str): The text prompt to send to the assistant.
        - assistant_id (int): The ID of the assistant to whom the request should be sent.

        Returns:
        Optional[str]: The assistant's response to the prompt, or None if the assistant ID is invalid.
        """

        if assistant_id is None or assistant_id not in cls._assistants:
            return None

        assistant = cls._assistants[assistant_id]
        ans = await assistant.request(thread_id=thread_id, prompt=prompt)
        return ans
