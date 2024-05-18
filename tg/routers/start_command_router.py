import os

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import FSInputFile, Message
from aiogram.utils.deep_linking import decode_payload
from loguru import logger
from telegram.constants import ParseMode

from config import settings
from services import AssistantService, TtsService
from tg.states import ActivatedState
from utils import Strings

# Initialize the router and bot instance
router = Router()
bot = settings.bot


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    """
    Handles the '/start' command from users, which initiates the process of loading an assistant based on a provided company ID.

    This function decodes the company ID from the command arguments, attempts to load an assistant for the company, and transitions the conversation to the 'activated' state.

    Parameters:
    - message (Message): The incoming message from the user.
    - command (CommandObject): The command object containing the command arguments.
    - state (FSMContext): The current state context of the conversation.

    Returns:
    None
    """

    if command.args is None:
        await state.set_state(ActivatedState.wait_name)
        await message.answer(Strings.WAIT_NAME_MSG)
        return
    else:
        await message.answer(Strings.ASSISTANT_IS_LOADING_MSG)

        company_id = int(decode_payload(command.args))

        try:
            assistant = await AssistantService.get_assistant(None, None, company_id)
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

        await message.answer(Strings.ASSISTANT_ACTIVATED_MSG)

        response = await AssistantService.request(
            thread.id, Strings.ASSISTANT_HELLO_MSG, await assistant.get_id()
        )

        await message.answer(response, parse_mode=ParseMode.MARKDOWN)

        try:
            response_audio_file_path = await TtsService.text_to_speech(response)
            response = FSInputFile(response_audio_file_path)
            await message.answer_voice(response)
        except Exception as e:
            logger.error(
                f"Error in start_command_router while converting answer to audio: {e}"
            )
        finally:
            os.remove(response_audio_file_path)
