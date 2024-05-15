import os

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import FSInputFile, Message
from loguru import logger

from analytics.types import EventType
from config import settings
from services import AnalyticsService, AssistantService, TtsService
from tg.states import ThreadIdState
from utils import Strings

router = Router()
bot = settings.bot


@router.message(ThreadIdState.thread_id, F.text)
async def text_message(message: Message, state: FSMContext):
    """
    Handles text messages by sending a wait message to the user, processing the text with the AssistantService,
    converting the response to speech with the TtsService, and sending the speech audio back to the user.

    Parameters:
    - message (Message): The message object received from the user.

    Returns:
    - None
    """

    AnalyticsService.track_event(
        user_id=message.from_user.id, event_type=EventType.TextMessageSent
    )

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
            message.from_user.id, data["thread_id"], message.text
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
        logger.error(f"Error in text_message_router: {e}")
