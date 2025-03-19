import requests
import datetime
import json
from scheduler import book_timeslot
import re
import api_key

api_key = api_key.api['api_key']

def check_email(email):
    regex = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    if re.search(regex, email):
        print("Valid Email")
        return True
    else:
        print("Invalid Email")
        return False

def getLastMessage(offset=None):
    url = "https://api.telegram.org/bot{}/getUpdates".format(api_key)
    params = {"timeout": 60, "offset": offset} if offset else {"timeout": 60}
    response = requests.get(url, params=params)
    data = response.json()

    if not data['result']:
        print("Нет новых сообщений.")
        return None, None, None, offset

    last_msg = data['result'][-1]['message']['text']
    chat_id = data['result'][-1]['message']['chat']['id']
    update_id = data['result'][-1]['update_id']
    return last_msg, chat_id, update_id, update_id + 1  # Возвращаем update_id + 1 для offset

def sendMessage(chat_id, text_message):
    url = 'https://api.telegram.org/bot' + str(api_key) + '/sendMessage?text=' + str(text_message) + '&chat_id=' + str(chat_id)
    response = requests.get(url)
    return response

def sendInlineMessageForService(chat_id):
    text_message = 'Hi! I am your Hair Sylist Bot!\nI can help you book an appointment.\n\nYou can control me using these commands\n\n/start-to start chatting with the bot\n/cancel-to stop chatting with the bot.\n\nFor more information please contact automationfeed@gmail.com'
    keyboard = {'keyboard': [
        [{'text': 'Cut'}, {'text': 'Dye'}],
        [{'text': 'Perm'}, {'text': 'Reborn'}]
    ]}
    key = json.JSONEncoder().encode(keyboard)
    url = 'https://api.telegram.org/bot' + str(api_key) + '/sendmessage?chat_id=' + str(chat_id) + '&text=' + str(text_message) + '&reply_markup=' + key
    response = requests.get(url)
    return response

def sendInlineMessageForBookingTime(chat_id):
    text_message = 'Please choose a time slot...'
    current_time = datetime.datetime.now()
    current_hour = str(current_time)[11:13]
    # ----------- Chunk of if statement to determine which inline keyboard to reply user ----------------
    if int(current_hour) < 8:
        keyboard = {'keyboard': [
            [{'text': '08:00'}], [{'text': '10:00'}],
            [{'text': '12:00'}], [{'text': '14:00'}],
            [{'text': '16:00'}], [{'text': '18:00'}],
        ]}
    elif 8 <= int(current_hour) < 10:
        keyboard = {'keyboard': [
            [{'text': '10:00'}],
            [{'text': '12:00'}], [{'text': '14:00'}],
            [{'text': '16:00'}], [{'text': '18:00'}],
        ]}
    elif 10 <= int(current_hour) < 12:
        keyboard = {'keyboard': [
            [{'text': '12:00'}], [{'text': '14:00'}],
            [{'text': '16:00'}], [{'text': '18:00'}],
        ]}
    elif 12 <= int(current_hour) < 14:
        keyboard = {'keyboard': [
            [{'text': '14:00'}],
            [{'text': '16:00'}], [{'text': '18:00'}],
        ]}
    elif 14 <= int(current_hour) < 16:
        keyboard = {'keyboard': [
            [{'text': '16:00'}], [{'text': '18:00'}],
        ]}
    elif 16 <= int(current_hour) < 18:
        keyboard = {'keyboard': [
            [{'text': '18:00'}],
        ]}
    elif 18 <= int(current_hour) < 24:
        keyboard = {'keyboard': [
            [{'text': '19:00'}],
        ]}    
    else:
        return sendMessage(chat_id, 'Please try again tmr')
    # ----------------------------------------------------------------------------------------------------
    key = json.JSONEncoder().encode(keyboard)
    url = 'https://api.telegram.org/bot' + str(api_key) + '/sendmessage?chat_id=' + str(chat_id) + '&text=' + str(text_message) + '&reply_markup=' + key
    response = requests.get(url)
    return response

def run():
    offset = None  # Инициализируем offset
    update_id_for_booking_of_time_slot = ''
    event_description = ''
    booking_time = ''

    while True:
        try:
            current_last_msg, chat_id, current_update_id, offset = getLastMessage(offset)
            if current_last_msg is None:
                continue  # Нет новых сообщений, ждем

            if current_last_msg == '/start':
                sendInlineMessageForService(chat_id)
            elif current_last_msg in ['Cut', 'Dye', 'Perm', 'Reborn']:
                event_description = current_last_msg
                sendInlineMessageForBookingTime(chat_id)
            elif current_last_msg in ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '19:00']:
                booking_time = current_last_msg
                update_id_for_booking_of_time_slot = current_update_id
                sendMessage(chat_id, "Please enter email address:")
            elif current_last_msg == '/cancel':
                update_id_for_booking_of_time_slot = ''
                sendMessage(chat_id, "Booking cancelled.")
            elif update_id_for_booking_of_time_slot != current_update_id and update_id_for_booking_of_time_slot != '':
                if check_email(current_last_msg):
                    update_id_for_booking_of_time_slot = ''
                    sendMessage(chat_id, "Booking please wait.....")
                    input_email = current_last_msg
                    response = book_timeslot(event_description, booking_time, input_email)
                    if response:
                        sendMessage(chat_id, f"Appointment is booked. See you at {booking_time}")
                    else:
                        sendMessage(chat_id, "Please try another timeslot and try again tomorrow")
                else:
                    sendMessage(chat_id, "Please enter a valid email.\nEnter /cancel to quit chatting with the bot\nThanks!")

        except Exception as e:
            print(f"Ошибка: {e}")
            continue

if __name__ == "__main__":
    run()