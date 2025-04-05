import datetime
import json
import re
import threading
import time
from collections import namedtuple
import requests

from scheduler import book_timeslot, check_event_exists

with open("/timeassist/src/config/config.json", "r") as config_file:
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
    date_pattern = r"(?:\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})"
    time_pattern = r"\d{2}:\d{2}"
    datedetect = re.search(date_pattern, message)
    if datedetect:
        date = datedetect.group(0)
        day = date.replace("/", ".")
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
                        "Неправильный формат. Используйте: время, день, событие.",
                    )
            else:
                continue

        except Exception as e:
            print(f"Ошибка: {e}")
            continue


if __name__ == "__main__":
    run()
