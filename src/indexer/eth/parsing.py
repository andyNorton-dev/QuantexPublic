from web3 import Web3
import time
from datetime import datetime
from collections import defaultdict

# Конфигурация
INFURA_URL = "https://mainnet.infura.io/v3/11cecb921a8b4a8e8ffb4e6957e7a82d"
USDT_CONTRACT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"  # USDT контракт в Ethereum
WALLET_ADDRESS = "0xd11D7D2cb0aFF72A61Df37fD016EE1bd9F180633"
BLOCK_CHUNK_SIZE = 100  # Уменьшаем размер чанка для предотвращения превышения лимита

# Инициализация Web3
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

def get_block_timestamp(block_number):
    try:
        block = w3.eth.get_block(block_number)
        return block.timestamp
    except Exception as e:
        print(f"Ошибка при получении информации о блоке {block_number}: {str(e)}")
        return None

def get_incoming_eth_transactions(address, start_block=None, end_block=None):
    address = w3.to_checksum_address(address)
    incoming_txs = []
    
    # Если блоки не указаны, берем последние 1000 блоков
    if start_block is None or end_block is None:
        latest_block = w3.eth.block_number
        end_block = latest_block
        start_block = max(0, latest_block - 1000)
    
    print(f"Поиск ETH транзакций с блока {start_block} по {end_block}")
    
    # Разбиваем диапазон на чанки
    for chunk_start in range(start_block, end_block + 1, BLOCK_CHUNK_SIZE):
        chunk_end = min(chunk_start + BLOCK_CHUNK_SIZE - 1, end_block)
        
        try:
            # Получаем блоки в текущем чанке
            for block_number in range(chunk_start, chunk_end + 1):
                try:
                    block = w3.eth.get_block(block_number, full_transactions=True)
                    
                    # Фильтруем транзакции, где получатель - наш адрес
                    for tx in block.transactions:
                        if tx.get('to') and tx['to'].lower() == address.lower():
                            incoming_txs.append({
                                'tx_hash': tx['hash'].hex(),
                                'from': tx['from'],
                                'value': w3.from_wei(tx['value'], 'ether'),
                                'block': block_number,
                                'timestamp': block.timestamp,
                                'token': 'ETH'
                            })
                    
                except Exception as e:
                    print(f"Ошибка при обработке блока {block_number}: {str(e)}")
                    continue
            
            print(f"Обработаны блоки {chunk_start}-{chunk_end}, найдено {len(incoming_txs)} ETH транзакций")
            
            # Небольшая задержка, чтобы не превысить лимиты API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Ошибка при обработке чанка {chunk_start}-{chunk_end}: {str(e)}")
            continue
    
    return incoming_txs

