import pandas as pd
import numpy as np
from utils.strategy import check_strategy

def create_mock_data(trend="up", pullback=True, ha_turn=True):
    # Create 100 days of data
    dates = pd.date_range(start="2023-01-01", periods=100)
    
    # Base price movement
    if trend == "up":
        # Flat then up to ensure EMAs are right, but let's make it simple
        # 100 to 110 (slow up) to keep EMA21 > EMA55 but weak momentum
        prices = np.linspace(100, 110, 100)
    else:
        prices = np.linspace(150, 100, 100) # Downtrend
        
    # Inject volatility
    noise = np.random.normal(0, 1, 100)
    prices += noise
    
    # Create DataFrame
    df = pd.DataFrame(index=dates)
    df['Open'] = prices 
    df['High'] = prices + 1
    df['Low'] = prices - 1
    df['Close'] = prices + 0.5
    
    # Manipulate specific days for the setup
    if trend == "up":
        # Force 21 > 55 by end
        # (Linear linspace 100->150 usually does this after some time)
        pass
        
    if pullback:
        # Create a dip near the end (e.g., indexes -5 to -2)
        # We need to calculate roughly where EMA 21 is. 
        # Approx price is 148. EMA might be 147.
        # We want Low to dip to EMA.
        for i in range(-5, -1):
            # Make it a strong red candle series
            df.iloc[i, df.columns.get_loc('Open')] = 148 # High open
            df.iloc[i, df.columns.get_loc('Close')] = 140 # Low close (Deep Red)
            df.iloc[i, df.columns.get_loc('Low')] = 138 # Very low
            df.iloc[i, df.columns.get_loc('High')] = 149
            
    if ha_turn:
        # Latest Candle: Massive Green
        # Force standard signals to be huge
        df.iloc[-1, df.columns.get_loc('Open')] = 140
        df.iloc[-1, df.columns.get_loc('Close')] = 160 
        df.iloc[-1, df.columns.get_loc('High')] = 165
        df.iloc[-1, df.columns.get_loc('Low')] = 140
        
        # Previous Candle: Red (already set in pulback loop if active)
        # ensure it stays red
        df.iloc[-2, df.columns.get_loc('Close')] = df.iloc[-2]['Open'] - 1 # Red
        
    return df

print("Test 1: Perfect Setup")
df = create_mock_data(trend="up", pullback=True, ha_turn=True)
res = check_strategy(df)
print(f"Result: {res['signal']} - {res['details']}")

print("\nTest 2: No Pullback")
df2 = create_mock_data(trend="up", pullback=False, ha_turn=True)
res2 = check_strategy(df2)
print(f"Result: {res2['signal']} - {res2['details']}")

print("\nTest 3: Downtrend")
df3 = create_mock_data(trend="down", pullback=True, ha_turn=True)
res3 = check_strategy(df3)
print(f"Result: {res3['signal']} - {res3['details']}")
