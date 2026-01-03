import sys
import os
import threading
import pygame
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QSystemTrayIcon, QMenu, QAction, QFrame, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QBrush, QPen, QPixmap

# Инициализация pygame для звуков
pygame.mixer.init()

def get_base_path():
    """Возвращает базовый путь для ресурсов"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_PATH = get_base_path()

class SignalHandler(QObject):
    log_message = pyqtSignal(str)
    status_update = pyqtSignal(str)
    listening_state = pyqtSignal(bool)
    jarvis_response = pyqtSignal(str)
    timer_update = pyqtSignal(str)

class PulsingCircle(QWidget):
    """Анимированный индикатор прослушивания - ЧБ версия"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self.pulse_radius = 40
        self.is_active = False
        self.color = QColor("#888888")
        
        self.animation = QTimer(self)
        self.animation.timeout.connect(self.animate)
        self.pulse_direction = 1
        
    def start_pulse(self):
        self.is_active = True
        self.color = QColor("#ffffff")
        self.animation.start(50)
        self.update()
        
    def stop_pulse(self):
        self.is_active = False
        self.color = QColor("#888888")
        self.animation.stop()
        self.pulse_radius = 40
        self.update()
        
    def animate(self):
        self.pulse_radius += self.pulse_direction * 2
        if self.pulse_radius >= 50:
            self.pulse_direction = -1
        elif self.pulse_radius <= 35:
            self.pulse_direction = 1
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        
        # Внешнее свечение
        if self.is_active:
            for i in range(3):
                alpha = 40 - i * 12
                color = QColor(self.color)
                color.setAlpha(alpha)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(center, self.pulse_radius + i * 10, self.pulse_radius + i * 10)
        
        # Основной круг
        painter.setBrush(QBrush(QColor("#1a1a1a")))
        painter.setPen(QPen(self.color, 2))
        painter.drawEllipse(center, 35, 35)
        
        # Иконка микрофона
        painter.setPen(QPen(self.color, 3))
        painter.drawLine(center.x(), center.y() - 10, center.x(), center.y() + 5)
        painter.drawArc(center.x() - 8, center.y() - 15, 16, 20, 0, 180 * 16)
        painter.drawLine(center.x() - 10, center.y() + 10, center.x() + 10, center.y() + 10)
        painter.drawLine(center.x(), center.y() + 10, center.x(), center.y() + 15)


