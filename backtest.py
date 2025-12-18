import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
# from utils.data_fetcher import get_stock_data # Removing Streamlit dependency
from utils.strategy import check_strategy
import sys

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_stock_data_local(symbol, period="2y", interval="1d"):
    """
    Fetches historical data using yfinance directly, bypassing Streamlit cache.
    """
    try:
        # Auto_adjust=True fixes the OHLC vs Adj Close confusion
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            return None
        
        # Flatten MultiIndex if present
        if isinstance(df.columns, pd.MultiIndex):
            # Dropping level 1 (Ticker) to get standard OHLC columns
            df.columns = df.columns.get_level_values(0)
            
        # Ensure index is datetime
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"[!] Veri hatasi {symbol}: {e}")
        return None

class BacktestEngine:
    def __init__(self, symbol, period="2y", initial_capital=100000):
        self.symbol = symbol
        self.period = period
        self.initial_capital = initial_capital
        self.trades = []
        self.equity_curve = []
        
    def run(self):
        """Run backtest on historical data (Strictly Daily)"""
        print(f"\n{'='*60}")
        print(f"Backtest GÜNLÜK: {self.symbol}")
        print(f"{'='*60}")
        
        # Fetch data using local function
        df = get_stock_data_local(self.symbol, period=self.period)
        if df is None or len(df) < 100:
            print(f"[!] Yetersiz veri: {self.symbol}")
            return None
            
        # Initialize
        position = None  # {'entry_price', 'entry_date', 'stop_loss', 'shares'}
        capital = self.initial_capital
        
        # Walk through history
        for i in range(60, len(df)):  # Start after 60 bars for EMA calculation
            current_data = df.iloc[:i+1].copy()
            current_row = current_data.iloc[-1]
            current_date = current_data.index[-1]
            current_price = current_row['Close']
            
            # Check strategy signal
            signal = check_strategy(current_data, pullback_tolerance=0.015)
            
            # Entry logic
            if position is None and signal['signal']:
                # Calculate position size
                shares = int(capital * 0.95 / current_price)  # Use 95% of capital
                if shares > 0:
                    position = {
                        'entry_price': current_price,
                        'entry_date': current_date,
                        'stop_loss': signal['stop_loss'],
                        'shares': shares
                    }
                    print(f"[ALIŞ] {current_date.date()} - Fiyat: {current_price:.2f} TL - Adet: {shares} ({signal['details']})")
            
            # Exit logic (if in position)
            elif position is not None:
                exit_signal = False
                exit_reason = ""
                exit_price = current_price
                
                # Stop loss hit
                if current_price <= position['stop_loss']:
                    exit_signal = True
                    exit_reason = "Stop Loss"
                    exit_price = position['stop_loss']
                
                # Take profit (20% gain)
                elif current_price >= position['entry_price'] * 1.20:
                    exit_signal = True
                    exit_reason = "Take Profit (20%)"
                
                # Trailing stop: Update stop loss as price moves up
                else:
                    # Recalculate EMA for trailing stop
                    new_signal = check_strategy(current_data, pullback_tolerance=0.015)
                    if 'stop_loss' in new_signal and new_signal['stop_loss'] > position['stop_loss']:
                        position['stop_loss'] = new_signal['stop_loss']
                
                if exit_signal:
                    # Execute exit
                    pnl = (exit_price - position['entry_price']) * position['shares']
                    pnl_pct = ((exit_price / position['entry_price']) - 1) * 100
                    capital += pnl
                    
                    trade = {
                        'entry_date': position['entry_date'],
                        'entry_price': position['entry_price'],
                        'exit_date': current_date,
                        'exit_price': exit_price,
                        'shares': position['shares'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'reason': exit_reason,
                        'days_held': (current_date - position['entry_date']).days
                    }
                    self.trades.append(trade)
                    
                    emoji = "[+]" if pnl > 0 else "[-]"
                    print(f"{emoji} SATIŞ: {current_date.date()} - Fiyat: {exit_price:.2f} TL - "
                          f"K/Z: {pnl:+.2f} TL ({pnl_pct:+.1f}%) - Sebep: {exit_reason}")
                    
                    position = None
            
            # Track equity
            if position:
                current_value = capital + (current_price * position['shares'])
            else:
                current_value = capital
            
            self.equity_curve.append({
                'date': current_date,
                'equity': current_value,
                'price': current_price
            })
        
        # Close any open position at the end
        if position is not None:
            final_price = df.iloc[-1]['Close']
            pnl = (final_price - position['entry_price']) * position['shares']
            pnl_pct = ((final_price / position['entry_price']) - 1) * 100
            capital += pnl
            
            self.trades.append({
                'entry_date': position['entry_date'],
                'entry_price': position['entry_price'],
                'exit_date': df.index[-1],
                'exit_price': final_price,
                'shares': position['shares'],
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': 'End of Backtest',
                'days_held': (df.index[-1] - position['entry_date']).days
            })
            print(f"[i] Pozisyon kapandı (backtest sonu): K/Z: {pnl:+.2f} TL ({pnl_pct:+.1f}%)")
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        if not self.trades:
            return None
        
        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)
        
        # Basic metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = trades_df['pnl'].sum()
        total_return_pct = ((self.initial_capital + total_pnl) / self.initial_capital - 1) * 100
        
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        # Max drawdown
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # Average holding period
        avg_hold_days = trades_df['days_held'].mean()
        
        metrics = {
            'symbol': self.symbol,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'avg_hold_days': avg_hold_days,
            'final_capital': self.initial_capital + total_pnl,
            'trades_df': trades_df,
            'equity_df': equity_df
        }
        
        return metrics
    
    def print_report(self, metrics):
        """Print backtest report"""
        if metrics is None:
            print("[!] Sonuç yok")
            return
        
        print(f"\n{'='*60}")
        print(f"BACKTEST SONUÇLARI: {metrics['symbol']}")
        print(f"{'='*60}")
        print(f"Toplam İşlem Sayısı     : {metrics['total_trades']}")
        print(f"Kazanan İşlem           : {metrics['winning_trades']}")
        print(f"Kaybeden İşlem          : {metrics['losing_trades']}")
        print(f"Kazanma Oranı           : {metrics['win_rate']:.1f}%")
        print(f"Toplam Kazanç/Kayıp     : {metrics['total_pnl']:+,.2f} TL")
        print(f"Getiri Oranı            : {metrics['total_return_pct']:+.2f}%")
        print(f"Ortalama Kazanç         : {metrics['avg_win']:,.2f} TL")
        print(f"Ortalama Kayıp          : {metrics['avg_loss']:,.2f} TL")
        print(f"Maksimum Düşüş          : {metrics['max_drawdown']:.2f}%")
        print(f"Ortalama Tutma Süresi   : {metrics['avg_hold_days']:.0f} gün")
        print(f"Başlangıç Sermayesi     : {self.initial_capital:,.2f} TL")
        print(f"Bitiş Sermayesi         : {metrics['final_capital']:,.2f} TL")
        print(f"{'='*60}\n")
    
    def plot_results(self, metrics):
        """Create visualization of backtest results"""
        if metrics is None:
            return None
        
        trades_df = metrics['trades_df']
        equity_df = metrics['equity_df']
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Sermaye Eğrisi', 'Hisse Fiyatı & İşlemler'),
            vertical_spacing=0.12,
            row_heights=[0.4, 0.6]
        )
        
        # Equity curve
        fig.add_trace(
            go.Scatter(
                x=equity_df['date'], 
                y=equity_df['equity'],
                mode='lines',
                name='Sermaye',
                line=dict(color='#2E86DE', width=2)
            ),
            row=1, col=1
        )
        
        # Price chart
        fig.add_trace(
            go.Scatter(
                x=equity_df['date'],
                y=equity_df['price'],
                mode='lines',
                name='Fiyat',
                line=dict(color='gray', width=1)
            ),
            row=2, col=1
        )
        
        # Entry/Exit markers
        entries = trades_df[['entry_date', 'entry_price']].values
        exits = trades_df[['exit_date', 'exit_price']].values
        
        fig.add_trace(
            go.Scatter(
                x=entries[:, 0],
                y=entries[:, 1],
                mode='markers',
                name='Alış',
                marker=dict(color='green', size=10, symbol='triangle-up')
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=exits[:, 0],
                y=exits[:, 1],
                mode='markers',
                name='Satış',
                marker=dict(color='red', size=10, symbol='triangle-down')
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title=f"{self.symbol} - Backtest Analizi",
            height=800,
            showlegend=True,
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Tarih", row=2, col=1)
        fig.update_yaxes(title_text="Sermaye (TL)", row=1, col=1)
        fig.update_yaxes(title_text="Fiyat (TL)", row=2, col=1)
        
        return fig


if __name__ == "__main__":
    # Test symbols
    test_symbols = ["THYAO.IS", "AKBNK.IS", "EREGL.IS", "SASA.IS", "TUPRS.IS"]
    
    print(f"\n{'#'*60}")
    print(f"BIST 100 - 21/55 EMA PULLBACK STRATEJİSİ BACKTEST")
    print(f"{'#'*60}")
    
    all_results = []
    
    for symbol in test_symbols:
        bt = BacktestEngine(symbol, period="2y", interval="1d", initial_capital=100000)
        metrics = bt.run()
        
        if metrics:
            bt.print_report(metrics)
            all_results.append(metrics)
            
            # Save chart
            fig = bt.plot_results(metrics)
            if fig:
                fig.write_html(f"backtest_{symbol.replace('.IS', '')}.html")
                print(f"[OK] Grafik kaydedildi: backtest_{symbol.replace('.IS', '')}.html\n")
    
    # Summary
    if all_results:
        print(f"\n{'='*60}")
        print(f"ÖZET - TÜM HİSSELER")
        print(f"{'='*60}")
        
        summary_df = pd.DataFrame([{
            'Hisse': m['symbol'],
            'İşlem': m['total_trades'],
            'Kazanma %': f"{m['win_rate']:.1f}%",
            'Getiri %': f"{m['total_return_pct']:+.1f}%",
            'K/Z (TL)': f"{m['total_pnl']:+,.0f}",
            'Max Düşüş': f"{m['max_drawdown']:.1f}%"
        } for m in all_results])
        
        print(summary_df.to_string(index=False))
        print(f"{'='*60}\n")
