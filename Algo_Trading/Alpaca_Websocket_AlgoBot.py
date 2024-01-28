import websocket
import json
import pandas as pd
import pandas_ta as ta
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta

class AlpacaWebSocket:
    def __init__(self, symbol, api_key, api_secret, period=30, max_candles=100, full_history=False, historic_days=7):
        self.symbol = symbol
        self.api_key = api_key
        self.api_secret = api_secret
        self.websocket_url = "wss://stream.data.alpaca.markets/v2/iex"
        self.ws = websocket.WebSocketApp(self.websocket_url,
                                        on_open=self.on_open,
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close,
                                        )
        self.bars_data_1min = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.bars_data_period = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'sma_10', 'sma_50', 'cross_signal'])
        self.period = period
        self.max_candles = max_candles
        self.full_history = full_history
        self.historic_days = historic_days
        
        self.get_historical_data()
        
    def on_message(self, ws, message):
        data = json.loads(message)
        print("Received: ", data)

        if isinstance(data, list) and len(data) == 1 and data[0].get("T") == "success" and data[0].get("msg") == "connected":
            print("Connection successful.")
            self.authenticate()
            return
        
        if isinstance(data, list) and len(data) == 1 and data[0].get("T") == "success" and data[0].get("msg") == "authenticated":
            print("Authentication successful.")
            self.subscribe()
            return
        
        if data[0].get("T") == "b":
            self.handle_bars_data(data[0])
    
    def handle_bars_data(self, bars_data):
        timestamp = bars_data.get("t")
        open_price = bars_data.get("o")
        high_price = bars_data.get("h")
        low_price = bars_data.get("l")
        close_price = bars_data.get('c')
        volume = bars_data.get("v")

        new_data = {
            'timestamp': timestamp,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        }

        #Checking to start candle at a 30 minute interval
        interval_test = datetime.fromisoformat(timestamp[:-1]).minute

        print(f"Obtained minute: {new_data}")

        if self.bars_data_1min.empty and interval_test in [0, 30]:
            self.bars_data_1min = pd.concat([self.bars_data_1min, pd.DataFrame([new_data])], ignore_index=True)
            print(f"Added minute: {new_data}")
        elif not self.bars_data_1min.empty:
            self.bars_data_1min = pd.concat([self.bars_data_1min, pd.DataFrame([new_data])], ignore_index=True)
            print(f"Added minute: {new_data}")

        #Creates a period size bar
        if len(self.bars_data_1min) >= self.period:
            last_bars = self.bars_data_1min[-30:]
            aggregated_data = {
                'timestamp': last_bars['timestamp'].iloc[-1],
                'open': last_bars['open'].iloc[0],
                'high': last_bars['high'].max(),
                'low': last_bars['low'].min(),
                'close': last_bars['close'].iloc[-1],
                'volume': last_bars['volume'].sum()
            }

            #Append bar to period df
            self.bars_data_period = pd.concat([self.bars_data_period, pd.DataFrame([aggregated_data])], ignore_index=True)

            self.bars_data_period['sma_10'] = ta.sma(self.bars_data_period['close'], length=10)
            self.bars_data_period['sma_50'] = ta.sma(self.bars_data_period['close'], length=50)

            #Assign cross_signal
            self.bars_data_period['cross_signal'] = cross_signal_calc(self.bars_data_period)
            
            #Limit
            if len(self.bars_data_period) > self.max_candles:
                self.bars_data_period = self.bars_data_period.iloc[-self.max_candles:]
            
            #Information
            print("1 minute df:\n", self.bars_data_1min)
            print(f"Last 15 Candles ({self.period} min)")
            print(self.bars_data_period.tail(15))

            #Reset 1min df
            self.bars_data_1min = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    def get_historical_data(self):
        API = tradeapi.REST(self.api_key, self.api_secret, base_url='https://data.alpaca.markets')

        #Calculate and convert time
        end_time = datetime.now()
        start_time = end_time - timedelta(days=self.historic_days)
        
        start_time_iso = start_time.isoformat() + 'Z'
        end_time_iso = end_time.isoformat() + 'Z'

        #Obtaining past data
        historical_data = API.get_bars(self.symbol, '30Min', start=start_time_iso, end=end_time_iso).df

        #Reseting index
        historical_data.reset_index(inplace=True)
        historical_data.rename(columns={'index': 'timestamp'}, inplace=True)
        
        #Adding technical Indicators and cross signal
        historical_data['sma_10'] = ta.sma(historical_data['close'], length=10)
        historical_data['sma_50'] = ta.sma(historical_data['close'], length=50)
        historical_data['cross_signal'] = None

        if not self.full_history:
            #Remove first 50 rows
            historical_data = historical_data.iloc[50:]

        #Start index at 0
        historical_data.index = range(len(historical_data))
        
        #Calculate cross_signal
        historical_data['cross_signal'] = cross_signal_calc(historical_data)

        #Append historical data
        self.bars_data_period = pd.concat([self.bars_data_period, historical_data[self.bars_data_period.columns]])

    def on_error(self, ws, error):
        print("Error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("Closed:", close_status_code, close_msg)
    
    def on_open(self, ws):
        print("Opened Connection")
        print("Current Data:")
        print(self.bars_data_period)
        print(self.bars_data_period['cross_signal'].value_counts())
        backtest_total_profit, backtest_trades, backtest_ind_profit, percentages, ave_percent, highest_percent, lowest_percent = back_testing(self.bars_data_period)
        print(f'Backtest Total Profit: ${backtest_total_profit:.2f}')
        print(f'Backtest trades: {backtest_trades}')
        print(f'Backtest Individual Profits {backtest_ind_profit}')
        print(f'Percentages: {percentages}')
        print(f'Average Percentage: {ave_percent:.4f}%')
        print(f'Highest Percentage: {highest_percent:.4f}%')
        print(f'Lowest Percent: {lowest_percent:.4f}%')
    
    def authenticate(self):
        #Authentication Message
        auth_message = {"action": "auth", "key": self.api_key, "secret": self.api_secret}
        self.ws.send(json.dumps(auth_message))
    
    def subscribe(self):
        #Subscription Message to Stock
        subscribed_message = {"action": "subscribe", "bars": [self.symbol]}
        self.ws.send(json.dumps(subscribed_message))
    
    def close_connection(self):
        self.ws.close()

    def start_connection(self):
        self.ws.run_forever()
    

def cross_signal_calc(df):
    for i in range(1, len(df)):
        prev_sma_10 = df['sma_10'].iloc[i-1]
        prev_sma_50 = df['sma_50'].iloc[i-1]
        cur_sma_10 = df['sma_10'].iloc[i]
        cur_sma_50 = df['sma_50'].iloc[i]

        if (prev_sma_10 <= prev_sma_50) and (cur_sma_10 >= cur_sma_50):
            #If sma_10 crosses above sma_50, buy signal
            df.at[i, 'cross_signal'] = 1
        elif (prev_sma_10 >= prev_sma_50) and (cur_sma_10 <= cur_sma_50):
        #If sma_10 crosses below sma_50, sell signal
            df.at[i, 'cross_signal'] = -1
        else:
            #Neutral Signal
            df.at[i, 'cross_signal'] = 0
         
    return df['cross_signal']

def back_testing(df):
    cross_signal = df['cross_signal']

    trades = []
    percent_changes = []
    profits = []
    total_profit = 0
    bought = False
    buy_price = 0

    for i in range(len(cross_signal)):

        if cross_signal[i] == 1:
            buy_price = df['open'].iloc[i]
            bought = True
            trades.append(buy_price)

        elif cross_signal[i] == -1 and bought:
            sell_price = df['open'].iloc[i] 
            value = sell_price - buy_price

            total_profit += value
            profits.append(value)

            trades.append(sell_price)

            percent_changes.append(((sell_price-buy_price)/buy_price)*100)
            bought = False
        
    average_percent = 0
    highest_percent = 0
    lowest_percent = 1000
    for percent in percent_changes:
        average_percent += percent
        if highest_percent < percent:
            highest_percent = percent
        if lowest_percent > percent:
            lowest_percent = percent
    
        
    average_percent /= len(percent_changes)
    
    return total_profit, trades, profits, percent_changes, average_percent, highest_percent, lowest_percent