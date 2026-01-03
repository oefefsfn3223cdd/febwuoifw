"""
Модуль управления медиа - музыка, видео, скриншоты, запись экрана
"""
import os
import subprocess
import webbrowser
import pyautogui
import datetime

KEYWORDS = [
    "скриншот", "снимок экрана", "сделай скриншот",
    "пауза", "стоп", "играй", "плей", "следующий трек", "предыдущий трек",
    "включи музыку", "выключи музыку", "поставь на паузу",
    "следующее", "предыдущее", "перемотай",
    "открой проводник", "мой компьютер", "рабочий стол",
    "сверни всё", "сверни окна", "покажи рабочий стол",
    "разверни", "закрой окно", "закрой это",
    "переключи окно", "альт таб"
]

SCREENSHOTS_FOLDER = "screenshots"

def ensure_screenshots_folder():
    if not os.path.exists(SCREENSHOTS_FOLDER):
        os.makedirs(SCREENSHOTS_FOLDER)

def handle_command(text, tts, config):
    text = text.lower().strip()
    
    # Скриншоты
    if "скриншот" in text or "снимок экрана" in text:
        ensure_screenshots_folder()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SCREENSHOTS_FOLDER}/screenshot_{timestamp}.png"
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            if tts: tts.speak("Скриншот сохранён")
        except Exception as e:
            print(f"Screenshot error: {e}")
            if tts: tts.speak("Не удалось сделать скриншот")
        return
    
    # Управление медиа (глобальные горячие клавиши)
    if text in ["пауза", "стоп", "поставь на паузу"]:
        pyautogui.press('playpause')
        if tts: tts.speak("Готово")
        return
    
    if text in ["играй", "плей", "продолжи"]:
        pyautogui.press('playpause')
        if tts: tts.speak("Воспроизвожу")
        return
    
    if "следующий" in text or "следующее" in text:
        pyautogui.press('nexttrack')
        if tts: tts.speak("Следующий трек")
        return
    
    if "предыдущий" in text or "предыдущее" in text:
        pyautogui.press('prevtrack')
        if tts: tts.speak("Предыдущий трек")
        return
    
    # Проводник и папки
    if "проводник" in text or "мой компьютер" in text:
        os.startfile("explorer")
        if tts: tts.speak("Открываю проводник")
        return
    
    if "рабочий стол" in text and "покажи" not in text:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        os.startfile(desktop)
        if tts: tts.speak("Открываю рабочий стол")
        return
    
    if "загрузки" in text or "downloads" in text:
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        os.startfile(downloads)
        if tts: tts.speak("Открываю загрузки")
        return
    
    if "документы" in text:
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        os.startfile(docs)
        if tts: tts.speak("Открываю документы")
        return
    
    # Управление окнами
    if "сверни всё" in text or "сверни окна" in text or "покажи рабочий стол" in text:
        pyautogui.hotkey('win', 'd')
        if tts: tts.speak("Готово")
        return
    
    if "разверни" in text:
        pyautogui.hotkey('win', 'up')
        if tts: tts.speak("Развернул")
        return
    
    if "закрой окно" in text or "закрой это" in text:
        pyautogui.hotkey('alt', 'f4')
        if tts: tts.speak("Закрываю")
        return
    
    if "переключи окно" in text or "альт таб" in text:
        pyautogui.hotkey('alt', 'tab')
        if tts: tts.speak("Переключаю")
        return
    
    if "сверни" in text:
        pyautogui.hotkey('win', 'down')
        if tts: tts.speak("Свернул")
        return
