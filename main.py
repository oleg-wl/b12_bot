#!venv/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
from dotenv import load_dotenv

from loguru import logger

from source.start import Start
from source.book import BookSeat
from source.unbook import UnbookSeat
from source.whos import WhosSeat

from source.error_handler import error_handler

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
)


load_dotenv("config.env")

def main():

    token = os.getenv("BOT_API")

    s = Start()
    b = BookSeat()
    ub = UnbookSeat()
    ws = WhosSeat()

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

    unbook_seat_handler = CommandHandler("myseats", ub.check_my_seats)
    unbook_seat_conv = ub.conversation(entry=[unbook_seat_handler])

    whos_handler = CommandHandler('whos', ws.whos_date)
    whos_conv = ws.conversation(entry=[whos_handler])

    help_handler = CommandHandler("help", s.help)

    app.add_handlers([start_conv, book_seat_conv, unbook_seat_conv, whos_conv])
    app.add_handler(help_handler)
    app.add_error_handler(error_handler)

    app.run_polling()


if __name__ == "__main__":

    fmt = "<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <level>{level}</level> | user: {extra[user]} chat: {extra[chat]} - {message}"

    logger.remove()
    logger.add(sys.stdout, format=fmt, level="DEBUG", colorize=True)
    logger.add(
        "b12bot.log",
        format=fmt,
        colorize=False,
        level="INFO",
        rotation="5MB",
        backtrace=True,
        diagnose=True,
    )

    main()