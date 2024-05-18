from typing import List

from loguru import logger
from openai import AsyncOpenAI

from .vector_store import VectorStore


class Assistant:
    """
    Assistant, is designed to manage interactions with an AI assistant,
    including initializing the assistant with company-specific configurations,
    sending requests to the assistant, and processing responses.
    """

    # A dictionary containing configuration options for the speech service, such as the model to use.
    _base_config = {
        "name": "AiCompanyAssistant",
        "model": "gpt-4o",
        "assistant_instructions": """ 
            Ты выступаешь в качестве ассистента в компании {company_name},
            и выполняешь роль менеджера чата на веб-сайте {company_url}, принадлежащем этой компании. 
            Твоя основная задача - обслуживать пользователей, предоставляя им точную информацию 
            о компании и её продуктах/услугах. Ты должен адекватно реагировать на вопросы, 
            связанные с деятельностью компании, и корректно отказываться от обсуждения несвязанных тем. 
            Важно поддерживать позитивный тон разговора, стараясь понять потребности клиента и предлагая ему помощь. 
            Эффективность твоей работы напрямую влияет на впечатление от взаимодействия с компанией и может 
            стать решающим фактором в принятии решения о сотрудничестве.
        """,
        "vector_store_name": """
            Данные о компании {company_name}.
        """,
        "vector_store_instructions": """
            В случае, если вы не можете дать ответ из своего контекста на запрос пользователя на тему компании,  
            попробуйте поискать ответ в данных файлах.
        """,
        "run_instructions": """Твое имя - Оксана. Ты представляешь компанию {company_name}. 
                               Ты обслуживаешь пользователей на сайте компании {company_url}.
                               Отказывайся от обсуждения несвязанных тем. 
                               Отвечай только на вопросы по поводу твоей компании.
                               """,
        "tools": [
            {"type": "file_search"},
        ],
    }

    def __init__(self) -> None:
        """
        Initializes the Assistant object with default configurations.

        Attributes:
        - _async_client: An instance of AsyncOpenAI client for making API calls.
        - _assistant: The OpenAI assistant associated with this manager.
        - _vector_storages: A list to hold instances of VectorStore for storing vectors.
        - _config: A configuration dictionary with settings for the assistant and vector stores.
        - company_name: The name of the company this assistant is managed for.
        - company_url: The URL of the company this assistant is managed for.

        Returns:
        None
        """

        self._async_client = None
        self._assistant = None
        self._vector_storages = []
        self._config = self._base_config.copy()

        self.company_name = ""
        self.company_url = ""

    async def initialize(
        self,
        async_client: AsyncOpenAI,
        company_name: str,
        company_url: str,
        data_file_paths: List[str],
    ) -> None:
        """
        Initializes the Assistant with the given company details and sets up the assistant and vector storages.

        Parameters:
        - async_client (AsyncOpenAI): The asynchronous OpenAI client for API interactions.
        - company_name (str): The name of the company.
        - company_url (str): The URL of the company.
        - data_file_paths (List[str]): Paths to data files used for initializing vector stores.

        Returns:
        None
        """

        self._async_client = async_client
        self.company_name = company_name
        self.company_url = company_url

        # Configuring instructions with company-specific details
        self._config["assistant_instructions"] = self._config[
            "assistant_instructions"
        ].format(company_name=self.company_name, company_url=self.company_url)

        self._config["run_instructions"] = self._config["run_instructions"].format(
            company_name=self.company_name, company_url=self.company_url
        )

        # Creating the assistant with configured instructions
        self._assistant = await self._async_client.beta.assistants.create(
            name=self._config["name"],
            instructions=self._config["assistant_instructions"],
            model=self._config["model"],
            tools=self._config["tools"],
        )

        # Initializing vector stores and associating them with the assistant
        try:
            store = VectorStore()
            await store.initialization(
                name=self._config["vector_store_name"].format(
                    company_name=self.company_name
                ),
                file_paths=data_file_paths,
                instructions=self._config["vector_store_instructions"],
                async_client=self._async_client,
            )

            self._assistant = await self._async_client.beta.assistants.update(
                assistant_id=self._assistant.id,
                tool_resources={
                    "file_search": {"vector_store_ids": [store.vector_store.id]}
                },
            )

            self._vector_storages.append(store)

            # Updating run instructions to include vector store instructions
            self._config["run_instructions"] += "\n".join(
                [vs.instructions for vs in self._vector_storages]
            )
        except Exception as e:
            logger.error(f"Error in store initialization in assistant: {e}.")

    async def request(
        self,
        thread_id: str,
        prompt: str,
    ) -> str:
        """
        Sends a request to the assistant and returns the response.

        Parameters:
        - thread_id (str): The ID of the conversation thread.
        - prompt (str): The text prompt to send to the assistant.

        Returns:
        str: The assistant's response to the prompt.
        """

        if self._async_client is None:
            raise ValueError(
                "async_client must be initialized before calling speech_to_text."
            )

        # Sending the prompt to the assistant
        user_message = await self._async_client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=prompt
        )

        # Running the assistant with the configured instructions
        run = await self._async_client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=self._assistant.id,
            instructions=self._config["run_instructions"],
        )

        # Handling required actions and polling for completion
        if run.status == "requires_action":
            tool_outputs = []
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                run = await self._async_client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
                )

        # Processing the completed run's messages
        if run.status == "completed":
            messages = await self._async_client.beta.threads.messages.list(
                thread_id=thread_id
            )

            if messages.data and messages.data[0].role == "assistant":
                message_content = messages.data[0].content[0].text
                citations = []
                annotations = message_content.annotations
                for index, annotation in enumerate(annotations):
                    if file_citation := getattr(annotation, "file_citation", None):
                        cited_file: dict = await self._async_client.files.retrieve(
                            file_citation.file_id
                        )
                        citations.append(cited_file.filename)
                    if index < len(citations):
                        message_content.value = message_content.value.replace(
                            annotation.text, ""
                        )
                ans = message_content.value
                return ans
            else:
                raise Exception("No assistant message found.")
        else:
            raise Exception(f'Run status is not <completed>, it\'s "{run["status"]}".')

    async def get_id(self) -> str:
        """
        Retrieves the ID of the assistant.

        Returns:
        str: The ID of the assistant.
        """

        return self._assistant.id
