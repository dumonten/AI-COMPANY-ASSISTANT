from typing import Any, Dict, List, Optional

from loguru import logger
from openai import AsyncOpenAI

from config import settings

from .vector_store import VectorStore


class Assistant:
    _base_config = {
        "name": "AiCompanyAssistant",
        "model": "gpt-3.5-turbo",
        "assistant_instructions": """
            В качестве ассистента в компании {company_name},
            вы выполняете роль менеджера чата на нашем веб-сайте {company_url}. 
            Ваша основная задача - обслуживать пользователей, предоставляя им точную информацию 
            о нашей компании и её продуктах/услугах. Вы должны адекватно реагировать на вопросы, 
            связанные с деятельностью компании, и корректно отказываться от обсуждения несвязанных тем. 
            Важно поддерживать позитивный тон разговора, стараясь понять потребности клиента и предлагая ему помощь. 
            Эффективность вашей работы напрямую влияет на впечатление от взаимодействия с компанией и может 
            стать решающим фактором в принятии решения о сотрудничестве.
        """,
        "run_instructions": "",
        "tools": [
            {"type": "file_search"},
        ],
    }

    def __init__(self):
        self._async_client: Optional[AsyncOpenAI] = None
        self._assistant: Optional[Any] = None  
        self._vector_storages: List[VectorStore] = []
        self._config: Dict[str, str] = self._base_config.copy()

        self.id: str = ""
        self.company_name: str = ""
        self.company_url: str = ""

    async def initialize(
        self, company_name: str, company_url: str, data_file_paths: List[str]
    ) -> None:
        self._async_client = settings.async_client
        self.company_name = company_name
        self.company_url = company_url

        self._config["assistant_instructions"].format(
            company_name=self.company_name, company_url=self.company_url
        )

        self._assistant = await self._async_client.beta.assistants.create(
            name=self._config["name"],
            instructions=self._config["assistant_instructions"],
            model=self._config["model"],
            tools=self._config["tools"],
        )

        try:
            store = VectorStore()
            await store.initialization(
                name=f"Данные о компании {self.company_name}.",
                file_paths=data_file_paths,
                instructions="""
                    В случае, если вы не можете дать ответ из своего контекста на запрос пользователя на тему компании,  
                    попробуйте поискать ответ в данных файлах.
                """
            )

            self._vector_storages.append(store)

            self._config["run_instructions"] += "\n".join(
                [vs.instructions for vs in self._vector_storages]
            )
        except ValueError as ve:
            logger.error(f"Error in store initialization in assistant: {ve}")

    async def request(cls, thread_id: str, prompt: str) -> str:
        if cls._async_client is None:
            raise ValueError(
                "async_client must be initialized before calling speech_to_text."
            )

        user_message = await cls._async_client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=prompt
        )

        run = await cls._async_client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=cls._assistant.id,
            instructions=cls._config["run_instructions"],
        )

        if run.status == "requires_action":
            tool_outputs = []
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                """
                 if tool.function.name == "save_values":
                    is_saved = await cls.save_values(
                        user_id=user_id,
                        key_values=", ".join(
                            json.loads(tool.function.arguments)["key_values"]
                        ),
                    )

                    if is_saved:
                        output = Strings.KEY_VALUES_ARE_DEFINED
                    else:
                        output = Strings.KEY_VALUES_ARE_NOT_DEFINED

                    tool_outputs.append(
                        {
                            "tool_call_id": tool.id,
                            "output": output,
                        }
                    )

                """
                run = await cls._async_client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
                )

        if run.status == "completed":
            messages = await cls._async_client.beta.threads.messages.list(
                thread_id=thread_id
            )

            if messages.data and messages.data[0].role == "assistant":
                message_content = messages.data[0].content[0].text
                citations = []
                annotations = message_content.annotations
                for index, annotation in enumerate(annotations):
                    if file_citation := getattr(annotation, "file_citation", None):
                        cited_file = await cls._async_client.files.retrieve(
                            file_citation.file_id
                        )
                        citations.append(cited_file.filename)
                    if index < len(citations):
                        message_content.value = message_content.value.replace(
                            annotation.text, f" [Источник: {citations[index]}]"
                        )
                ans = message_content.value
                return ans
            else:
                raise ValueError("No assistant message found")
        else:
            raise ValueError(f'Run status is not <completed>, it\'s "{run.status}".')




