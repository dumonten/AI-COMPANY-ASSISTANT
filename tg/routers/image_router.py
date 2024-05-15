import os
import pathlib

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import FSInputFile, Message
from loguru import logger

from analytics.types import EventType
from config import settings
from services import AnalyticsService, AssistantService, EmotionService, TtsService
from tg.states import ThreadIdState
from utils import Strings

router = Router()
bot = settings.bot


@router.message(ThreadIdState.thread_id, F.photo)
async def image(message: Message, state: FSMContext):
    """
    Handles messages with image by sending a wait message to the user, processing the image with the EmotionService,
    converting the response to speech with the TtsService, and sending the speech audio back to the user.

    Parameters:
    - message (Message): The message object received from the user.

    Returns:
    - None
    """

    AnalyticsService.track_event(
        user_id=message.from_user.id, event_type=EventType.ImageSent
    )

    await message.answer(Strings.WAIT_MSG)

    file = await bot.get_file(message.photo[-1].file_id)
    file_on_disk = pathlib.Path("", f"{message.photo[-1].file_id}.jpg")
    await bot.download_file(file.file_path, destination=file_on_disk)

    try:
        emotion_state = await EmotionService.identify_emotions(file_on_disk)

        data = await state.storage.get_data(
            StorageKey(
                bot_id=bot.id,
                user_id=message.from_user.id,
                chat_id=message.chat.id,
            )
        )

        response = await AssistantService.request(
            message.from_user.id,
            data["thread_id"],
            Strings.EMOTION_STATE_USER_ANS + emotion_state,
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
        logger.error(f"Error in image_router: {e}")
    finally:
        os.remove(file_on_disk)
