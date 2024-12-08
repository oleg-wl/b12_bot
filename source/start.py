import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from loguru import logger

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import database

from .utils import KeyboardBuilder


class Start:

    AUTH = 1

    kb = KeyboardBuilder()
    context_logger = logger.bind()
    

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # По команде /start первичная авторизация. Если пароль верный, чатайди запишем в базу и повторная авториация будет не нужна 
        uid = update.effective_chat.id
        uname = update.message.from_user.username

        if update.message.chat.type in ['group', 'supergroup']:
            message_id = update.message.message_id

            kb = [[InlineKeyboardButton('Написать боту', url = 'tg://user?id={}'.format(context.bot.id))]]

            await update.message.reply_text(
                reply_to_message_id=message_id,
                text = 'Привет {}. Для брони мест напиши мне в личные сообщения'.format(update.message.from_user.name),
                reply_markup = InlineKeyboardMarkup(kb)

            )
            logger.debug('/Start command in groupchat')
            return ConversationHandler.END

        # проверить, что юзер уже есть в БД по чатайди
        user = database.check_user_chat_id(engine=database.engine, chat_id=uid)

        if user:
            logger.debug('/Start command in private chat - user: {}', user)
            await context.bot.send_message(
                chat_id=uid,
                text=f"Привет {uname}, рад снова видеть тебя.\n/book - для бронирования места\n/myseats - твои места\n/whois - посмотреть кто занял место (в разработке)",
            )
            return ConversationHandler.END

        # если юзера нет попросить пароль
        elif user == None:
            logger.debug('/Start in private chat - try auth -  user: {}', user)
            await context.bot.send_message(
                chat_id=uid,
                text=f"Привет {uname}, для работы тебе надо авторизоваться. Введи пароль",
            )
            # на шаге авторизации MessageHandler проверит пароль
            return self.AUTH

    async def auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        uid: int = update.effective_chat.id
        fname = update.effective_chat.first_name
        # заменить юзернейм именем если юзернейм None
        username = update.effective_chat.username if update.effective_chat.username is not None else fname
        lname = update.effective_chat.last_name
        now = datetime.datetime.now()

        passwd = update.message.text

        access = database.check_password(engine=database.engine, password=passwd)
        logger.debug('Trying access')
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
                    chat_id=uid, text="Аксес грандед"
                )
                logger.debug('Password correct. chat_id:{}, username:{}, firstname:{} inserted', uid, username, fname)
                return ConversationHandler.END

            except Exception as e:
                logger.exception(e)
                await context.bot.send_message(chat_id=uid, text="some error")
                return ConversationHandler.END
        else:
            logger.debug('Password incorrect. pass: {}, chat_id:{}, username:{}, firstname:{} inserted', passwd, uid, username, fname)
            await context.bot.send_message(chat_id=uid, text='Неверный пароль попробуй еще раз')
            return self.AUTH


    def conversation(self, entry: list[CommandHandler]) -> ConversationHandler:

        conversation = ConversationHandler(per_message=False,
            entry_points=entry,
            states={
                self.AUTH: [
                    MessageHandler(callback=self.auth, filters=(~filters.COMMAND)),
                ],
            },
            fallbacks=entry,
        )
        return conversation
    
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        await context.bot.send_message(
            chat_id=chat_id,
            text='Бот для брони места в офисе - Невская ратуша, корп4 эт2\nМеста: 2В.001, 2В.007,2В.008, 2В.011, 2В.012, 2А.002, 2А.003 забронены по дефолту. Для брони /book: лимит три дня. если бронить разные места внутри дня, бронь перезаписывается - 1 день - 1 место\nТвои активные брони на ближайшие 5 дней: /myseats\nЕсли надо оптом снять бронь (отпуск или заболел) напиши @lordcrabov'
        )
