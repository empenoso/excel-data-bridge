@echo off
chcp 65001 >nul
title Эксель XML API Server

echo Запуск сервера FastAPI...
echo.
echo (закройте это окно, чтобы остановить сервер)
echo.
echo Михаил Шардин https://shardin.name/
echo.
echo ========================================

REM Проверяем наличие файла
if not exist "investing_proxy.py" (
    echo ОШИБКА: Файл investing_proxy.py не найден!
    pause
    exit /b 1
)

REM Устанавливаем переменные для лучшего отображения логов
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

echo Проверяем Python и uvicorn...
python --version
python -c "import uvicorn; print(f'uvicorn версия: {uvicorn.__version__}')" 2>nul
if errorlevel 1 (
    echo ВНИМАНИЕ: uvicorn не найден или работает некорректно
)

echo.
echo Запуск сервера...
echo ========================================

REM Запуск через python модуль с дополнительными параметрами для логирования и автоперезагрузки
python -m uvicorn investing_proxy:app --host 127.0.0.1 --port 8000 --log-level info --reload

REM Если не получилось, пробуем прямой запуск
if errorlevel 1 (
    echo.
    echo ========================================
    echo Пробуем прямой запуск Python файла...
    echo ========================================
    python -u investing_proxy.py
)

echo.
echo Сервер остановлен.
pause