"""This is a very simple example on how one could implement a custom error handler."""
import html
import json
from loguru import logger
import traceback
import os

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

LOG_CHAT_ID = os.getenv('LOG_CHAT_ID')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""

    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    
    message_1: str = (
        "An exception was rised in bot \n"
        "</pre>\n\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"

    )
    
    message_2 = (
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    if len(message_1) > 4095: message_1 = message_1[-4095:] 
    if len(message_2) > 4095: message_2 = message_2[-4095:] 

    # send the message
    await context.bot.send_message(
        chat_id=LOG_CHAT_ID, text=message_1, parse_mode=ParseMode.HTML
    )

    await context.bot.send_message(
        chat_id=LOG_CHAT_ID, text=message_2, parse_mode=ParseMode.HTML
    )
