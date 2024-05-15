import json
import os

from loguru import logger
from openai import AsyncOpenAI

from repositories import UserRepository
from utils import Strings

"""
Надо сделать AssistantService -> он будет получать от юзера url по которому нужно создать ассистента 
Далее он создет assistant. У assistant будет файл с конфигурацией. Как класс. Он будет содержать strings 
запросов. То есть полный config и тулы весь набор бойца. 

У самого ассистента будет векторная БД (надо вынести в отдельный класс), которую он будет использовать.
Там будут лежать данные из их веб страниц. 

"""


class Assistant:
    _config = {
        "name": "Voice AI Assistant",
        "model": "gpt-3.5-turbo",
        "assistant_instructions": (
            "You should {URL} in a conversation with the user to understand their personal values, "
            "beliefs, and what they {name_comapny} important in life. You should ask open-ended questions "
            "to encourage the user to share their thoughts and feelings. The goal is to gather insights "
            "into the user's core values, which  include aspects such as family, career, personal growth, "
            "health, and {}. You should listen carefully to the user's responses and use them to identify "
            "patterns or recurring themes that reflect the user's life values."
        ),
        "run_instructions": "",
        "tools": [
            {"type": "file_search"},
            {
                "type": "function",
                "function": {
                    "name": "save_values",
                    "description": (
                        "Get the key {name_comapny} values of the user."
                        "After you determine the basic values of the user, call this function."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key_values": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": (
                                    "An array of strings representing the user's identified key life values."
                                    "Each string in the array should be a single value that the user has "
                                    "identified as important to their life. Record the values in English."
                                ),
                            }
                        },
                        "required": ["key_values"],
                    },
                },
            },
        ],
    }

    def __init__(self):
        self._async_client = None
        self._assistant = None
        self._vector_storages = []

        self.name_company = ""
        self.url = ""


"""
    async def initialize(cls, async_client: AsyncOpenAI):
        cls._async_client = async_client

        cls._assistant = await cls._async_client.beta.assistants.create(
            name=cls._config["name"],
            instructions=cls._config["assistant_instructions"],
            model=cls._config["model"],
            tools=cls._config["tools"],
        )

        try:
            anxiety_storage = cls.AssistantServiceVectorStorage()
            await anxiety_storage.initialization(
                name="Statements about Anxiety",
                file_paths=[".//.//Anxiety.docx"],
                instructions="If the user asks a question on the topic of Anxiety, try to look for the answer in the files.",
            )
            cls._vector_storages.append(anxiety_storage)
        except ValueError as ve:
            logger.info(f"Error: {ve}")

        cls._config["run_instructions"] += "\n".join(
            [vs.instructions for vs in cls._vector_storages]
        )

    async def create_thread(cls, user_id: int) -> str:
        thread = await cls._async_client.beta.threads.create()
        return thread.id

    async def request(cls, user_id: int, thread_id: str, prompt: str) -> str:
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

    async def save_values(cls, user_id: int, key_values: str) -> bool:
    
        AnalyticsService.track_event(
            user_id=user_id, event_type=EventType.KeyValueRevealed
        )

        logger.info(
            f"Detected user key values: user_id[{user_id}] key_values[{key_values}]"
        )

        is_correct = await ValidateService.validate_key_values(key_values)

        if is_correct:
            user_repo = UserRepository()
            try:
                await user_repo.update_user_values(
                    user_id=user_id, key_values=key_values
                )
                logger.info(f"Key values for user_id[{user_id}] updated successfully")
            except ValueError as ve:
                try:
                    # If the user does not exist, save the user's values as a new record
                    await user_repo.save_user_values(
                        user_id=user_id, key_values=key_values
                    )
                    logger.info(f"Key values for user_id[{user_id}] saved successfully")
                except ValueError as ve:
                    logger.info(
                        f"Error in database while saving  user_id[{user_id}] key_vaues: {ve}"
                    )
        return is_correct
    """
