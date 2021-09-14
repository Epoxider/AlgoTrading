import websocket, json, datetime
import alpaca_trade_api as tradeapi
import pandas_ta as ta
from multiprocessing import freeze_support

class Bot():
    def __init__(self, symbol_list, timeframe):

        self.symbol_list = symbol_list
        self.timeframe = timeframe
        self.symbol_data_dict = {}   # Keys = symbols, values = strategy datafames

        with open("keys.json", "r") as f:
            self.key_dict = json.loads(f.readline().strip())


        self.url = 'https://paper-api.alpaca.markets'
        self.api = tradeapi.REST(self.key_dict['api_key_id'], self.key_dict['api_secret'], self.url, api_version='v2')

        # Custom strategy from my monke brain
        # Note: This calculates the indicators, NOT when to buy sell
        #       need to calculate buy/sell logic in addition
        self.strat = ta.Strategy(
            name='betttt',
            ta = [
                {'kind': 'ema', 'length': 60},
                {'kind': 'ema', 'length': 180},
            ]
        )

        # for each symbol get get the barset history
        for symbol in symbol_list:
            self.symbol_data_dict[symbol] = self.get_barset(symbol)
            self.symbol_data_dict[symbol].ta.strategy(self.strat)

        '''
        Exapmle of different strategies you can use. More found in indicator_list.txt 
        self.strat = ta.Strategy(
            name='betttt',
            ta = [
                #{'kind': 'sma', 'length': 5},
                #{'kind': 'sma', 'length': 13},
                #{'kind': 'ema', 'length': 60},
                #{'kind': 'ema', 'length': 180},
                #{'kind': 'macd', 'length': 20},
                #{'kind': 'bbands', 'length': 20},
                #{'kind': 'obv'},
                #{'kind': 'ad'},
                #{'kind': 'adx'},
                #{'kind': 'cci'},
                #{'kind': 'stoch'},
                #{'kind': 'sma', 'close': 'volume', 'length': 20, 'prefix': 'VOLUME'}
            ]
        )
        '''


# DATA MANIUPLATION
##################################################################################################
    def convert_data(self, df):
        # Converts the dataframe returned from alpaca to one that works with pandas_ta
        data = {}
        #data['date'] = df['t']
        data['open'] = df['o']
        data['high'] = df['h']
        data['low'] = df['l']
        data['close'] = df['c']
        data['volume'] = df['v']
        print(data)
        return data


    def add_data(self, symbol, symbol_data):
        self.check_market_close()
        data = self.convert_data(symbol_data)

        self.symbol_data_dict[symbol].append(data, ignore_idex=True)
        self.symbol_data_dict[symbol].ta.strategy(self.strat)

        self.ema_check(symbol)

    def clear_df_data(self, symbol):
        self.symbol_data_dict[symbol] = None

    def check_market_close(self):
        c = self.api.get_clock().is_open
        if c == False:
            exit()


# WEB SOCKET STREAMING
##################################################################################################
    def start_stream(self):
        socket = 'wss://stream.data.alpaca.markets/v2/iex'
        ws = websocket.WebSocketApp(socket, on_open=self.on_open, on_message=self.on_message, on_close=self.on_close)
        ws.run_forever()

    # What happens when websocket connection is made
    def on_open(self,ws):
        print("opened")
        auth_data = {
            "action": "auth",
            'key': self.key_dict['api_key_id'],
            'secret': self.key_dict['api_secret']
        }
        ws.send(json.dumps(auth_data))

        listen_message = {"action": "subscribe", "bars": self.symbol_list}
        ws.send(json.dumps(listen_message))

    # What happens when websocket receives a message from alpaca
    def on_message(self, ws, message):
        message = json.loads(message)
        print('MESSAGE: ' + message)
        #print('MESSAGE LEN: ' + str(len(message[0])))
        #print('MESSAGE OPEN: ' + str(message[0]['o']))
        #if message[0]['T'] == 'b':
            #self.add_data(stock, message[stock])

    # can you guess what his does?
    def on_close(ws):
        print("Closed Connection")



