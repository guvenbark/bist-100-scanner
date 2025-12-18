import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from utils.strategy import check_rsi_strategy_v2
import sys
import os

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_stock_data_local(symbol, period="2y"):
    """
    Fetches historical data using yfinance directly. Strictly Daily (1d).
    """
    try:
        df = yf.download(symbol, period=period, interval="1d", progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"[!] Error {symbol}: {e}")
        return None

class BacktestEngineV2:
    def __init__(self, symbol, period="2y", interval="1d", initial_capital=100000):
        self.symbol = symbol
        self.period = period
        self.interval = interval
        self.initial_capital = initial_capital
        self.trades = []
        self.equity_curve = []
        
    def run(self):
        print(f"\n{'='*60}\nRSI V2 Backtest (GÜNLÜK): {self.symbol}\n{'='*60}")
        df = get_stock_data_local(self.symbol, period=self.period)
        if df is None or len(df) < 60: return None
            
        position = None
        capital = self.initial_capital
        
        for i in range(55, len(df)):
            current_data = df.iloc[:i+1].copy()
            current_row = current_data.iloc[-1]
            current_date = current_data.index[-1]
            current_price = current_row['Close']
            
            signal = check_rsi_strategy_v2(current_data)
            
            if position is None and signal['signal']:
                shares = int(capital * 0.95 / current_price)
                if shares > 0:
                    position = {
                        'entry_price': current_price,
                        'entry_date': current_date,
                        'sl': signal['stop_loss'],
                        'tp': signal['take_profit'],
                        'shares': shares,
                        'highest_price': current_price
                    }
                    print(f"[ALIŞ] {current_date.date()} - Fiyat: {current_price:.2f} TL")
            
            elif position is not None:
                # Update highest price for trailing stop logic if wanted, 
                # but let's stick to TP/SL for V2 comparison
                position['highest_price'] = max(position['highest_price'], current_price)
                
                exit_signal = False
                exit_reason = ""
                exit_price = current_price
                
                if current_price <= position['sl']:
                    exit_signal, exit_reason, exit_price = True, "Stop Loss", position['sl']
                elif current_price >= position['tp']:
                    exit_signal, exit_reason, exit_price = True, "Take Profit", position['tp']
                elif current_data['RSI'].iloc[-1] < 48: # Stricter exit than 45
                    exit_signal, exit_reason = True, "RSI Trend End"
                
                if exit_signal:
                    pnl = (exit_price - position['entry_price']) * position['shares']
                    capital += pnl
                    self.trades.append({'pnl': pnl, 'pnl_pct': (exit_price/position['entry_price']-1)*100, 'symbol': self.symbol})
                    print(f"[-] SATIŞ: {current_date.date()} - K/Z: {(exit_price/position['entry_price']-1)*100:+.1f}% ({exit_reason})")
                    position = None
            
            val = capital + (current_price * position['shares']) if position else capital
            self.equity_curve.append({'date': current_date, 'equity': val})
        
        return self.summary(capital)

    def summary(self, final_capital):
        if not self.trades: return None
        df = pd.DataFrame(self.trades)
        return {
            'symbol': self.symbol,
            'trades': len(df),
            'win_rate': (len(df[df['pnl'] > 0]) / len(df) * 100),
            'return_pct': ((final_capital / self.initial_capital) - 1) * 100
        }

if __name__ == "__main__":
    symbols = [
        "THYAO.IS", "AKBNK.IS", "EREGL.IS", "TUPRS.IS", "BIMAS.IS",
        "ASELS.IS", "KCHOL.IS", "SISE.IS", "SAHOL.IS", "GARAN.IS"
    ]
    results = []
    for s in symbols:
        m = BacktestEngineV2(s).run()
        if m: results.append(m)
    
    if results:
        print(f"\n{'='*60}\nÖZET SONUÇLAR (V2)\n{'='*60}")
        print(pd.DataFrame(results).to_string(index=False))
