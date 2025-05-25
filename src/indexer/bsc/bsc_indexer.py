import time
import sys
import os
from decimal import Decimal
import json
from typing import List, Dict, Any

# Добавляем директорию src в путь Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.indexer.bsc.parsing import get_transactions_for_multiple_wallets
import requests
from src.api.indexer.shemas import BscIndexerModel, BscTransaction, BscTransactionUsdt

def get_last_block_and_wallets():
    response = requests.get('http://localhost:5000/indexer/bsc/wallets')
    data = response.json()
    return data

def post_transactions(transactions):
    transactions_bsc = []
    transactions_usdt = []
    
    for wallet in transactions:
        for tx_hash, tx_data in transactions[wallet]['bsc'].items():
            bsc_value = float(tx_data) if isinstance(tx_data, Decimal) else tx_data
            transactions_bsc.append({
                'address': wallet,
                'hash_tx': str(tx_hash),
                'bsc': float(bsc_value)
            })
        for tx_hash, tx_data in transactions[wallet]['usdt'].items():
            usdt_value = float(tx_data) if isinstance(tx_data, Decimal) else tx_data
            transactions_usdt.append({
                'address': wallet,
                'hash_tx': str(tx_hash),
                'usdt': float(usdt_value)
            })
    
    transactions_data = {
        'transactions_bsc': transactions_bsc,
        'transactions_usdt': transactions_usdt
    }
    
    # Подробное логирование
    print("\nОтправляемые данные:")
    print(json.dumps(transactions_data, indent=2))
    
    print("\nОтправляем транзакции")
    try:
        response = requests.post('http://localhost:5000/indexer/bsc', json=transactions_data)
        if response.status_code != 200:
            print(f"Ошибка при отправке данных: {response.status_code}")
            print(f"Текст ошибки: {response.text}")
            return None
        
        # Проверяем, есть ли данные в ответе
        if response.text:
            try:
                return response.json()
            except json.JSONDecodeError:
                print(f"Ошибка при разборе JSON ответа: {response.text}")
                return None
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке запроса: {str(e)}")
        return None

while True:
    try:
        response = get_last_block_and_wallets()
        if isinstance(response, list):  # Проверяем, что ответ - это список
            wallets = response  # Используем список напрямую
            print(f"Получены адреса кошельков: {wallets}")
            result = get_transactions_for_multiple_wallets(wallets)
            if result:  # Проверяем, что получили какие-то транзакции
                post_transactions(result)
        else:
            print("Ошибка: Неверный формат ответа от API")
            print("Полученный ответ:", response)
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        print(f"Тип ошибки: {type(e).__name__}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())
    time.sleep(15)