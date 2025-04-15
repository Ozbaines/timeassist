import datetime
import json
import re
import threading
import time
from collections import namedtuple
import requests

from scheduler import book_timeslot, check_event_exists

with open("config/config.json", "r") as config_file: #Для контейнера: /timeassist/src/config/config.json
    config = json.load(config_file)
    api_key = config["api_key"]

# Список для хранения событий
events_list = []

# Именованный кортеж для возврата данных из getLastMessage
MessageData = namedtuple(
    "MessageData", ["last_msg", "chat_id", "update_id", "user_name"]
)


def getLastMessage(offset=None):
    url = f"https://api.telegram.org/bot{api_key}/getUpdates"
    params = {"timeout": 60, "offset": offset} if offset else {"timeout": 60}
    response = requests.get(url, params=params)
    data = response.json()

    if not data.get("result"):
        # print("Нет новых сообщений.")
        return None, offset

    last_update = data["result"][-1]
    if "message" not in last_update:
        print("Сообщение не содержит данных 'message'.")
        return None, offset

    last_msg = last_update["message"].get("text", "")
    chat_id = last_update["message"]["chat"]["id"]
    update_id = last_update["update_id"]
    user_name = last_update["message"]["from"].get("first_name", "Unknown")

    return MessageData(last_msg, chat_id, update_id, user_name), update_id + 1


def sendMessage(chat_id, text_message):
    url = f"https://api.telegram.org/bot{api_key}/sendMessage?text={text_message}&chat_id={chat_id}"
    response = requests.get(url)
    return response


def parse_event_message(message):
    try:
        normalized_msg = ' '.join(message.lower().strip().split())
        date_keywords = {
            'завтра': (datetime.date.today() + datetime.timedelta(days=1)).strftime('%d.%m.%Y'),
            'послезавтра': (datetime.date.today() + datetime.timedelta(days=2)).strftime('%d.%m.%Y')
        }
        keyword_variations = {
            'послезавтра': ['послезавтра', 'послезавтро', 'после завтра', 'poslezavtra'],
            'завтра': ['завтра', 'завтро', 'zavtra']    
        }
        weekdays = {
            'в понедельник': 0, 'понедельник': 0, 'v ponedelnik': 0, 'впонедельник': 0, 'vponedelnik': 0, 'понидельник': 0, 'monday': 0,
            'во вторник': 1, 'в вторник': 1, 'вторник': 1, 'v vtornik': 1, 'vo vtornik': 1, 'tuesday': 1,
            'в среду': 2, 'среда': 2, 'среду': 2, 'wednesday': 2,
            'в четверг': 3, 'четверг': 3, 'Thursday': 3,
            'в пятницу': 4, 'пятница': 4, 'пятницу': 4, 'friday': 4,
            'в субботу': 5, 'суббота': 5, 'субботу': 5, 'subbota': 5, 'subboty': 5, 'saturday': 5,
            'в воскресение': 6, 'в воскресенье': 6, 'воскресенье': 6, 'воскресенью': 6, 'воскресение': 6, 'voskresenie': 6, 'sunday': 6
        }
        for base_keyword, date_str in date_keywords.items():
            for variation in keyword_variations.get(base_keyword, [base_keyword]):
                if variation in normalized_msg:
                    message = normalized_msg.replace(variation, date_str)
                    break

        for day_name, day_num in weekdays.items():
            if day_name in normalized_msg:
                days_ahead = (day_num - datetime.date.today().weekday()) % 7
                if days_ahead == 0:  # Если сегодня этот день недели
                    days_ahead = 7    # Берем следующий
                target_date = datetime.date.today() + datetime.timedelta(days=days_ahead)
                date_str = target_date.strftime('%d.%m.%Y')
                message = normalized_msg.replace(day_name, date_str)
                break
        
            # ---------
        date_pattern = r"(?:\d{2}[./-]\d{2}[./-]\d{4}|\d{2}[./-]\d{2}[./-]\d{2}|\d{4}[./-]\d{2}[./-]\d{2})"
        time_pattern = r"\d{2}:\d{2}"
        datedetect = re.search(date_pattern, message)
        if datedetect:
            date = datedetect.group(0)
            day = date.replace("/", ".").replace("-", ".")
            if len(day.split('.')[2]) == 2:
                day2, month, year = day.split('.')
                day = f"{day2}.{month}.20{year}"
            text = message.replace(date, "")
        else:
            return None

        timedetect = re.search(time_pattern, message)
        if timedetect:
            time = timedetect.group(0)
            event = text.replace(time, "")
        else:
            return None
        return {"time": time, "day": day, "event": event}
    
    except Exception as e:
        print(f"Ошибка при парсинге сообщения '{message}': {str(e)}")
        return None

def add_event_to_list(event_time, event_date, event_name, chat_id, event_id):
    event_datetime = datetime.datetime.strptime(
        f"{event_date} {event_time}", "%d.%m.%Y %H:%M"
    )
    events_list.append(
        {
            "datetime": event_datetime,
            "name": event_name,
            "chat_id": chat_id,
            "event_id": event_id,
        }
    )


def check_reminders():
    while True:
        now = datetime.datetime.now()
        for event in events_list[:]:
            time_difference = (event["datetime"] - now).total_seconds()
            if 0 < time_difference <= 1800:
                if check_event_exists(event["event_id"]):
                    reminder_message = f"⏰ Напоминание: событие '{event['name']}' начнется через 30 минут!"
                    sendMessage(event["chat_id"], reminder_message)
                events_list.remove(event)
                print(f"Событие '{event['name']}' удалено из списка напоминаний.")
            elif time_difference <= 0:
                events_list.remove(event)
                print(
                    f"Событие '{event['name']}' удалено из списка напоминаний (время прошло)."
                )
        time.sleep(60)


def run():
    offset = None

    # Запускаем поток для проверки напоминаний
    reminder_thread = threading.Thread(target=check_reminders, daemon=True)
    reminder_thread.start()

    while True:
        try:
            message_data, offset = getLastMessage(offset)
            if message_data is None:
                continue
            if "@timeassistBot" in message_data.last_msg:
                message = message_data.last_msg.replace("@timeassistBot", "").strip()
                parsed_event = parse_event_message(message)
                if parsed_event:
                    event_id = book_timeslot(
                        parsed_event["event"],
                        parsed_event["time"],
                        parsed_event["day"],
                        message_data.user_name,
                    )
                    if event_id:
                        sendMessage(
                            message_data.chat_id,
                            "Событие успешно добавлено в календарь!",
                        )
                        add_event_to_list(
                            parsed_event["time"],
                            parsed_event["day"],
                            parsed_event["event"],
                            message_data.chat_id,
                            event_id,
                        )
                        print(
                            f"Событие '{parsed_event['event']}' добавлено в список напоминаний (ID: {event_id})."
                        )
                    else:
                        sendMessage(
                            message_data.chat_id,
                            "Ошибка при добавлении события в календарь.",
                        )
                else:
                    sendMessage(
                        message_data.chat_id,
                        "Привет, но у тебя неправильный формат, используй: время, день, событие. Все получится.",
                    )
            else:
                continue

        except Exception as e:
            print(f"Ошибка: {e}")
            continue


if __name__ == "__main__":
    run()
