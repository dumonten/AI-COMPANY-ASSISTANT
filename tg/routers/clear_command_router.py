from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services import AssistantService
from utils import Strings

router = Router()


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    """
    Handles the "/clear" command by clearing the context.

    Parameters:
    - message (Message): The message object received from the user.

    Returns:
    - None
    """

    await message.reply(Strings.CLEAR_MSG)
