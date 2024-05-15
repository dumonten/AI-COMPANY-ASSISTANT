import os
import pathlib

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import FSInputFile, Message
from loguru import logger

from config import settings
from services import AssistantService, SttService, TtsService
from tg.states import ActivatedState
from utils import Strings

router = Router()
bot = settings.bot


@router.message(ActivatedState.activated, F.voice)
async def voice_message(message: Message, state: FSMContext):
    """
    Handles voice messages by downloading the voice message, converting it to text with the SttService,
    processing the text with the AssistantService, converting the response to speech with the TtsService,
    and sending the speech audio back to the user.

    Parameters:
    - message (Message): The message object received from the user.

    Returns:
    - None
    """

    await message.answer(Strings.WAIT_MSG)

    file = await bot.get_file(message.voice.file_id)
    file_on_disk = pathlib.Path("", f"{message.voice.file_id}.ogg")
    await bot.download_file(file.file_path, destination=file_on_disk)

    try:
        text = await SttService.speech_to_text(file_on_disk)

        data = await state.storage.get_data(
            StorageKey(
                bot_id=bot.id,
                user_id=message.from_user.id,
                chat_id=message.chat.id,
            )
        )

        response = await AssistantService.request(
            message.from_user.id, data["thread_id"], text
        )

        await message.answer(response)

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
    except Exception as e:
        logger.error(f"Error in voice_message_router: {e}")
    finally:
        os.remove(file_on_disk)
