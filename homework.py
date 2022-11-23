import json
import logging
import os
import requests
import sys
import time
import telegram

from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import (
    AnswerError, DictionaryError,
    RequestError, UndocumentedStatusError
)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s - %(name)s'
)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler(sys.stdout)
)


def send_message(bot, message):
    """Отправляет сообщение в Телеграм."""
    try:
        logger.debug('Попытка отправить сообщение в Telegram.')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение в Telegram отправлено: {message}')
    except telegram.error.TelegramError as tg_error:
        error_message = f'Ошибка отправки сообщения: {tg_error}'
        logger.error(error_message)  # без логгирования здесь тесты не проходят
        raise telegram.error.TelegramError from tg_error


def get_api_answer(timestamp: int) -> dict:
    """Получает ответ от API Яндекс.Практикума."""
    current_timestamp = timestamp or int(time.time())
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            api_error = (
                f'Эндпоинт {ENDPOINT} недоступен!'
                f'HTTP-код ответа: {response.status_code}'
            )
            raise AnswerError(api_error)
        return response.json()
    except requests.exceptions.RequestException as request_error:
        api_error = (
            f'Ошибка запроса (RequestException).'
            f'Код ответа API: {request_error}'
        )
        raise RequestError(api_error) from request_error
    except json.JSONDecodeError as value_error:
        api_error = (
            f'Ошибка значения (ValueError). Код ответа API: {value_error}'
        )
        raise json.JSONDecodeError(api_error) from value_error


def check_response(response: dict) -> list:
    """Проверяет полученные от API данные."""
    if not isinstance(response, dict):
        error_message = (
            'Полученные данные не являются словарем!'
        )
        raise TypeError(error_message)
    homeworks = response.get('homeworks')
    api_keys = list(response.keys())
    if 'homeworks' not in api_keys or 'current_date' not in api_keys:
        error_message = (
            'Отсутствуют ключи homeworks или current_date '
            'в полученном словаре'
        )
        raise DictionaryError(error_message)
    if not isinstance(homeworks, list):
        error_message = (
            'Данные по ключу homeworks не являются списком!'
        )
        raise TypeError(error_message)
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекает из ответа API статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        error_message = (
            f'Ошибка: отсутствует ключ homework_name: {homework_name}'
        )
        raise UndocumentedStatusError(error_message)
    if 'status' not in homework:
        error_message = (
            f'Ошибка: отсутствует ключ status: {homework_status}'
        )
        raise UndocumentedStatusError(error_message)
    if homework_status not in HOMEWORK_VERDICTS:
        error_message = (
            f'Ошибка: незадокументированный статус'
            f'домашней работы: {homework_status}'
        )
        raise UndocumentedStatusError(error_message)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка присутствия переменных окружения (токенов)."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(
            'Работа программы завершена! Отсутствуют переменные окружения.'
        )
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if current_status != message:
                    current_status = message
                    send_message(bot, message)
                current_timestamp = response.get('current_date')
            logger.debug(
                'Статус не изменился. Следующая проверка через 10 минут.'
            )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.critical(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
