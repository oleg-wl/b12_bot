import datetime
from telegram import Update
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
from .exceptions import IncorrectPasswordType

from .utils import Keyboard

kb = Keyboard()
kb()


class Start:

    AUTH, PASS, DATES, SEATS = range(4)

    def __repr__(self):
        return "Экземпляр класса Start"

    @logger.catch
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        uid = update.effective_chat.id
        uname = update.effective_chat.username

        user = database.check_user(engine=database.engine, chat_id=uid)

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

        try:
            # проверяем пароль на корректность. Пароль должен быть строкой или приводиться к строке
            # если тип пароля некорректный дается возможность ввести пароль повторно
            access = database.check_password(engine=database.engine, password=passwd)
        except IncorrectPasswordType:
            await context.bot.send_message(chat_id=uid, text="Incorrect password input")
            return self.AUTH
        else:
            # access = True если хеши паролей совпали
            if access:
                try:
                    database.insert_user(
                        engine=database.engine,
                        chat_id=uid,
                        username=username,
                        firstname=fname,
                        lastname=lname,
                        created_at=now,
                    )
                    await context.bot.send_message(
                        chat_id=uid, text="ok", reply_markup=kb.kb_PASS
                    )
                    return self.PASS
                
                # в начало конверсейшена если эксепшен
                # TODO: добавить эксепшены SQLA на повторный ввод пароля если ошибки базы
                except Exception as e:
                    logger.exception(e)
                    await context.bot.send_message(chat_id=uid, text="some error")
                    return ConversationHandler.END
            else:
                await context.bot.send_message(
                    chat_id=uid, text="Incorrect password try again"
                )
                return self.AUTH
    
    @logger.catch
    async def dates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid: int = update.effective_chat.id
        
        days = database.select_days(engine=database.engine)

        kb_days = kb.build_days_keyboard(days=days)

        query = update.callback_query
        await query.answer()

        #await context.bot.send_message(chat_id=uid, text='days', reply_markup=kb_days)
        await query.edit_message_text(text='days', reply_markup=kb_days)
        
        try:
            button_data = update.callback_query.data.lower()
            context.user_data["day"] = days[int(button_data)]
        except ValueError:
            pass
        except KeyError:
            pass
        logger.debug(context.user_data['day'])

        return self.DATES

    async def seats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        await query.answer()

        button_data = update.callback_query.data.lower()
        logger.debug(button_data)

        return ConversationHandler.END


    def conversation(self, entry: list[CommandHandler]) -> ConversationHandler:

        conversation = ConversationHandler(
            entry_points=entry,
            states={
                self.AUTH: [
                    MessageHandler(callback=self.auth, filters=(~filters.COMMAND)),
                ],
                self.PASS: [
                    #CallbackQueryHandler(self.seats, pattern="seats"),
                    CallbackQueryHandler(self.dates, pattern="dates"),
                ],
                self.DATES: [
                    CallbackQueryHandler(callback=self.seats, )
                ],
                self.SEATS: [],
            },
            fallbacks=entry,
        )
        return conversation
