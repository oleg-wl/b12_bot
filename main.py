#!venv/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
from dotenv import load_dotenv

from loguru import logger

from source.start import StartCommand
from source.book import GROUP_CHAT_ID, BookCommand
from source.unbook import UnbookCommand
from source.whos import WhosCommand

from source.error_handler import error_handler

from telegram import (
    Update
    )

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    ChatJoinRequestHandler
)

load_dotenv("config.env")
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

# Обработчики отдельных комманд
async def chat_join(update: Update, context: CallbackContext):
    pass


@logger.catch
def main():

    token = os.getenv("BOT_API")

    s = StartCommand()
    b = BookCommand()
    ub = UnbookCommand()
    ws = WhosCommand()

    # увеличены таймауты если что-то с сетью
    app = (
        ApplicationBuilder()
        .token(token)
#        .read_timeout(10)
#        .get_updates_read_timeout(10)
        .concurrent_updates(concurrent_updates=False)
        .build()
    )

    start_handler = CommandHandler("start", s.start)
    start_conv = s.conversation(entry=[start_handler])

    book_seat_handler = CommandHandler("book", b.dates)
    book_seat_conv = b.conversation(entry=[book_seat_handler])

#    FIXME: переименовать unbook в myseats command
    unbook_seat_handler = CommandHandler("myseats", ub.check_my_seats)
    unbook_seat_conv = ub.conversation(entry=[unbook_seat_handler])

    whos_handler = CommandHandler('whos', ws.whos_date)
    whos_conv = ws.conversation(entry=[whos_handler])

    help_handler = CommandHandler("help", s.help)

    chat_join_handler = ChatJoinRequestHandler(callback=chat_join, chat_id=GROUP_CHAT_ID, block=False)

    app.add_handlers([start_conv, book_seat_conv, unbook_seat_conv, whos_conv])
    app.add_handler(help_handler)
    app.add_error_handler(error_handler)

    app.run_polling()


if __name__ == "__main__":

    fmt = "<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <level>{level}</level> | {extra} - {message}"

    logger.remove()
    logger.add(sys.stdout, 
               format=fmt, 
               level="TRACE", 
               colorize=True,
               catch=True)

    # лог в файл только инфо
    logger.add(
        "b12bot.log",
        format=fmt,
        colorize=False,
        level="INFO",
        rotation="5MB",
        backtrace=False,
        diagnose=False,
    )

    # отдельный логгер для ошибок
    logger.add(
        "errors.log",
        format=fmt,
        colorize=False,
        level="ERROR",
        rotation="5MB",
        backtrace=True,
        diagnose=True,
        catch=True
    )

    main()