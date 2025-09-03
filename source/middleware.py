from telegram import Update
from telegram.ext import ContextTypes

class GrAuthMiddleware:
    def __init__(self, channel_id):
        self.channel_id = channel_id
    
    async def check_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user = update.effective_user
        
        try:
            member = await context.bot.get_chat_member(
                chat_id=self.channel_id, 
                user_id=user.id
            )
            
            if member.status in ["member", "administrator", "creator"]:
                return True
            else:
                await update.message.reply_text(
                    "❌ Это секретный бот \n"
                )
                return False
                
        except Exception:
            await update.message.reply_text("⚠️ Ошибка проверки")
            return False
