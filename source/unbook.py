import datetime
import json
import os

import re
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
from .start import CoreCommand

GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")


class UnbookCommand(CoreCommand):

    STAGE_MYSEAT, STAGE_UNBOOK = range(6, 8)

    def __init__(self) -> None:
        super().__init__()

        self.booked_seats: Sequence[Row[Tuple[datetime.datetime, int]]] = None

        # переопределить кнопку назад
        self.kb.back_button = [InlineKeyboardButton(text='<< Вернуться',callback_data=json.dumps({"action":"unbook_back"}))]
        self.kb.bkb = InlineKeyboardMarkup([self.kb.back_button])

    def __repr__(self):
        return super().__repr__()

    async def check_my_seats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        _, _chat_id, context_logger = self._initialisation(update=update)
        
        # Проверка на сообщение в групповом чате
        _check_group_chat: int | None = await self._check_group(update=update, context=context)
        if _check_group_chat: return ConversationHandler.END

        # выбрать места для брони
        self.booked_seats = (
            database.select_my_seats_to_unbook(engine=database.engine, chat_id=_chat_id)
        )
        context_logger.trace('check_my_seats:: booked_seats - {}'.format(self.booked_seats))

        # проверка - если нет занятых мест -> конец
        if len(self.booked_seats) == 0:
            
            context_logger.info("нет нет занятых мест", self.booked_seats)
            await context.bot.send_message(
                chat_id=_chat_id,
                text="Ты не занял места на ближайшее время\n/book - чтобы занять \U0001F4BA",
            )
            return ConversationHandler.END

        buttons = []
        for r in self.booked_seats:
            date: str = r[0].strftime(database.FORMAT)
            seat: str = r[1]
            buttons.append("{} место {}".format(date, seat))

        context_logger.info('check_my_seats:: {}'.format(repr(self)))

        query = update.callback_query

        if query != None and query.data == '{"action": "unbook_back"}':        
            await query.answer()

            await query.edit_message_text(
                text="Твои места на ближайшие дни. Выбери, с какого снять бронь",
                reply_markup=self.kb.build_booked_seats_keyboard(buttons),
            )
            return self.STAGE_MYSEAT

        else:
            await context.bot.send_message(
                chat_id=_chat_id,
                text="Твои места на ближайшие дни. Выбери, с какого снять бронь",
                reply_markup=self.kb.build_booked_seats_keyboard(buttons),
            )

            return self.STAGE_MYSEAT

    async def check_unbook_seat(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):

        _, _, context_logger = self._initialisation(update=update)
        
        query = update.callback_query

        action, i = self._json_callback(query=query)

        if action == 'booked_seats_command':
            await query.answer()

            self.selected_unbook_date: datetime.datetime = self.booked_seats[i][0]
            self.selected_unbook_seat = self.booked_seats[i][1]
            
            await query.edit_message_text(
                text="Освободить место {} на {}".format(
                    self.selected_unbook_seat,
                    self.selected_unbook_date.strftime(database.FORMAT),
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(text="Да >>>", callback_data=json.dumps({"action":"unbook"}))],
                        self.kb.back_button,
                    ]
                ),
            )
            return self.STAGE_UNBOOK

    async def unbook(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        #снять бронь и написать в чат
        
        _username, _chat_id, context_logger = self._initialisation(update=update)

        database.unbook_seat(
            engine=database.engine,
            selected_unbook_date=self.selected_unbook_date,
            selected_unbook_seat=self.selected_unbook_seat,
        )

        query = update.callback_query
        action, _ = self._json_callback(query=query)

        if action == 'unbook':
            await query.answer()

            msg = "Место {} освобождено на {}".format(
                self.selected_unbook_seat,
                self.selected_unbook_date.strftime(database.FORMAT),
            )
            context_logger.info('unbook:: {}'.format(repr(self)))
            await query.edit_message_text(msg)
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)
            return ConversationHandler.END

    def conversation(self, entry: list[CommandHandler]) -> ConversationHandler:
        pattern = re.compile(pattern='{"action": "booked_seats_command".*')

        conversation = ConversationHandler(
            entry_points=entry,
            states={
                self.STAGE_MYSEAT: [
                    CallbackQueryHandler(callback=self.check_unbook_seat, pattern=pattern),
                ],
                self.STAGE_UNBOOK: [
                    CallbackQueryHandler(callback=self.check_my_seats, pattern='{"action": "unbook_back"}'),
                    CallbackQueryHandler(callback=self.unbook, pattern='{"action": "unbook"}'),
                ],
            },
            fallbacks=entry,
            #conversation_timeout=10,
            #per_message=True,
            per_chat=True,
            per_user=True,
        )
        return conversation
