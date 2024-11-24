from venv import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class Keyboard:

    back_button = [InlineKeyboardButton("<< Вернуться", callback_data="back")]
    bkb = InlineKeyboardMarkup([back_button])

    def _build_menu(
        self, buttons: list, n_cols: int, header_buttons=None, footer_buttons=None
    ):
        menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
        logger.debug(menu)
        if header_buttons:
            menu.insert(0, [header_buttons])
        if footer_buttons:
            menu.append(footer_buttons)
        return menu

    def _PASS(self) -> InlineKeyboardMarkup:

        days_button = [
            InlineKeyboardButton("Выбрать дату", callback_data="dates"),
            InlineKeyboardButton("Посмотреть свои места", callback_data="seats"),
        ]

        return InlineKeyboardMarkup(self._build_menu(days_button, 1))
    
    def build_days_keyboard(self, days: list):

        day_buttons = [InlineKeyboardButton(day, callback_data=str(i)) for i, day in enumerate(days)]

        return InlineKeyboardMarkup(self._build_menu(day_buttons, 1, footer_buttons=self.back_button))
    
    def build_seats_keyboard(self, seats: list) -> InlineKeyboardMarkup:

        seats_buttons = [InlineKeyboardButton(seat, callback_data=str(i)) for i, seat in enumerate(seats)]

        def columns(seats: list):
            l = len(seats)
            if l < 6:
                    return 1
            elif l < 12: 
                return 2
            elif l < 18:
                return 3
            else: return 4
        cols = columns(seats)
                
        return InlineKeyboardMarkup(self._build_menu(seats_buttons, cols, footer_buttons=self.back_button))

    def __call__(self) -> None:
        
        self.kb_PASS: InlineKeyboardMarkup = self._PASS()