from typing import Any, List, Tuple

from openai import AsyncOpenAI


class VectorStore:
    def __init__(
        self,
    ) -> None:
        self.name: str = ""
        self.instructions: str = ""
        self.vector_store: Any = None
        self.file_batch: Any = None
        self.file_paths: List[str] = []
        self._async_client: AsyncOpenAI = None

    async def initialization(
        self,
        name: str,
        file_paths: List[str],
        instructions: str,
        async_client: AsyncOpenAI,
    ) -> None:
        self.name = name
        self.file_paths = file_paths
        self.instructions = instructions
        self._async_client = async_client

        self.vector_store = await self._async_client.beta.vector_stores.create(
            name=self.name
        )

        # Local variable 'file_streams' is explicitly typed
        file_streams: List[Any] = [open(path, "rb") for path in self.file_paths]

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