def get_incoming_usdt_transactions(address, start_block=None, end_block=None):
    address = w3.to_checksum_address(address)
    
    # ABI для USDT (только Transfer event)
    usdt_abi = '''
    [{
        "anonymous": false,
        "inputs": [
            {"indexed": true, "name": "from", "type": "address"},
            {"indexed": true, "name": "to", "type": "address"},
            {"indexed": false, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }]
    '''
    
    usdt_contract = w3.eth.contract(
        address=w3.to_checksum_address(USDT_CONTRACT),
        abi=usdt_abi
    )
    
    # Если блоки не указаны, берем последние 1000 блоков
    if start_block is None or end_block is None:
        latest_block = w3.eth.block_number
        end_block = latest_block
        start_block = max(0, latest_block - 1000)
    
    print(f"Поиск USDT транзакций с блока {start_block} по {end_block}")
    
    incoming_usdt = []
    
    # Разбиваем диапазон на чанки
    for chunk_start in range(start_block, end_block + 1, BLOCK_CHUNK_SIZE):
        chunk_end = min(chunk_start + BLOCK_CHUNK_SIZE - 1, end_block)
        
        try:
            # Получаем все Transfer события в текущем чанке
            event_filter = {
                'fromBlock': chunk_start,
                'toBlock': chunk_end,
                'address': w3.to_checksum_address(USDT_CONTRACT),
                'topics': [
                    # Transfer event signature
                    '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
                    # Any from address
                    None,
                    # To our address (padded to 32 bytes)
                    '0x' + '0' * 24 + address[2:].lower()
                ]
            }
            
            events = w3.eth.get_logs(event_filter)
            
            for event in events:
                try:
                    # Декодируем данные события
                    decoded_event = usdt_contract.events.Transfer().process_log(event)
                    tx_hash = event['transactionHash'].hex()
                    
                    incoming_usdt.append({
                        'tx_hash': tx_hash,
                        'from': decoded_event['args']['from'],
                        'value': decoded_event['args']['value'] / 10**6,  # USDT имеет 6 decimals
                        'block': event['blockNumber'],
                        'timestamp': get_block_timestamp(event['blockNumber']),
                        'token': 'USDT'
                    })
                except Exception as e:
                    print(f"Ошибка при обработке события USDT: {str(e)}")
                    continue
            
            print(f"Обработаны блоки {chunk_start}-{chunk_end}, найдено {len(events)} USDT транзакций")
            
            # Небольшая задержка, чтобы не превысить лимиты API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Ошибка при обработке блоков {chunk_start}-{chunk_end}: {str(e)}")
            time.sleep(1)  # Увеличиваем задержку при ошибке
            continue
    
    return incoming_usdt

def get_all_incoming_transactions(wallet_address, start_block=None, end_block=None):
    eth_txs = get_incoming_eth_transactions(wallet_address, start_block, end_block)
    usdt_txs = get_incoming_usdt_transactions(wallet_address, start_block, end_block)
    
    # Объединяем и сортируем по времени
    all_txs = eth_txs + usdt_txs
    all_txs.sort(key=lambda x: x['block'], reverse=True)
    
    return all_txs

