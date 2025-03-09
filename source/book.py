import datetime
import json
import re
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from loguru import logger

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)

import database

from .start import CoreCommand

GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID') 


class BookCommand(CoreCommand):

    STAGE_DATE, STAGE_SEAT, STAGE_BOOK = range(2, 5)

    def __init__(self) -> None:
        super().__init__()

        self.selected_seat: str = None
        self.selected_date: datetime.datetime = None
        self.free_seats = None

    def __repr__(self):
        return super().__repr__()
    
    async def dates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # получить список дат

        _, _chat_id, context_logger = self._initialisation(update=update)
        
        #проверка что бот не в групповом чате
        _check_group_chat: int | None = await self._check_group(update=update, context=context)
        if _check_group_chat: return ConversationHandler.END

        # забрать дни
        self.days: list = database.select_days(engine=database.engine, d=3)
        kb_days: InlineKeyboardMarkup = self.kb.build_days_keyboard(action='dates', days=self.days)        
        context_logger.trace("dates keyboard - {}". format(kb_days.inline_keyboard))

        query = update.callback_query

        #проверка на callback_query сценарий: кнопка "Вернуться"
        if query != None and query.data == '{"action": "back"}':

            await query.answer()
            await query.edit_message_caption(
                caption="Выбери день для брони", reply_markup=kb_days
            )
            return self. STAGE_DATE

        await context.bot.send_photo(chat_id=_chat_id, caption="Выбери день для брони", reply_markup=kb_days, photo='seats.jpg')
        
        context_logger.info("dates:: {}".format(repr(self)))
        return self.STAGE_DATE

    async def seats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # выбор даты и показ свободных мест на эту дату

        _, _, context_logger = self._initialisation(update=update)

        query = update.callback_query
        await query.answer()

        # проверка коллбека для выбора даты
        action, i = self._json_callback(query=query)
        
        if action == 'dates':
            self.selected_date = datetime.datetime.strptime(
                self.days[i], database.FORMAT
            ).date()
            self.free_seats: filters.Sequence[int] = database.select_free_seats(
                engine=database.engine, date=self.selected_date
            )
            context_logger.info("seats:: {}".format(repr(self)))

        elif action == 'back':
            self.free_seats: filters.Sequence[int] = database.select_free_seats(
                engine=database.engine, date=self.selected_date
            )
            context_logger.info("seats:: {}".format(repr(self)))
            

            # если свободных мест нет
        if (len(self.free_seats) <= 0) | (self.free_seats == None):
            await query.edit_message_caption(
                caption="Свободных мест на эту дату нет", reply_markup=self.kb.bkb
            )
            return self.STAGE_DATE
        
        elif self.free_seats:
            fs = self.kb.build_seats_keyboard(self.free_seats)
            await query.edit_message_caption(
                caption="Выбери место", reply_markup=fs
            )
            context_logger.trace("seats keyboard - {}". format(fs.inline_keyboard))

            return self.STAGE_SEAT


    async def check_book_seat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        _, _, context_logger = self._initialisation(update=update)
        
        query = update.callback_query
        await query.answer()

        action, i = self._json_callback(query=query)
         
        if action == 'seats':
            self.selected_seat: str = self.free_seats[i]

            context_logger.info("check_book_seat:: {}".format(repr(self)))
            
            await query.edit_message_caption(
                caption=f"Занять {self.selected_seat} на {self.selected_date}?",
                reply_markup=InlineKeyboardMarkup(
                    [
                        self.kb.back_button,
                        [InlineKeyboardButton(text="Да >>>", callback_data=json.dumps({'action':'book'}))],
                    ]
                ),
            )
            return self.STAGE_BOOK

    async def book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        _username, _chat_id, context_logger = self._initialisation(update=update)
        
        c = database.book_seat(
            engine=database.engine,
            chat_id=_chat_id,
            selected_date=self.selected_date,
            selected_seat=self.selected_seat,
        )
        context_logger.trace(c)

        query = update.callback_query
        await query.answer()

        match c:
            case 0:
                context_logger.warning(f"parralel book {c}")
                fs = self.kb.build_seats_keyboard(self.free_seats)
                await query.edit_message_caption(
                    caption="Выбранное место уже заняли пока ты выбирал",
                    reply_markup=fs,
                )
                # вернуть клавиатуру со свободными местами и перейти на стадию выбора места
                return self.STAGE_SEAT

            case 1:
                context_logger.info(
                    "book:: {}".format(repr(self))
                )
                msg = f"{self.selected_date.strftime(database.FORMAT)} забронировано место - {self.selected_seat}"
                await query.edit_message_caption(
                    caption=msg,
                )

                await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=' @{} '.format(_username) + msg)
                return ConversationHandler.END
            
            case _:
                context_logger.info(
                   f"book:: - unbooked {c}, booked {self.selected_seat}, date {self.selected_date}"
                )
                msg = f"{self.selected_date.strftime(database.FORMAT)} забронировано место - {self.selected_seat}. С места {c} снята бронь."
                
                await query.edit_message_caption(
                    caption=msg,
                )
                await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=' @{} '.format(_username) + msg)

                return ConversationHandler.END


    def conversation(self, entry: list[CommandHandler]) -> ConversationHandler:

        conversation = ConversationHandler(
            entry_points=entry,
            states={
                self.STAGE_DATE: [
                    CallbackQueryHandler(callback=self.seats),
                ],
                self.STAGE_SEAT: [
                    CallbackQueryHandler(callback=self.dates, pattern='{"action": "back"}'),
                    CallbackQueryHandler(callback=self.check_book_seat),
                ],
                self.STAGE_BOOK: [
                    CallbackQueryHandler(callback=self.seats, pattern='{"action": "back"}'),
                    CallbackQueryHandler(callback=self.book, pattern='{"action": "book"}'),
                ],
            },
            fallbacks=[
                    CallbackQueryHandler(callback=self.seats),
                ],
            #conversation_timeout=20,
            #per_message=True,
            per_chat=True,
            per_user=True,
        )
        return conversation
