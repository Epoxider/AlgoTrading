import numpy as np
import matplotlib.pyplot as plt

from smartsifter import SDEM
from get_historicial import History

class Algorithm():
    def __init__(self, symbol, data):
        self.data = data
        self.data_hist = History(symbol=symbol, timeframe=('1Min')).get_history()
        self.sdem = SDEM(1/2, 1.)
        self.prices = np.array(list(self.data_hist.keys()))
        self.dates = np.array(list(self.data_hist.values()))
        self.train_and_fit()
        self.anomoly_list = []
        self.train_model_get_scores(data)

    def train_model_get_scores(self, data):
        self.price_train = self.prices[:int(len(self.prices) * 0.7)]
        self.price_test = self.prices[int(len(self.prices) * 0.3):]
        self.date_train = self.dates[:int(len(self.dates) * 0.7)]
        self.date_test = self.dates[int(len(self.dates) * 0.3):]
        self.sdem.fit(self.price_train.reshape(-1,1))
        self.scores = []
        for count, price in enumerate(data):
            price = price.reshape(1,-1)
            self.sdem.update(price)
            self.scores.append(-self.sdem.score_samples(price))
            if len(self.scores) > 2:
                diff = self.percent_difference(self.scores[-1], self.scores[-2])
                if diff > 6.0: # 600% difference
                    print('anomoly found at price: ' + str(count) + ' with a percent diff of ' + str(diff))

        return self.scores

    def percent_difference(self,a,b):
        numerator = abs(a-b)
        denominator = abs((a+b)/2)
        result = numerator/denominator * 100
        return result

    def plot_data(self):
        fig, ax = plt.subplots(2,1)
        fig.tight_layout()
        ax[0].set_title('Data')
        ax[0].plot(self.price_test)
        ax[1].set_title('Scores')
        ax[1].plot(self.scores)
        plt.pause(0.01)
        plt.show()

model = Algorithm('AAPL')
model.plot_data()