import websocket, json, datetime, pytz
import alpaca_trade_api as tradeapi
import pandas_ta as ta
import matplotlib.pyplot as plt
from multiprocessing import freeze_support
from alpaca_trade_api.rest import TimeFrame
from datetime import date

class Bot():

    def __init__(self, symbol_list, timeframe):
        self.symbol_list = symbol_list
        self.timeframe = timeframe
        self.qty_to_order = 10
        self.confidence = 0
        self.symbol_data_dict = {}   # Keys = symbols, values = strategy datafames
        self.todays_date = datetime.date.today().strftime('%d_%m_%Y')

        with open("keys.json", "r") as f:
            self.key_dict = json.loads(f.readline().strip())

        self.url = 'https://paper-api.alpaca.markets'
        self.api = tradeapi.REST(self.key_dict['api_key_id'], self.key_dict['api_secret'], self.url, api_version='v2')

        self.setup_strategy()


    # DATA MANIUPLATION
    ##################################################################################################
    def setup_strategy(self):
        self.ema_small = 12
        self.ema_big = 26
        self.sma_small = 12
        self.sma_big = 26

        # 5 indicators: sma, ema, bbands, macd, rsi
        self.strat = ta.Strategy(
            name='betttt',
            ta = [
                {'kind': 'sma', 'length': self.sma_small},
                {'kind': 'sma', 'length': self.sma_big},
                {'kind': 'ema', 'length': self.ema_small},
                {'kind': 'ema', 'length': self.ema_big},
                {"kind": "bbands", "length": 20, "col_names": ("BBL", "BBM", "BBU", "BBB", "BBP")},
                {'kind': 'macd', 'col_names': ('MACD', 'MACDH', 'MACD_S')},
                {'kind': 'rsi'},
            ]
        )

        for symbol in self.symbol_list:
            self.confidence = 0
            self.symbol_data_dict[symbol] = self.get_barset(symbol)
            self.symbol_data_dict[symbol].ta.strategy(self.strat)

            todays_date = datetime.datetime.now().strftime('%Y-%m-%d')

            print(symbol+'\n\n'+self.symbol_data_dict[symbol].tail(5).to_string())
            # Below code is just for when market is offline
            
            self.sma_check(symbol)
            self.ema_check(symbol)
            self.macd_check(symbol)
            self.bbands_check(symbol)
            self.rsi_check(symbol)
            print('\n\n'+symbol)
            self.get_position(symbol)

            fp = open('Stock_Data/'+'Test_Writing/'+ symbol + '_' + todays_date+'.txt', 'a')
            fp.truncate(0)
            fp.write(self.symbol_data_dict[symbol].to_string())
            fp.close()
            


    def add_data(self, symbol):
        self.check_market_close()
        df = self.symbol_data_dict[symbol] 
        df.ta.strategy(self.strat)
        self.symbol_data_dict[symbol] = df
        print('\n\n*******************************************************\n\
            '+ symbol + '\n' + str(self.symbol_data_dict[symbol].tail(5).to_string(index=False)))

        self.sma_check(symbol)
        self.ema_check(symbol)
        self.macd_check(symbol)
        self.bbands_check(symbol)
        self.rsi_check(symbol)
        self.order_post_checker(symbol)


    def plot_data(self, symbol):
        closing = self.symbol_data_dict[symbol]['close']
        bband_upper = self.symbol_data_dict[symbol]['BBU']
        bband_lower = self.symbol_data_dict[symbol]['BBL']

        plt.xticks(rotation=90)
        plt.plot(bband_upper, 'r--', label='bband_upper')
        plt.plot(bband_lower, 'g--', label='bband_lower')
        plt.plot(closing, label='close')
        plt.legend()
        plt.show()


    def clear_df_data(self, symbol):
        self.symbol_data_dict[symbol] = None


    def check_market_close(self):
        c = self.api.get_clock().is_open
        if c == False:
            todays_date = datetime.datetime.now().strftime('%Y-%m-%d')
            for stock in self.symbol_data_dict:
                with open('Stock_Data/'+str(stock)+'/'+todays_date+'.txt', 'w') as f:
                    f.write(self.symbol_data_dict[stock].to_string())
            exit()


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
        self.confidence = 0
        print(message)
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
            print('\nPosition quantity response: ' + response.qty)
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

        end_date = datetime.datetime.now(datetime.timezone.utc)

        end_date = end_date - datetime.timedelta(minutes=15)
        start_date = end_date - datetime.timedelta(days=5)

        barset_symbol_data = barset_api.get_bars(symbol=symbol, timeframe=self.timeframe, start=start_date.isoformat(), end=end_date.isoformat(), limit=500).df
        return barset_symbol_data


    # Indicators
    ##################################################################################################
    def ema_check(self, symbol):
        ema_col_small = 'EMA_' + str(self.ema_small)
        ema_col_big = 'EMA_' + str(self.ema_big)
        ema_flag = self.symbol_data_dict[symbol][ema_col_small].iloc[-1] > self.symbol_data_dict[symbol][ema_col_big].iloc[-1] 
        print('ema flag: ' + str(ema_flag))
        if ema_flag:
            self.confidence += 0.5
        else:
            self.confidence -= 0.5
        

    def sma_check(self, symbol):
        sma_col_small = 'SMA_' + str(self.sma_small)
        sma_col_big = 'SMA_' + str(self.sma_big)
        # if sma small > sma big: add 0.5 else sub 0.5
        sma_flag = self.symbol_data_dict[symbol][sma_col_small].iloc[-1] > self.symbol_data_dict[symbol][sma_col_big].iloc[-1] 
        print('sma flag: ' + str(sma_flag))
        if sma_flag:
            self.confidence += 0.5
        else:
            self.confidence -= 0.5


    def macd_check(self, symbol):
        # MACD buy sign is when macd goes from below the signal column to above
        # the flag is used to see if macd is currently > or < signal
        macd_flag = self.symbol_data_dict[symbol]['MACD'].iloc[-1] >= self.symbol_data_dict[symbol]['MACD_S'].iloc[-1] 
        print('macd flag: ' + str(macd_flag))
        if macd_flag:
            self.confidence += 0.5
        else:
            self.confidence -= 0.5


    def rsi_check(self, symbol):
        if self.symbol_data_dict[symbol]['RSI_14'].iloc[-1] > 70: 
            self.confidence -= 0.5
            print('rsi: ' + 'True')
        elif self.symbol_data_dict[symbol]['RSI_14'].iloc[-1] < 30: 
            self.confidence += 0.5
            print('rsi: ' + 'False')
        else:
            print('rsi: No change')


    def bbands_check(self, symbol):
        if self.symbol_data_dict[symbol]['BBM'].iloc[-1] <= self.symbol_data_dict[symbol]['BBL'].iloc[-1]:
            self.confidence += 0.5
            print('bbands: True')
        elif self.symbol_data_dict[symbol]['BBM'].iloc[-1] >= self.symbol_data_dict[symbol]['BBU'].iloc[-1]:
            self.confidence -= 0.5
            print('bbands: False')
        else:
            print('bbands: No change')


    def order_post_checker(self, symbol):
        position_response = self.get_position(symbol)
        print('Confidence: ' + str(self.confidence))
        print('POS RESP TYPE: ' + str(type(position_response)))
        if position_response:
            pos_qty = int(position_response.qty)
            if self.confidence < 0: 
                if pos_qty > 0:
                    print('SUBMITTING SELL ORDER\n')
                    self.post_order(symbol, 'sell')
            elif self.confidence > 0:
                if pos_qty > 0:
                    print('SUBMITTING BUY ORDER\n')
                    self.post_order(symbol, 'buy')
        else:
            if self.confidence > 0:
                print('SUBMITTING BUY ORDER\n')
                self.post_order(symbol, 'buy')


    # ORDER FUNCTIONS
    ##################################################################################################
    def post_order(self, symbol, side):
        order_response = self.api.submit_order(symbol=symbol, qty=self.qty_to_order, side=side, type='market', time_in_force='gtc')
        print('\nOrder response: \n' + str(order_response))


    def cancel_order(self):
        cancel_response = self.api.cancel_all_orders()
        print('\nCancel response: ' + str(cancel_response))
        return cancel_response


if __name__ == '__main__':
    freeze_support()
    #symbols = ['GME', 'TSLA', 'AAPL', 'AMZN', 'MSFT']
    symbols = ['GME']
    bot = Bot(symbols, TimeFrame.Minute)
    bot.start_stream()

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

# Custom strategy from my monke brain
# Note: This calculates the indicators, NOT when to buy sell
#       need to calculate buy/sell logic in addition
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
