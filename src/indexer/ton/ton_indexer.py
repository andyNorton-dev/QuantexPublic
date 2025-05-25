ton_api_url = ""
import requests
import time
LT_LIST = []

def get_ton_wallets():
    response = requests.get('http://localhost:5000/indexer/ton/wallets')
    data = response.json()
    return data

def save_ton_transactions(transactions):
    response = requests.post('http://localhost:5000/indexer/ton', json=transactions)
    data = response.json()
    return data

def getLastlt(lt):
    if lt not in LT_LIST:
        LT_LIST.append(lt)
        return False
    return True

def getNewAccountTransaction(wallet, last_lt):
    transactionRequest = requests.get(f"https://tonapi.io/v2/blockchain/accounts/{wallet}/transactions?limit=100&sort_order=desc")
    transactionList = transactionRequest.json()['transactions']
    if len(transactionList) == 0:
        return None
    lastTrx = transactionList[0]
    if lastTrx['lt'] == last_lt:
        return None
    return lastTrx

def getAccountEvent(lastTrx, last_lt):
    actions = requests.get(f'https://tonapi.io/v2/accounts/{lastTrx["account"]["address"]}/events/{lastTrx["hash"]}?subject_only=false')
    newBlocks = []
    for i in actions.json()['actions']:

        if(i['type'] == "TonTransfer"):
            object = i['TonTransfer']
            recipient = object['recipient']
            amount = object['amount']
            print(recipient['address'], lastTrx["account"]["address"])
            if(recipient['address'] == lastTrx["account"]["address"]):
                newBlocks.append({'type': "ton", 'amount': int(amount) / (10 ** 9), 'lt': lastTrx['lt']})
        if (i['type'] == "JettonTransfer") :
            object = i['JettonTransfer']
            recipient = object['recipient']
            amount = object['amount']
            if (recipient['address'] == lastTrx["account"]["address"] and object['jetton']['address'] == "0:b113a994b5024a16719f69139328eb759596c38a25f59028b146fecdc3621dfe") :
                newBlocks.append({'type' : "usdt", 'amount' : int(amount) / (10 ** 6), 'lt': lastTrx['lt']})
    return newBlocks
def start_indexer(wallet: str, last_lt: int):
    lastTrx = getNewAccountTransaction(wallet, last_lt)
    if not lastTrx:
        return 0
    newBlocks = getAccountEvent(lastTrx, last_lt)
    return newBlocks
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    while True:
        wallets = get_ton_wallets()
        result = []
        if wallets:
            for wallet in wallets:
                transactions = start_indexer(wallet['address'], wallet['last_lt'])
                if transactions ==0 or len(transactions) == 0:
                    print(f"No transactions for wallet {wallet}")
                else:
                    transaction = {"wallet":wallet['address'],"type":transactions[0]['type'],"amount":transactions[0]['amount'],"lt":transactions[0]['lt']}
                    result.append(transaction)
            print(result)
            save_ton_transactions(result)
        time.sleep(2)
