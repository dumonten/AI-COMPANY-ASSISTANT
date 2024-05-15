from loguru import logger
from openai import AsyncOpenAI


class VectorStore:
    def __init__(self):
        self.name = ""
        self.instructions = ""
        self.vector_store = None
        self.file_batch = None
        self.file_paths = []
        self._async_client = None

    async def initialization(self, name, file_paths, instructions, async_client):
        self.name = name
        self.file_paths = file_paths
        self.instructions = instructions
        self._async_client = async_client

        self.vector_store = await self._async_client.beta.vector_stores.create(
            name=self.name
        )

        file_streams = [open(path, "rb") for path in self.file_paths]

        self.file_batch = (
            await self._async_client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=self.vector_store.id, files=file_streams
            )
        )

        if not (
            self.file_batch.status == "completed"
            and self.file_batch.file_counts.completed == len(self.file_paths)
        ):
            raise ValueError(
                f"Something went wrong when uploading files to vector storage with name: {self.name} in assistant."
            )
