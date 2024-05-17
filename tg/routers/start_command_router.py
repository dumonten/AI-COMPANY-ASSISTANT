from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message
from aiogram.utils.deep_linking import decode_payload
from loguru import logger

from config import settings
from services import AssistantService
from tg.states import ActivatedState
from utils import Strings

router = Router()
bot = settings.bot


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    """
    Handles the "/start" command by sending a welcome message to the user.

    Parameters:
    - message (Message): The message object received from the user.

    Returns:
    - None
    """

    if command.args is None:
        await state.set_state(ActivatedState.wait_name)
        await message.answer(Strings.WAIT_NAME_MSG)
        return
    else:
        company_id = int(decode_payload(command.args))

        await message.answer(Strings.ASSISTANT_IS_LOADING_MSG)

        try:
            assistant = await AssistantService.get_assistant(None, None, company_id)
        except Exception as e:
            assistant = None
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

        await message.answer(Strings.ASSISTANT_ACTIVATED_MSG)

        response = await AssistantService.request(
            thread.id, Strings.ASSISTANT_HELLO_MSG, await assistant.get_id()
        )

        await message.answer(response)
