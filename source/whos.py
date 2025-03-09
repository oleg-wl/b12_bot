import datetime
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


class WhosSeat(CoreCommand):
    
    STAGE_DATE, STAGE_BACK = range(10, 12)

    def __init__(self):
        super().__init__()
    
    def __repr__(self):
        return super().__repr__()
    
    async def whos_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        _, _chat_id, context_logger = self._initialisation(update=update)

        _check_group_chat: int | None = await self._check_group(update=update, context=context)
        if _check_group_chat: return ConversationHandler.END

        self.days = database.select_days(engine=database.engine, d=3)
        #TODO: json
        kb_days: InlineKeyboardMarkup = self.kb.build_days_keyboard(days=self.days)

        query = update.callback_query
        if (query) and (query != None):
            await query.answer()

            await query.edit_message_text(
                text="Выбери день для просмотра", reply_markup=kb_days)
            return self.STAGE_DATE

        context_logger.info('whos_date:: {}'.format(repr(self)))

        await context.bot.send_message(chat_id=_chat_id, text="Выбери день для просмотра", reply_markup=kb_days)
        
        return self.STAGE_DATE
    
    async def whos_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        _, _chat_id, context_logger = self._initialisation(update=update)
        query = update.callback_query
        await query.answer()

        #TODO: json
        d = update.callback_query.data
        if re.fullmatch(pattern=re.compile("[0-9]+"), string=d):
            selected_date = datetime.datetime.strptime(
                self.days[int(update.callback_query.data.lower())], database.FORMAT
            ).date()
        
        whos_msg = database.show_who_booked(engine=database.engine, date=selected_date)

        await query.edit_message_text(text='Места заняты:\n' + whos_msg, reply_markup=InlineKeyboardMarkup([self.kb.back_button]))
        
        return self.STAGE_BACK        

    def conversation(self, entry):
        
        conversation = ConversationHandler(
            entry_points=entry,
            states={
                self.STAGE_DATE: [
                    CallbackQueryHandler(callback=self.whos_message),
                ],
                self.STAGE_BACK: [
                    CallbackQueryHandler(callback=self.whos_date, pattern="back"),
                ],
            },
            fallbacks=[CallbackQueryHandler(callback=self.cancel_conversation, pattern='cancel')],
            #conversation_timeout=10,
            #per_message=True,
            per_chat=True,
            per_user=True,
        )
        return conversation