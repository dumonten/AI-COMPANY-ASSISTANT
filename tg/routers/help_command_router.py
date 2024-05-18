from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from utils import Strings

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handles the "/help" command by sending a help message to the user.

    Parameters:
    - message (Message): The message object received from the user.

    Returns:
    - None
    """

    await message.reply(Strings.HELP_MSG)
