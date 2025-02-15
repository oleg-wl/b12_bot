#!venv/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
from dotenv import load_dotenv

from loguru import logger

from source.start import Start
from source.book import BookSeat
from source.unbook import UnbookSeat

from source.error_handler import error_handler

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
)


@logger.catch()
def main():

    load_dotenv("config.env")
    token = os.getenv("BOT_API")

    s = Start()
    b = BookSeat()
    ub = UnbookSeat()

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

    book_seat_handler = CommandHandler("book", b.dates)
    book_seat_conv = b.conversation(entry=[book_seat_handler])

    unbook_seat_handler = CommandHandler("myseats", ub.check_my_seats)
    unbook_seat_conv = ub.conversation(entry=[unbook_seat_handler])

    help_handler = CommandHandler("help", s.help)

    app.add_handlers([start_conv, book_seat_conv, unbook_seat_conv])
    app.add_handler(help_handler)
    app.add_error_handler(error_handler)

    app.run_polling(timeout=30)


if __name__ == "__main__":

    fmt = "<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <level>{level}</level> | {message}"

    logger.remove()
    logger.add(sys.stdout, format=fmt, level="ERROR", colorize=True)
    logger.add(
        "b12bot.log",
        format=fmt,
        colorize=False,
        level="DEBUG",
        rotation="5MB",
        backtrace=True,
        diagnose=True,
    )

    main()