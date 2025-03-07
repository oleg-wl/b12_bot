"""This is a very simple example on how one could implement a custom error handler."""
import json
from loguru import logger
import traceback
import os
import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

LOG_CHAT_ID = os.getenv('LOG_CHAT_ID')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Handler пишет трейсбек в файл error.log и сообщает в чат об ошибке

    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    
    error_log_message: str = (
        f"|{datetime.datetime.now().strftime(format='%d.%m.%Y %H:%M:%S')}|ERROR|\n"
        f"update = {json.dumps(update_str, indent=2, ensure_ascii=False)}"
        f"context.chat_data = {str(context.chat_data)}\n\n"
        f"context.user_data = {str(context.user_data)}\n\n"
        f"{tb_string}"
    )

    with open('error.log', mode='wt', encoding='utf8') as error_file:
        error_file.write(error_log_message)
        

    # send the message
    await context.bot.send_message(
        chat_id=LOG_CHAT_ID, text='b12bot: exception \n'+context.error, parse_mode=ParseMode.HTML
    )
