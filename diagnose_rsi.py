import pandas as pd
import numpy as np
import yfinance as yf
from utils.strategy import check_rsi_strategy
import sys

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_stock_data_local(symbol, period="2y", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"[!] Error {symbol}: {e}")
        return None

def diagnose_strategy(symbol):
    print(f"\n--- DIAGNOSING {symbol} ---")
    df = get_stock_data_local(symbol)
    if df is None: return

    # Calculate Indicators
    rsi_period = 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate EMA 200 for Trend filter
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    trades = []
    position = None
    
    for i in range(200, len(df)): # Start after 200 for EMA
        current_data = df.iloc[:i+1].copy()
        current_row = current_data.iloc[-1]
        current_date = current_data.index[-1]
        current_price = current_row['Close']
        current_rsi = current_row['RSI']
        is_above_ema200 = current_price > current_row['EMA200']
        
        signal = check_rsi_strategy(current_data)
        
        if position is None and signal['signal']:
            position = {
                'entry_price': current_price,
                'entry_date': current_date,
                'sl': signal['stop_loss'],
                'tp': signal['take_profit'],
                'entry_rsi': current_rsi,
                'was_above_ema200': is_above_ema200
            }
        elif position is not None:
            exit_reason = ""
            exit_price = current_price
            
            if current_price <= position['sl']:
                exit_reason = "STOP_LOSS"
                exit_price = position['sl']
            elif current_price >= position['tp']:
                exit_reason = "TAKE_PROFIT"
                exit_price = position['tp']
            elif current_row['RSI'] < 45:
                exit_reason = "RSI_EXIT"
            
            if exit_reason:
                pnl_pct = ((exit_price / position['entry_price']) - 1) * 100
                trades.append({
                    'entry_date': position['entry_date'],
                    'exit_date': current_date,
                    'pnl_pct': pnl_pct,
                    'reason': exit_reason,
                    'entry_rsi': position['entry_rsi'],
                    'was_above_ema200': position['was_above_ema200']
                })
                position = None

    if not trades:
        print("No trades found.")
        return

    trades_df = pd.DataFrame(trades)
    print("\nTrade Summary Statistics:")
    print(trades_df.groupby('reason')['pnl_pct'].agg(['count', 'mean', 'sum']))
    
    print("\nPerformance relative to EMA 200 Trend Filter:")
    print(trades_df.groupby('was_above_ema200')['pnl_pct'].agg(['count', 'mean', 'sum']))

if __name__ == "__main__":
    diagnose_strategy("THYAO.IS")
    diagnose_strategy("BIMAS.IS")
