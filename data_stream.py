import os, sys, time, json, requests
import alpaca_trade_api as tradeapi


base_url = 'https://paper-api.alpaca.markets'


with open("keys.json", "r") as f:
    key_dict = json.loads(f.readline().strip())

api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], base_url, api_version='v2')

#print(api.get_account())

appl_q = []

conn = tradeapi.StreamConn(
        base_url=base_url,
        #data_stream='polygon',
        key_id=key_dict['api_key_id'],
        secret_key=key_dict['api_secret']
    )

@conn.on(r'^account_updates$')
async def on_account_updates(conn, channel, account):
    print('account', account)

@conn.on(r'^AM.AAPL$')
async def on_minute_bars(conn, channel, data):
    #print(data.close)
    #appl_q.append(data['close'])
    print('Data: ', data.close, ' Average is ' )#str(sum(appl_q)/len(appl_q)))

'''
@conn.on(r'^AM.TSLA$')
async def on_minute_bars(conn, channel, data):
    print('tick')
    print(data)
'''

conn.run(['AM.AAPL'])
#conn.run(['A.*', 'AM.*', 'account_updates'])