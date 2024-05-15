import json
from typing import List

from loguru import logger
from openai import AsyncOpenAI

from utils import Emotions, encode_image


class EmotionService:
    """
    A class for identifying emotions from images.
    It uses an OpenAI AsyncClient to process images and determine the emotional state of the faces depicted.
    """

    # A dictionary containing configuration options for the speech service, such as the model to use.
    config = {
        "model": "gpt-3.5-turbo",
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "identify_emotions",
                    "description": (
                        "Use this function whenever a photo with a detected human face is received. "
                        "The function parameter should include the identified emotional state of the face depicted in the image."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "emotion": {
                                "type": "string",
                                "enum": Emotions.POSSIBLE_EMOTIONS,
                                "description": (
                                    "Emotion as string from enum which represents the facial expression most accurately."
                                ),
                            }
                        },
                        "required": ["emotion"],
                    },
                },
            },
        ],
        "max_tokens": 300,
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
    async def identify_emotions(cls, image_path: str) -> List[str]:
        """
        Identifies the emotional state of the face depicted in the image.

        Parameters:
        - image_path (str): Path to the image file containing the face to analyze.

        Returns:
        - List[str]: A list of identified emotions from the image.
        """

        if cls.async_client is None:
            raise ValueError(
                "async_client must be initialized before calling speech_to_text."
            )

        try:
            base64_image = encode_image(image_path)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Your objective is to identify the emotion of the individual "
                        "depicted in the image based on their facial expression."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "auto",
                            },
                        },
                    ],
                },
            ]

            response = await cls.async_client.chat.completions.create(
                model=cls.config["model"],
                messages=messages,
                tools=cls.config["tools"],
                tool_choice={
                    "type": "function",
                    "function": {"name": "identify_emotions"},
                },
            )

            output = response.choices[0].message.tool_calls[0]
            arguments_dict = json.loads(output.function.arguments)
            return arguments_dict["emotion"]
        except Exception as e:
            logger.info(
                f"Unable to generate ChatCompletion response in EmotionService. Exception: {e}"
            )
            return False
