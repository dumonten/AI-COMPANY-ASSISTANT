from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message

from config import settings
from tg.states import ActivatedState
from utils import Strings
from utils.functions import validate_company_name

# Initialize the router and bot instance
router = Router()
bot = settings.bot


@router.message(ActivatedState.wait_name)
async def get_company_name(message: Message, state: FSMContext):
    """
    Handles incoming messages from users who have entered the 'wait_name' state of the conversation flow.

    This function validates the company name provided by the user and transitions the conversation to the next state ('wait_url') if the validation passes.

    Parameters:
    - message (Message): The incoming message from the user.
    - state (FSMContext): The current state context of the conversation.

    Returns:
    None
    """

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
