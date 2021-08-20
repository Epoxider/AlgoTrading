import pandas as pd
import numpy as np
import smartsifter as ss
import matplotlib.pyplot as plt
from smartsifter import SDEM
from sklearn.model_selection import train_test_split


df = pd.read_csv('AAPL.csv')
#df['Close'].plot()

close = df['Close']

days = [i for i in range(0, len(df))]
days = np.array(days).reshape(-1,1)

x_train = np.array(close[:int(len(close) * 0.7)])
x_test = np.array(close[int(len(close) * 0.3):])
#x_test = np.array(close)

sdem = SDEM(1/2, 1.)
sdem.fit(x_train.reshape(-1,1))

scores = []

fig, ax = plt.subplots(2,1)
fig.tight_layout()
ax[1].set_title('Scores')
ax[0].set_title('Data')

for count, x in enumerate(x_test):
  x = x.reshape(1,-1)
  sdem.update(x)
  scores.append(-sdem.score_samples(x))
  if sdem.score_samples(x) < -3.40:
    print('found anomoly at ' + str(count) + ' with a score of ' + str(sdem.score_samples(x)))

  ax[0].plot(x_test)
  ax[1].plot(scores)
  plt.pause(0.01)

plt.show()



