import requests
from datetime import datetime
from decimal import Decimal

# Адрес контракта USDT в сети BSC
USDT_CONTRACT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"  # BSC USDT (USD Tether)

def get_bsc_transactions(wallet_address, api_key, min_amount_wei=1000000000000000):  # 0.001 BNB в wei
    """
    Получает все входящие транзакции для указанного адреса кошелька в сети BSC
    :param wallet_address: str - адрес кошелька (0x...)
    :param api_key: str - API ключ от BscScan
    :param min_amount_wei: int - минимальная сумма транзакции в wei
    :return: list - список транзакций
    """
    url = "https://api.bscscan.com/api"
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": api_key
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data["status"] == "1":
        transactions = data["result"]
        # Фильтруем только входящие транзакции с суммой больше минимальной
        incoming_txs = [
            tx for tx in transactions 
            if tx["to"].lower() == wallet_address.lower() 
            and int(tx["value"]) >= min_amount_wei
        ]
        return incoming_txs
    else:
        print("Ошибка при получении транзакций:", data.get("message", "Неизвестная ошибка"))
        return []

def get_usdt_transactions(wallet_address, api_key):
    """
    Получает все входящие USDT транзакции для указанного адреса кошелька в сети BSC
    :param wallet_address: str - адрес кошелька (0x...)
    :param api_key: str - API ключ от BscScan
    :return: list - список транзакций
    """
    url = "https://api.bscscan.com/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": USDT_CONTRACT_ADDRESS,
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": api_key
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data["status"] == "1":
        transactions = data["result"]
        # Фильтруем только входящие USDT транзакции
        incoming_txs = [
            tx for tx in transactions 
            if tx["to"].lower() == wallet_address.lower() 
            and tx["contractAddress"].lower() == USDT_CONTRACT_ADDRESS.lower()  # Проверяем, что это точно USDT
        ]
        return incoming_txs
    else:
        print("Ошибка при получении USDT транзакций:", data.get("message", "Неизвестная ошибка"))
        return []

def get_transactions_for_multiple_wallets(wallet_addresses, api_key="M1G58PDI6V2D5DATZ9A1SJ9V24UGTD4YKF"):
    """
    Получает все транзакции (BSC и USDT) для списка кошельков
    :param wallet_addresses: list - список адресов кошельков
    :param api_key: str - API ключ от BscScan
    :return: dict - словарь с транзакциями по каждому кошельку
    """
    result = {}
    
    for wallet in wallet_addresses:
        result[wallet] = {
            'bsc': {},
            'usdt': {}
        }
        
        # Получаем BSC транзакции
        bsc_txs = get_bsc_transactions(wallet, api_key)
        for tx in bsc_txs:
            value_in_bnb = Decimal(tx['value']) / Decimal('1000000000000000000')  # Конвертируем из wei в BNB
            result[wallet]['bsc'][tx['hash']] = value_in_bnb
            
        # Получаем USDT транзакции
        usdt_txs = get_usdt_transactions(wallet, api_key)
        for tx in usdt_txs:
            # USDT в BSC имеет 18 десятичных знаков
            value_in_usdt = Decimal(tx['value']) / Decimal('1000000000000000000')
            result[wallet]['usdt'][tx['hash']] = value_in_usdt
    
    return result

def format_timestamp(timestamp):
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

# Пример использования:
# wallet_addresses = ["0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97", "0x6C248334F7eE5C4bD58FFEAD8e151E4107ef3438"]
# result = get_transactions_for_multiple_wallets(wallet_addresses)
# 
# for address, data in result.items():
#     print(f"\nКошелек: {address}")
#     
#     print("BSC транзакции:")
#     for block, value in sorted(data['bsc'].items(), reverse=True):
#         print(f"  Блок {block}: {value} BNB")
#     
#     print("USDT транзакции:")
#     for block, value in sorted(data['usdt'].items(), reverse=True):
#         print(f"  Блок {block}: {value} USDT")