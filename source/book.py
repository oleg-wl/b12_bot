import datetime
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

from .start import Start

GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID') 


class BookSeat(Start):
    DATES, SEATS, BOOK = range(2, 5)

    def __init__(self) -> None:
        super().__init__()
        logger.debug(self.__repr__())


    def __repr__(self):
        return "book class init"

    async def dates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid: int = update.effective_chat.id

        if update.effective_chat.type in ['group', 'supergroup']:
            message_id = update.message.message_id

            kb = [[InlineKeyboardButton('Написать боту', url = 'tg://user?id={}'.format(context.bot.id))]]

            await update.message.reply_text(
                reply_to_message_id=message_id,
                text = 'Привет {}. Для брони мест напиши мне в личные сообщения'.format(update.message.from_user.name),
                reply_markup = InlineKeyboardMarkup(kb)

            )
            logger.success('/book in group chat {}', message_id)
            return ConversationHandler.END

        self.days = database.select_days(engine=database.engine, d=3)
        kb_days = self.kb.build_days_keyboard(days=self.days)
        
        logger.debug(self.days)

        #проверка на callback_query сценарий: кнопка "Вернуться"
        if update.callback_query != None:
            query = update.callback_query
            await query.answer()

            await query.edit_message_caption(
                caption="Выбери день для брони", reply_markup=kb_days
            )
            return self.DATES

        await context.bot.send_photo(chat_id=uid, caption="Выбери день для брони", reply_markup=kb_days, photo='seats.jpg')
        
        return self.DATES

    async def seats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        await query.answer()

        d = update.callback_query.data
        if re.fullmatch(pattern=re.compile("[0-9]+"), string=d):
            self.selected_date = datetime.datetime.strptime(
                self.days[int(update.callback_query.data.lower())], database.FORMAT
            ).date()
        self.free_seats: filters.Sequence[str] = database.select_free_seats(
            engine=database.engine, date=self.selected_date
        )
        logger.debug("selected date {}".format(self.selected_date))
        logger.debug("free seats {}".format(self.free_seats))

        # если свободных мест нет
        if (len(self.free_seats) <= 0) | (self.free_seats == None):
            await query.edit_message_caption(
                caption="Свободных мест на эту дату нет", reply_markup=self.kb.bkb
            )
            return self.SEATS
        
        else:

            fs = self.kb.build_seats_keyboard(self.free_seats)
            await query.edit_message_caption(
                caption="Выбери место", reply_markup=fs
            )

            return self.SEATS


    async def check_book_seat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid: int = update.effective_chat.id
        query = update.callback_query
        await query.answer()

        self.selected_seat: str = self.free_seats[
            int(update.callback_query.data.lower())
        ]
        logger.debug("Selected seat {}".format(self.selected_seat))

        await query.edit_message_caption(
            caption=f"Занять {self.selected_seat} на {self.selected_date}?",
            reply_markup=InlineKeyboardMarkup(
                [
                    self.kb.back_button,
                    [InlineKeyboardButton(text="Да >>>", callback_data="book")],
                ]
            ),
        )
        return self.BOOK

    async def book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid: int = update.effective_chat.id
        username = update.effective_chat.username

        c = database.book_seat(
            engine=database.engine,
            chat_id=uid,
            selected_date=self.selected_date,
            selected_seat=self.selected_seat,
        )

        query = update.callback_query
        await query.answer()

        match c:
            case 0:
                logger.debug(f"truing parralel update {c}")
                fs = self.kb.build_seats_keyboard(self.free_seats)
                await query.edit_message_caption(
                    caption="Выбранное место уже заняли пока ты выбирал",
                    reply_markup=fs,
                )
                return self.SEATS

            case 1:
                logger.debug(
                    f"seat booked {self.selected_seat} on {self.selected_date}"
                )
                msg = f"{self.selected_date.strftime(database.FORMAT)} забронировано место - {self.selected_seat}"
                await query.edit_message_caption(
                    caption=msg,
                )

                await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=' @{} '.format(username) + msg)
                return ConversationHandler.END
            
            case _:
                logger.debug(
                    f"previous seat {c} seat to book {self.selected_seat} on {self.selected_date}"
                )
                msg = f"{self.selected_date.strftime(database.FORMAT)} забронировано место - {self.selected_seat}. С места {c} снята бронь."
                await query.edit_message_caption(
                    caption=msg,
                )

                await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=' @{} '.format(username) + msg)

                return ConversationHandler.END


    def conversation(self, entry: list[CommandHandler]) -> ConversationHandler:

        conversation = ConversationHandler(
            entry_points=entry,
            states={
                self.DATES: [
                    CallbackQueryHandler(callback=self.seats),
                ],
                self.SEATS: [
                    CallbackQueryHandler(callback=self.dates, pattern="back"),
                    CallbackQueryHandler(callback=self.check_book_seat),
                ],
                self.BOOK: [
                    CallbackQueryHandler(callback=self.seats, pattern="back"),
                    CallbackQueryHandler(callback=self.book, pattern="book"),
                ],
            },
            fallbacks=entry,
        )
        return conversation
