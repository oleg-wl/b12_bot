#!venv/bin/python
# -*- coding: UTF-8 -*-

import os
from dotenv import load_dotenv
import loguru

import source

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)

load_dotenv('config.env')
TOKEN = os.getenv('BOT_API')

def main(token: str):
    s = source.Start()
      
    app = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler("start", s.start)
    start_conv = s.conversation(entry=[start_handler])

    app.add_handlers([start_conv])

    app.run_polling()

if __name__ == '__main__':
    main(token=TOKEN)