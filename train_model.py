from re import A
import numpy as np
import matplotlib.pyplot as plt

from smartsifter import SDEM
from get_historicial import History
from data_stream import Data_Stream

class Algorithm():
    def __init__(self, data):
        self.data = data['close'].values

    def train_and_fit(self):
        self.price_train = self.data[:int(len(self.data) * 0.7)]
        self.price_test = self.data[int(len(self.data) * 0.3):]
        self.sdem = SDEM(1/2, 1.)
        self.sdem.fit(self.price_train.reshape(-1,1))
        self.scores = []
        for count, price in enumerate(self.price_test):
            price = price.reshape(1,-1)
            self.sdem.update(price)
            self.scores.append(-self.sdem.score_samples(price))
            if len(self.scores) > 2:
                diff = self.percent_difference(self.scores[-1], self.scores[-2])
                if diff > 0.5: # 600% difference
                    print('anomoly found at price: ' + str(count) + ' with a percent diff of ' + str(diff))

    def percent_difference(self,a,b):
        numerator = abs(a-b)
        denominator = abs((a+b)/2)
        result = numerator/denominator * 100
        return result

    def plot_data(self):
        fig, ax = plt.subplots(2,1)
        fig.tight_layout()
        ax[1].set_title('Scores')
        ax[0].set_title('Data')
        ax[0].plot(self.price_test)
        ax[1].plot(self.scores)
        plt.show()