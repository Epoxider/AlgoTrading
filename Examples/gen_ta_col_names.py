import alpaca_trade_api as tradeapi
import json, datetime
import pandas_ta as ta

with open('indicat_cols.txt', 'r') as f:
    fdata = f.read().splitlines()
    print(fdata)
    
with open("keys.json", "r") as f:
    key_dict = json.loads(f.readline().strip())

symbol = 'AAPL'
timeframe = '1Min'
barset_url = 'https://data.alpaca.markets/v2/' + symbol + '/bars'
barset_api = tradeapi.REST(key_dict['api_key_id'], key_dict['api_secret'], barset_url, api_version='v2')
end_date = datetime.datetime.now(datetime.timezone.utc)
start_date = end_date - datetime.timedelta(days=1)
symbol_barset_data = barset_api.get_barset(symbols=symbol, timeframe=timeframe, start=start_date, end=end_date, limit=500).df
#df = symbol_barset_data['AAPL']
l = ['open', 'high', 'low', 'close', 'volume']
col_list = []
col_dict = {}

def write_cols():
    for indi in fdata:
        col_list = []
        df = symbol_barset_data['AAPL']
        strat = ta.Strategy(
            name='betttt',
            ta = [
                {'kind': indi, 'length': 20},
            ]
        )
        df.ta.strategy(strat)
        for col in df:
            if col not in l:
                print(type(col), '\n', col, '\n')
                col_list.append(col)
                col_dict[indi] = col_list
            else:
                continue

    j_data = json.dumps(col_dict, indent=4)
    with open('col_names.json', 'w') as f:
        f.write(j_data)
        #print(col_dict)

'''
strat = ta.Strategy(
    name='betttt',
    ta = [
        {'kind': 'vortex', 'length': 20},
    ]
)
df.ta.strategy(strat)
print(df)
exit()
for col in df:
    if col not in l:
        print(col)
        col_list.append(col)
        #print(col_list)
        col_dict['short_run'] = col_list
        print(col_dict)
'''

write_cols()



