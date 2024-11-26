#!venv/bin/python
# -*- coding: UTF-8 -*-

import os
from dotenv import load_dotenv
import loguru
import click

import source

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)


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