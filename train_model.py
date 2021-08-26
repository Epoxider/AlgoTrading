from re import A
import numpy as np
import matplotlib.pyplot as plt

from smartsifter import SDEM
from get_historicial import History
from data_stream import Data_Stream

class Algorithm():
    def __init__(self, symbol):
        self.data = Data_Stream().get_stream_data()
        self.hist_min_data = History(symbol=symbol, timeframe=('1Min')).get_history()
        self.hist_day_data = History(symbol=symbol, timeframe=('1Day')).get_history()
        self.hist_prices_list = list(self.data.keys())
        self.hist_dates_list = list(self.data.values())

        self.hist_prices = np.array(list(self.data.keys()))
        self.hist_dates = np.array(list(self.data.values()))

    def Calc_MACD(self, data):
        short_ema = []
        last_12_avg = sum(data[-12:])/len(data[-12:])
        short_ema.append(last_12_avg)
        for i in range(12):
            ema = ( ( i * (2 / (12 + 1) ) ) + short_ema[-1])
            short_ema.append(ema)

        long_ema = []
        last_26_avg = sum(data[-26:])/len(data[-26:])
        long_ema.append(last_26_avg)
        for i in range(26):
            ema = ( ( i * (2 / (26 + 1) ) ) + long_ema[-1])
            long_ema.append(ema)

        self.macd = []
        zipr = zip(long_ema[-12:], short_ema)
        for l1, l2 in zipr:
            self.macd.append(l2 - l1)

        self.signal = []
        avg_ema = sum(self.macd)/len(self.macd)
        self.signal.append(avg_ema)
        for i in range(9):
            ema = ( ( i * (2 / (12 + 1) ) ) + self.signal[-1])
            self.signal.append(ema)

        print(self.macd, self.signal)
        
        # Two lists to plot: self.macd, self.signal
        # If self.signal is > self.macd: SELL else BUY GET YOUR NUGGIES 

    def Update_MACD(self, datum):
            ema = ( ( datum * (2 / (12 + 1) ) ) + self.signal[-1])
            self.signal.append(ema)


    def train_and_fit(self):
        self.price_train = self.hist_prices[:int(len(self.prices) * 0.7)]
        self.price_test = self.hist_prices[int(len(self.prices) * 0.3):]
        self.date_train = self.hist_dates[:int(len(self.dates) * 0.7)]
        self.date_test = self.hist_dates[int(len(self.dates) * 0.3):]
        self.sdem = SDEM(1/2, 1.)
        self.sdem.fit(self.price_train.reshape(-1,1))
        scores = []
        for price in self.price_test:
            price = price.reshape(1,-1)
            self.sdem.update(price)
            scores.append(-self.sdem.score_samples(price))

    def plot_data(self):
        fig, ax = plt.subplots(2,1)
        fig.tight_layout()
        ax[1].set_title('Scores')
        ax[0].set_title('Data')
        ax[0].plot(self.price_test)
        ax[1].plot(self.scores)
        plt.show()

#aapl_hist = History(symbol='AAPL', timeframe='1Min')
#data = aapl_hist.get_history()

#model = ModelData('AAPL')
#model.train_and_fit()
#model.plot_data()

Data_Stream('AAPL')