import json, requests, datetime
import alpaca_trade_api as tradeapi

#url = 'https://data.alpaca.markets/v2/stocks/AAPL/trades'
url = 'https://data.alpaca.markets/v1/bars'

with open("keys.json", "r") as f:
    key_dict = json.loads(f.readline().strip())

api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], url, api_version='v2')

todays_date = datetime.datetime.now(datetime.timezone.utc)
start_date = todays_date - datetime.timedelta(days=6)

todays_date = todays_date.isoformat()
start_date = start_date.isoformat()

barset = api.get_barset(symbols='AAPL', timeframe='1Min', start=start_date, end=todays_date, limit=1000)

#with open('./aapl_min_data.json', 'a') as f:
#    barset_json = json.dump(barset._raw, f)

[print(i.c) for i in barset['AAPL']]