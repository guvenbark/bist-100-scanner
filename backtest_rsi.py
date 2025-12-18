import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from utils.strategy import check_rsi_strategy
import sys
import os

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_stock_data_local(symbol, period="2y", interval="1d"):
    """
    Fetches historical data using yfinance directly.
    """
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"[!] Veri hatası {symbol}: {e}")
        return None

class BacktestEngineRSI:
    def __init__(self, symbol, period="2y", interval="1d", initial_capital=100000):
        self.symbol = symbol
        self.period = period
        self.interval = interval
        self.initial_capital = initial_capital
        self.trades = []
        self.equity_curve = []
        
    def run(self):
        print(f"\n{'='*60}")
        print(f"RSI Backtest: {self.symbol}")
        print(f"{'='*60}")
        
        df = get_stock_data_local(self.symbol, period=self.period, interval=self.interval)
        if df is None or len(df) < 50:
            print(f"[!] Yetersiz veri: {self.symbol}")
            return None
            
        position = None
        capital = self.initial_capital
        
        for i in range(20, len(df)):
            current_data = df.iloc[:i+1].copy()
            current_row = current_data.iloc[-1]
            current_date = current_data.index[-1]
            current_price = current_row['Close']
            
            # Check strategy signal
            signal = check_rsi_strategy(current_data)
            
            # Entry logic
            if position is None and signal['signal']:
                shares = int(capital * 0.95 / current_price)
                if shares > 0:
                    position = {
                        'entry_price': current_price,
                        'entry_date': current_date,
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit'],
                        'shares': shares
                    }
                    print(f"[ALIŞ] {current_date.date()} - Fiyat: {current_price:.2f} TL - RSI: {current_data['RSI'].iloc[-1]:.2f}")
            
            # Exit logic
            elif position is not None:
                exit_signal = False
                exit_reason = ""
                exit_price = current_price
                
                # Stop loss hit
                if current_price <= position['stop_loss']:
                    exit_signal = True
                    exit_reason = "Stop Loss"
                    exit_price = position['stop_loss']
                
                # Take profit hit
                elif current_price >= position['take_profit']:
                    exit_signal = True
                    exit_reason = "Take Profit"
                    exit_price = position['take_profit']
                
                # RSI Exit (Cross below 45 to exit trend)
                elif current_data['RSI'].iloc[-1] < 45:
                    exit_signal = True
                    exit_reason = "RSI Trend End"
                
                if exit_signal:
                    pnl = (exit_price - position['entry_price']) * position['shares']
                    pnl_pct = ((exit_price / position['entry_price']) - 1) * 100
                    capital += pnl
                    
                    self.trades.append({
                        'entry_date': position['entry_date'],
                        'entry_price': position['entry_price'],
                        'exit_date': current_date,
                        'exit_price': exit_price,
                        'shares': position['shares'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'reason': exit_reason,
                        'days_held': (current_date - position['entry_date']).days
                    })
                    
                    emoji = "[+]" if pnl > 0 else "[-]"
                    print(f"{emoji} SATIŞ: {current_date.date()} - Fiyat: {exit_price:.2f} TL - K/Z: {pnl_pct:+.1f}% - Sebep: {exit_reason}")
                    
                    position = None
            
            current_value = capital + (current_price * position['shares']) if position else capital
            self.equity_curve.append({
                'date': current_date,
                'equity': current_value,
                'price': current_price,
                'rsi': current_data['RSI'].iloc[-1] if 'RSI' in current_data.columns else 50
            })
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        if not self.trades:
            return None
        
        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)
        
        total_pnl = trades_df['pnl'].sum()
        win_rate = (len(trades_df[trades_df['pnl'] > 0]) / len(trades_df) * 100)
        
        metrics = {
            'symbol': self.symbol,
            'total_trades': len(trades_df),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return_pct': (total_pnl / self.initial_capital) * 100,
            'final_capital': self.initial_capital + total_pnl,
            'trades_df': trades_df,
            'equity_df': equity_df
        }
        return metrics

    def plot_results(self, metrics):
        if metrics is None: return None
        
        trades_df = metrics['trades_df']
        equity_df = metrics['equity_df']
        
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Sermaye Eğrisi', 'Hisse Fiyatı & İşlemler', 'RSI (14)'),
            vertical_spacing=0.1,
            row_heights=[0.3, 0.4, 0.3],
            shared_xaxes=True
        )
        
        # Equity
        fig.add_trace(go.Scatter(x=equity_df['date'], y=equity_df['equity'], name='Sermaye', line=dict(color='blue')), row=1, col=1)
        
        # Price
        fig.add_trace(go.Scatter(x=equity_df['date'], y=equity_df['price'], name='Fiyat', line=dict(color='gray')), row=2, col=1)
        
        # Entry/Exit
        fig.add_trace(go.Scatter(x=trades_df['entry_date'], y=trades_df['entry_price'], mode='markers', name='Alış', marker=dict(color='green', size=10, symbol='triangle-up')), row=2, col=1)
        fig.add_trace(go.Scatter(x=trades_df['exit_date'], y=trades_df['exit_price'], mode='markers', name='Satış', marker=dict(color='red', size=10, symbol='triangle-down')), row=2, col=1)
        
        # RSI
        fig.add_trace(go.Scatter(x=equity_df['date'], y=equity_df['rsi'], name='RSI', line=dict(color='purple')), row=3, col=1)
        fig.add_hline(y=50, line_dash="dash", line_color="red", row=3, col=1)
        
        fig.update_layout(height=900, title=f"{self.symbol} RSI > 50 Backtest", showlegend=True)
        return fig

if __name__ == "__main__":
    symbols = ["THYAO.IS", "AKBNK.IS", "EREGL.IS", "TUPRS.IS", "BIMAS.IS"]
    all_metrics = []
    
    for symbol in symbols:
        engine = BacktestEngineRSI(symbol)
        m = engine.run()
        if m:
            all_metrics.append(m)
            fig = engine.plot_results(m)
            fig.write_html(f"backtest_rsi_{symbol.replace('.IS', '')}.html")
    
    if all_metrics:
        print(f"\n{'='*60}\nÖZET SONUÇLAR\n{'='*60}")
        summary = pd.DataFrame([{
            'Hisse': m['symbol'],
            'İşlem': m['total_trades'],
            'Başarı %': f"{m['win_rate']:.1f}%",
            'Getiri %': f"{m['total_return_pct']:+.1f}%"
        } for m in all_metrics])
        print(summary.to_string(index=False))