def get_transactions_for_multiple_wallets(wallet_addresses, start_block=None, end_block=None):
    """
    Получает транзакции для нескольких кошельков одновременно.
    
    Args:
        wallet_addresses (list): Список адресов кошельков
        start_block (int, optional): Начальный блок для поиска
        end_block (int, optional): Конечный блок для поиска
        
    Returns:
        dict: Словарь с информацией о транзакциях для каждого кошелька
        {
            '0x1234...': {
                'usdt': {'номер блока': 'сколько пришло в usdt'},
                'eth': {'номер блока': 'сколько пришло в эфириме'}
            },
            ...
        }
    """
    # Если блоки не указаны, берем последние 1000 блоков
    if start_block is None or end_block is None:
        latest_block = w3.eth.block_number
        end_block = latest_block
        start_block = max(0, latest_block - 500)
    
    print(f"Поиск транзакций для {len(wallet_addresses)} кошельков с блока {start_block} по {end_block}")
    
    # Инициализируем результат
    result = {}
    for address in wallet_addresses:
        result[address] = {
            'usdt': {},
            'eth': {}
        }
    
    # Получаем ETH транзакции для всех кошельков
    print("Поиск ETH транзакций...")
    
    # Разбиваем диапазон на чанки
    for chunk_start in range(start_block, end_block + 1, BLOCK_CHUNK_SIZE):
        chunk_end = min(chunk_start + BLOCK_CHUNK_SIZE - 1, end_block)
        
        try:
            # Получаем блоки в текущем чанке
            for block_number in range(chunk_start, chunk_end + 1):
                try:
                    block = w3.eth.get_block(block_number, full_transactions=True)
                    
                    # Фильтруем транзакции для всех адресов
                    for tx in block.transactions:
                        if tx.get('to'):
                            to_address = tx['to'].lower()
                            for address in wallet_addresses:
                                if to_address == address.lower():
                                    # Добавляем транзакцию в результат
                                    if block_number not in result[address]['eth']:
                                        result[address]['eth'][block_number] = 0
                                    result[address]['eth'][block_number] += w3.from_wei(tx['value'], 'ether')
                    
                except Exception as e:
                    print(f"Ошибка при обработке блока {block_number}: {str(e)}")
                    continue
            
            print(f"Обработаны блоки {chunk_start}-{chunk_end} для ETH транзакций")
            
            # Небольшая задержка, чтобы не превысить лимиты API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Ошибка при обработке чанка {chunk_start}-{chunk_end} для ETH транзакций: {str(e)}")
            continue
    
    # Получаем USDT транзакции для всех кошельков
    print("Поиск USDT транзакций...")
    
    # ABI для USDT (только Transfer event)
    usdt_abi = '''
    [{
        "anonymous": false,
        "inputs": [
            {"indexed": true, "name": "from", "type": "address"},
            {"indexed": true, "name": "to", "type": "address"},
            {"indexed": false, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }]
    '''
    
    usdt_contract = w3.eth.contract(
        address=w3.to_checksum_address(USDT_CONTRACT),
        abi=usdt_abi
    )
    
    # Создаем фильтры для каждого адреса
    for address in wallet_addresses:
        address = w3.to_checksum_address(address)
        
        # Разбиваем диапазон на чанки
        for chunk_start in range(start_block, end_block + 1, BLOCK_CHUNK_SIZE):
            chunk_end = min(chunk_start + BLOCK_CHUNK_SIZE - 1, end_block)
            
            try:
                # Получаем все Transfer события в текущем чанке
                event_filter = {
                    'fromBlock': chunk_start,
                    'toBlock': chunk_end,
                    'address': w3.to_checksum_address(USDT_CONTRACT),
                    'topics': [
                        # Transfer event signature
                        '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
                        # Any from address
                        None,
                        # To our address (padded to 32 bytes)
                        '0x' + '0' * 24 + address[2:].lower()
                    ]
                }
                
                events = w3.eth.get_logs(event_filter)
                
                for event in events:
                    try:
                        # Декодируем данные события
                        decoded_event = usdt_contract.events.Transfer().process_log(event)
                        block_number = event['blockNumber']
                        
                        # Добавляем транзакцию в результат
                        if block_number not in result[address]['usdt']:
                            result[address]['usdt'][block_number] = 0
                        result[address]['usdt'][block_number] += decoded_event['args']['value'] / 10**6  # USDT имеет 6 decimals
                        
                    except Exception as e:
                        print(f"Ошибка при обработке события USDT для адреса {address}: {str(e)}")
                        continue
                
                print(f"Обработаны блоки {chunk_start}-{chunk_end} для USDT транзакций адреса {address}")
                
                # Небольшая задержка, чтобы не превысить лимиты API
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Ошибка при обработке блоков {chunk_start}-{chunk_end} для USDT транзакций адреса {address}: {str(e)}")
                time.sleep(1)  # Увеличиваем задержку при ошибке
                continue
    
    return result

def get_latest_block():
    """
    Получает номер последнего блока в сети Ethereum.
    
    Returns:
        int: Номер последнего блока
    """
    try:
        latest_block = w3.eth.block_number
        return latest_block
    except Exception as e:
        print(f"Ошибка при получении последнего блока: {str(e)}")
        return None

# latest_block = w3.eth.block_number
# start_block = latest_block - 200
# wallet_addresses = [
#     "0xd11D7D2cb0aFF72A61Df37fD016EE1bd9F180633",
#     "0x6Adb3baB5730852eB53987EA89D8e8f16393C200"
# ]

# result = get_transactions_for_multiple_wallets(wallet_addresses, start_block, latest_block)
# print(result)

# for address, data in result.items():
#     print(f"\nКошелек: {address}")
    
#     print("ETH транзакции:")
#     for block, value in sorted(data['eth'].items(), reverse=True):
#         print(f"  Блок {block}: {value} ETH")
    
#     print("USDT транзакции:")
#     for block, value in sorted(data['usdt'].items(), reverse=True):
#         print(f"  Блок {block}: {value} USDT")