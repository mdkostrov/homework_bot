class AnswerError(Exception):
    """Ошибка ответа API."""


class DictionaryError(Exception):
    """Ошибка словаря в полученном ответе."""


class RequestError(Exception):
    """Ошибка запроса к API."""


class UndocumentedStatusError(Exception):
    """Ошибка статуса домашней работы (незадокументированный статус)."""
