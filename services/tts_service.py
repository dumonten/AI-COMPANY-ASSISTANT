import uuid

from openai import AsyncOpenAI


class TtsService:
    """
    A class for converting text to speech using an OpenAI client and a configuration.
    """

    # A dictionary containing configuration options for the speech service, such as the model and voice to use.
    _config = {
        "model": "tts-1",
        "voice": "nova",
    }

    # An OpenAI client for making requests to the speech service.
    _async_client = None

    @classmethod
    def initialize(cls, async_client: AsyncOpenAI):
        """
        Initializes the TtsService with an instance of AsyncOpenAI.

        Parameters:
        - async_client (AsyncOpenAI): An instance of AsyncOpenAI to use for making requests to the speech service.

        Returns:
        - None
        """

        cls._async_client = async_client

    @classmethod
    async def text_to_speech(cls, text: str) -> str:
        """
        Converts the provided text to speech and saves it as an MP3 file.

        Parameters:
        - text (str): The text to convert to speech.

        Returns:
        - str: The path to the generated MP3 file.

        Raises:
        - ValueError: If the async_client is not initialized before calling this method.
        """

        if cls._async_client is None:
            raise ValueError(
                "async_client must be initialized before calling speech_to_text."
            )

        path_to_file = str(uuid.uuid4()) + ".mp3"
        async with cls._async_client.audio.speech.with_streaming_response.create(
            model=cls._config["model"], voice=cls._config["voice"], input=text
        ) as model:
            await model.stream_to_file(path_to_file)
        return path_to_file