# GETTERS
##################################################################################################
    def get_clock(self):
        clock_response = self.api.get_clock()
        print('\nCLOCK BOOL:' + str(clock_response.is_open) + '\n')
    
    def get_list_of_orders(self):
        order_list_response = self.api.list_orders()
        print(order_list_response)
        return order_list_response

    def get_position(self, symbol):
        position_response = self.api.get_position(symbol)
        print(position_response.qty)
        return position_response

    def get_position_list(self):
        position_list_response = self.api.list_positions()
        #print(position_list_response)
        return position_list_response

    def get_account_info(self):
        account_response = self.api.get_account()
        print(account_response)
        return account_response

    def get_barset(self, symbol):
        # Takes in a symbol and creates the URL to get barset
        barset_url = 'https://data.alpaca.markets/v2/' + symbol + '/bars'
        barset_api = tradeapi.REST(self.key_dict['api_key_id'], self.key_dict['api_secret'], barset_url, api_version='v2')

        todays_date = datetime.datetime.now(datetime.timezone.utc)
        start_date = todays_date - datetime.timedelta(days=1)

        barset_df = barset_api.get_barset(symbols=symbol, timeframe=self.timeframe, start=start_date, end=todays_date, limit=500).df
        return barset_df[symbol]


# Indicators
##################################################################################################
    def ema_check(self, symbol):
        position_list = self.get_position_list()
        sma_flag = self.symbol_data_dict[symbol]['EMA_60'].iloc[-1] > self.symbol_data_dict[symbol]['EMA_180'].iloc[-1] 
        print('EMA FLAG: ' + str(sma_flag))
        if len(position_list) == 0 and sma_flag:
            print("STEPPING INTO BUY CONDITIONAL")
            self.post_order('AAPL', 10, 'buy')
        elif len(position_list)!= 0 and not sma_flag:
            position = self.get_position()
            if position.qty != 0:
                print("STEPPING INTO SELL CONDITIONAL")
                self.post_order('AAPL', 10, 'sell')

    def sma_check(self, symbol):
        position_list = self.get_position_list()
        sma_flag = self.symbol_data_dict[symbol]['SMA_5'].iloc[-1] > self.symbol_data_dict[symbol]['SMA_13'].iloc[-1] 
        print('SMA FLAG: ' + str(sma_flag))
        if len(position_list) == 0 and sma_flag:
            print("STEPPING INTO BUY CONDITIONAL")
            self.post_order('AAPL', 10, 'buy')
        elif len(position_list)!= 0 and not sma_flag:
            position = self.get_position()
            if position.qty != 0:
                print("STEPPING INTO SELL CONDITIONAL")
                self.post_order('AAPL', 10, 'sell')

    def macd_check_buy(self, symbol):
        # MACD buy sign is when macd goes from below the signal column to above
        # the flag is used to see if macd is currently > or < signal
        macd_flag = False
        for count, row in self.symbol_data_dict[symbol].iterrows():
            if (macd_flag) == False and (row['MACD_12_26_9'] > row['MACDs_12_26_9']):
                print("************\nBUY NOW at count: ", count, '\n************')
                macd_flag = True
            elif (macd_flag == True) and (row['MACD_12_26_9'] < row['MACDs_12_26_9']):
                print("************\nSELL NOW at count: ", count, '\n************')
                macd_flag = False
            else:
                continue


# ORDER FUNCTIONS
##################################################################################################
    def post_order(self, symbol, qty, side):
        print('SUBMITTING ORDER\n')
        order_response = self.api.submit_order(symbol=symbol, qty=qty, side=side, type='market', time_in_force='gtc')
        print(order_response)
        return order_response

    def cancel_order(self):
        cancel_response = self.api.cancel_all_orders()
        print(cancel_response)
        return cancel_response


if __name__ == '__main__':
    freeze_support()
    symbols = ['GME', 'TSLA', 'AAPL']
    bot = Bot(symbols, 'minute')
    bot.start_stream()
