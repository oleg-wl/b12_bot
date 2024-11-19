from telegram import InlineKeyboardButton, InlineKeyboardMarkup



class Keyboard:

    back_button = [InlineKeyboardButton("<< Вернуться", callback_data="back")]
    bkb = InlineKeyboardMarkup([back_button])

    @staticmethod
    def build_menu(buttons: list, n_cols: int,
                header_buttons=None,
                footer_buttons=None):
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, [header_buttons])
        if footer_buttons:
            menu.append([footer_buttons])
        return menu