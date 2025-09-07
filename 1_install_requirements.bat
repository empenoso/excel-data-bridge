@echo off
chcp 65001 >nul
title Установка зависимостей Python

echo ========================================
echo Установка зависимостей для проекта
echo ========================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

echo Python найден:
python --version
echo.

REM Проверяем наличие файла requirements.txt
if not exist "requirements.txt" (
    echo ОШИБКА: Файл requirements.txt не найден!
    pause
    exit /b 1
)

echo Обновляем pip...
python -m pip install --upgrade pip
echo.

echo Устанавливаем зависимости...
python -m pip install -r requirements.txt
echo.

echo Проверяем установку uvicorn...
python -m uvicorn --version
if errorlevel 1 (
    echo ВНИМАНИЕ: uvicorn может быть установлен некорректно
) else (
    echo uvicorn установлен успешно!
)

echo.
echo ========================================
echo Установка завершена!
echo ========================================
pause