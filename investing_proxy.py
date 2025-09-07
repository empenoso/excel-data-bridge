#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📊 Образовательный FastAPI сервис для получения курса USD/RUB 📊

⚠️ ВАЖНОЕ УВЕДОМЛЕНИЕ О НАЗНАЧЕНИИ И ИСПОЛЬЗОВАНИИ ⚠️

Данный Python-скрипт создан ИСКЛЮЧИТЕЛЬНО в образовательных и исследовательских целях 
для демонстрации работы с публичными API и веб-технологиями.

🎯 НАЗНАЧЕНИЕ:
- Образовательная демонстрация работы FastAPI
- Изучение методов получения публичной финансовой информации
- Тестирование различных подходов к веб-скрапингу
- Академические исследования в области финансовых данных

👤 ЦЕЛЕВАЯ АУДИТОРИЯ:
- Студенты, изучающие программирование и финансы
- Разработчики, изучающие FastAPI и веб-скрапинг
- Исследователи в области финансовых технологий
- Частные лица для образовательных целей

⚡ ТЕХНИЧЕСКИЕ ОСОБЕННОСТИ:
- Использует FastAPI для создания REST API
- Поддерживает множественные стратегии получения данных
- Предоставляет данные в JSON, XML и текстовых форматах
- Оптимизирован для интеграции с Excel через функции ВЕБСЛУЖБА

🔧 ТРЕБОВАНИЯ К ОКРУЖЕНИЮ:
- Python 3.8+
- fastapi, uvicorn, requests, cloudscraper
- Стабильное интернет-соединение

📝 ПОРЯДОК ИСПОЛЬЗОВАНИЯ:
1. Установите зависимости: pip install fastapi uvicorn requests cloudscraper
2. Запустите сервер: python investing_api.py
3. Откройте http://localhost:8000/docs для изучения API
4. Используйте endpoints только для тестирования и обучения

⚖️ ДИСКЛЕЙМЕР:
Этот код предоставляется "КАК ЕСТЬ", без каких-либо гарантий. Использование 
кода означает согласие с условиями и принятие полной ответственности за его применение.

Всегда соблюдайте условия использования веб-ресурсов и применимое законодательство.

Автор: Михаил Шардин https://shardin.name/
Дата создания: 07.09.2025
Версия: 1.2
Лицензия: MIT (только для образовательных целей)

Актуальная версия: https://github.com/empenoso/excel-data-bridge

