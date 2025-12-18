import yfinance as yf
import pandas as pd
import streamlit as st

# Expanded list of BIST 100 symbols (approximate)
# In a real scenario, we might scrape this or use an API that returns the current constituents.
BIST_100_SYMBOLS = [
    "AEFES.IS", "AGHOL.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKFGY.IS", "AKSA.IS", "AKSEN.IS",
    "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "AYDEM.IS",
    "BAGFS.IS", "BERA.IS", "BIMAS.IS", "BIOEN.IS", "BRSAN.IS", "BRYAT.IS", "BUCIM.IS", "CANTE.IS",
    "CCOLA.IS", "CEMTS.IS", "CIMSA.IS", "CWENE.IS", "DOAS.IS", "DOHOL.IS", "ECILC.IS", "ECZYT.IS",
    "EGEEN.IS", "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "EUPWR.IS", "EUREN.IS",
    "FROTO.IS", "GARAN.IS", "GENIL.IS", "GESAN.IS", "GLYHO.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS",
    "HALKB.IS", "HEKTS.IS", "IMASM.IS", "IPEKE.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGYO.IS",
    "ISMEN.IS", "IZMDC.IS", "KARSN.IS", "KCAER.IS", "KCHOL.IS", "KMPUR.IS", "KONTR.IS", "KORDS.IS",
    "KOZAA.IS", "KOZAL.IS", "KRDMD.IS", "KZBGY.IS", "MAVI.IS", "MGROS.IS", "MIATK.IS", "ODAS.IS",
    "OTKAR.IS", "OYAKC.IS", "PENTA.IS", "PETKM.IS", "PGSUS.IS", "PSGYO.IS", "QUAGR.IS", "SAHOL.IS",
    "SASA.IS", "SELEC.IS", "SISE.IS", "SKBNK.IS", "SMRTG.IS", "SNGYO.IS", "SOKM.IS", "TAVHL.IS",
    "TCELL.IS", "THYAO.IS", "TKFEN.IS", "TOASO.IS", "TSKB.IS", "TTKOM.IS", "TTRAK.IS", "TUKAS.IS",
    "TUPRS.IS", "TURSG.IS", "ULKER.IS", "VAKBN.IS", "VESBE.IS", "VESTL.IS", "YKBNK.IS", "YYLGD.IS", "ZOREN.IS"
]

@st.cache_data(ttl=3600)
def get_stock_data(symbol, period="2y", interval="1d"):
    """
    Fetches historical data for a given symbol. Defaulted to Daily (1d).
    """
    try:
        # We strictly use interval from call, which is now locked to '1d' in main.py
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        # yfinance sometimes returns MultiIndex columns, we flat them if necessary
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Ensure index is datetime
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def get_all_bist_100_data(symbols=BIST_100_SYMBOLS, period="1y", interval="1d"):
    """
    Fetches data for multiple symbols. 
    NOTE: Detailed strategy checking usually needs loop, but we can bulk fetch to save time if needed.
    However, for this strategy step-by-step is often cleaner for debugging.
    """
    data_map = {}
    for sym in symbols:
        df = get_stock_data(sym, period=period, interval=interval)
        if df is not None and not df.empty:
            data_map[sym] = df
    return data_map
