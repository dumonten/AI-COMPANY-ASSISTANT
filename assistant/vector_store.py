from typing import Any, List

from openai import AsyncOpenAI


class VectorStore:
    """
    VectorStore represents a vector store for managing and storing vectors, typically used in machine learning applications.
    """

    def __init__(
        self,
    ) -> None:
        """
        Initializes a new VectorStore instance.

        Args:
        None

        Returns:
        None
        """
        self.name = ""
        self.instructions = ""
        self.vector_store = None
        self.file_batch = None
        self.file_paths = []
        self._async_client = None

    async def initialization(
        self,
        name: str,
        file_paths: List[str],
        instructions: str,
        async_client: AsyncOpenAI,
    ) -> None:
        """
        Initializes the VectorStore with specified parameters and uploads files to the vector store.

        This method configures the vector store with a name, instructions, and a list of file paths to upload.
        It then creates a vector store instance and uploads the specified files to it.

        Parameters:
        - name (str): The name of the vector store.
        - file_paths (List[str]): A list of file paths to the files that will be uploaded to the vector store.
        - instructions (str): Instructions for the vector store, which may include configuration details.
        - async_client (AsyncOpenAI): An asynchronous client for interacting with the OpenAI API.

        Returns:
        None
        """
        self.name = name
        self.file_paths = file_paths
        self.instructions = instructions
        self._async_client = async_client

        # Creating the vector store instance
        self.vector_store = await self._async_client.beta.vector_stores.create(
            name=self.name
        )

        # Checking if file_paths is None to avoid unnecessary operations
        if self.file_paths is None:
            return

        # Opening the files in binary mode for reading
        file_streams = [open(path, "rb") for path in self.file_paths]

        # Uploading the files to the vector store and waiting for the upload to complete
        self.file_batch = (
            await self._async_client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=self.vector_store.id, files=file_streams
            )
        )

        # Verifying that all files were successfully uploaded
        if not (
            self.file_batch.status == "completed"
            and self.file_batch.file_counts.completed == len(self.file_paths)
        ):
            raise ValueError(
                f"Something went wrong when uploading files to vector storage with name: {self.name} in assistant."
            )
