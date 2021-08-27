import re
from pandas.core.frame import DataFrame
import websocket, json
import alpaca_trade_api as tradeapi
import pandas as pd
import pandas_ta as ta

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
    listen_message = {"action": "subscribe", "bars": ["TSLA"]}
    ws.send(json.dumps(listen_message))

def change_msg_names(message):
    message = re.sub('c', 'close', message)
    message = re.sub('o', 'open', message)
    message = re.sub('h', 'high', message)
    message = re.sub('s', 'symbol', message)
    message = re.sub('v', 'volume', message)
    message = re.sub('t', 'date', message)
    return message

def on_message(ws, message):
    global df
    global price_array

    change_msg_names(message=message)
    message = json.loads(message)
    if message[0]['T'] == 'b':
        price_array.append(message[0]['close'])
        df = df.append(message, ignore_index=True)
        df.ta.log_return(cumulative=True, append=True)
        df.ta.percent_return(cumulative=True, append=True)
        print(df)


def on_close(ws):
    print("closed connection")

#socket = "wss://data.alpaca.markets/stream"
socket = 'wss://stream.data.alpaca.markets/v2/iex'

df = pd.DataFrame()
price_array = []

ws = websocket.WebSocketApp(socket, on_open=on_open, on_message=on_message, on_close=on_close)
ws.run_forever()