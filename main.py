#!venv/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
from dotenv import load_dotenv

from loguru import logger

from telegram import (
    Update
    )

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    TypeHandler,
    filters
)

from source.start import StartCommand
from source.book import GROUP_CHAT_ID, BookCommand
from source.unbook import UnbookCommand
from source.whos import WhosCommand

from source.error_handler import error_handler
from source.middleware import GrAuthMiddleware, ChatMembershipMiddleware


load_dotenv("config.env")
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

def main():

    token = os.getenv("BOT_API")
    group_cheker = ChatMembershipMiddleware(GROUP_CHAT_ID)

    s = StartCommand()
    b = BookCommand()
    ub = UnbookCommand()
    ws = WhosCommand()

    # увеличены таймауты если что-то с сетью
    app = (
        ApplicationBuilder()
        .token(token)
        .build()
    )

    start_handler = CommandHandler("start", s.start, filters=filters.COMMAND)

    book_seat_handler = CommandHandler("book", b.dates, filters=filters.COMMAND)
    book_seat_conv = b.conversation(entry=[book_seat_handler])

    unbook_seat_handler = CommandHandler("myseats", ub.check_my_seats, filters=filters.COMMAND)
    unbook_seat_conv = ub.conversation(entry=[unbook_seat_handler])

    whos_handler = CommandHandler('whos', ws.whos_date, filters=filters.COMMAND)
    whos_conv = ws.conversation(entry=[whos_handler])

    help_handler = CommandHandler("help", s.help, filters=filters.COMMAND)

    # Добавляем middleware
    # app.add_handler(TypeHandler(Update, group_cheker), group=1)
    app.add_handler(start_handler)
    app.add_handlers([book_seat_conv, unbook_seat_conv, whos_conv])
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
        rotation="2MB",
        backtrace=False,
        diagnose=False,
        catch=False, 
    )

    # отдельный логгер для ошибок
    logger.add(
        "errors.log",
        format=fmt,
        colorize=False,
        level="ERROR",
        rotation="2MB",
        backtrace=True,
        diagnose=True,
        catch=True, 
    )

    main()