from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message

from config import settings
from services import AssistantService
from tg.states import ActivatedState
from utils import Strings

router = Router()
bot = settings.bot


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Handles the "/start" command by sending a welcome message to the user.

    Parameters:
    - message (Message): The message object received from the user.

    Returns:
    - None
    """

    assistant = await AssistantService.get_assistant("", "Аскона", "https://askona.by/")
    thread = await AssistantService.create_thread(message.from_user.id)

    await state.set_state(ActivatedState.activated)
    await state.storage.set_data(
        key=StorageKey(
            bot_id=bot.id, user_id=message.from_user.id, chat_id=message.chat.id
        ),
        data={"thread_id": thread.id, "assistant_id": await assistant.get_id()},
    )
