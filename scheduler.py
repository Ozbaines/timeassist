from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=55560)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('calendar', 'v3', credentials=creds)

def book_timeslot(event_description, time, day, user_name):
    service = get_calendar_service()
    try:
        # Преобразуем день и время в формат datetime
        event_date = datetime.datetime.strptime(day, "%d.%m.%Y")  # Ожидаемый формат дня: ДД.ММ.ГГГГ
        event_time = datetime.datetime.strptime(time, "%H:%M")  # Ожидаемый формат времени: ЧЧ:ММ
        # Комбинируем дату и время
        start_time = event_date.replace(hour=event_time.hour, minute=event_time.minute, second=0, microsecond=0).isoformat() + "+03:00"  # Moscow time
        end_time = (event_date.replace(hour=event_time.hour, minute=event_time.minute, second=0, microsecond=0) + datetime.timedelta(hours=1)).isoformat() + "+03:00"  # Moscow time
    except ValueError:
        return False  # Если формат времени или дня неправильный

    event = {
        'summary': f"{event_description} (от {user_name})",  # Добавляем имя пользователя в описание
        'description': f"Событие создано пользователем {user_name}.",
        'start': {
            'dateTime': start_time,
            'timeZone': 'Europe/Moscow',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Europe/Moscow',
        },
        'attendees': [
            {'email': 'ozzybaines95@gmail.ru'},  # Все события добавляются в этот календарь
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))
    return True