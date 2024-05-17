from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message
from aiogram.utils.deep_linking import create_start_link

from config import settings
from services import AssistantService
from tg.states import ActivatedState
from utils import Strings
from utils.functions import validate_company_name

router = Router()
bot = settings.bot


@router.message(ActivatedState.wait_name)
async def get_company_name(message: Message, state: FSMContext):
    status, reply = validate_company_name(message.text)

    if status:
        await state.set_state(ActivatedState.wait_url)
        await state.storage.set_data(
            key=StorageKey(
                bot_id=bot.id, user_id=message.from_user.id, chat_id=message.chat.id
            ),
            data={"company_name": reply},
        )
        await message.answer(Strings.WAIT_URL_MSG)
    else:
        await message.answer(reply)
