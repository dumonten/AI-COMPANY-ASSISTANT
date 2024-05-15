import asyncio
from asyncio.exceptions import CancelledError

from aiogram import Dispatcher
from loguru import logger

from config import settings
from services import (
    AssistantService,
    EmotionService,
    SttService,
    TtsService,
    ValidateService,
)
from tg.routers import (
    clear_command_router,
    get_sources_router,
    help_command_router,
    image_router,
    start_command_router,
    text_message_router,
    voice_message_router,
)


async def main():
    """
    Initializes the bot, sets up routers for handling different types of messages and commands,
    and starts the bot's polling loop.

    Returns:
    - None
    """

    dp = Dispatcher()

    bot = settings.bot
    async_client = settings.async_client

    # Initialize services with the async client.
    await AssistantService.initialize(async_client=async_client)
    ValidateService.initialize(async_client=async_client)
    SttService.initialize(async_client=async_client)
    TtsService.initialize(async_client=async_client)
    EmotionService.initialize(async_client=async_client)

    # Include routers for handling different types of messages and commands.
    dp.include_router(get_sources_router)
    dp.include_router(start_command_router)
    dp.include_router(help_command_router)
    dp.include_router(clear_command_router)
    dp.include_router(image_router)
    dp.include_router(text_message_router)
    dp.include_router(voice_message_router)

    logger.info("Bot started")

    # Start the bot's polling loop.
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit, CancelledError):
        # Handle keyboard interrupts and system exits gracefully.
        logger.info("Bot stopped")
