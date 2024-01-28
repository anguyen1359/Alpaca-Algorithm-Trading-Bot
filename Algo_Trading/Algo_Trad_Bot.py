from Alpaca_Websocket_AlgoBot import AlpacaWebSocket
import alpaca_trade_api as tradeapi
import threading
import time

api_key = 'Key'
api_secret = 'Secret'
symbol = 'SPY'

alpaca_ws = AlpacaWebSocket(symbol=symbol, api_key=api_key, api_secret=api_secret)
API = tradeapi.REST(api_key, api_secret, base_url='https://paper-api.alpaca.markets')

recorded_last_row = None

def trade_loop(exit_event):
    global recorded_last_row

    try:
        while not exit_event.is_set():
            print("Checking Conditions")
            current_last_row = alpaca_ws.bars_data_period.iloc[-1]

            #Checking if it is new data
            if recorded_last_row is None or not recorded_last_row.equals(current_last_row):
                cross_signal = current_last_row['cross_signal']

                #Execute Buy Signal
                if cross_signal == 1:
                    API.submit_order(
                        symbol=symbol,
                        qty=5,
                        side='buy',
                        type='market',
                        time_in_force='gtc'
                    )
                    price = API.get_latest_trade(symbol=symbol).price
                    print(f"Executed Buy Order of {1} {symbol} stock at ${price}")
        
                #Execute Sell Signal
                elif cross_signal == -1:
                    #Checking if we stocks to sell
                    current_quantity = float(API.get_position(symbol=symbol).qty)
            
                    if current_quantity > 0.0:
                        API.submit_order(
                            symbol=symbol,
                            qty=5,
                            side='sell',
                            type='market',
                            time_in_force='gtc'
                        )
                        price = API.get_latest_trade(symbol=symbol).price
                        print(f"Executed Sell Order of {1} {symbol} stock at ${price}")
                    else:
                        print(f"No stocks to sell for {symbol}")
    
                #Update last recorded row
                recorded_last_row = current_last_row.copy()

            print("Completed Checking Conditions")
            time.sleep(10*60)
    except KeyboardInterrupt:
        print("Executed Trading Bot")
        exit_event.set()
        

#Start Trade Bot
try:
    exit_event = threading.Event()
    trade_thread = threading.Thread(target=trade_loop, args=(exit_event,))
    trade_thread.start()
    alpaca_ws.start_connection()
except KeyboardInterrupt:
    exit_event.set()
    trade_thread.join()
    print("Trading Bot Terminated")