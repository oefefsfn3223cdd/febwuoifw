import os
import importlib
import json
import sys
from fuzzywuzzy import fuzz
from prompt_toolkit import prompt
import requests


def get_base_path():
    """Возвращает базовый путь для ресурсов"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CommandProcessor:
    def __init__(self, config_path="config.json", tts=None):
        self.base_path = get_base_path()
        self.config = {}
        self.load_config(config_path)
        self.modules = []
        self.tts = tts
        self.load_modules()

    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

    def load_modules(self):
        modules_path = os.path.join(self.base_path, "modules")
        if not os.path.exists(modules_path):
            print(f"⚠️ Modules path not found: {modules_path}")
            return
            
        sys.path.insert(0, self.base_path)
        
        # Приоритет загрузки модулей (smart_assistant должен быть последним как fallback)
        module_priority = ['system_control', 'app_control', 'media_control', 'web_control', 'input_control', 'timer_control', 'smart_assistant']
        loaded_names = set()
        
        # Сначала загружаем по приоритету
        for module_name in module_priority:
            self._load_module(module_name)
            loaded_names.add(module_name)
        
        # Затем остальные модули
        try:
            modules_dir = os.path.join(self.base_path, "modules")
            if os.path.exists(modules_dir):
                for filename in os.listdir(modules_dir):
                    if filename.endswith(".py") and not filename.startswith("__"):
                        module_name = filename[:-3]
                        if module_name not in loaded_names:
                            self._load_module(module_name)
        except Exception as e:
            print(f"Error loading additional modules: {e}")
    
    def ask_llm(self, prompt: str) -> str:
        print(f"🧠 Sending to LLM: {prompt}")

        SYSTEM_PROMPT = (
            "Ты голосовой ассистент на русском языке. "
            "Отвечай КОРОТКО и ПО ДЕЛУ. "
            "Максимум 1–2 коротких предложения. "
            "Без воды, без объяснений, без лишних слов. "
            "Если можно — ответь одним предложением."
        )

        try:
            import requests

            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:3b",
                    "prompt": f"{SYSTEM_PROMPT}\n\nПользователь: {prompt}\nАссистент:",
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "num_predict": 50
                    }
                },
                timeout=10
            )

            print(f"🧠 LLM status: {r.status_code}")
            data = r.json()

            answer = data.get("response", "").strip()
            print(f"🤖 LLM answer: {answer}")

            return answer

        except Exception as e:
            print(f"❌ LLM exception: {e}")
            return ""



    def _load_module(self, module_name):
        try:
            module = importlib.import_module(f"modules.{module_name}")
            if hasattr(module, "handle_command") and hasattr(module, "KEYWORDS"):
                self.modules.append(module)
                print(f"✓ Loaded module: {module_name} ({len(module.KEYWORDS)} keywords)")
        except Exception as e:
            print(f"✗ Failed to load module {module_name}: {e}")

    def process(self, text):
        text = text.lower().strip()
        if not text:
            return False
            
        print(f"\n🎤 Processing: '{text}'")
        
        # Собираем все совпадения с их scores
        matches = []
        
        for module in self.modules:
            best_keyword_ratio = 0
            best_keyword = ""
            best_keyword_len = 0
            
            for keyword in module.KEYWORDS:
                ratio = 0
                
                # Точное совпадение фразы - максимальный приоритет
                if keyword in text:
                    # Чем длиннее keyword, тем выше приоритет
                    ratio = 100 + len(keyword)
                elif text in keyword:
                    ratio = 95
                else:
                    # Fuzzy matching
                    ratio = max(
                        fuzz.token_set_ratio(keyword, text),
                        fuzz.partial_ratio(keyword, text)
                    )
                
                # Предпочитаем более длинные (специфичные) keywords при равном score
                if ratio > best_keyword_ratio or (ratio == best_keyword_ratio and len(keyword) > best_keyword_len):
                    best_keyword_ratio = ratio
                    best_keyword = keyword
                    best_keyword_len = len(keyword)
            
            if best_keyword_ratio >= 80:
                matches.append({
                    'module': module,
                    'score': best_keyword_ratio,
                    'keyword': best_keyword,
                    'keyword_len': best_keyword_len
                })
        
        # Сортируем по score, затем по длине keyword (более специфичные первые)
        matches.sort(key=lambda x: (x['score'], x['keyword_len']), reverse=True)
        
        if matches:
            best = matches[0]
            print(f"🎯 Best match: {best['module'].__name__} (score: {best['score']}, keyword: '{best['keyword']}')")
            
            try:
                best['module'].handle_command(text, self.tts, self.config)
                return True
            except Exception as e:
                print(f"❌ Error executing command: {e}")
                import traceback
                traceback.print_exc()
                if self.tts:
                    self.tts.speak("Произошла ошибка при выполнении команды.")
        else:
            print("🤖 No command match → sending to LLM")

            answer = self.ask_llm(text)

            if answer:
                print(f"🤖 LLM answer: {answer}")
                if self.tts:
                    self.tts.speak(answer)
            else:
                if self.tts:
                    self.tts.speak("Я не смог придумать ответ.")
        
        return False
    
    def reload_modules(self):
        """Перезагрузка модулей без перезапуска"""
        self.modules = []
        self.load_modules()
        print("🔄 Modules reloaded")