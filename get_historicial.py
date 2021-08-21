import json, datetime
import numpy as np
import alpaca_trade_api as tradeapi
from numpy.core.defchararray import array
class History():
    
    def __init__(self, symbol, timeframe):
        self.url = 'https://data.alpaca.markets/v1/bars'
        self.symbol = symbol
        self.timeframe = timeframe
        self.todays_date = datetime.datetime.now(datetime.timezone.utc)
        self.start_date = self.todays_date - datetime.timedelta(days=6)
        self.todays_date = self.todays_date.isoformat()
        self.start_date = self.start_date.isoformat()

        with open("keys.json", "r") as f:
            key_dict = json.loads(f.readline().strip())

        api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], self.url, api_version='v2')
        self.barset = api.get_barset(symbols=self.symbol, timeframe='1Min', start=self.start_date, end=self.todays_date, limit=1000)
    
    def get_history(self):

        hist_dict = {}
        for v in self.barset[self.symbol]:
            close = float(v.c)
            hist_dict[close] = v.t.date().strftime('%Y-%m-%d')

        return hist_dict

    def write_history(self):

        with open('./aapl_min_data.json', 'a') as f:
            json.dump(self.barset._raw, f)

'''
h = History('AAPL', '1Min')
d = h.get_history()
#print(list(d.values())[0])
counter = 0
for i in d.values():
    print(i.date())
    counter += 1
    if counter > 2:
        break
'''