@echo off
title MONO Assistant - Установка
color 0F
echo.
echo ========================================
echo    MONO ASSISTANT - УСТАНОВКА
echo ========================================
echo.

:: Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo.
    echo Скачайте Python с https://python.org
    echo При установке отметьте "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [OK] Python найден
echo.
echo Устанавливаю зависимости...
echo Это может занять несколько минут...
echo.

:: Устанавливаем зависимости
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Не удалось установить зависимости
    pause
    exit /b 1
)

echo.
echo [OK] Все зависимости установлены!
echo.
echo ========================================
echo    ЗАПУСК MONO ASSISTANT
echo ========================================
echo.

:: Запускаем приложение
python main.py

pause
