# TimeAssist Bot 🤖📅

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-✔-success.svg)
![Google Calendar API](https://img.shields.io/badge/Google_Calendar_API-v3-orange.svg)

Телеграм-бот для управления событиями Google Calendar через удобный чат-интерфейс.


## 🎯 Цели проекта
- Интеграция Google Calendar с Telegram
- Упрощение создания и управления событиями
- Автоматические напоминания о событиях
- Кроссплатформенный доступ к календарю

## ✨ Функционал
- Создание событий через тег бота
- Напоминания за 30 минут до события
- Просмотр предстоящих событий
- Мультипользовательский режим

## ⚡ Быстрый старт

### Предварительные требования
- Python 3.11+
- Docker (опционально)
- Telegram Bot Token
- Google Cloud Project с Calendar API

### Установка
```bash
git clone https://github.com/yourusername/timeassist-bot.git
cd timeassist-bot
cp config/config.example.json config/config.json
