import datetime
import json
import re

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


class WhosCommand(CoreCommand):
    
    STAGE_DATE, STAGE_BACK = range(10, 12)

    def __init__(self):
        super().__init__()
        
        # переопределить кнопку назад
        self.kb.back_button = [InlineKeyboardButton(text='<< Вернуться',callback_data=json.dumps({"action":"whos_back"}))]
        self.kb.bkb = InlineKeyboardMarkup([self.kb.back_button])
    
    def __repr__(self):
        return super().__repr__()
    
    async def whos_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        _, _chat_id, context_logger = self._initialisation(update=update)

        _check_group_chat: int | None = await self._check_group(update=update, context=context)
        if _check_group_chat: return ConversationHandler.END

        self.days = database.select_days(engine=database.engine, d=3)
        kb_days: InlineKeyboardMarkup = self.kb.build_days_keyboard(action='whos_command', days=self.days)

        query = update.callback_query
        
        context_logger.info('whos_date:: {}'.format(repr(self)))
        if query != None and query.data == '{"action": "whos_back"}':
            await query.answer()

            await query.edit_message_text(
                text="Выбери день для просмотра", reply_markup=kb_days)
            return self.STAGE_DATE

        else:
            await context.bot.send_message(chat_id=_chat_id, text="Выбери день для просмотра", reply_markup=kb_days)
            
            return self.STAGE_DATE
    
    async def whos_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        _, _chat_id, context_logger = self._initialisation(update=update)
        
        query = update.callback_query
        
        # проверка коллбека для выбора даты
        action, i = self._json_callback(query=query)

        if action == 'whos_command':
            await query.answer()
            selected_date = datetime.datetime.strptime(
                self.days[i], database.FORMAT
            ).date()
        
            whos_msg = database.show_who_booked(engine=database.engine, date=selected_date)

            await query.edit_message_text(text='Места заняты:\n' + whos_msg, reply_markup=InlineKeyboardMarkup([self.kb.back_button]))
            
            return self.STAGE_BACK        

    def conversation(self, entry):
        pattern = re.compile(pattern='{"action": "whos_command".*')

        conversation = ConversationHandler(
            entry_points=entry,
            states={
                self.STAGE_DATE: [
                    CallbackQueryHandler(callback=self.whos_message, pattern=pattern),
                ],
                self.STAGE_BACK: [
                    CallbackQueryHandler(callback=self.whos_date, pattern='{"action": "whos_back"}'),
                ],
            },
            fallbacks=entry,
            #conversation_timeout=10,
            #per_message=True,
            per_chat=True,
            per_user=True,
        )
        return conversation