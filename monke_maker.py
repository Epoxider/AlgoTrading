import websocket, json, datetime
import alpaca_trade_api as tradeapi
import pandas_ta as ta
import pandas as pd
import pytz
from multiprocessing import freeze_support

pd.set_option('max_column', None)

class Bot():
    def __init__(self, symbol_list, timeframe):
        self.symbol_list = symbol_list
        self.timeframe = timeframe
        self.confidence= 0.0
        self.qty_to_order = 10
        self.symbol_data_dict = {}   # Keys = symbols, values = strategy datafames
        self.todays_date = datetime.date.today().strftime('%d_%m_%Y')

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
                {'kind': 'ema', 'length': 12},
                {'kind': 'ema', 'length': 26},
                #{"kind": "bbands", "length": 20, "col_names": ("BBL", "BBM", "BBU", "BBB", "BBP")},
                #{'kind': 'macd', 'col_names': ('MACD', 'MACDH', 'MACD_S')},
                #{'kind': 'rsi'},
            ]
        )

        self.ema_col_small = 'EMA_' + str(12)
        self.ema_col_big = 'EMA_' + str(26)


        for symbol in self.symbol_list:
            self.symbol_data_dict[symbol] = self.get_barset(symbol)
            self.symbol_data_dict[symbol].ta.strategy(self.strat)
            print(symbol+'\n\n'+self.symbol_data_dict[symbol].tail(5).to_string())


        '''
        ################################################################
        EXAMPLE DATA MANIPULATION AND SHOWING DATA HISTORY AND STRAT DF
        ################################################################

        if rsi > 70: sell 
        if rsi < 30: buy

        if macd cross from below to above macd_s: buy else: sell

        if bband mid < bband lower: buy
        if bband mid > bband high: sell




        # Can use l to ignore default columns in df

        l = ['open', 'high', 'low', 'close', 'volume']

        # Read each indicator from indi_cols txt line by line
        with open('indicat_cols.txt', 'r') as f:
            indis = f.read().splitlines()

        # Create a new dataframe with for each indicator
        for count, indi in enumerate(indis):
            #if count > 10: break
            self.strat = ta.Strategy(
                name='betttt',
                ta = [
                    {'kind': indi},
                    #{'kind': 'ema', 'length': 13},
                    #{'kind': 'sma', 'length': 5},
                    #{'kind': 'sma', 'length': 13},
                    #{'kind': 'macd', 'length': 20},
                    #{'kind': 'bbands', 'length': 20},
                ]
            )
            # For each symbol, get barset, apply strat, remove cols found in l \
            # (to just show new cols from pandas ta), write out 
            for symbol in symbol_list:
                self.symbol_data_dict[symbol] = self.get_barset(symbol)
                self.symbol_data_dict[symbol].ta.strategy(self.strat)

                my_col = set(self.symbol_data_dict[symbol].columns)
                [my_col.remove(i) for i in l]
                print('\n'+self.symbol_data_dict[symbol][my_col].tail(5).to_string(index=False))

                with open('ex_cols.txt', 'a') as f:
                    f.write(self.symbol_data_dict[symbol][my_col].tail(5).to_string(index=False)+'\n'+'\n')


        ################################################################
        END EXAMPLE
        ################################################################
        '''


# DATA MANIUPLATION
##################################################################################################

    def add_data(self, symbol):
        print('inside add daata function\n')
        self.check_market_close()
        print('after market close')
        df = self.symbol_data_dict[symbol] 
        df.ta.strategy(self.strat)
        self.symbol_data_dict[symbol] = df
        print('\n\n*******************************************************\n\
            '+ symbol + '\n' + str(self.symbol_data_dict[symbol].tail(5)))

        self.ema_check(symbol)

        if self.post_order_flag:
            self.post_order(symbol, self.qty_to_order)

        with open('Stock_Data/'+symbol+'/'+self.todays_date+'.txt', 'a') as f:
            f.write(self.symbol_data_dict[symbol].tail().to_string(index=False))

    def clear_df_data(self, symbol):
        self.symbol_data_dict[symbol] = None

    def check_market_close(self):
        c = self.api.get_clock().is_open
        if c == False:
            exit()

    def ema_values(self, small, big):
        self.ema_col_small = 'EMA_' + str(small)
        self.ema_col_big = 'EMA_' + str(big)


