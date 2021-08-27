import matplotlib.pyplot as plt
from numpy.lib.function_base import append, rot90
import pandas as pd
from pandas.io.formats import style
import pandas_ta as ta
from multiprocessing import freeze_support

if __name__ == '__main__':
    #l1 = [i for i in range(1,300)]
    #l2 = [i for i in range(1,300)]
    #l3 = [i for i in range(1,300)]

    l1 = [i for i in range(1,50)]
    l2 = [i for i in range(1,50)]
    l3 = [i for i in range(1,50)]
    d = {
        'A': l1, 'B': l2, 'Close': l3
    }
    df = pd.DataFrame(d)
    print(df)
    #df = pd.read_csv('AAPL.csv', usecols=['Close'])
    #df = pd.read_csv('AAPL.csv')
    #print(df)
    macd_df = df.ta.macd()
    #macd_df = df.ta.macd(close=df['Close'], append=True)
    print(macd_df)
    #sma_df = ta.sma(df['Close'])
    #print(sma_df)
    #bb_df = ta.bbands(df['Close'])
    #fig, ax = plt.subplots(4,1,figsize=(18,12))
    #ax[0].set_title('Data')
    #ax[1].set_title('MACD')
    #ax[2].set_title('RSI')
    #ax[3].set_title('BBAND')
    #ax[0].plot(df['Close'])
    #ax[1].plot(macd_df['MACD_12_26_9'])
    #ax[2].plot(rsi_df)
    #ax[3].plot(bb_df)
    #fig.tight_layout()
    #plt.show()

#bb_df = ta.bbands(df['Close'])

#plt.plot(bb_df)
#plt.show()