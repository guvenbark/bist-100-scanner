import pandas as pd

def calculate_ema(df, length=21):
    """
    Calculates Exponential Moving Average (EMA) using pure Pandas.
    """
    return df['Close'].ewm(span=length, adjust=False).mean()

def calculate_heikin_ashi(df):
    """
    Calculates Heikin Ashi candles using pure Pandas.
    Returns a DataFrame with HA_Open, HA_High, HA_Low, HA_Close.
    """
    ha = pd.DataFrame(index=df.index)
    
    # HA Close: (Open + High + Low + Close) / 4
    ha['HA_close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    
    # HA Open: (Prev HA Open + Prev HA Close) / 2
    # This requires iterating or a cumulative calculation.
    # We initialize the first HA Open as the first candle's Open (or (O+C)/2).
    
    ha_open_list = []
    # Initialize first candle
    # Standard convention: HA_Open[0] = (Open[0] + Close[0]) / 2
    prev_ha_open = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
    prev_ha_close = ha['HA_close'].iloc[0] # Use the computed HA Close
    
    ha_open_list.append(prev_ha_open)
    
    # Iterate
    # Note: This loop can be slow for massive data, but for 2y daily data (approx 500 rows) it's instant.
    # For vectorization, we could use numba but we want to avoid deps.
    # Python loop is fine here.
    
    for i in range(1, len(df)):
        # HA_Open = (Prev HA Open + Prev HA Close) / 2
        # Use the *just computed* HA Close from previous step? 
        # Actually HA Open depends on PREVIOUS HA values.
        # Yes: HA_Open[i] = (HA_Open[i-1] + HA_Close[i-1]) / 2
        
        # We need the previous HA Close from our DataFrame (which is fully computed above? Yes, HA_Close depends only on current O/H/L/C)
        prev_ha_close_val = ha['HA_close'].iloc[i-1]
        
        curr_ha_open = (prev_ha_open + prev_ha_close_val) / 2
        ha_open_list.append(curr_ha_open)
        
        # Update state for next
        prev_ha_open = curr_ha_open
        
    ha['HA_open'] = ha_open_list
    
    # HA High: Max(High, HA_Open, HA_Close)
    ha['HA_high'] = df[['High']].join(ha[['HA_open', 'HA_close']]).max(axis=1)
    
    # HA Low: Min(Low, HA_Open, HA_Close)
    ha['HA_low'] = df[['Low']].join(ha[['HA_open', 'HA_close']]).min(axis=1)
    
    return ha

def calculate_atr(df, length=14):
    """
    Calculates Average True Range (ATR).
    """
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    
    return true_range.rolling(window=length).mean()

def calculate_adx(df, length=14):
    """
    Calculates Average Directional Index (ADX).
    """
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff().apply(lambda x: -x)
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    # Simple logic for DM
    plus_dm.mask(plus_dm < minus_dm, 0, inplace=True)
    minus_dm.mask(minus_dm < plus_dm, 0, inplace=True)
    
    tr = calculate_atr(df, length=1) # TR is ATR(1)
    
    tr_smooth = tr.rolling(length).sum()
    plus_di = 100 * (plus_dm.rolling(length).sum() / tr_smooth)
    minus_di = 100 * (minus_dm.rolling(length).sum() / tr_smooth)
    
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.rolling(length).mean()
    
    return adx
