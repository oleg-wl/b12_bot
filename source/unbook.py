import datetime
import os

from typing import Sequence
from typing import Tuple

from sqlalchemy import Row
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from loguru import logger

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
)

import database
from .start import Start

GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")


class UnbookSeat(Start):

    def __init__(self) -> None:
        super().__init__()

    MYSEATS, UNBOOK = range(6, 8)

    def __repr__(self):
        return "Экземпляр класса UnbookSeats"

    async def check_my_seats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        uid = update.effective_chat.id

        if update.effective_chat.type in ["group", "supergroup"]:
            message_id = update.message.message_id

            kb = [
                [
                    InlineKeyboardButton(
                        "Написать боту",
                        url="tg://user?id={}".format(context.bot.id),
                    )
                ]
            ]

            await update.message.reply_text(
                reply_to_message_id=message_id,
                text="Привет {}. Для брони мест напиши мне в личные сообщения".format(
                    update.message.from_user.name
                ),
                reply_markup=InlineKeyboardMarkup(kb),
            )
            logger.debug("/Start command in groupchat")
            return ConversationHandler.END

        self.booked_seats: Sequence[Row[Tuple[datetime.datetime, int]]] = (
            database.select_my_seats_to_unbook(engine=database.engine, chat_id=uid)
        )

        # проверка - если нет занятых мест -> конец
        if len(self.booked_seats) == 0:
            logger.debug("no seats for {}, seats {}", uid, self.booked_seats)
            await context.bot.send_message(
                chat_id=uid,
                text="Ты не занял места на ближайшее время /book - чтобы занять",
            )
            return ConversationHandler.END

        buttons = []
        for r in self.booked_seats:
            date = r[0].strftime(database.FORMAT)
            seat: str = r[1]
            buttons.append("{} место {}".format(date, seat))
            logger.debug("Types check: date {}, seat {}", date, seat)

        logger.debug('=== update callback query {} ===', update.callback_query)
        if update.callback_query != None:
            query = update.callback_query
            query.answer()

            await query.edit_message_text(
                text="Твои места на ближайшие дни. Выбери, с какого снять бронь",
                reply_markup=self.kb.build_booked_seats_keyboard(buttons),
            )
            return self.MYSEATS

        await context.bot.send_message(
            chat_id=uid,
            text="Твои места на ближайшие дни. Выбери, с какого снять бронь",
            reply_markup=self.kb.build_booked_seats_keyboard(buttons),
        )
        logger.debug("/Unbook for seats {}", self.booked_seats)

        return self.MYSEATS

    async def check_unbook_seat(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):

        query = update.callback_query
        await query.answer()

        try:
            i = int(query.data)
        except ValueError:
            pass
        else:
            logger.debug("/unbook:selected to unbook callback: {}", i)

            self.selected_unbook_date: datetime.datetime = self.booked_seats[i][0]
            self.selected_unbook_seat = self.booked_seats[i][1]
            logger.debug(
                "seat to unbook date {} seat {}".format(
                    self.selected_unbook_date, self.selected_unbook_seat
                )
            )

            await query.edit_message_text(
                text="Освободить место {} на {}".format(
                    self.selected_unbook_seat,
                    self.selected_unbook_date.strftime(database.FORMAT),
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(text="Да >>>", callback_data="unbook")],
                        self.kb.back_button,
                    ]
                ),
            )
            return self.UNBOOK

    async def unbook(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        database.unbook_seat(
            engine=database.engine,
            selected_unbook_date=self.selected_unbook_date,
            selected_unbook_seat=self.selected_unbook_seat,
        )

        query = update.callback_query
        await query.answer()

        msg = "Место {} освобождено на {}".format(
            self.selected_unbook_seat,
            self.selected_unbook_date.strftime(database.FORMAT),
        )
        await query.edit_message_text(msg)
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)
        logger.debug("message sent to group chat_id {}", GROUP_CHAT_ID)
        return ConversationHandler.END

    def conversation(self, entry: list[CommandHandler]) -> ConversationHandler:

        conversation = ConversationHandler(
            per_message=False,
            entry_points=entry,
            states={
                self.MYSEATS: [
                    CallbackQueryHandler(callback=self.check_unbook_seat),
                ],
                self.UNBOOK: [
                    CallbackQueryHandler(callback=self.check_my_seats, pattern="back"),
                    CallbackQueryHandler(callback=self.unbook, pattern="unbook"),
                ],
            },
            fallbacks=entry,
        )
        return conversation
