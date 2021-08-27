import websocket, json
import alpaca_trade_api as tradeapi
import pandas as pd
import datetime
import pandas_ta as ta
from get_historicial import History
from train_model import Algorithm

from pandas.core.frame import DataFrame
from collections import defaultdict

with open("keys.json", "r") as f:
    key_dict = json.loads(f.readline().strip())

def on_open(ws):
    print("opened")
    auth_data = {
        "action": "auth",
        'key': key_dict['api_key_id'],
        'secret': key_dict['api_secret']
    }

    ws.send(json.dumps(auth_data))
    #listen_message = {"action": "subscribe", "bars": ["TSLA", 'AAPL', 'GME', 'AMZN']}
    #listen_message = {"action": "subscribe", "bars": ["GME", "AAPL", "TSLA"]}
    listen_message = {"action": "subscribe", "bars": ["GME"]}
    ws.send(json.dumps(listen_message))

def on_message(ws, message):
    message = json.loads(message)
    print(message)
    if message[0]['T'] == 'b':
        print('in conditional\n')
        data['Date'] = message[0]['t']
        data['Open'] = message[0]['o']
        data['High'] = message[0]['h']
        data['Low'] = message[0]['l']
        data['Close'] = message[0]['c']
        data['Volume'] = message[0]['v']
        add_data(data)

def on_close(ws):
    print("closed connection")

def add_data(inc_data):
    global df, data
    print(inc_data)
    df = df.append(inc_data, ignore_index=True)
    print('DF:\n', df)
    print('DF CLOSE:\n', df['Close'])
    macd = df.ta.macd(df['Close'])
    print('MACD:\n', macd)


symbol = 'GME'
timeframe = '1Min'
todays_date = datetime.datetime.now(datetime.timezone.utc)
start_date = todays_date - datetime.timedelta(days=1)
url = 'https://data.alpaca.markets/v2/GME/bars'
data = {}

api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], url, api_version='v2')
inc_df = api.get_barset(symbols=symbol, timeframe=timeframe, start=start_date, end=todays_date, limit=1000).df
df = inc_df['GME']

#model = Algorithm(df)
#model.train_and_fit()
#model.plot_data()
macd = df.ta.macd()
print('MACD:\n', macd)

'''
if flagged above and macd > signal:
    continue
elif flagged above and macd < signal:
    sell
elif flagged below and macd < signal


buy if flagged below and macd > signal else continue
sell if flagged above and macd < signal else continue
'''

def macd_check_buy(df):
    # MACD buy sign is when macd goes from below the signal column to above
    # the flag is used to see if macd is currently > or < signal
    for count , row in df.iterrows():
        if count == 0 and row['MACD_12_26_9'] < row['MACDs_12_26_9']:
            macd_flag = False
        else:
            macd_flag = True

        if macd_flag == False and row['MACD_12_26_9'] > row['MACDs_12_26_9']:
            print("BUY NOW")
            macd_flag = not macd_flag
            print(row['MACD_12_26_9'])
        elif not macd_flag and row['MACD_12_26_9'] < row['MACDs_12_26_9']:
            print("SELL NOW")
            macd_flag = not macd_flag
            print(row['MACD_12_26_9'])
        else:
            continue

macd_check_buy(macd)

def start_stream():
    socket = 'wss://stream.data.alpaca.markets/v2/iex'

    api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], url, api_version='v2')
    inc_df = api.get_barset(symbols=symbol, timeframe=timeframe, start=start_date, end=todays_date, limit=1000).df
    df = inc_df['GME'] 
    macd = df.ta.macd()

    print(macd)
    print('MACD:\n', macd)

    ws = websocket.WebSocketApp(socket, on_open=on_open, on_message=on_message, on_close=on_close)
    ws.run_forever()