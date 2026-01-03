"""
Smart Assistant module
ТОЛЬКО утилитарные функции.
Диалог и болтовня обрабатываются LLM (Ollama), НЕ ЗДЕСЬ.
"""

import datetime
import math
import re
import json
import os
import requests

# ⚠️ ТОЛЬКО функциональные ключевые слова
KEYWORDS = [
    # Время и дата
    "который час", "сколько времени", "время",
    "дата", "какой день", "какое число",

    # Калькулятор
    "посчитай", "сколько будет", "вычисли",

    # Погода
    "погода", "какая погода", "температура",

    # Заметки
    "запомни", "заметка", "что запомнил", "мои заметки",
]

NOTES_FILE = "jarvis_notes.json"

WORD_TO_NUM = {
    "ноль": 0, "один": 1, "два": 2, "три": 3, "четыре": 4,
    "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9,
    "десять": 10, "одиннадцать": 11, "двенадцать": 12,
    "тринадцать": 13, "четырнадцать": 14, "пятнадцать": 15,
    "шестнадцать": 16, "семнадцать": 17, "восемнадцать": 18,
    "девятнадцать": 19, "двадцать": 20,
    "тридцать": 30, "сорок": 40, "пятьдесят": 50,
    "шестьдесят": 60, "семьдесят": 70,
    "восемьдесят": 80, "девяносто": 90,
    "сто": 100, "тысяча": 1000
}


# ===================== NOTES =====================

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


# ===================== CALCULATOR =====================

def words_to_number(text):
    result = text
    for word, num in sorted(WORD_TO_NUM.items(), key=lambda x: -len(x[0])):
        result = result.replace(word, str(num))
    return result


def calculate(expression):
    try:
        expr = expression.lower()
        expr = words_to_number(expr)

        expr = (
            expr.replace("плюс", "+")
            .replace("минус", "-")
            .replace("умножить на", "*")
            .replace("умножить", "*")
            .replace("разделить на", "/")
            .replace("делить на", "/")
            .replace("делить", "/")
            .replace("в степени", "**")
            .replace("степень", "**")
        )

        expr = re.sub(r"[^\d+\-*/().]", "", expr)

        if expr and re.search(r"\d", expr):
            return eval(expr, {"__builtins__": {}, "math": math})

    except Exception as e:
        print(f"Calculator error: {e}")

    return None


# ===================== WEATHER =====================

def get_weather(city="Москва"):
    try:
        import urllib.parse
        city_encoded = urllib.parse.quote(city)

        response = requests.get(
            f"https://wttr.in/{city_encoded}?format=%t+%C&lang=ru",
            timeout=10
        )

        if response.status_code == 200:
            return response.text.strip()

    except Exception as e:
        print(f"Weather error: {e}")

    return None


# ===================== MAIN HANDLER =====================

def handle_command(text, tts, config):
    text = text.lower().strip()

    # ===== ВРЕМЯ / ДАТА =====
    if "который час" in text or "сколько времени" in text or text == "время":
        now = datetime.datetime.now()
        tts.speak(f"Сейчас {now.hour} часов {now.minute} минут")
        return

    if "дата" in text or "какой день" in text or "какое число" in text:
        now = datetime.datetime.now()
        days = [
            "понедельник", "вторник", "среда",
            "четверг", "пятница", "суббота", "воскресенье"
        ]
        months = [
            "января", "февраля", "марта", "апреля",
            "мая", "июня", "июля", "августа",
            "сентября", "октября", "ноября", "декабря"
        ]
        tts.speak(
            f"Сегодня {days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year} года"
        )
        return

    # ===== КАЛЬКУЛЯТОР =====
    if any(w in text for w in ["посчитай", "сколько будет", "вычисли"]):
        expr = (
            text.replace("посчитай", "")
            .replace("сколько будет", "")
            .replace("вычисли", "")
            .strip()
        )
        result = calculate(expr)
        if result is not None:
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            tts.speak(f"Результат: {result}")
        else:
            tts.speak("Не смог вычислить.")
        return

    # ===== ПОГОДА =====
    if "погода" in text or "температура" in text:
        city = "Москва"
        words = text.split()
        if "в" in words:
            idx = words.index("в")
            if idx + 1 < len(words):
                city = words[idx + 1]

        weather = get_weather(city)
        if weather:
            tts.speak(f"Погода в городе {city}: {weather}")
        else:
            tts.speak("Не удалось получить данные о погоде.")
        return

    # ===== ЗАМЕТКИ =====
    if "запомни" in text or "заметка" in text:
        note = text.replace("запомни", "").replace("заметка", "").strip()
        if note:
            notes = load_notes()
            notes.append({
                "text": note,
                "date": datetime.datetime.now().isoformat()
            })
            save_notes(notes)
            tts.speak("Запомнил.")
        else:
            tts.speak("Что нужно запомнить?")
        return

    if "что запомнил" in text or "мои заметки" in text:
        notes = load_notes()
        if notes:
            tts.speak(f"У вас {len(notes)} заметок.")
        else:
            tts.speak("Заметок пока нет.")
        return
