import pandas as pd
import numpy as np
from utils.indicators import calculate_ema, calculate_heikin_ashi, calculate_adx, calculate_atr

def check_strategy(df, pullback_tolerance=0.015):
    """
    Checks the strategy conditions for a given stock DataFrame.
    
    Strategy:
    1. 21 EMA > 55 EMA (Trend)
    2. Price pulled back to 21 EMA (Low <= 21 EMA * (1 + tolerance) and Low >= 21 EMA * (1 - tolerance)) 
       OR simply Low <= 21 EMA * (1 + tolerance) if we just want "near or below" but strictly above 55? 
       Let's stick to "Pullback to 21 EMA": Low touches or gets very close.
       User said: "wait for pullback to 21 EMA".
    3. Heikin Ashi signal: Green candle.
    
    Returns:
        dict: {
            'signal': bool, 
            'details': str (reason/status),
            'last_price': float,
            'stop_loss': float,
            'take_profit': float
        }
    """
    # Ensure sufficient data
    if df is None or len(df) < 55:
        return {'signal': False, 'details': 'Insufficient data'}
    
    # Calculate Indicators
    df['EMA_21'] = calculate_ema(df, length=21)
    df['EMA_55'] = calculate_ema(df, length=55)
    
    ha = calculate_heikin_ashi(df)
    df = pd.concat([df, ha], axis=1)
    
    # Get latest data point (assuming we run this on "closed" candles or live)
    # Using row -1 is current/latest candle.
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 1. Trend Condition: 21 EMA > 55 EMA
    # We check if the trend is largely established or just crossed. 
    # User said: "Wait for 21 EMA to cross 55 EMA upwards".
    if not (curr['EMA_21'] > curr['EMA_55']):
        return {'signal': False, 'details': 'No Uptrend (21 EMA <= 55 EMA)'}
    
    # Check if they are "wide" enough? (Optional, but user didn't specify). 
    
    # 2. Pullback Condition
    # "Wait for price to pullback to 21 EMA"
    # This implies we look at RECENT history to see if it touched/neared 21 EMA, 
    # OR if the *current* setup is the bounce from that pullback.
    
    # Let's assess if the *Low* of the current or recent candles touched the 21 EMA zone.
    # We define "Pullback Zone" as being within X% of EMA 21.
    # And specifically, we want the current action to be a "bounce" (HA Green).
    
    ema21 = curr['EMA_21']
    low_price = curr['Low']
    
    # Is current or very recent candle "interacting" with 21 EMA?
    # Strict interpretation: The entry signal is when HA turns green AFTER a pullback.
    # So we look back a small window (e.g., last 3-5 candles) to see if ANY Low touched the EMA 21 zone.
    
    intersects_ema = False
    window = 5 # Looback
    for i in range(1, window + 1):
        if len(df) < i + 1: break
        past_row = df.iloc[-1 * i]
        # Check if Low is close to EMA 21 (e.g. within +1.5% and maybe slightly below is OK if above 55)
        # We can say: Low <= EMA_21 * (1 + tolerance)
        past_ema21 = past_row['EMA_21']
        past_low = past_row['Low']
        
        # We want to ensure it's not a deep crash below 55.
        if past_low <= past_ema21 * (1 + pullback_tolerance):
            intersects_ema = True
            break
            
    if not intersects_ema:
        return {'signal': False, 'details': 'No recent pullback to 21 EMA'}

    # 3. Heikin Ashi Signal
    # "HA candle turns green"
    # Current HA Close > HA Open (Green)
    # AND Previous HA Close <= HA Open (Red) -> This is a "Turn"
    # OR just Current Green if we want to catch continuation immediately?
    # User said "turn to green", implying a switch.
    
    curr_ha_green = curr['HA_close'] > curr['HA_open']
    prev_ha_red = prev['HA_close'] <= prev['HA_open']
    
    # Note: Sometimes the pullback happens, and we get a green immediately. 
    # Let's enforce strictly "Turn Green" OR "Green after touching line".
    # Because if we wait for "Turn", we might miss it if it stays green but touches line? 
    # Usually pullback = red candles. So "Turn to Green" is the standard trigger.
    
    if curr_ha_green and prev_ha_red:
        # Valid Buy Signal
        stop_loss = ema21 # User: "21 EMA stoploss"
        take_profit = curr['Close'] * 1.05 # Placeholder, user said 21 EMA can be TP too? No, "21 EMA take profit olarakta ayarlayabilirsin" (You can set 21 EMA as TP too? No, that implies Trailing SL).
        # Actually user said: "21 ema take profit olarakta ayarlayabilirsin" -> likely means Trailing Stop until 21 EMA adds.
        # But for Signal, we just report Entry.
        
        # BREAKOUT DETECTION (Resistance)
        # Look back 20-50 days to find the highest high (resistance)
        # If current Close > Resistance, it's a breakout.
        lookback_period = 60 # Approx 3 months
        if len(df) > lookback_period:
            recent_data = df.iloc[-(lookback_period+1):-1] # Exclude current candle
            resistance_level = recent_data['High'].max()
            
            # Check for breakout (Current close > Resistance)
            # Allow small margin (e.g. 1%) or strict break
            is_breakout = curr['Close'] > resistance_level
            
            breakout_info = f" | 💥 Kırılım: {resistance_level:.2f} TL" if is_breakout else f" | Direnç: {resistance_level:.2f} TL"
        else:
            breakout_info = ""

        return {
            'signal': True,
            'details': 'BUY Signal (Trend + Pullback + HA Green)' + breakout_info,
            'last_price': curr['Close'],
            'stop_loss': stop_loss
        }
    
    elif curr_ha_green and not prev_ha_red:
         return {'signal': False, 'details': 'HA is Green but no Turn (Continuation?)'}

