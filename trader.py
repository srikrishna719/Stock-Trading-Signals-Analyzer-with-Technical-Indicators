import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go

def fetch_stock_data(symbol, start_date, end_date):
    return yf.download(symbol, start=start_date, end=end_date)

def signal_generator(df):
    open = df.Open.iloc[-1]
    close = df.Close.iloc[-1]
    previous_open = df.Open.iloc[-2]
    previous_close = df.Close.iloc[-2]
    
    if open > close and previous_open < previous_close and close < previous_open and open >= previous_close:
        return 1  # Selling signal
    elif open < close and previous_open > previous_close and close > previous_open and open <= previous_close:
        return 2  # Buying signal
    else:
        return 0  # No signal

def generate_candlestick_signals(data):
    signal = [0]
    for i in range(1, len(data)):
        df = data[i-1:i+1]
        signal.append(signal_generator(df))
    data["signal"] = signal
    return data

def generate_sma_signals(data, short_window=20, long_window=50):
    data['SMA_short'] = data['Close'].rolling(short_window).mean()
    data['SMA_long'] = data['Close'].rolling(long_window).mean()
    data['signal'] = np.where(data['SMA_short'] > data['SMA_long'], 1, 0)
    data['positions'] = data['signal'].diff()
    return data

def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    data['EMA_short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA_long'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['EMA_short'] - data['EMA_long']
    data['MACD_signal'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    data['MACD_diff'] = data['MACD'] - data['MACD_signal']
    return data

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data

def plot_signals(data, stock_symbol, strategy, short_window=20, long_window=50, rsi_window=14):
    if strategy == 'candlestick':
        buy_signals = data[data['signal'] == 2]
        sell_signals = data[data['signal'] == 1]
        trace = go.Scatter(x=data.index, y=data['Close'], mode='lines', name=f'{stock_symbol} Close Price')
        buy_scatter = go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers', name='Buy', marker=dict(color='green', size=8))
        sell_scatter = go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers', name='Sell', marker=dict(color='red', size=8))
        layout = go.Layout(title=f'{stock_symbol} Trading Signals', xaxis=dict(title='Date'), yaxis=dict(title='Price'))
        fig = go.Figure(data=[trace, buy_scatter, sell_scatter], layout=layout)
        fig.show()
    
    elif strategy == 'sma':
        data = generate_sma_signals(data, short_window, long_window)
        buy_signals = data[data['positions'] == 1]
        sell_signals = data[data['positions'] == -1]
        trace = go.Scatter(x=data.index, y=data['Close'], mode='lines', name=f'{stock_symbol} Close Price')
        sma_short_trace = go.Scatter(x=data.index, y=data['SMA_short'], mode='lines', name='SMA Short', line=dict(dash='dash'))
        sma_long_trace = go.Scatter(x=data.index, y=data['SMA_long'], mode='lines', name='SMA Long', line=dict(dash='dash'))
        buy_scatter = go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers', name='Buy', marker=dict(color='green', size=8))
        sell_scatter = go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers', name='Sell', marker=dict(color='red', size=8))
        layout = go.Layout(title=f'{stock_symbol} Trading Signals with SMA', xaxis=dict(title='Date'), yaxis=dict(title='Price'))
        fig = go.Figure(data=[trace, sma_short_trace, sma_long_trace, buy_scatter, sell_scatter], layout=layout)
        fig.show()
    
    elif strategy == 'macd':
        data = generate_sma_signals(data, short_window, long_window)
        data = calculate_macd(data)
        buy_signals = data[data['positions'] == 1]
        sell_signals = data[data['positions'] == -1]
        trace = go.Scatter(x=data.index, y=data['Close'], mode='lines', name=f'{stock_symbol} Close Price')
        buy_scatter = go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers', name='Buy', marker=dict(color='green', size=8))
        sell_scatter = go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers', name='Sell', marker=dict(color='red', size=8))
        macd_trace = go.Scatter(x=data.index, y=data['MACD'], mode='lines', name='MACD')
        macd_signal_trace = go.Scatter(x=data.index, y=data['MACD_signal'], mode='lines', name='MACD Signal')
        macd_diff_trace = go.Bar(x=data.index, y=data['MACD_diff'], name='MACD Diff')
        layout = go.Layout(title=f'{stock_symbol} Trading Signals with MACD', xaxis=dict(title='Date'), yaxis=dict(title='Price'), yaxis2=dict(title='MACD', overlaying='y', side='right'))
        fig = go.Figure(data=[trace, buy_scatter, sell_scatter, macd_trace, macd_signal_trace, macd_diff_trace], layout=layout)
        fig.show()
    
    elif strategy == 'sma_rsi':
        data = generate_sma_signals(data, short_window, long_window)
        data = calculate_rsi(data, window=rsi_window)
        buy_signals = data[data['positions'] == 1]
        sell_signals = data[data['positions'] == -1]
        trace = go.Scatter(x=data.index, y=data['Close'], mode='lines', name=f'{stock_symbol} Close Price')
        sma_short_trace = go.Scatter(x=data.index, y=data['SMA_short'], mode='lines', name='SMA Short', line=dict(color='rgba(0, 100, 80, 0.4)', width=2, dash='dash'))
        sma_long_trace = go.Scatter(x=data.index, y=data['SMA_long'], mode='lines',name='SMA Long', line=dict(color='rgba(255, 182, 193, 0.4)', width=2, dash='dash'))
        buy_scatter = go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers', name='Buy', marker=dict(color='green', size=8))
        sell_scatter = go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers', name='Sell', marker=dict(color='red', size=8))
        rsi_trace = go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI', line=dict(color='rgba(148, 0, 211, 0.4)', width=2))
        layout = go.Layout(title=f'{stock_symbol} Trading Signals with SMA and RSI', xaxis=dict(title='Date'), yaxis=dict(title='Price'), yaxis2=dict(title='RSI', overlaying='y', side='right', range=[0, 100]))
        fig = go.Figure(data=[trace, sma_short_trace, sma_long_trace, buy_scatter, sell_scatter, rsi_trace], layout=layout)
        fig.show()

def analyze_stock(stock_symbol, strategy, short_window=20, long_window=50, rsi_window=14):
    end_date = pd.Timestamp.today()
    start_date = end_date - pd.Timedelta(days=3*365)

    stock_data = fetch_stock_data(stock_symbol, start_date, end_date)
    
    if strategy == 'candlestick':
        stock_data = generate_candlestick_signals(stock_data)
    
    plot_signals(stock_data, stock_symbol, strategy, short_window, long_window, rsi_window)

def main():
    stock_symbol = input("Enter the stock symbol (e.g., AAPL): ")
    strategy = input("Select the strategy (candlestick, sma, macd, sma_rsi): ")
    
    short_window = 20
    long_window = 50
    rsi_window = 14
    
    if strategy == "sma":
        short_window = int(input("Enter the short window period: "))
        long_window = int(input("Enter the long window period: "))
    elif strategy == "macd":
        short_window = int(input("Enter the short window period for MACD: "))
        long_window = int(input("Enter the long window period for MACD: "))
        signal_window = int(input("Enter the signal window period for MACD: "))
    elif strategy == "sma_rsi":
        short_window = int(input("Enter the short window period for SMA: "))
        long_window = int(input("Enter the long window period for SMA: "))
        rsi_window = int(input("Enter the window period for RSI: "))
    
    analyze_stock(stock_symbol, strategy, short_window, long_window, rsi_window)

if __name__ == "__main__":
    main()
