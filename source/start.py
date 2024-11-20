import datetime
from venv import logger
from telegram import Update

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import database

from utils import Keyboard

kb = Keyboard()


class Start:

    AUTH, PASS, ERROR = range(3)

    def __repr__(self):
        return "Экземпляр класса Start"

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        uid = update.effective_chat.id
        uname = update.effective_chat.username

        user = database._check_user(engine=database.engine, chat_id=uid)

        if user == None:
            await context.bot.send_message(
                chat_id=uid,
                text=f"Привет {uname}, для работы тебе надо авторизоваться. Введи пароль",
            )
            return self.AUTH

        else:

            await context.bot.send_message(
                chat_id=uid,
                text=f"Привет {uname}, рад снова видеть тебя.",
                reply_markup=kb.kb_PASS,
            )
            return self.PASS

    @logger.catch
    async def auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        uid: int = update.effective_chat.id
        username = update.effective_chat.username
        fname = update.effective_chat.first_name
        lname = update.effective_chat.last_name
        now = datetime.datetime.now()

        passwd = update.message.text

        access = database._check_password(engine=database.engine, password=passwd)
        if access:
            try:
                database._insert_user(
                    chat_id=uid,
                    username=username,
                    firstname=fname,
                    lastname=lname,
                    created_at=now,
                )
                await context.bot.send_message(chat_id=uid, text="ok")
            except:
                await context.bot.send_message(chat_id=uid, text="some error")
                return ConversationHandler.END
        else:
            attempt = database._bad_user(
                engine=database.engine, chat_id=uid, username=username
            )
            if attempt > 5:
                return ConversationHandler.END
            await context.bot.send_message(chat_id=uid, text="incorrect password")
            return self.AUTH

    def conversation(self, entry: list[CommandHandler]) -> ConversationHandler:

        conversation = ConversationHandler(
            entry_points=entry,
            states={
                self.START: [
                    CallbackQueryHandler(self.about, pattern="1"),
                    CallbackQueryHandler(self.howto, pattern="2"),
                    CallbackQueryHandler(self.ndfl, pattern="3")
                ],
                self.AUTH: [
                    MessageHandler(callback=self.count_ndfl, filters=~(filters.COMMAND)),
                    CallbackQueryHandler(self.back, pattern="back"),
                ],
                self.PASS : [
                    CallbackQueryHandler(self.back, pattern="back")
                    ],
                self.ERROR : [
                    MessageHandler(callback=self.count_ndfl, filters=~(filters.COMMAND)),
                    CallbackQueryHandler(self.back, pattern="back")
                    ]
            },
            fallbacks=entry,
        )
        return conversation