import os

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import FSInputFile, Message
from loguru import logger

from config import settings
from services import AssistantService, TtsService
from tg.states import ActivatedState
from utils import Strings

router = Router()
bot = settings.bot


@router.message(ActivatedState.activated, F.text)
async def text_message(message: Message, state: FSMContext):
    """
    Handles text messages by sending a wait message to the user, processing the text with the AssistantService,
    converting the response to speech with the TtsService, and sending the speech audio back to the user.

    Parameters:
    - message (Message): The message object received from the user.

    Returns:
    - None
    """

    await message.answer(Strings.WAIT_MSG)

    try:
        data = await state.storage.get_data(
            StorageKey(
                bot_id=bot.id,
                user_id=message.from_user.id,
                chat_id=message.chat.id,
            )
        )

        response = await AssistantService.request(
            data["thread_id"], message.text, data["assistant_id"]
        )

        await message.answer(response)

        """
        try:
            response_audio_file_path = await TtsService.text_to_speech(response)
            response = FSInputFile(response_audio_file_path)
            await message.answer_voice(response)
        except Exception as e:
            logger.error(
                f"Error in voice_message_router while converting answer to audio: {e}"
            )
        finally:
            os.remove(response_audio_file_path)
        """
    except Exception as e:
        logger.error(f"Error in text_message_router: {e}")
