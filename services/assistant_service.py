import json
import os

from loguru import logger
from openai import AsyncOpenAI

from repositories import UserRepository
from utils import Strings


class AssistantService:
    """
    A class for interacting with an AI assistant using an OpenAI client and a configuration.
    """

    class AssistantServiceVectorStorage:
        """
        A class for managing vector storage related to an AI assistant's tasks.
        This includes creating vector stores, uploading files, and updating the assistant's tool resources.
        """

        def __init__(self):
            """
            Initializes the vector storage manager with empty or default values.
            """

            self.vector_store = None
            self.file_batch = None
            self.file_paths = []
            self.name = ""
            self.instructions = ""

        async def initialization(self, name, file_paths, instructions):
            """
            Initializes the vector storage manager with specific configurations and uploads files.

            Parameters:
            - name (str): The name of the vector store to create.
            - file_paths (list[str]): A list of file paths to upload to the vector store.
            - instructions (str): Instructions or metadata associated with the vector store.

            Returns:
            None

            Raises:
            - ValueError: If the file batch upload does not complete successfully or if the number of uploaded files does not match the expected count.
            """

            self.name = name
            self.file_paths = file_paths
            self.instructions = instructions

            self.vector_store = (
                await AssistantService.async_client.beta.vector_stores.create(
                    name=self.name
                )
            )

            """
            file_streams = [open(path, "rb") for path in self.file_paths]

            self.file_batch = await AssistantService.async_client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=self.vector_store.id, files=file_streams
            )
            """

            AssistantService.assistant = (
                await AssistantService.async_client.beta.assistants.update(
                    assistant_id=AssistantService.assistant.id,
                    tool_resources={
                        "file_search": {"vector_store_ids": [self.vector_store.id]}
                    },
                )
            )

            """
            if not (
                self.file_batch.status == "completed"
                and self.file_batch.file_counts.completed == len(self.file_paths)
            ):
                raise ValueError(
                    f"Something went wrong when uploading files to vector storage with name: {self.name} in assistant."
                )
            """

    # A dictionary containing configuration options for the speech service, such as the model to use.
    config = {
        "name": "Voice AI Assistant",
        "model": "gpt-3.5-turbo",
        "assistant_instructions": (
            "You should engage in a conversation with the user to understand their personal values, "
            "beliefs, and what they consider important in life. You should ask open-ended questions "
            "to encourage the user to share their thoughts and feelings. The goal is to gather insights "
            "into the user's core values, which could include aspects such as family, career, personal growth, "
            "health, and community. You should listen carefully to the user's responses and use them to identify "
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
                        "Get the key life values of the user."
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

    # An OpenAI client for making requests to the speech service.
    async_client = None

    assistant = None

    vector_storages = []

    @classmethod
    async def initialize(cls, async_client: AsyncOpenAI):
        """
        Initializes the AssistantService with an instance of AsyncOpenAI and creates an assistant.

        Parameters:
        - async_client (AsyncOpenAI): An instance of AsyncOpenAI to use for making requests to the assistant service.

        Returns:
        - None
        """

        cls.async_client = async_client

        cls.assistant = await cls.async_client.beta.assistants.create(
            name=cls.config["name"],
            instructions=cls.config["assistant_instructions"],
            model=cls.config["model"],
            tools=cls.config["tools"],
        )

        try:
            anxiety_storage = cls.AssistantServiceVectorStorage()
            await anxiety_storage.initialization(
                name="Statements about Anxiety",
                file_paths=[".//.//Anxiety.docx"],
                instructions="If the user asks a question on the topic of Anxiety, try to look for the answer in the files.",
            )
            cls.vector_storages.append(anxiety_storage)
        except ValueError as ve:
            logger.info(f"Error: {ve}")

        cls.config["run_instructions"] += "\n".join(
            [vs.instructions for vs in cls.vector_storages]
        )

    @classmethod
    async def create_thread(cls, user_id: int) -> str:
        """
        Creates a new thread for a user or conversation.

        Parameters:
        - user_id (int): A unique identifier for the user or conversation.

        Returns:
        - str: The thread ID.
        """

        thread = await cls.async_client.beta.threads.create()
        return thread.id

    @classmethod
    async def request(cls, user_id: int, thread_id: str, prompt: str) -> str:
        """
        Sends a prompt to the assistant and retrieves the response.

        Parameters:
        - user_id (int): A unique identifier for the user or conversation.
        - prompt (str): The text prompt to send to the assistant.

        Returns:
        - str: The assistant's response as text.

        Raises:
        - Exception: If the run status is not 'completed' or if no assistant message is found.
        """

        if cls.async_client is None:
            raise ValueError(
                "async_client must be initialized before calling speech_to_text."
            )

        user_message = await cls.async_client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=prompt
        )

        run = await cls.async_client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=cls.assistant.id,
            instructions=cls.config["run_instructions"],
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

                run = await cls.async_client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
                )

        if run.status == "completed":
            messages = await cls.async_client.beta.threads.messages.list(
                thread_id=thread_id
            )

            if messages.data and messages.data[0].role == "assistant":
                message_content = messages.data[0].content[0].text
                citations = []
                annotations = message_content.annotations
                for index, annotation in enumerate(annotations):
                    if file_citation := getattr(annotation, "file_citation", None):
                        cited_file = await cls.async_client.files.retrieve(
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

    @classmethod
    async def save_values(cls, user_id: int, key_values: str) -> bool:
        """
        Asynchronously saves or updates user values in the database after validation.

        This class method first validates the provided key_values using a validation service.
        If the validation is successful, it attempts to update the user's values in the database.
        If the user does not exist (indicated by a ValueError), it saves the user's values as a new record.
        The method returns a boolean indicating the success of the validation process.

        Parameters:
        - cls (type): The class that this method is bound to.
        - user_id (int): The unique identifier for the user.
        - key_values (str): The key-value pairs to be saved or updated for the user.

        Returns:
        - bool: True if the validation is successful, False otherwise.
        """

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

    @classmethod
    async def get_sources(cls):
        """
        Retrieves and formats information about all vector storages.

        This method constructs a formatted string detailing each vector storage's name and associated file names.

        Returns:
        - str: A formatted string listing all vector storages and their file names.
        """

        ans = f"There are <b>{len(cls.vector_storages)}</b> vector storages:\n"
        for vs in cls.vector_storages:
            file_names = "\n\t".join(
                [
                    f"'<i>{os.path.basename(file_path)}</i>'"
                    for file_path in vs.file_paths
                ]
            )
            ans += f"name: '<i>{vs.name}</i>'\n\t" + file_names
        return ans

    @classmethod
    async def clear_context(cls, user_id: int):
        """
        Deletes a thread for a user or conversation.

        Parameters:
        - user_id (int): A unique identifier for the user or conversation.

        Returns:
        - None
        """

        if user_id in cls.threads:
            del cls.threads[user_id]
