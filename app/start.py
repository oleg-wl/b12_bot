import datetime
from telegram import Update

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from database.init_db import DBA_tools
from database.sql import _check_password, _check_user

db = DBA_tools()

class Start:

    def __repr__(self):
        return 'Экземпляр класса Start'
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        uid = update.effective_chat.id
        uname = update.effective_chat.username
        fname = update.effective_chat.first_name
        lname = update.effective_chat.last_name
        now = datetime.datetime.now()

        user = _check_user(chat_id=uid)

        if user == None:
            await context.bot.send_message(
                chat_id=uid,
                text=f"Привет {uname}, пожалуйста введи пароль"
                )


