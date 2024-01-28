# Alpaca Algorithm Trading Bot

I've developed a Trading bot that connects to a Websocket server using the Alpaca API as well as executing orders.
Note: I do not recommend using this bot for making financial decisions.

# Strategy
- The Bot's Strategy is based on Small Moving Averages of 10 and 50
    - Whenever SMA10 crosses above SMA50, it makes a buy order
    - Whenever SMA10 crosses below SMA50, it makes a sell order
 
# Files
- Alpaca_Websocket_AlgoBot.py: Contains the Websocket class to connect to live server and provides data for the strategy, also where the backtesting is done
- Algo_Trad_Bot.ipynb: Juypter Notebook of the trading bot running
- Algo_Trad_Bot.py: Python File of trading bot running

# Results
- Overall, average return was relativly low (+0.2% - +1.1%)
- Highest Performing Stock was TSLA with Average Return of +1.1% and range of return of +40% and -11%