"""

import requests
import json
import time
import locale
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import logging
import random
import sys
import os

# --- Настройка кодировки ---
os.environ["PYTHONUTF8"] = "1"
sys.stdout.reconfigure(encoding='utf-8')

# Настройка русской локали
try:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
    except locale.Error:
        print("⚠️ Не удалось установить русскую локаль.")

# Настройка логирования
# Явно указываем поток вывода sys.stdout, чтобы гарантировать отображение логов в консоли .bat
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)-8s - %(message)s',
    stream=sys.stdout
)

app = FastAPI(
    title="USD/RUB Exchange Rate API",
    description="API для получения курса USD/RUB с Investing.com",
    version="1.0.2"
)

class InvestingParser:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        ]
        self.session = None
        self.init_session()

    def init_session(self):
        self.session = requests.Session()
        user_agent = random.choice(self.user_agents)
        headers = {
            'User-Agent': user_agent, 'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7', 'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive', 'DNT': '1', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        self.session.headers.update(headers)
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

    def try_cloudscraper(self):
        try:
            import cloudscraper
            logging.info("Используем cloudscraper для обхода CloudFlare...")
            scraper = cloudscraper.create_scraper()
            url = "https://api.investing.com/api/financialdata/2186/historical/chart/"
            params = {'interval': 'PT1M', 'pointscount': '160'}
            response = scraper.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return self.process_data(response.json())
            return {'error': f'HTTP Error {response.status_code}'}
        except Exception as e:
            logging.error(f"Ошибка CloudScraper: {str(e)}")
            return {'error': f'CloudScraper error: {str(e)}'}

    def try_requests(self):
        try:
            logging.info("Пробуем прямой запрос через requests...")
            url = "https://api.investing.com/api/financialdata/2186/historical/chart/"
            params = {'interval': 'PT1M', 'pointscount': '160'}
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return self.process_data(response.json())
            return {'error': f'HTTP Error {response.status_code}'}
        except Exception as e:
            logging.error(f"Ошибка requests: {str(e)}")
            return {'error': f'Requests error: {str(e)}'}

    def unix_to_excel_timestamp(self, unix_timestamp):
        return (unix_timestamp / 86400) + 25569

    def format_rate_russian(self, rate):
        return str(rate).replace('.', ',')

    def process_data(self, data):
        if 'data' not in data or not data['data']:
            return {'error': 'No data in investing.com response'}
        latest_record = data['data'][-1]
        timestamp_ms, rate = latest_record[0], latest_record[4]
        unix_timestamp = int(timestamp_ms / 1000)
        excel_timestamp = self.unix_to_excel_timestamp(unix_timestamp)
        return {
            'rate': rate, 'rate_formatted': self.format_rate_russian(rate),
            'timestamp': unix_timestamp, 'timestamp_excel': excel_timestamp,
            'datetime': datetime.fromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'success', 'source': 'Investing.com'
        }

    def get_usd_rub_data(self):
        strategies = [("CloudScraper", self.try_cloudscraper), ("Direct Requests", self.try_requests)]
        for name, func in strategies:
            logging.info(f"Trying strategy: {name}")
            result = func()
            if 'rate' in result:
                logging.info(f"SUCCESS {name}! Rate: {result['rate']}")
                return result
            logging.warning(f"FAILED {name}: {result.get('error', 'Unknown error')}")
        return {'error': 'All strategies failed'}

parser = InvestingParser()

@app.on_event("startup")
def print_startup_message():
    """
    Выводит в консоль информационное сообщение при старте сервера.
    """
    print("="*70)
    print("🚀 FastAPI СЕРВЕР ДЛЯ ПОЛУЧЕНИЯ USD/RUB С INVESTING.COM")
    print("="*70)
    print("📊 Доступные endpoints:")
    print("   • http://localhost:8000/usd_rub - JSON формат")
    print("   • http://localhost:8000/usd_rub/xml - XML формат")
    print("   • http://localhost:8000/usd_rub/rate - курс (русский: 81,25)")
    print("   • http://localhost:8000/usd_rub/rate/en - курс (английский: 81.25)")
    print("   • http://localhost:8000/usd_rub/timestamp - Excel timestamp (с запятой)")
    print("   • http://localhost:8000/usd_rub/datetime - Дата и время (текст)")
    print("   • http://localhost:8000/usd_rub/timestamp/unix - Unix timestamp")
    print("   • http://localhost:8000/status - статус сервера")
    print("   • http://localhost:8000/docs - Swagger документация")
    print()
    print("📋 Для Excel используйте формулы:")
    print("   Курс (русский): =ВЕБСЛУЖБА(\"http://localhost:8000/usd_rub/rate\")")
    print("   Дата (текст): =ВЕБСЛУЖБА(\"http://localhost:8000/usd_rub/datetime\")")
    print("   Дата (Excel): =ВЕБСЛУЖБА(\"http://localhost:8000/usd_rub/timestamp\")")
    print("="*70)
    # Конец информационного блока
    
@app.get("/usd_rub")
async def get_usd_rub():
    data = parser.get_usd_rub_data()
    if 'error' in data: raise HTTPException(500, detail=data)
    return data

@app.get("/usd_rub/xml")
async def get_usd_rub_xml():
    data = parser.get_usd_rub_data()
    root = Element('currency_data')
    if 'error' in data:
        SubElement(root, 'error').text = str(data['error'])
    else:
        for key, value in data.items():
            SubElement(root, key).text = str(value).replace('.', ',') if isinstance(value, float) else str(value)
    pretty_xml = minidom.parseString(tostring(root, 'utf-8')).toprettyxml(indent="  ", encoding='utf-8')
    return Response(content=pretty_xml, media_type='application/xml; charset=utf-8')

@app.get("/usd_rub/rate")
async def get_rate_only():
    data = parser.get_usd_rub_data()
    if 'error' in data: raise HTTPException(500, detail=data)
    return Response(content=data['rate_formatted'], media_type='text/plain; charset=utf-8')

@app.get("/usd_rub/rate/en")
async def get_rate_only_english():
    data = parser.get_usd_rub_data()
    if 'error' in data: raise HTTPException(500, detail=data)
    return Response(content=str(data['rate']), media_type='text/plain')

@app.get("/usd_rub/timestamp")
async def get_timestamp_excel():
    data = parser.get_usd_rub_data()
    if 'error' in data: raise HTTPException(500, detail=data)
    return Response(content=str(data['timestamp_excel']).replace('.', ','), media_type='text/plain; charset=utf-8')

@app.get("/usd_rub/timestamp/unix")
async def get_timestamp_unix():
    data = parser.get_usd_rub_data()
    if 'error' in data: raise HTTPException(500, detail=data)
    return Response(content=str(data['timestamp']), media_type='text/plain')

@app.get("/usd_rub/datetime")
async def get_datetime_text():
    data = parser.get_usd_rub_data()
    if 'error' in data: raise HTTPException(500, detail=data)
    return Response(content=data['datetime'], media_type='text/plain; charset=utf-8')

@app.get("/status")
async def status():
    return {'status': 'running', 'version': app.version}

@app.get("/")
async def root():
    return {'title': app.title, 'version': app.version, 'docs': '/docs'}

if __name__ == '__main__':
    # Этот блок нужен только для прямого запуска файла python investing_proxy.py
    import uvicorn
    uvicorn.run("__main__:app", host="localhost", port=8000, reload=True)