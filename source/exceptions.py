# модуль с кастомными эксепшенами

class IncorrectPasswordType(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
