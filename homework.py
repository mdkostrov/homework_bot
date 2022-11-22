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
    AnswerError, DictionaryError, RequestError, UndocumentedStatusError
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
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(
            f'Сообщение в Telegram отправлено: {message}')
    except telegram.TelegramError as tg_error:
        logger.error(
            f'Сообщение в Telegram не отправлено: {tg_error}'
        )


def get_api_answer(current_timestamp: int) -> dict:
    """Получает ответ от API Яндекс.Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            api_error = (
                f'Эндпоинт {ENDPOINT} недоступен!'
                f'HTTP-код ответа: {response.status_code}'
            )
            logger.error(api_error)
            raise AnswerError(api_error)
        return response.json()
    except requests.exceptions.RequestException as request_error:
        api_error = (
            f'Ошибка запроса (RequestException). Код ответа API: {request_error}'
        )
        logger.error(api_error)
        raise RequestError(api_error) from request_error
    except json.JSONDecodeError as value_error:
        api_error = (
            f'Ошибка значения (ValueError). Код ответа API: {value_error}'
        )
        logger.error(api_error)
        raise json.JSONDecodeError(api_error) from value_error



def check_response(response: dict) -> list:
    """Проверяет полученные от API данные."""
    if not type(response) is dict:
        error_message = (
            'Полученные данные не являются словарем!'
        )
        logger.error(error_message)
        raise TypeError(error_message)
    if response.get('homeworks') is None:
        error_message = (
            'Ключ homeworks имеет неверное значение'
        )
        logger.error(error_message)
        raise DictionaryError(error_message)
    if not type(response.get('homeworks')) is list:
        error_message = (
            'Данные по ключу homeworks не являются списком!'
        )
        logger.error(error_message)
        raise TypeError(error_message)
    if response['homeworks'] == []:
        return {}
    return response['homeworks'][0]


def parse_status(homework: dict) -> str:
    """Извлекает из ответа API статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        error_message = (
            f'Ошибка: пустое значение homework_name {homework_name}'
        )
        logger.error(error_message)
        raise UndocumentedStatusError(error_message)
    if homework_status is None:
        error_message = (
            f'Ошибка: пустое значение homework_status {homework_status}'
        )
        logger.error(error_message)
        raise UndocumentedStatusError(error_message)
    if homework_status not in HOMEWORK_VERDICTS:
        error_message = (
            f'Ошибка: незадокументированный статус домашней работы {homework_status}'
        )
        logger.error(error_message)
        raise UndocumentedStatusError(error_message)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка присутствия переменных окружения (токенов)."""
    tokens_error = (
        'Отсутствует переменная окружения (токен):'
    )
    tokens_exist = True
    if PRACTICUM_TOKEN is None:
        tokens_exist = False
        logger.critical(
            f'{tokens_error} PRACTICUM_TOKEN'
        )
    if TELEGRAM_TOKEN is None:
        tokens_exist = False
        logger.critical(
            f'{tokens_error} TELEGRAM_TOKEN'
        )
    if TELEGRAM_CHAT_ID is None:
        tokens_exist = False
        logger.critical(
            f'{tokens_error} TELEGRAM_CHAT_ID'
        )
    return tokens_exist


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
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
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
