# Модуль с вспомогательными классами
# добавлен класс KeyboardBuilder

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import json

class KeyboardBuilder:

    # inline-кнопка "назад" pattern={"action": "back"}
    back_button = [InlineKeyboardButton("<< Вернуться", callback_data=json.dumps({'action': "back"}))]
    bkb = InlineKeyboardMarkup([back_button])
    
    # inline-кнопка "выйти из диалога"
    cancel_button = [InlineKeyboardButton("Выйти", callback_data="cancel")]
    ckb = InlineKeyboardMarkup([cancel_button])

    def _build_menu(
        self,
        buttons: list[InlineKeyboardButton],
        n_cols: int,
        header_buttons=None,
        footer_buttons=None,
    ) -> list[list[InlineKeyboardButton]]:

        menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
        logger.debug(menu)
        if header_buttons:
            menu.insert(0, [header_buttons])
        if footer_buttons:
            menu.append(footer_buttons)
        return menu


    def build_days_keyboard(self, action: str, days: list) -> InlineKeyboardMarkup:
        """
        Клавиатура с днями для запроса
        в callback_data передается json с ключем action для дополнительной проверки, если метод используется в разных CallbackQueryHanler-ах
        итоговый callback должен быть переведен в словарь json loads
        
        :param str action: название для проверки 
        :param list days: лист с днями
        :return InlineKeyboardMarkup: клавиатура
        """

        day_buttons = [
            InlineKeyboardButton(
                day, callback_data=json.dumps({'action': action, 'i':str(i)}))
            for i, day in enumerate(days) 
        ]

        return InlineKeyboardMarkup(self._build_menu(day_buttons, 1))
    
    def build_seats_keyboard(self, seats: list) -> InlineKeyboardMarkup:
        # клавиатура с свободными местами

        action = 'seats'
        
        seats_buttons = [
            InlineKeyboardButton(seat, callback_data=json.dumps({'action': action, 'i': str(i)}))
            for i, seat in enumerate(seats)
        ]

        def columns(seats: list):
            l = len(seats)
            if l < 6:
                return 1
            elif l < 12:
                return 2
            elif l < 18:
                return 3
            else:
                return 4

        cols = columns(seats)

        return InlineKeyboardMarkup(
            self._build_menu(seats_buttons, cols, footer_buttons=self.back_button)
        )

    def build_booked_seats_keyboard(self, booked_seats: list):

        action = 'booked_seats_command'

        booked_seats_buttons = [
            InlineKeyboardButton(booked_seat, callback_data=json.dumps({'action': action, 'i':str(i)}))
            for i, booked_seat in enumerate(booked_seats)
        ]
        return InlineKeyboardMarkup(
            self._build_menu(booked_seats_buttons, 1)
        )

if __name__ == '__main__':
    k = KeyboardBuilder()
    test = k.build_days_keyboard(action='action', days=['2021-01-01', '2022-01-02'])
    print(test)