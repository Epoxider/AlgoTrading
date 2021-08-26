import json
import alpaca_trade_api as tradeapi

base_url = 'https://paper-api.alpaca.markets'

with open("keys.json", "r") as f:
    key_dict = json.loads(f.readline().strip())

#api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], base_url, api_version='v2')
#print(api.get_account())

list_of_price_queues = []

conn = tradeapi.StreamConn(
        base_url=base_url,
        #data_stream='polygon',
        key_id=key_dict['api_key_id'],
        secret_key=key_dict['api_secret']
    )

@conn.on(r'^account_updates$')
async def on_account_updates(conn, channel, account):
    print('account', account)

@conn.on(r'^AM$')
async def on_minute_bars(conn, channel, data):
    print('Data: ', data.close)
    [q.append(data) for q in list_of_price_queues]

class Data_Stream():
    def __init__(self, symbol):
        self.symbol = 'AM.%s' %(symbol)
        global list_of_price_queues
        conn.run([self.symbol])

    def get_stream_data(self):
        return list_of_price_queues