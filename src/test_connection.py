from scheduler import get_calendar_service  

def check_google_calendar_connection():
    try:
        service = get_calendar_service()
        calendars = service.calendarList().list().execute()
        print("✅ Успешное подключение к Google Calendar!")
        print(f"Доступные календари: {len(calendars.get('items', []))}")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    check_google_calendar_connection()