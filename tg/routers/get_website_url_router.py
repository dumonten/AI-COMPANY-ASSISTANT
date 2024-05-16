import re
from urllib.parse import urlparse

import requests
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message
from aiogram.utils.deep_linking import create_start_link

from config import settings
from services import AssistantService
from tg.states import ActivatedState
from utils import Strings
from utils.functions import check_url

router = Router()
bot = settings.bot


@router.message(ActivatedState.wait_url)
async def cmd_help(message: Message, state: FSMContext):
    """
    Handles the "/help" command by sending a help message to the user.

    Parameters:
    - message (Message): The message object received from the user.

    Returns:
    - None
    """
    status, reply = check_url(message.text)
    if status:
        data = await state.storage.get_data(
            key=StorageKey(
                bot_id=bot.id, user_id=message.from_user.id, chat_id=message.chat.id
            )
        )
        await message.answer(Strings.ASSISTANT_CREATING)
        assistant = await AssistantService.get_assistant(
            None, data["company_name"], reply
        )
        thread = await AssistantService.create_thread(message.from_user.id)

        await state.set_state(ActivatedState.activated)
        await state.storage.set_data(
            key=StorageKey(
                bot_id=bot.id, user_id=message.from_user.id, chat_id=message.chat.id
            ),
            data={"thread_id": thread.id, "assistant_id": await assistant.get_id()},
        )

        link = await create_start_link(bot, await assistant.get_id(), encode=True)
        await message.answer(f"{Strings.ASSISTANT_CREATED} {link}")
    else:
        await message.answer(reply)
