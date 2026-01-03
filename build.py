"""
Скрипт для сборки MONO Assistant в EXE файл
Запустите: python build.py
"""
import os
import subprocess
import sys

def install_pyinstaller():
    """Устанавливает PyInstaller если его нет"""
    try:
        import PyInstaller
        print("✓ PyInstaller уже установлен")
    except ImportError:
        print("Устанавливаю PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller установлен")

def build_exe():
    """Собирает EXE файл"""
    print("\n" + "="*50)
    print("Сборка MONO Assistant")
    print("="*50 + "\n")
    
    # Путь к иконке
    icon_path = "sounds/interface/logo/с фоном.png"
    ico_path = "mono.ico"
    
    # Конвертируем PNG в ICO если нужно
    if os.path.exists(icon_path) and not os.path.exists(ico_path):
        try:
            from PIL import Image
            img = Image.open(icon_path)
            img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"✓ Иконка создана: {ico_path}")
        except ImportError:
            print("⚠ Pillow не установлен, иконка не будет добавлена")
            ico_path = None
        except Exception as e:
            print(f"⚠ Ошибка создания иконки: {e}")
            ico_path = None
    
    # Команда PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=MONO Assistant",
        "--onefile",  # Один EXE файл
        "--windowed",  # Без консоли
        "--clean",
        # Добавляем все необходимые данные
        "--add-data=config.json;.",
        "--add-data=sounds;sounds",
        "--add-data=model;model",
        "--add-data=modules;modules",
        "--add-data=core;core",
        "--add-data=ui;ui",
        # Скрытые импорты
        "--hidden-import=pyttsx3.drivers",
        "--hidden-import=pyttsx3.drivers.sapi5",
        "--hidden-import=pygame",
        "--hidden-import=vosk",
        "--hidden-import=pyaudio",
        "--hidden-import=pycaw",
        "--hidden-import=comtypes",
        "--hidden-import=screen_brightness_control",
        "--hidden-import=fuzzywuzzy",
        "--hidden-import=pyautogui",
        "--hidden-import=pyperclip",
        "--hidden-import=psutil",
        "--hidden-import=requests",
    ]
    
    # Добавляем иконку если есть
    if ico_path and os.path.exists(ico_path):
        cmd.append(f"--icon={ico_path}")

    # Workaround: ensure PyQt5 Qt plugins path is visible to PyInstaller.
    # On Windows with non-ASCII user paths PyInstaller's Qt hook may fail to
    # locate the plugins. Add the plugins directory via --paths using its
    # short (8.3) path when available.
    try:
        import PyQt5
        pyqt_plugins = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
        if os.path.isdir(pyqt_plugins):
            short_path = pyqt_plugins
            try:
                import ctypes
                buf = ctypes.create_unicode_buffer(260)
                if ctypes.windll.kernel32.GetShortPathNameW(pyqt_plugins, buf, len(buf)):
                    short_path = buf.value
            except Exception:
                short_path = pyqt_plugins
            cmd.append(f"--paths={short_path}")
            print(f"✓ Добавлен путь плагинов PyQt5 для PyInstaller: {short_path}")
    except Exception:
        pass
    
    # Главный файл
    cmd.append("main.py")
    
    print("Запускаю сборку...")
    print(f"Команда: {' '.join(cmd)}\n")
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "="*50)
        print("✓ СБОРКА ЗАВЕРШЕНА!")
        print("="*50)
        print(f"\nEXE файл: dist/MONO Assistant.exe")
        print("\nДля распространения скопируйте папку dist/")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Ошибка сборки: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Устанавливаем зависимости для сборки
    print("Проверяю зависимости для сборки...")
    
    try:
        from PIL import Image
        print("✓ Pillow установлен")
    except ImportError:
        print("Устанавливаю Pillow для создания иконки...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    
    install_pyinstaller()
    build_exe()
