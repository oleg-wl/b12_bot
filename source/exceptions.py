# модуль с кастомными эксепшенами

class IncorrectPassword(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
