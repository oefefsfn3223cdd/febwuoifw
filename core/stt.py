import json
import os
import sys
import pyaudio
from vosk import Model, KaldiRecognizer

def get_base_path():
    """Возвращает базовый путь для ресурсов"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SpeechToText:
    def __init__(self, config_path="config.json"):
        self.base_path = get_base_path()
        self.config = {}
        self.load_config(config_path)
        
        # Путь к модели относительно базового пути
        model_name = self.config.get("stt", {}).get("model_path", "model")
        self.model_path = os.path.join(self.base_path, model_name)
        
        self.model = None
        self.recognizer = None
        self.pa = pyaudio.PyAudio()
        self.stream = None
        
        self.initialize_model()

    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

    def initialize_model(self):
        if not os.path.exists(self.model_path):
            print(f"Error: Vosk model not found at '{self.model_path}'")
            return

        try:
            print(f"Loading Vosk model from {self.model_path}...")
            self.model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            print("Vosk model loaded successfully.")
        except Exception as e:
            print(f"Failed to load model: {e}")

    def start_stream(self):
        if self.stream is None:
            try:
                self.stream = self.pa.open(format=pyaudio.paInt16, 
                                         channels=1, 
                                         rate=16000, 
                                         input=True, 
                                         frames_per_buffer=8000)
                self.stream.start_stream()
            except Exception as e:
                print(f"Error starting audio stream: {e}")

    def stop_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def listen(self):
        if not self.model:
            return ""

        if self.stream is None:
            self.start_stream()

        try:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")
                if text:
                    return text
        except Exception as e:
            print(f"Error during listening: {e}")
            self.stop_stream() # Try to reset stream on error
        
        return ""

if __name__ == "__main__":
    stt = SpeechToText()
    if stt.model:
        print("Listening... (Press Ctrl+C to stop)")
        try:
            while True:
                text = stt.listen()
                if text:
                    print(f"Recognized: {text}")
        except KeyboardInterrupt:
            print("\nStopped.")