from openai import AsyncOpenAI


class SttService:
    """
    A class for converting speech to text using an OpenAI client and a configuration.
    """

    # A dictionary containing configuration options for the speech service, such as the model to use.
    config = {
        "model": "whisper-1",
    }

    # An OpenAI client for making requests to the speech service.
    async_client = None

    @classmethod
    def initialize(cls, async_client: AsyncOpenAI):
        """
        Initializes the SttService with an instance of AsyncOpenAI.

        Parameters:
        - async_client (AsyncOpenAI): An instance of AsyncOpenAI to use for making requests to the speech service.

        Returns:
        - None
        """

        cls.async_client = async_client

    @classmethod
    async def speech_to_text(cls, path_to_file: str) -> str:
        """
        Converts the speech in the given audio file to text.

        Parameters:
        - path_to_file (str): The path to the audio file containing the speech to be converted.

        Returns:
        - str: The transcription of the speech as text.

        Raises:
        - ValueError: If the async_client is not initialized before calling this method.
        """

        if cls.async_client is None:
            raise ValueError(
                "async_client must be initialized before calling speech_to_text."
            )

        with open(path_to_file, "rb") as audio_file:
            transcription = await cls.async_client.audio.transcriptions.create(
                model=cls.config["model"], file=audio_file, response_format="text"
            )

        return transcription
