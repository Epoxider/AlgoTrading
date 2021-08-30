import websocket, json, datetime, requests
import alpaca_trade_api as tradeapi
import pandas as pd
import pandas_ta as ta
from get_historicial import History
from multiprocessing import freeze_support
#from train_model import Algorithm

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

data = {}

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


symbol = 'GME'
timeframe = '1Min'
todays_date = datetime.datetime.now(datetime.timezone.utc)
start_date = todays_date - datetime.timedelta(days=1)
url = 'https://data.alpaca.markets/v2/'

def get_clock():
    global url
    url = url + 'clock'
    clock_api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], url, api_version='v2')
    clock_response = clock_api.get_clock()
    return clock_response

def get_barset(symbol):
    global url
    url = url + symbol + '/bars'
    bars_api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], url, api_version='v2')
    inc_df = bars_api.get_barset(symbols=symbol, timeframe=timeframe, start=start_date, end=todays_date, limit=1000).df
    df = inc_df[symbol]
    return df

def post_order(symbol, qty, side):
    global url
    url = url + 'orders'
    tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], url, api_version='v2')
    order_response = orders_api.submit_order(symbol=symbol, qty=qty, side=side, type='market', time_in_force='gtc')
    return order_response

#inc_df = bars_api.get_barset(symbols=symbol, timeframe=timeframe, start=start_date, end=todays_date, limit=1000).df

def macd_check_buy(df):
    # MACD buy sign is when macd goes from below the signal column to above
    # the flag is used to see if macd is currently > or < signal
    macd_flag = False
    for count , row in df.iterrows():
        if (macd_flag) == False and (row['MACD_12_26_9'] > row['MACDs_12_26_9']):
            print("************\nBUY NOW at count: ", count, '\n************')
            macd_flag = True
        elif (macd_flag == True) and (row['MACD_12_26_9'] < row['MACDs_12_26_9']):
            print("************\nSELL NOW at count: ", count, '\n************')
            macd_flag = False
        else:
            continue

def start_stream():
    socket = 'wss://stream.data.alpaca.markets/v2/iex'
    api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], url, api_version='v2')
    inc_df = api.get_barset(symbols=symbol, timeframe=timeframe, start=start_date, end=todays_date, limit=1000).df
    #df = inc_df['GME']     # Check main func 
    ws = websocket.WebSocketApp(socket, on_open=on_open, on_message=on_message, on_close=on_close)
    ws.run_forever()

# my custom strat atm: 
strat = ta.Strategy(
    name='betttt',
    description='SMA BBANDS RSI MACD VOLUME_SMA',
    ta = [
        {'kind': 'sma', 'length': 20},
        {'kind': 'sma', 'length': 50},
        {'kind': 'bbands', 'length': 20},
        {'kind': 'rsi'},
        {'kind': 'macd', 'length': 20},
        {'kind': 'sma', 'close': 'volume', 'length': 20, 'prefix': 'VOLUME'}
    ]
)

if __name__ == '__main__':
    #freeze_support()
    df = pd.read_csv('AAPL.csv')
    df.ta.strategy(strat)
    macd_check_buy(df)
    ddf = df.drop(columns=['Date', 'Open', 'High', 'Low'])
    print(ddf.tail().to_string())