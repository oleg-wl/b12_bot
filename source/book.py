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

        self.selected_seat: str = None
        self.selected_date: datetime.datetime = None

    def __repr__(self):
        return "book class init"

    async def dates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid: int = update.effective_chat.id

        #проверка что бот не в групповом чате
        _check_group_chat: int | None = await self._check_group(update=update, context=context)

        logger.bind(user=update.effective_user.name, chat=context._chat_id).debug('check group chat - {}'.format(_check_group_chat))
        if _check_group_chat: return ConversationHandler.END

        # забрать дни
        self.days = database.select_days(engine=database.engine, d=3)
        kb_days = self.kb.build_days_keyboard(days=self.days)
        
        logger.bind(user=update.effective_user.name, chat=context._chat_id).info("Enter conversation book")

        #проверка на callback_query сценарий: кнопка "Вернуться"
        if update.callback_query != None and update.callback_query.data == 'back':
            query = update.callback_query
            await query.answer()

            await query.edit_message_caption(
                caption="Выбери день для брони", reply_markup=kb_days
            )
            return self.DATES

        await context.bot.send_photo(chat_id=uid, caption="Выбери день для брони", reply_markup=kb_days, photo='seats.jpg')
        
        logger.bind(user=update.effective_user.name, chat=context._chat_id).info("conversation book, selected date {}".format(self.selected_date))
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
        logger.bind(user=update.effective_user.name, chat=context._chat_id).info("Conversation book, state {}".format(self.DATES))

        # если свободных мест нет
        if (len(self.free_seats) <= 0) | (self.free_seats == None):
            await query.edit_message_caption(
                caption="Свободных мест на эту дату нет", reply_markup=self.kb.bkb
            )
            return self.DATES
        
        else:

            fs = self.kb.build_seats_keyboard(self.free_seats)
            await query.edit_message_caption(
                caption="Выбери место", reply_markup=fs
            )

            logger.bind(user=update.effective_user.name, chat=context._chat_id).info("conversation book, state {}, selected date{}".format(self.DATES, self.selected_date))
            return self.SEATS


    async def check_book_seat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid: int = update.effective_chat.id
        query = update.callback_query
        await query.answer()

        self.selected_seat: str = self.free_seats[
            int(update.callback_query.data.lower())
        ]

        logger.bind(user=update.effective_user.name, chat=context._chat_id).info("conversation book, state {}, selected seat {}".format(self.SEATS, self.selected_seat))

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
                logger.bind(user=update.effective_user.name, chat=context._chat_id).debug(f"parralel book {c}")
                fs = self.kb.build_seats_keyboard(self.free_seats)
                await query.edit_message_caption(
                    caption="Выбранное место уже заняли пока ты выбирал",
                    reply_markup=fs,
                )
                return self.SEATS

            case 1:
                logger.bind(user=update.effective_user.name, chat=context._chat_id).info(
                    f"Забронировано место {self.selected_seat}, дата - {self.selected_date}"
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

    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        _message = update.message
        
        query = update.callback_query
        await query.answer()

        if _message.caption: #проверить если сообщение с картинкой
            
            await query.edit_message_caption('Диалог завершен')

        elif _message.text:  #проверить если в сообщении текст

            await query.edit_message_text('Диалог завершен')
            
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
            fallbacks=[CallbackQueryHandler(callback=self.cancel_conversation, pattern='cancel')],
            #conversation_timeout=20,
            #per_message=True,
            per_chat=True,
            per_user=True,
        )
        return conversation
