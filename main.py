#!venv/bin/python
# -*- coding: UTF-8 -*-

import os
from dotenv import load_dotenv
from sys import stdout
from loguru import logger

#for debugging purp
import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger.add(sink=stdout, level='DEBUG')
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from source.start import Start
from source.book import BookSeat
from source.unbook import UnbookSeat

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
    
    help_handler = CommandHandler('help', s.help)

    app.add_handlers([start_conv, book_seat_conv, unbook_seat_conv, help_handler])

    app.run_polling(timeout=30)


if __name__ == "__main__":
    main()