def get_stock_data_local(symbol, period="2y"):
    """
    Fetches historical data using yfinance directly. Strictly Daily (1d).
    """
    try:
        df = yf.download(symbol, period=period, interval="1d", progress=False, auto_adjust=True)
        if df.empty:
            print(f"No data fetched for {symbol}")
            return None
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def check_rsi_strategy(df, rsi_period=14):
    """
    Checks for RSI > 50 crossover strategy.
    
    Signal: RSI crosses above 50 (Previous RSI <= 50, Current RSI > 50)
    """
    if df is None or len(df) < rsi_period + 1:
        return {'signal': False, 'details': 'Insufficient data'}

    # Calculate RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    
    # Avoid division by zero
    rs = gain / loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50) # Fallback

    curr_rsi = df['RSI'].iloc[-1]
    prev_rsi = df['RSI'].iloc[-2]

    # Signal: RSI crossing above 50

def check_rsi_strategy_v2(df, rsi_period=14):
    """
    Improved RSI Strategy (V2) - DESIGNED FOR DAILY (1D) TIMEFRAME:
    1. Trend: EMA 21 > EMA 55 (Uptrend confirmation)
    2. Momentum: RSI crosses above 55 (Strength confirmation)
    """
    if df is None or len(df) < 55:
        return {'signal': False, 'details': 'Insufficient data'}

    # Calculate Indicators
    df['EMA_21'] = calculate_ema(df, length=21)
    df['EMA_55'] = calculate_ema(df, length=55)
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # Conditions
    trend_ok = curr['EMA_21'] > curr['EMA_55']
    momentum_ok = curr['RSI'] > 55 and prev['RSI'] <= 55
    
    if trend_ok and momentum_ok:
        return {
            'signal': True,
            'details': f'V2 BUY (Trend + RSI>55: {curr["RSI"]:.2f})',
            'last_price': curr['Close'],
            'stop_loss': curr['Close'] * 0.93, # 7% Stop Loss (slightly wider)
            'take_profit': curr['Close'] * 1.15 # 15% Take Profit
        }
    

def check_rsi_strategy_v3(df, rsi_period=14):
    """
    V3 Strategy: Profit Optimization
    1. Trend Control: EMA 21 > EMA 55
    2. Trend Strength: ADX > 25 (Avoid consolidation)
    3. Momentum: RSI crosses above 55
    """
    if df is None or len(df) < 60:
        return {'signal': False, 'details': 'Insufficient data'}

    # Calculate Indicators
    df['EMA_21'] = calculate_ema(df, length=21)
    df['EMA_55'] = calculate_ema(df, length=55)
    df['ADX'] = calculate_adx(df, length=14)
    df['ATR'] = calculate_atr(df, length=14)
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # Conditions
    trend_ok = curr['EMA_21'] > curr['EMA_55']
    strength_ok = curr['ADX'] > 25
    momentum_ok = curr['RSI'] > 55 and prev['RSI'] <= 55
    
    if trend_ok and strength_ok and momentum_ok:
        # Dynamic Stop Loss based on ATR (2.5x ATR)
        stop_loss = curr['Close'] - (2.5 * curr['ATR'])
        
        return {
            'signal': True,
            'details': f'V3 BUY (Trend Robust | ADX: {curr["ADX"]:.1f})',
            'last_price': curr['Close'],
            'stop_loss': stop_loss,
            'atr': curr['ATR']
        }
    
    if not trend_ok: reason = "No Trend"
    elif not strength_ok: reason = f"Weak Trend (ADX: {curr['ADX']:.1f})"
    else: reason = f"RSI: {curr['RSI']:.2f}"
    
    return {'signal': False, 'details': reason}
