import sys
import os
import json
import threading
import time
from PyQt5.QtWidgets import QApplication
from core.tts import TextToSpeech
from core.stt import SpeechToText
from core.processor import CommandProcessor
from ui.gui import AssistantGUI

def get_base_path():
    """Возвращает базовый путь для ресурсов (работает и для EXE и для .py)"""
    if getattr(sys, 'frozen', False):
        # Запущено как EXE
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

class JarvisAssistant:
    def __init__(self):
        self.config = self.load_config()
        self.tts = TextToSpeech(os.path.join(BASE_PATH, "config.json"))
        self.stt = SpeechToText(os.path.join(BASE_PATH, "config.json"))
        self.processor = CommandProcessor(config_path=os.path.join(BASE_PATH, "config.json"), tts=self.tts)
        self.is_listening = False
        self.gui = None
        self.first_start = True

    def load_config(self):
        config_path = os.path.join(BASE_PATH, "config.json")
        example_path = os.path.join(BASE_PATH, "config.example.json")
        
        # Если config.json не существует, копируем из example
        if not os.path.exists(config_path):
            if os.path.exists(example_path):
                import shutil
                shutil.copy(example_path, config_path)
                print("✅ Создан config.json из шаблона")
            else:
                raise FileNotFoundError("Не найден config.json или config.example.json")
        
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def start_listening(self):
        self.is_listening = True
        
        if self.gui:
            self.gui.signals.log_message.emit("🚀 Система запущена")
            self.gui.signals.status_update.emit("Слушаю...")
            self.gui.signals.listening_state.emit(True)
        
        # Приветствие только при первом запуске
        if self.first_start and self.config.get("assistant", {}).get("greeting", True):
            name = self.config.get("assistant", {}).get("name", "Моно")
            self.tts.speak(f"Привет! Я {name}, к вашим услугам.")
            self.first_start = False
        
        wake_words = self.config.get("assistant", {}).get("wake_words", ["джарвис"])
        
        while self.is_listening:
            try:
                text = self.stt.listen()
                if not text:
                    continue
                
                text_lower = text.lower().strip()
                
                if self.gui:
                    self.gui.signals.log_message.emit(f"Вы: {text}")
                
                # Проверяем wake word
                is_wake_word = any(word in text_lower for word in wake_words)
                
                # Убираем wake word из команды
                command_text = text_lower
                for word in wake_words:
                    command_text = command_text.replace(word, "").strip()
                
                # Если сказали только wake word
                if not command_text and is_wake_word:
                    responses = ["Да, сэр?", "Слушаю вас", "Чем могу помочь?", "К вашим услугам"]
                    import random
                    self.tts.speak(random.choice(responses))
                    continue
                
                # Пропускаем пустые команды (шум)
                if not command_text or len(command_text) < 2:
                    continue

                # Обрабатываем команду
                print(f"\n{'='*50}")
                self.processor.process(command_text)
                # Ответы теперь отправляются через TTS напрямую в GUI
                        
            except Exception as e:
                print(f"Error in listening loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.5)

    def stop_listening(self):
        self.is_listening = False
        self.stt.stop_stream()
        
        if self.gui:
            self.gui.signals.status_update.emit("Пауза")
            self.gui.signals.listening_state.emit(False)
            self.gui.signals.log_message.emit("⏸️ Прослушивание остановлено")

def main():
    from PyQt5.QtCore import Qt
    from ui.gui import SplashScreen
    
    # Настройка для высокого DPI
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("MONO ASSISTANT")
    app.setStyle("Fusion")
    
    # Создаём ассистента
    assistant = JarvisAssistant()
    gui = AssistantGUI(assistant)
    assistant.gui = gui
    assistant.tts.set_gui(gui)
    
    # Splash screen с анимацией
    splash = SplashScreen()
    
    def on_splash_finished():
        gui.show()
        # Автозапуск прослушивания и приветствие
        gui.start_with_greeting()
    
    splash.finished.connect(on_splash_finished)
    splash.start_animation()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()