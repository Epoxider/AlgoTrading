import numpy as np
import matplotlib.pyplot as plt

from smartsifter import SDEM
from get_historicial import History

class ModelData():
    def __init__(self, symbol):
        self.data = History(symbol=symbol, timeframe=('1Min')).get_history()
        self.sdem = SDEM(1/2, 1.)
        self.prices = np.array(list(self.data.keys()))
        self.dates = np.array(list(self.data.values()))
        self.train_and_fit()

    def train_and_fit(self):
        self.price_train = self.prices[:int(len(self.prices) * 0.7)]
        self.price_test = self.prices[int(len(self.prices) * 0.3):]
        self.date_train = self.dates[:int(len(self.dates) * 0.7)]
        self.date_test = self.dates[int(len(self.dates) * 0.3):]
        self.sdem.fit(self.price_train.reshape(-1,1))

    def plot_data(self):
        fig, ax = plt.subplots(2,1)
        fig.tight_layout()
        ax[1].set_title('Scores')
        ax[0].set_title('Data')
        scores = []
        for price in self.price_test:
            price = price.reshape(1,-1)
            self.sdem.update(price)
            scores.append(-self.sdem.score_samples(price))
            ax[0].plot(self.price_test)
            ax[1].plot(scores)
            plt.pause(0.01)

        plt.show()

#aapl_hist = History(symbol='AAPL', timeframe='1Min')
#data = aapl_hist.get_history()

model = ModelData('AAPL')
model.train_and_fit()
model.plot_data()