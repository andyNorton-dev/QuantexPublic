import time
from parsing import get_transactions_for_multiple_wallets
import requests
from decimal import Decimal

def get_last_block_and_wallets():
    response = requests.get('http://localhost:5000/indexer/eth/last_block_and_wallets')
    data = response.json()
    return data

def post_transactions(transactions):
    transactions_result = {
        "transactions_eth": [],
        "transactions_usdt": []
    }
    for wallet in transactions:
        for tx in transactions[wallet]['eth']:
            eth_value = float(transactions[wallet]['eth'][tx]) if isinstance(transactions[wallet]['eth'][tx], Decimal) else transactions[wallet]['eth'][tx]
            transactions_result['transactions_eth'].append({'address': wallet, 'block': tx, 'eth': eth_value})
        for tx in transactions[wallet]['usdt']:
            usdt_value = float(transactions[wallet]['usdt'][tx]) if isinstance(transactions[wallet]['usdt'][tx], Decimal) else transactions[wallet]['usdt'][tx]
            transactions_result['transactions_usdt'].append({'address': wallet, 'block': tx, 'usdt': usdt_value})
    print(transactions_result)
    
    print("Отправляем транзакции")
    response = requests.post('http://localhost:5000/indexer/eth', json=transactions_result)
    return response.json()

while True:
    response = get_last_block_and_wallets()
    wallets = response['wallets']
    result = get_transactions_for_multiple_wallets(wallets)
    post_transactions(result)
    time.sleep(15)