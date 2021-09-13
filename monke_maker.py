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
    def __init__(self, symbol, timeframe):
        self.symbol = symbol
        self.timeframe = timeframe

        with open("keys.json", "r") as f:
            self.key_dict = json.loads(f.readline().strip())

        self.url = 'https://paper-api.alpaca.markets'
        self.barset_url = 'https://data.alpaca.markets/v2/' + symbol + '/bars'
        self.api = tradeapi.REST(self.key_dict['api_key_id'], self.key_dict['api_secret'], self.url, api_version='v2')
        self.barset_api = tradeapi.REST(self.key_dict['api_key_id'], self.key_dict['api_secret'], self.barset_url, api_version='v2')
        self.data = {}
        self.df = self.get_barset()

        self.strat = ta.Strategy(
            name='betttt',
            ta = [
                #{'kind': 'sma', 'length': 5},
                #{'kind': 'sma', 'length': 13},
                {'kind': 'ema', 'length': 60},
                {'kind': 'ema', 'length': 180},
                #{'kind': 'macd', 'length': 20},
                #{'kind': 'bbands', 'length': 20},
                #{'kind': 'obv'},
                #{'kind': 'ad'},
                #{'kind': 'adx'},
                #{'kind': 'cci'},
                #{'kind': 'stoch'},
                #{'kind': 'stoch'},
                #{'kind': 'sma', 'close': 'volume', 'length': 20, 'prefix': 'VOLUME'}
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
        listen_message = {"action": "subscribe", "bars": ['AAPL']}
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
            print('\nDATA: ' + str(self.data))
            self.add_data(self.data)

    def on_close(ws):
        print("closed connection")

    def get_clock(self):
        clock_response = self.api.get_clock()
        print('\nCLOCK BOOL:' + str(clock_response.is_open) + '\n')
    
    def get_account_info(self):
        account_response = self.api.get_account()
        print(account_response)
        return account_response

    def get_barset(self):
        todays_date = datetime.datetime.now(datetime.timezone.utc)
        start_date = todays_date - datetime.timedelta(days=1)
        inc_df = self.barset_api.get_barset(symbols=self.symbol, timeframe=self.timeframe, start=start_date, end=todays_date, limit=500).df
        self.df = inc_df[self.symbol]
        return self.df

    def post_order(self, symbol, qty, side):
        print('SUBMITTING ORDER\n')
        order_response = self.api.submit_order(symbol=symbol, qty=qty, side=side, type='market', time_in_force='gtc')
        #print(order_response)
        return order_response

    def get_list_of_orders(self):
        order_list_response = self.api.list_orders()
        print(order_list_response)
        return order_list_response

    def cancel_order(self):
        cancel_response = self.api.cancel_all_orders()
        print(cancel_response)
        return cancel_response
    
    def get_position(self):
        position_response = self.api.get_position(self.symbol)
        print(position_response.qty)
        return position_response

    def get_position_list(self):
        position_list_response = self.api.list_positions()
        #print(position_list_response)
        return position_list_response

    def apply_strat(self):
        self.df.ta.strategy(self.strat)
        return self.df

    def add_data(self, inc_data):
        print(inc_data)
        self.check_market_close()
        self.df = self.df.append(inc_data, ignore_index=True)
        self.df.ta.strategy(self.strat)
        print('DF:\n', self.df.tail(10))
        print("JUMPING INTO EMA CHECK")
        self.ema_check()

    def clear_df_data(self):
        self.df = None

    def check_market_close(self):
        c = self.api.get_clock().is_open
        if c == False:
            print('CLOCK BOOL:' + str(c))
            exit()

#################################################
    def ema_check(self):
        position_list = self.get_position_list()
        sma_flag = self.df['EMA_60'].iloc[-1] > self.df['EMA_180'].iloc[-1] 
        print('SMA FLAG: ' + str(sma_flag))
        if len(position_list) == 0 and sma_flag:
            print("STEPPING INTO BUY CONDITIONAL")
            self.post_order('AAPL', 10, 'buy')
        elif len(position_list)!= 0 and not sma_flag:
            position = self.get_position()
            if position.qty != 0:
                print("STEPPING INTO SELL CONDITIONAL")
                self.post_order('AAPL', 10, 'sell')

    def sma_check(self):
        position_list = self.get_position_list()
        sma_flag = self.df['SMA_5'].iloc[-1] > self.df['SMA_13'].iloc[-1] 
        print('SMA FLAG: ' + str(sma_flag))
        if len(position_list) == 0 and sma_flag:
            print("STEPPING INTO BUY CONDITIONAL")
            self.post_order('AAPL', 10, 'buy')
        elif len(position_list)!= 0 and not sma_flag:
            position = self.get_position()
            if position.qty != 0:
                print("STEPPING INTO SELL CONDITIONAL")
                self.post_order('AAPL', 10, 'sell')

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
        self.df.ta.strategy(self.strat)
        ws = websocket.WebSocketApp(socket, on_open=self.on_open, on_message=self.on_message, on_close=self.on_close)
        ws.run_forever()

if __name__ == '__main__':
    freeze_support()
    bot = Bot('AAPL', 'minute')
    bot.start_stream()
    #df = bot.apply_strat()
    #print(df.tail(15))