# WEB SOCKET STREAMING
##################################################################################################
    def start_stream(self):
        socket = 'wss://stream.data.alpaca.markets/v2/iex'
        ws = websocket.WebSocketApp(socket, on_open=self.on_open, on_message=self.on_message, on_close=self.on_close)
        ws.run_forever()

    # What happens when websocket connection is made
    def on_open(self,ws):
        print("Opened websocket connection successfully!")
        auth_data = {
            "action": "auth",
            'key': self.key_dict['api_key_id'],
            'secret': self.key_dict['api_secret']
        }
        ws.send(json.dumps(auth_data))
        print('SEND JSON')
        listen_message = {"action": "subscribe", "bars": self.symbol_list}
        ws.send(json.dumps(listen_message))

    # What happens when websocket receives a message from alpaca
    def on_message(self, ws, message):
        message = json.loads(message)
        self.post_order_flag = False
        if message[0]['T'] == 'b':
            data = {}
            #data['date'] = symbol_data['t']
            data['open'] = message[0]['o']
            data['high'] = message[0]['h']
            data['low'] = message[0]['l']
            data['close'] = message[0]['c']
            data['volume'] = message[0]['v']
            print(data)
            self.add_data(str(message[0]['S']))

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
        print('\nOrder list: ' + order_list_response)
        return order_list_response

    def get_position(self, symbol):
        try:
            response = self.api.get_position(symbol)
            print('\nPosition quantity response: ' + str(response.qty))
            return response
        except Exception as e:
            print(e)
            return None

    def get_position_list(self):
        position_list_response = self.api.list_positions()
        return position_list_response

    def get_account_info(self):
        account_response = self.api.get_account()
        print('\nAccount response: ' + str(account_response))
        return account_response

    def get_barset(self, symbol):
        # Takes in a symbol and creates the URL to get barset
        barset_url = 'https://data.alpaca.markets/v2/' + symbol + '/bars'
        barset_api = tradeapi.REST(self.key_dict['api_key_id'], self.key_dict['api_secret'], barset_url, api_version='v2')

        # Need to calculate end date first to correctly subtract time to get start date
        end_date = datetime.datetime.now(pytz.timezone('US/Eastern'))
        start_date = end_date - datetime.timedelta(days=1)
        barset_symbol_data = barset_api.get_barset(symbols=symbol, timeframe=self.timeframe, start=start_date, end=end_date, limit=500).df

        return barset_symbol_data[symbol]


# Indicators
##################################################################################################
    def ema_check(self, symbol):
        position_response = self.get_position(symbol)
        if position_response is not None:
            position_qty = position_response.qty
        else:
            position_qty = None

        ema_flag = self.symbol_data_dict[symbol][self.ema_col_small].iloc[-1] > self.symbol_data_dict[symbol][self.ema_col_big].iloc[-1] 
        print('\n*****\nEMA FLAG: '+str(ema_flag)+'\n*****\n')
        if position_qty == None and ema_flag:
            print("STEPPING INTO BUY CONDITIONAL")
            self.confidence += 0.5
            self.post_order_flag = True
        elif position_qty != None and not ema_flag:
            print("STEPPING INTO SELL CONDITIONAL")
            self.confidence -= 0.5
            self.post_order_flag = True
        

    def sma_check(self, symbol):
        position_response = self.get_position(symbol)
        if position_response is not None:
            position_qty = position_response.qty
        else:
            position_qty = None

        sma_flag = self.symbol_data_dict[symbol]['SMA_5'].iloc[-1] > self.symbol_data_dict[symbol]['SMA_13'].iloc[-1] 
        if position_qty is None and sma_flag:
            print("STEPPING INTO BUY CONDITIONAL")
            self.confidence += 0.5
            self.post_order_flag = True
        elif position_qty is not None and not sma_flag:
            print("STEPPING INTO SELL CONDITIONAL")
            self.confidence -= 0.5
            self.post_order_flag = True

    def macd_check(self, symbol):
        # MACD buy sign is when macd goes from below the signal column to above
        # the flag is used to see if macd is currently > or < signal
        macd_flag = False
        for count, row in self.symbol_data_dict[symbol].iterrows():
            if (macd_flag) == False and (row['MACD_12_26_9'] > row['MACDs_12_26_9']):
                print("************\nBUY NOW at count: ", count, '\n************')
                self.confidence += 0.5
                self.post_order_flag = True
            elif (macd_flag == True) and (row['MACD_12_26_9'] < row['MACDs_12_26_9']):
                print("************\nSELL NOW at count: ", count, '\n************')
                self.confidence -= 0.5
                self.post_order_flag = True
            else:
                continue

    def rsi_check(self, symbol):
        if self.symbol_data_dict[symbol]:
            if self.symbol_data_dict['RSI_14'] > 70: 
                self.confidence -= 0.5
                self.post_order_flag = True
            if self.symbol_data_dict['RSI_14'] < 30: 
                self.confidence += 0.5
                self.post_order_flag = True

    def bbands_check(self, symbol):
        if self.symbol_data_dict[symbol]:
            if self.symbol_data_dict['BBM'] > self.symbol_data_dict['BBU']: 
                self.confidence -= 0.5
                self.post_order_flag = True
            if self.symbol_data_dict['BBM'] > self.symbol_data_dict['BBL']: 
                self.confidence -= 0.5
                self.post_order_flag = True

# ORDER FUNCTIONS
##################################################################################################
    def post_order(self, symbol, qty):
        print('SUBMITTING ORDER\n')
        if self.confidence > 0:
            side = 'buy'
        else:
            side = 'sell'

        order_response = self.api.submit_order(symbol=symbol, qty=qty, side=side, type='market', time_in_force='gtc')
        print('\nOrder response: ' + str(order_response))
        return order_response

    def cancel_order(self):
        cancel_response = self.api.cancel_all_orders()
        print('\nCancel response: ' + str(cancel_response))
        return cancel_response


if __name__ == '__main__':
    freeze_support()
    symbols = ['GME', 'TSLA', 'AAPL', 'AMZN', 'MSFT']
    bot = Bot(symbols, 'minute')
    bot.start_stream()
