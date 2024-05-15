from typing import Any, List

from loguru import logger
from openai import AsyncOpenAI

from config import settings


class VectorStore:
    def __init__(self):
        self.name: str = ""
        self.instructions: str = ""
        self.vector_store: Any = None
        self.file_batch: Any = None
        self.file_paths: List[str] = []

    async def initialization(
        self, name: str, file_paths: List[str], instructions: str
    ) -> None:
        self.name = name
        self.file_paths = file_paths
        self.instructions = instructions

        self.vector_store = await settings.async_client.beta.vector_stores.create(
            name=self.name
        )

        file_streams = [open(path, "rb") for path in self.file_paths]

        self.file_batch = (
            await settings.async_client.beta.vector_stores.file_batches.upload_and_poll(
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
