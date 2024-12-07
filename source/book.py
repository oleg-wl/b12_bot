import datetime
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from loguru import logger

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import database

from .utils import Keyboard

kb = Keyboard()
kb()


class BookSeat:

    DATES, SEATS, BOOK = range(3)

    context_logger = logger.bind()

    def __repr__(self):
        return "Экземпляр класса BookSeat"

    @logger.catch
    async def dates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid: int = update.effective_chat.id
        uname = update.effective_chat.username
        message_id = update.message.message_id
        
        if update.message.chat.type in ['group', 'supergroup']:

            kb = [[InlineKeyboardButton('Написать боту', url = 'tg://user?id={}'.format(context.bot.id))]]

            await update.message.reply_text(
                reply_to_message_id=message_id,
                text = 'Привет {}. Для брони мест напиши мне в личные сообщения'.format(uname),
                reply_markup = InlineKeyboardMarkup(kb)

            )
            return ConversationHandler.END

        self.days = database.select_days(engine=database.engine, d=3)
        kb_days = kb.build_days_keyboard(days=self.days)

        await context.bot.send_photo(chat_id=uid, text="Выбери день для брони", reply_markup=kb_days, photo='seats.jpg')

        return self.DATES

    async def seats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid: int = update.effective_chat.id

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

        # если свободных мест нет
        if (len(self.free_seats) < 0) | (self.free_seats == None):
            await query.edit_message_caption(
                caption="Свободных мест на эту дату нет", reply_markup=kb.bkb
            )
            return self.PASS

        fs = kb.build_seats_keyboard(self.free_seats)
        await query.edit_message_caption(
            caption="Выбери место", reply_markup=fs
        )

        logger.debug("selected date {}".format(self.selected_date))
        logger.debug("free seats {}".format(self.free_seats))

        return self.SEATS

    @logger.catch()
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
                    kb.back_button,
                    [InlineKeyboardButton(text="Да >>>", callback_data="book")],
                ]
            ),
        )
        return self.BOOK

    async def book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid: int = update.effective_chat.id

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
                fs = kb.build_seats_keyboard(self.free_seats)
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
                    reply_markup=kb.kb_PASS,
                )

                return ConversationHandler.END
            
            case _:
                logger.debug(
                    f"previous seat {c} seat to book {self.selected_seat} on {self.selected_date}"
                )
                msg = f"{self.selected_date.strftime(database.FORMAT)} забронировано место - {self.selected_seat}. С места {c} снята бронь."
                await query.edit_message_caption(
                    caption=msg,
                    reply_markup=kb.kb_PASS,
                )

                await context.bot.send_message(chat_id=)

                return ConversationHandler.END

    async def check_my_seats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        uid = update.effective_chat.id

        self.booked_seats = database.select_my_seats_d(
            engine=database.engine, chat_id=uid
        )
        query = update.callback_query
        await query.answer()

        # проверка если нет занятых мест возвращаем в меню
        if len(self.booked_seats) == 0:
            await query.edit_message_text('У тебя нет занятых мест на ближайшее время', reply_markup=kb.kb_PASS)
            return self.PASS
        
        buttons = []
        for r in self.booked_seats:
            date: datetime = r[0].strftime(database.FORMAT)
            seat: str = r[1]
            buttons.append("{} место {}".format(date, seat))

        await query.edit_message_text(
            "Твои места на ближайшие дни. Выбери, с какого снять бронь",
            reply_markup=kb.build_booked_seats_keyboard(buttons),
        )

        return self.MYSEATS

    async def check_unbook_seat(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):

        query = update.callback_query
        await query.answer()

        i = int(query.data)
        logger.debug(i)

        self.selected_unbook_date = self.booked_seats[i][0]
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
                [[InlineKeyboardButton(text="Да >>>", callback_data="unbook")], kb.back_button]
            ),
        )
        return self.UNBOOK

    async def unbook(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        database.unbook_seat(engine=database.engine, selected_unbook_date=self.selected_unbook_date, selected_unbook_seat=self.selected_unbook_seat)

        query =  update.callback_query
        await query.answer()

        await query.edit_message_text('Место освобождено', reply_markup=kb.kb_PASS)
        return self.PASS     

    def conversation(self, entry: list[CommandHandler]) -> ConversationHandler:

        conversation = ConversationHandler(per_message=False,
            entry_points=entry,
            states={
                self.AUTH: [
                    MessageHandler(callback=self.auth, filters=(~filters.COMMAND)),
                ],
                self.PASS: [
                    CallbackQueryHandler(self.check_my_seats, pattern="myseats"),
                    CallbackQueryHandler(self.dates, pattern="dates"),
                ],
                self.DATES: [
                    CallbackQueryHandler(callback=self.start, pattern="back"),
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
                self.MYSEATS: [
                    CallbackQueryHandler(callback=self.start, pattern="back"),
                    CallbackQueryHandler(callback=self.check_unbook_seat),
                ],
                self.UNBOOK: [
                    CallbackQueryHandler(callback=self.start, pattern="back"),
                    CallbackQueryHandler(callback=self.unbook, pattern="unbook"),
                ],
            },
            fallbacks=entry,
        )
        return conversation
