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
logger.add(stdout, level='DEBUG', format='{time}:{message}', backtrace=True, diagnose=True)
logger.add("bot.log", level="DEBUG", rotation='5MB', format='{level}:{line}:{name}:{function}:{time}:{message}')


def main():

    load_dotenv('config.env')
    token = os.getenv('BOT_API')

    s = source.Start()
      
    app = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler("start", s.start)
    start_conv = s.conversation(entry=[start_handler])

    app.add_handlers([start_conv])

    app.run_polling()

if __name__ == '__main__':
    main()