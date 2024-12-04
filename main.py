#!venv/bin/python
# -*- coding: UTF-8 -*-

import os
from sys import stdout
from dotenv import load_dotenv
from loguru import logger

import source

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
)

logger.remove()  # Remove the current handler
logger.add(
    stdout, level="WARNING", format="{time}:{message}", backtrace=False, diagnose=False
)
logger.add(
    "bot.log",
    level="INFO",
    rotation="5MB",
    format="{level}:{line}:{name}:{function}:{time}:{message}",
)


def main():

    load_dotenv("config.env")
    token = os.getenv("BOT_API")

    s = source.Start()

    # увеличены таймауты если что-то с сетью
    app = (
        ApplicationBuilder()
        .token(token)
        .read_timeout(10)
        .get_updates_read_timeout(10)
        .build()
    )

    start_handler = CommandHandler("start", s.start)
    start_conv = s.conversation(entry=[start_handler])

    app.add_handlers([start_conv])

    app.run_polling(timeout=30)


if __name__ == "__main__":
    main()
