import requests
import datetime
import json
from scheduler import book_timeslot
import re
import api_key

api_key = api_key.api['api_key']

def getLastMessage(offset=None):
    url = "https://api.telegram.org/bot{}/getUpdates".format(api_key)
    params = {"timeout": 60, "offset": offset} if offset else {"timeout": 60}
    response = requests.get(url, params=params)
    data = response.json()

    if not data.get('result'):
        print("Нет новых сообщений.")
        return None, None, None, None, offset

    last_update = data['result'][-1]
    if 'message' not in last_update:
        print("Сообщение не содержит данных 'message'.")
        return None, None, None, None, offset

    last_msg = last_update['message'].get('text', '')
    chat_id = last_update['message']['chat']['id']
    update_id = last_update['update_id']
    user_name = last_update['message']['from'].get('first_name', 'Unknown')  # Имя пользователя
    return last_msg, chat_id, update_id, user_name, update_id + 1  # Возвращаем update_id + 1 для offset

def sendMessage(chat_id, text_message):
    url = 'https://api.telegram.org/bot' + str(api_key) + '/sendMessage?text=' + str(text_message) + '&chat_id=' + str(chat_id)
    response = requests.get(url)
    return response

def parse_event_message(message):
    date_pattern = r"(?:\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})"
    time_pattern = r"\d{2}:\d{2}"
    datedetect = re.search(date_pattern, message)
    if datedetect:
        date = datedetect.group(0)
        day = date.replace('/', '.')
        text = message.replace(date, "")
    else:
        return None, None, None

    timedetect = re.search(time_pattern, message)
    if timedetect:
        time = timedetect.group(0)
        event = text.replace(time, "")
    else:
        return None, None, None

    return time, day, event

def run():
    offset = None  # Инициализируем offset

    while True:
        try:
            current_last_msg, chat_id, current_update_id, user_name, offset = getLastMessage(offset)
            if current_last_msg is None:
                continue  # Нет новых сообщений, ждем

            # Проверяем, что сообщение содержит тег бота
            if "@timeassistBot" in current_last_msg:
                # Убираем тег бота из сообщения
                message = current_last_msg.replace(f"@timeassistBot", "").strip()
                # Парсим сообщение
                parsed_event = parse_event_message(message)
                if parsed_event[0]:  # Проверяем, что парсинг прошел успешно
                    time, day, event = parsed_event
                    # Отправляем подтверждение
                    sendMessage(chat_id, f"Событие добавлено: {event} на {day} в {time}.")
                    # Создаем событие в календаре
                    response = book_timeslot(event, time, day, user_name)
                    if response:
                        sendMessage(chat_id, "Событие успешно добавлено в календарь!")
                    else:
                        sendMessage(chat_id, "Ошибка при добавлении события в календарь.")
                else:
                    sendMessage(chat_id, "Неправильный формат. Используйте: время, день, событие.")
            else:
                continue  # Игнорируем сообщения без тега бота

        except Exception as e:
            print(f"Ошибка: {e}")
            continue

if __name__ == "__main__":
    run()