class SplashScreen(QWidget):
    """Экран загрузки с анимацией"""
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 400)
        
        # Центрируем на экране
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 400) // 2, (screen.height() - 400) // 2)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Логотип
        self.logo_label = QLabel()
        logo_path = os.path.join(BASE_PATH, "sounds", "interface", "logo", "без фона.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)
        
        # Название
        self.title = QLabel("MONO ASSISTANT")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.title.setStyleSheet("color: white; letter-spacing: 3px;")
        layout.addWidget(self.title)
        
        # Подзаголовок
        self.subtitle = QLabel("Загрузка...")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setFont(QFont("Segoe UI", 10))
        self.subtitle.setStyleSheet("color: #888888;")
        layout.addWidget(self.subtitle)
        
        # Эффект прозрачности для анимации
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Анимация появления
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(800)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        # Анимация исчезновения
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out.finished.connect(self.on_fade_out_finished)
    
    def start_animation(self):
        # Воспроизводим звук открытия
        sound_path = os.path.join(BASE_PATH, "sounds", "interface", "open.wav")
        if os.path.exists(sound_path):
            try:
                sound = pygame.mixer.Sound(sound_path)
                sound.play()
            except:
                pass
        
        self.show()
        self.fade_in.start()
        
        # Через 2 секунды начинаем исчезновение
        QTimer.singleShot(2000, self.start_fade_out)
    
    def start_fade_out(self):
        self.fade_out.start()
    
    def on_fade_out_finished(self):
        self.hide()
        self.finished.emit()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Тёмный фон с закруглёнными углами
        painter.setBrush(QBrush(QColor(15, 15, 15, 240)))
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawRoundedRect(self.rect(), 20, 20)


class AssistantGUI(QMainWindow):
    def __init__(self, assistant_core):
        super().__init__()
        self.assistant = assistant_core
        self.signals = SignalHandler()
        self.signals.log_message.connect(self.append_log)
        self.signals.status_update.connect(self.update_status)
        self.signals.listening_state.connect(self.update_listening_state)
        self.signals.jarvis_response.connect(self.show_jarvis_response)
        self.signals.timer_update.connect(self.update_timer_display)
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("MONO ASSISTANT")
        self.setGeometry(100, 100, 450, 650)
        self.setMinimumSize(400, 550)
        
        # ЧБ минималистичный стиль
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0a;
            }
            QLabel {
                color: #ffffff;
            }
            QTextEdit {
                background-color: #111111;
                border: 1px solid #333333;
                border-radius: 10px;
                color: #cccccc;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
            QPushButton {
                background-color: #ffffff;
                border: none;
                border-radius: 25px;
                color: #000000;
                font-size: 14px;
                font-weight: bold;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #cccccc;
            }
            QPushButton#stopBtn {
                background-color: #333333;
                color: #ffffff;
            }
            QPushButton#stopBtn:hover {
                background-color: #444444;
            }
            QPushButton#settingsBtn {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 25px;
                color: #888888;
            }
            QPushButton#settingsBtn:hover {
                background-color: #222222;
                color: #ffffff;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Логотип
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignCenter)
        
        self.logo_label = QLabel()
        logo_path = os.path.join(BASE_PATH, "sounds", "interface", "logo", "без фона.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        logo_layout.addWidget(self.logo_label)
        layout.addWidget(logo_container)
        
        # Заголовок
        title_label = QLabel("MONO ASSISTANT")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff; letter-spacing: 3px;")
        layout.addWidget(title_label)
        
        subtitle = QLabel("Voice Assistant")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: #666666; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Индикатор прослушивания
        indicator_container = QWidget()
        indicator_layout = QHBoxLayout(indicator_container)
        indicator_layout.setAlignment(Qt.AlignCenter)
        self.pulse_indicator = PulsingCircle()
        indicator_layout.addWidget(self.pulse_indicator)
        layout.addWidget(indicator_container)
        
        # Статус
        self.status_label = QLabel("Готов к работе")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 14))
        self.status_label.setStyleSheet("color: #888888; margin: 10px;")
        layout.addWidget(self.status_label)
        
        # Блок ответа
        self.response_label = QLabel("")
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.response_label.setStyleSheet("""
            color: #ffffff;
            background-color: #1a1a1a;
            border: 1px solid #333333;
            border-radius: 10px;
            padding: 15px;
            margin: 5px;
        """)
        self.response_label.setWordWrap(True)
        self.response_label.setMinimumHeight(60)
        self.response_label.hide()
        layout.addWidget(self.response_label)
        
        # Таймер
        self.timer_label = QLabel("")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(QFont("Segoe UI", 12))
        self.timer_label.setStyleSheet("""
            color: #ffffff;
            background-color: #1a1a1a;
            border: 1px solid #444444;
            border-radius: 8px;
            padding: 8px;
        """)
        self.timer_label.hide()
        layout.addWidget(self.timer_label)
        
        # Лог
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("История команд...")
        layout.addWidget(self.log_area)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.btn_listen = QPushButton("🎤  Слушать")
        self.btn_listen.setFixedHeight(50)
        self.btn_listen.setCursor(Qt.PointingHandCursor)
        self.btn_listen.clicked.connect(self.toggle_listening)
        btn_layout.addWidget(self.btn_listen)
        
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setObjectName("settingsBtn")
        self.btn_settings.setFixedSize(50, 50)
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.clicked.connect(self.open_settings)
        btn_layout.addWidget(self.btn_settings)
        
        layout.addLayout(btn_layout)
        
        # Трей
        self.setup_tray()


    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Иконка для трея
        logo_path = os.path.join(BASE_PATH, "sounds", "interface", "logo", "без фона.png")
        if os.path.exists(logo_path):
            self.tray_icon.setIcon(QIcon(logo_path))
        
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
            }
            QMenu::item:selected {
                background-color: #333333;
            }
        """)
        
        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show)
        
        listen_action = QAction("Слушать", self)
        listen_action.triggered.connect(self.toggle_listening)
        
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(listen_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def append_log(self, text):
        if text.startswith("Вы:"):
            formatted = f'<span style="color: #888888;">👤 {text}</span>'
        elif text.startswith("Моно:") or text.startswith("Mono:"):
            formatted = f'<span style="color: #ffffff;">🤖 {text}</span>'
        elif "ошибка" in text.lower() or "error" in text.lower():
            formatted = f'<span style="color: #ff6666;">⚠️ {text}</span>'
        else:
            formatted = f'<span style="color: #666666;">{text}</span>'
        
        self.log_area.append(formatted)
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def update_status(self, text):
        self.status_label.setText(text)
    
    def show_jarvis_response(self, text):
        if text:
            self.response_label.setText(text)
            self.response_label.show()
            QTimer.singleShot(5000, self.hide_response)
        else:
            self.response_label.hide()
    
    def hide_response(self):
        self.response_label.hide()
    
    def update_timer_display(self, text):
        if text:
            self.timer_label.setText(f"⏱️ {text}")
            self.timer_label.show()
        else:
            self.timer_label.hide()
        
    def update_listening_state(self, is_listening):
        if is_listening:
            self.pulse_indicator.start_pulse()
            self.status_label.setStyleSheet("color: #ffffff; margin: 10px;")
        else:
            self.pulse_indicator.stop_pulse()
            self.status_label.setStyleSheet("color: #888888; margin: 10px;")
        
    def toggle_listening(self):
        if self.assistant.is_listening:
            self.assistant.stop_listening()
            self.btn_listen.setText("🎤  Слушать")
            self.btn_listen.setObjectName("")
            self.btn_listen.setStyleSheet("")
            self.update_status("Пауза")
            self.signals.listening_state.emit(False)
        else:
            threading.Thread(target=self.assistant.start_listening, daemon=True).start()
            self.btn_listen.setText("⏹  Стоп")
            self.btn_listen.setObjectName("stopBtn")
            self.btn_listen.setStyleSheet("""
                background-color: #333333;
                color: #ffffff;
            """)
            self.update_status("Слушаю...")
            self.signals.listening_state.emit(True)

    def open_settings(self):
        self.append_log("💡 Настройки: config.json")

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "MONO",
            "Свёрнут в трей",
            QSystemTrayIcon.Information,
            1500
        )
    
    def start_with_greeting(self):
        """Запускает прослушивание и приветствует"""
        threading.Thread(target=self.assistant.start_listening, daemon=True).start()
        self.btn_listen.setText("⏹  Стоп")
        self.btn_listen.setObjectName("stopBtn")
        self.btn_listen.setStyleSheet("background-color: #333333; color: #ffffff;")
        self.update_status("Слушаю...")
        self.signals.listening_state.emit(True)
