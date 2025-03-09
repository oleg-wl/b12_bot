# Модуль для отправки сообщений ботом асинхронно

# Немного юникода
# https://apps.timwhitlock.info/emoji/tables/unicode

from abc import ABC, abstractmethod
import os
import asyncio
import aiohttp

from database.db_tools import DBA_tools
from database.sql import show_chat_ids

from dotenv import load_dotenv
from loguru import logger

load_dotenv("config.env")

engine = DBA_tools().engine

smiles = ('\U0001F973', '\U00002705')

chat_ids = '680222638'
msg = "Привет! Бот обновился. Новая версия уже здесь \U0001F973\n\U00002705 Теперь можно посмотреть кто забронил какие места на ближайшие даты\nКоманда /whos уже добавлена\n\U00002705 еще небольшие исправления и новые баги"

class SendMessageClient(ABC):
    
    def __init__(self, token: str):
        self.request: str = 'https://api.telegram.org/bot{token}/'.format(token=token)
        self.headers: dict[str, str] = {
            'Accept':'application/json'
        }
        self.request_body: dict[str, str] = {
            'chat_id': None,
            'text': None,
        }

        # Создаем контейнер для объекта сессии aiohttp при инициализации объекта класса
        self.session: None
    
    async def __aenter__(self):
        # Создаем сессию при входе в контекстный менеджер
        self.session = aiohttp.ClientSession(self.request)
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        # Закрываем сессию при выходе из контекстного менеджера
        await self.session.close()

    @abstractmethod
    async def send_message(self, session: aiohttp.ClientSession, chat_id: str, message: str):
        pass


class AnnounceMessage(SendMessageClient):
    
    def __init__(self, token):
        super().__init__(token)

    async def send_message(self, chat_id, messsage:str):
        
        self.request_body['chat_id'] = chat_id
        self.request_body['text'] = messsage
        
        async with self.session.get('sendMessage', headers=self.headers, json=self.request_body) as response:
            resp_status = response.status
            resp_text = await response.text()
        match resp_status:
            case 200:
                logger.success(' Сообщение отправлено {}'.format(chat_id))
            
            case _:
                logger.error('Сообщение не отправлено. {} '.format(resp_text))


async def main():
    t = os.getenv('BOT_API')
#    chat_ids = show_chat_ids(engine=engine)
#    for chat_id in chat_ids:

    async with AnnounceMessage(token=t) as s:
        await s.send_message(chat_id=chat_ids, messsage=msg)


if __name__ == '__main__':
    asyncio.run(main())