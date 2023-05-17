# Yandex.Practicum Homework Telegram Bot
### Описание проекта.
Телеграм бот, который уведомляет о проверке ревьюером домашнего задания на платформе Яндекс.Практикум.

##### Технологии.
В проекте использованы следующие технологии:
Python 3.7, Python-telegram-bot 13.7, Requests 2.26.0.

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/mdkostrov/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение (для Windows):

```
python -m venv env
```

```
source venv/scripts/activate
```

Обновить установщик пакетов pip:

```
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Создать файл .env с переменными окружения:

```
touch .env
```

Заполнить его переменными (вручную или с помощью редактора nano):

```
nano .env
```
Пример заполнения:

```
PRACTICUM_TOKEN = <токен вашей учетной записи Яндекс.Практикума, получить можно по ссылке https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a>
TELEGRAM_TOKEN = <токен вашего бота в Telegram>
TELEGRAM_CHAT_ID = <id чата, куда придет сообщение>
```

Запуск приложения (для Windows):

```
python homework
```
