import re
from urllib.parse import urlparse

import requests
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message
from aiogram.utils.deep_linking import create_start_link
from loguru import logger

from config import settings
from repositories.company_respoitory import CompanyRepository
from services import AssistantService
from tg.states import ActivatedState
from utils import Strings
from utils.functions import check_url

router = Router()
bot = settings.bot


@router.message(ActivatedState.wait_url)
async def get_company_url(message: Message, state: FSMContext):
    status, reply = check_url(message.text)
    if status:
        data = await state.storage.get_data(
            key=StorageKey(
                bot_id=bot.id, user_id=message.from_user.id, chat_id=message.chat.id
            )
        )
        await message.answer(Strings.ASSISTANT_CREATING_MSG)
        try:
            assistant = await AssistantService.get_assistant(
                data["company_name"], reply
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            await message.answer(Strings.ASSISTANT_IS_DEAD)
            return

        thread = await AssistantService.create_thread(message.from_user.id)

        await state.set_state(ActivatedState.activated)
        await state.storage.set_data(
            key=StorageKey(
                bot_id=bot.id, user_id=message.from_user.id, chat_id=message.chat.id
            ),
            data={"thread_id": thread.id, "assistant_id": await assistant.get_id()},
        )

        company = await CompanyRepository.get_by_company_url(reply)
        company_id = company.id

        link = await create_start_link(bot, f"{company_id}", encode=True)
        await message.answer(f"{Strings.ASSISTANT_CREATED_MSG} {link}")
    else:
        await message.answer(reply)
