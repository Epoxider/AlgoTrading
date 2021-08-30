import websocket, json, datetime, requests
import alpaca_trade_api as tradeapi
import pandas as pd
import pandas_ta as ta
from get_historicial import History
from multiprocessing import freeze_support
#from train_model import Algorithm

from pandas.core.frame import DataFrame
from collections import defaultdict

class Bot():
    def __init__(self, symbol):
        self.symbol = symbol
        self.data = {}

        with open("keys.json", "r") as f:
            self.key_dict = json.loads(f.readline().strip())

        self.url = 'https://paper-api.alpaca.markets'
        self.barset_url = 'https://data.alpaca.markets/v2/' + symbol + '/bars'
        self.api = tradeapi.REST(self.key_dict['api_key_id'], self.key_dict['api_secret'], self.url, api_version='v2')
        self.barset_api = tradeapi.REST(self.key_dict['api_key_id'], self.key_dict['api_secret'], self.barset_url, api_version='v2')

        self.strat = ta.Strategy(
            name='betttt',
            ta = [
                {'kind': 'sma', 'length': 5},
                {'kind': 'sma', 'length': 13},
                {'kind': 'macd', 'length': 20},
            ]
        )

    def on_open(self,ws):
        print("opened")
        auth_data = {
            "action": "auth",
            'key': self.key_dict['api_key_id'],
            'secret': self.key_dict['api_secret']
        }

        ws.send(json.dumps(auth_data))
        #listen_message = {"action": "subscribe", "bars": ["GME", "AAPL", "TSLA"]}
        listen_message = {"action": "subscribe", "bars": ['GME']}
        ws.send(json.dumps(listen_message))


    def on_message(self, ws, message):
        message = json.loads(message)
        print(message)
        if message[0]['T'] == 'b':
            self.data['date'] = message[0]['t']
            self.data['open'] = message[0]['o']
            self.data['high'] = message[0]['h']
            self.data['low'] = message[0]['l']
            self.data['close'] = message[0]['c']
            self.data['volume'] = message[0]['v']
            self.add_data(self.data)

    def on_close(ws):
        print("closed connection")

    def add_data(self, inc_data):
        print(inc_data)
        self.df = self.df.append(inc_data, ignore_index=True)
        self.df.ta.strategy(self.strat)
        print('DF:\n', self.df.tail(10))

    def get_clock(self):
        clock_response = self.api.get_clock()
        print(clock_response.is_open)
    
    def get_account_info(self):
        account_response = self.api.get_account()
        print(account_response)
        return account_response

    def get_barset(self, symbol, timeframe):
        todays_date = datetime.datetime.now(datetime.timezone.utc)
        start_date = todays_date - datetime.timedelta(days=1)
        inc_df = self.barset_api.get_barset(symbols=symbol, timeframe=timeframe, start=start_date, end=todays_date, limit=500).df
        df = inc_df[symbol]
        return df

    def post_order(self, symbol, qty, side):
        order_response = self.api.submit_order(symbol=symbol, qty=qty, side=side, type='market', time_in_force='gtc')
        print(order_response)
        return order_response

    def get_list_of_orders(self):
        order_list_response = self.api.list_orders()
        print(order_list_response)
        return order_list_response

    def cancel_order(self):
        cancel_response = self.api.cancel_all_orders()
        print(cancel_response)
        return cancel_response


    def sma_check_buy(self, df):
        '''
        if there is an open order:
            pass
        else:
            if 5 is greater than 13:
                send buy
            else:
                wait for it to become greater
        '''
        if df['SMA_5'] > df['SMA_13']:
            self.post_order('GME', 10, 'buy')

    def macd_check_buy(self):
        # MACD buy sign is when macd goes from below the signal column to above
        # the flag is used to see if macd is currently > or < signal
        macd_flag = False
        for count, row in self.df.iterrows():
            if (macd_flag) == False and (row['MACD_12_26_9'] > row['MACDs_12_26_9']):
                print("************\nBUY NOW at count: ", count, '\n************')
                macd_flag = True
            elif (macd_flag == True) and (row['MACD_12_26_9'] < row['MACDs_12_26_9']):
                print("************\nSELL NOW at count: ", count, '\n************')
                macd_flag = False
            else:
                continue

    def start_stream(self):
        socket = 'wss://stream.data.alpaca.markets/v2/iex'
        self.df = self.get_barset(self.symbol, 'minute')
        self.df.ta.strategy(self.strat)
        self.macd_check_buy()
        print(self.df.tail(10))
        #api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], url, api_version='v2')
        #inc_df = api.get_barset(symbols=symbol, timeframe=timeframe, start=start_date, end=todays_date, limit=1000).df
        #df = inc_df['GME']     # Check main func 
        ws = websocket.WebSocketApp(socket, on_open=self.on_open, on_message=self.on_message, on_close=self.on_close)
        ws.run_forever()

    # my custom strat atm: 
    '''strat = ta.Strategy(
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
    '''

if __name__ == '__main__':
    freeze_support()
    bot = Bot('GME')
    bot.start_stream()
    #symbol = 'GME'
    #start_stream(symbol)
    #df = pd.read_csv('AAPL.csv')
    #df.ta.strategy(strat)
    #macd_check_buy(df)
    #ddf = df.drop(columns=['Date', 'Open', 'High', 'Low'])
    #print(ddf.tail().to_string())