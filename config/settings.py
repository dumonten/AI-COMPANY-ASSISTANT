import os
from concurrent.futures import ThreadPoolExecutor

from aiogram import Bot
from openai import AsyncOpenAI
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    A class for managing application settings, including environment variables.
    """

    BOT_KEY: str = Field(env="BOT_KEY")
    OPENAI_KEY: str = Field(env="OPENAI_KEY")
    SER_KEY: str = Field(env="SER_KEY")
    FIRE_CRAWL_KEY: str = Field(env="FIRE_CRAWL_KEY")
    DATABASE_URL: str = Field(env="DATABASE_URL")

    @property
    def bot(self) -> Bot:
        """
        Returns an instance of the Bot class, initialized with the BOT_KEY environment variable.

        Returns:
        - Bot: An instance of the Bot class.
        """

        if not hasattr(self, "_bot"):
            self._bot = Bot(token=self.BOT_KEY)
        return self._bot

    @property
    def async_client(self) -> AsyncOpenAI:
        """
        Returns an instance of the AsyncOpenAI class, initialized with the OPENAI_KEY environment variable.

        Returns:
        - AsyncOpenAI: An instance of the AsyncOpenAI class.
        """

        if not hasattr(self, "_async_client"):
            self._async_client = AsyncOpenAI(api_key=self.OPENAI_KEY)
        return self._async_client

    @property
    def thread_executor(self) -> ThreadPoolExecutor:
        """
        Returns a ThreadPoolExecutor instance for concurrent task execution.

        Returns:
        - ThreadPoolExecutor: An instance of ThreadPoolExecutor configured with 5 worker threads.
        """

        if not hasattr(self, "_thread_executor"):
            self._thread_executor = ThreadPoolExecutor(max_workers=5)
        return self._thread_executor

    class Config:
        """
        Configuration for the Settings class, specifying the location of the .env file and its encoding.
        """

        base_dir = os.path.dirname(os.path.abspath(__file__))
        env_file = os.path.join(base_dir, ".env")
        env_file_encoding = "utf-8"


settings = Settings()
