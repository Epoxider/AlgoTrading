import json, datetime
import alpaca_trade_api as tradeapi
from numpy.core.defchararray import array
class History():
    
    def __init__(self, symbol, timeframe):
        self.url = 'https://data.alpaca.markets/v1/bars'
        self.symbol = symbol
        self.timeframe = timeframe
        self.todays_date = datetime.datetime.now(datetime.timezone.utc)
        self.start_date = self.todays_date - datetime.timedelta(days=1)
        self.todays_date = self.todays_date.isoformat()
        self.start_date = self.start_date.isoformat()

        with open("keys.json", "r") as f:
            key_dict = json.loads(f.readline().strip())

        api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], self.url, api_version='v2')
        self.min_barset = api.get_barset(symbols=self.symbol, timeframe=self.timeframe, start=self.start_date, end=self.todays_date, limit=1000)
    
    def get_history(self):
        hist_dict = {}
        for v in self.min_barset[self.symbol]:
            close = float(v.c)
            hist_dict[close] = v.t.date().strftime('%Y-%m-%d')

        return hist_dict

    def write_history(self):
        with open('./aapl_min_data.json', 'a') as f:
            json.dump(self.min_barset._raw, f)
