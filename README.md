## Alpaca Algorithm Trading Bot

I've developed a Trading bot that connects to a Websocket server using the Alpaca API as well as executing orders.
Note: I do not recommend using this bot for making financial decisions.

## Table of Contents
- [Detailed Description](#detailed-description)
- [Strategy](#strategy)
- [Files](#files)
- [Results](#results)

## Detailed Description
I designed a trading bot which takes in stock information from a server and buys or sells a certain stock based on a strategy I implemented. You can look at the strategy I've implemented in the [Strategy](#strategy) section below. 

I designed the trading bot by connecting the bot to the Alpaca Trading API in order to allow the bot to buy or sell real stocks using paper money. The API allow allowed me to also connect to a Websocket Server which allow the bot to access real time data in order to effectively make trades based on the given strategy. The API gave access to historical data, which allowed me to manipulate the data in order to backtest the trading bot on historical prices, which the results are shown in the [Results](#results) Section. I had to implement threading in order for the bot to access both the market data and make buy or sell orders at the same time.

## Strategy
- The Bot's Strategy is based on Small Moving Averages of 10 and 50
    - Whenever SMA10 crosses above SMA50, it makes a buy order
    - Whenever SMA10 crosses below SMA50, it makes a sell order
 
## Files
- Alpaca_Websocket_AlgoBot.py: Contains the Websocket class to connect to live server and provides data for the strategy, also where the backtesting is done
- Algo_Trad_Bot.ipynb: Juypter Notebook of the trading bot running
- Algo_Trad_Bot.py: Python File of trading bot running

## Results
- Overall, average return was relativly low (+0.2% - +1.1%)
- Highest Performing Stock was TSLA with Average Return of +1.1% and range of return of +40% and -11%
