from abc import ABC, abstractmethod

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

class CoreCommand(ABC):
    """
    Абстрактный класс с основными атрибутами и методами для классов бота

    :param _type_ ABC: _description_
    """

    def __init__(self):

        self.kb = KeyboardBuilder()

    def __repr__(self):

        class_name = self.__class__.__name__
        
        attrs_lst = [f'{key}={value!r}' for key, value in self.__dict__.items() if not key.startswith('_')]
        attrs = ", ".join(attrs_lst)
        
        return f"{class_name}:attributes: {attrs}" 

    @classmethod
    def _initialisation(cls, update: Update) -> tuple[str, str|int]:
        """
        Функция возвращает юзернейм и чат айди и контекстный логгер

        :param Update update: update 
        :return : _username, _chat_id, context_logger 
        """

        _username: str = update.effective_chat.username
        _chat_id: str|int = update.effective_chat.id

        # аттрибут контекстного логгера для логгирования юзернейма и чат айди
        context_logger = logger.bind(username = _username, chat_id = _chat_id)

        return _username, _chat_id, context_logger
        
    @abstractmethod
    def conversation(self, entry):
        pass

    async def _check_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Метод для проверки, что запущена команда бота в групповом чате. Заглушка чтобы не пускать в групповой чат спамить

        :param Update update: update class
        :param ContextTypes.DEFAULT_TYPE context: context class
        :return bool: 1 - если бот запущен в группе, 0 - если бот в личном чате
        """

        if update.effective_chat.type in ['group', 'supergroup']:
            message_id = update.message.message_id

            kb = [[InlineKeyboardButton('Написать боту', url = 'tg://user?id={}'.format(context.bot.id))]]

            await update.message.reply_text(
                reply_to_message_id=message_id,
                text = 'Привет {}. Для брони мест напиши мне в личные сообщения'.format(update.message.from_user.name),
                reply_markup = InlineKeyboardMarkup(kb)

            )
            logger.info('попытка написать в групповой чат {}', message_id)
            return True
        return False

    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # для fallbascks     
        _message = update.message
        
        query = update.callback_query
        await query.answer()

        if _message.caption: #проверить если сообщение с картинкой
            
            await query.edit_message_caption('Диалог завершен')

        elif _message.text:  #проверить если в сообщении текст

            await query.edit_message_text('Диалог завершен')
            
        return ConversationHandler.END


class StartCommand(CoreCommand):

    STAGE_AUTH = 1

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return super().__repr__()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # По команде /start первичная авторизация. Если пароль верный, чатайди запишем в базу и повторная авториация будет не нужна 

        _username, _chat_id, context_logger = self._initialisation(update=update)

        _check_group_chat: int | None = await self._check_group(update=update, context=context)
        if _check_group_chat: return ConversationHandler.END

        # проверить, что юзер уже есть в БД по чатайди
        user = database.check_user_chat_id(engine=database.engine, chat_id=_chat_id)

        if user:
            context_logger.success('/Start command in private chat')
            await context.bot.send_message(
                chat_id=_chat_id,
                text=f"Привет {_username}, рад снова видеть тебя.\n/book - для бронирования места\n/myseats - твои места\n/whois - посмотреть кто занял место (в разработке)",
            )
            return ConversationHandler.END

        # если юзера нет попросить пароль
        elif user == None:
            logger.success('/Start in private chat - try auth')
            await context.bot.send_message(
                chat_id=_chat_id,
                text=f"Привет {_username}, для работы тебе надо авторизоваться. Введи пароль",
            )
            # на шаге авторизации MessageHandler проверит пароль
            return self.STAGE_AUTH

    async def auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

        _username, _chat_id, context_logger = StartCommand._initialisation(update=update)
        
        now = datetime.datetime.now()

        first_name = update.effective_chat.first_name
        last_name = update.effective_chat.last_name

        # fixed: заменить юзернейм именем если юзернейм None
        username = _username if _username is not None else first_name

        passwd = update.message.text

        access = database.check_password(engine=database.engine, password=passwd)
        context_logger.info('auth trying')
        if access:
            try:
                database.insert_user(
                    engine=database.engine,
                    chat_id=_chat_id,
                    username=username,
                    firstname=first_name,
                    lastname=last_name,
                    created_at=now,
                )
                await context.bot.send_message(
                    chat_id=_chat_id, text="Аксес грандед"
                )
                context_logger.success('Password correct. chat_id:{}, username:{}, firstname:{} inserted', _chat_id, username, first_name)
                return ConversationHandler.END

            except Exception as e:
                context_logger.exception(e)
                await context.bot.send_message(chat_id=_chat_id, text="some error")
                return ConversationHandler.END
        else:
            context_logger.warning('Password incorrect. pass: {}, chat_id:{}, username:{}, firstname:{} inserted', passwd, _chat_id, username, first_name)
            await context.bot.send_message(chat_id=_chat_id, text='Неверный пароль попробуй еще раз')
            return self.STAGE_AUTH


    def conversation(self, entry: list[CommandHandler]) -> ConversationHandler:

        conversation = ConversationHandler(
            entry_points=entry,
            states={
                self.STAGE_AUTH: [
                    MessageHandler(callback=self.auth, filters=(~filters.COMMAND)),
                ],
            },
            fallbacks=entry,
        )
        return conversation
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        _check_group_chat: int | None = await self._check_group(update=update, context=context)

        if not _check_group_chat:
        
            await update.message.reply_text(
                text='Бот для брони места в офисе - Невская ратуша, корп4 эт2\nМеста: 2В.001, 2В.007,2В.008, 2В.011, 2В.012, 2А.002, 2А.003 забронены по дефолту. Для брони /book: лимит три дня. если бронить разные места внутри дня, бронь перезаписывается - 1 день - 1 место\nТвои активные брони на ближайшие 5 дней: /myseats\nЕсли надо оптом снять бронь (отпуск или заболел) напиши @lordcrabov'
            )
