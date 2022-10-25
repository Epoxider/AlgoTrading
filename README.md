# AlgoTrading

First Step:
Copy code below into a file called "keys.json" and replace values with your respective keys
{"api_key_id": "PXXXXXXXXXXXXK", "api_secret" : "fXXXXXXXXXXXXXXXXXXXXXP"}

To run:
python3 monke_maker.py

This program pulls live market data and can calculate many different indicators for any number of symbols. Data is transfromed from a "bar" object (defined by alpaca) and transforms it into a pandas dataframe. There are many technical analysis librarys that use pandas dataframe, buts the one used in this program is "pandas_ta". To see all of the inidcators useable by "pandas_ta", look at the file "ta_indicators.json".

To define the symbols to watch, enter ticker names into the "symbols" list in the main function near bottom.

To define the timeframe of the data (minutes, hours, days, etc), the set property of the "TimeFrame" object (object imported from alpaca library) in the main function.
  Example: TimeFrame.Minute
           TimeFrame.Hour
           TimeFrame.Day
           
To define strategy and which indicators to use, go to the "setup_strategy" function in the Bot() class. You may need to define your variables, but if needed reference the "ta_indicators.json" file for how to define parameters for an indicator. See pandas_ta documentation for more details.



