import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
from utils.data_fetcher import get_stock_data, BIST_100_SYMBOLS, get_all_bist_100_data
# from utils.strategy import check_strategy # We will import dynamically based on strategy or strictly use check_strategy for now

# Import strategies
# Import strategies
from utils.strategy import check_strategy as check_strategy_ema
from utils.strategy import check_rsi_strategy_v2, check_rsi_strategy_v3

st.set_page_config(page_title="BIST ALIM SATIM STRATEJI", layout="wide")

# Initialize session state
if 'auto_scan_enabled' not in st.session_state:
    st.session_state.auto_scan_enabled = False
if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None
if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = "21/55 EMA & HA"

# Common Sidebar
st.sidebar.title("🚀 BIST ALIM SATIM STRATEJİ")
st.sidebar.markdown("---")

# Strategy Selection
strategy_mode = st.sidebar.radio(
    "Strateji Seçimi",
    ["21/55 EMA & HA", "RSI > 50 (V1-V2)", "RSI V3 (Kar Optimizasyonu)"],
    index=2
)
st.session_state.selected_strategy = strategy_mode

# Common Data Settings
st.sidebar.header("⚙️ Genel Ayarlar")
period = st.sidebar.selectbox("Veri Periyodu", ["6mo", "1y", "2y", "5y"], index=1)
# Enforced Daily Timeframe
interval = "1d"
st.sidebar.info("📅 Zaman Dilimi: **Günlük (Daily)**")

# Strategy Specific UI
if strategy_mode == "21/55 EMA & HA":
    st.title("📈 21/55 EMA & Heikin Ashi Stratejisi")
    st.markdown("""
    Bu strateji aşağıdaki kuralları takip eder:
    1. **Trend**: 21 EMA > 55 EMA olmalı.
    2. **Geri Çekilme (Pullback)**: Fiyat 21 EMA'ya yaklaşmalı veya dokunmalı.
    3. **Sinyal**: Heikin Ashi mumu **YEŞİLE** dönmeli.
    4. **Ekstra**: Fiyat son 2 ayın zirvesini geçerse **"💥 Kırılım"** olarak işaretlenir.
    """)
    
    # Strategy Specific Settings
    tolerance = st.sidebar.slider("Pullback Toleransı", 0.005, 0.05, 0.015, 0.005, format="%.3f")
    
    # Auto Scan Controls (Ideally shared but can be strategy specific logic)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 Otomatik Tarama")
    auto_scan = st.sidebar.toggle("Otomatik Tarama Aktif", value=st.session_state.auto_scan_enabled)
    scan_interval_minutes = st.sidebar.selectbox(
        "Tarama Aralığı", 
        [5, 10, 15, 30, 60], 
        index=1,
        format_func=lambda x: f"{x} dakika" if x < 60 else f"{x//60} saat"
    )
    
    # Update session state for auto scan
    st.session_state.auto_scan_enabled = auto_scan
    
    manual_scan = st.sidebar.button("🔍 Manuel Tarama Yap")

    # Determine if we should run a scan
    should_scan = False
    if manual_scan:
        should_scan = True
    elif auto_scan:
        if st.session_state.last_scan_time is None:
            should_scan = True  # First scan
        else:
            time_since_last = datetime.now() - st.session_state.last_scan_time
            if time_since_last >= timedelta(minutes=scan_interval_minutes):
                should_scan = True
    
    # Execution Logic
    if should_scan:
        st.write(f"{len(BIST_100_SYMBOLS)} hisse taranıyor... Lütfen bekleyin.")
        progress_bar = st.progress(0)
        
        results = []
        
        for i, symbol in enumerate(BIST_100_SYMBOLS):
            # Fetch Data
            df = get_stock_data(symbol, period=period, interval=interval)
            
            # Check Strategy
            if df is not None:
                res = check_strategy_ema(df, pullback_tolerance=tolerance)
                if res['signal']:
                    results.append({
                        "Symbol": symbol,
                        "Price": res['last_price'],
                        "Stop Loss (21EMA)": res['stop_loss'],
                        "Details": res['details']
                    })
            
            # Update Progress
            progress_bar.progress((i + 1) / len(BIST_100_SYMBOLS))
            
        progress_bar.empty()
        
        # Save results and timestamp
        st.session_state.scan_results = results
        st.session_state.last_scan_time = datetime.now()
        
        if results:
            st.success(f"✅ {len(results)} hisse bulundu!")
            results_df = pd.DataFrame(results)
            st.dataframe(results_df, use_container_width=True)
            
            # Select stock to view
            selected = st.selectbox("📊 Grafik görmek için hisse seçin:", results_df['Symbol'])
            
            if selected:
                df_sel = get_stock_data(selected, period=period, interval=interval)
                
                # Re-calc indicators for plotting
                from utils.indicators import calculate_ema, calculate_heikin_ashi
                df_sel['EMA_21'] = calculate_ema(df_sel, length=21)
                df_sel['EMA_55'] = calculate_ema(df_sel, length=55)
                ha = calculate_heikin_ashi(df_sel)
                df_sel = pd.concat([df_sel, ha], axis=1)

                # Create Chart
                fig = go.Figure()
                
                # Candle Stick (Heikin Ashi)
                fig.add_trace(go.Candlestick(
                    x=df_sel.index,
                    open=df_sel['HA_open'], high=df_sel['HA_high'],
                    low=df_sel['HA_low'], close=df_sel['HA_close'],
                    name='Heikin Ashi'
                ))
                
                # EMAs
                fig.add_trace(go.Scatter(x=df_sel.index, y=df_sel['EMA_21'], line=dict(color='orange', width=2), name='EMA 21'))
                fig.add_trace(go.Scatter(x=df_sel.index, y=df_sel['EMA_55'], line=dict(color='blue', width=2), name='EMA 55'))
                
                fig.update_layout(title=f"{selected} Analizi", xaxis_rangeslider_visible=False, height=600)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Kriterlere uyan hisse bulunamadı.")
            
    else:
        # Show cached results if available
        if st.session_state.scan_results is not None:
            results = st.session_state.scan_results
            
            # Display last scan time
            if st.session_state.last_scan_time:
                time_ago = datetime.now() - st.session_state.last_scan_time
                minutes_ago = int(time_ago.total_seconds() / 60)
                st.info(f"ℹ️ Son tarama: {minutes_ago} dakika önce")
            
            if results:
                st.success(f"✅ {len(results)} hisse bulundu!")
                results_df = pd.DataFrame(results)
                st.dataframe(results_df, use_container_width=True)
                
                # Select stock to view
                selected = st.selectbox("📊 Grafik görmek için hisse seçin:", results_df['Symbol'])
                
                if selected:
                    df_sel = get_stock_data(selected, period=period, interval=interval)
                    from utils.indicators import calculate_ema, calculate_heikin_ashi
                    df_sel['EMA_21'] = calculate_ema(df_sel, length=21)
                    df_sel['EMA_55'] = calculate_ema(df_sel, length=55)
                    ha = calculate_heikin_ashi(df_sel)
                    df_sel = pd.concat([df_sel, ha], axis=1)

                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df_sel.index,
                        open=df_sel['HA_open'], high=df_sel['HA_high'],
                        low=df_sel['HA_low'], close=df_sel['HA_close'],
                        name='Heikin Ashi'
                    ))
                    fig.add_trace(go.Scatter(x=df_sel.index, y=df_sel['EMA_21'], line=dict(color='orange', width=2), name='EMA 21'))
                    fig.add_trace(go.Scatter(x=df_sel.index, y=df_sel['EMA_55'], line=dict(color='blue', width=2), name='EMA 55'))
                    fig.update_layout(title=f"{selected} Analizi", xaxis_rangeslider_visible=False, height=600)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Kriterlere uyan hisse bulunamadı.")
        else:
            st.info("💡 Başlamak için 'Manuel Tarama Yap' butonuna tıklayın veya 'Otomatik Tarama'yı açın.")

        # Auto-refresh logic
        if st.session_state.auto_scan_enabled and strategy_mode == "21/55 EMA & HA":
            if st.session_state.last_scan_time:
                next_scan = st.session_state.last_scan_time + timedelta(minutes=scan_interval_minutes)
                seconds_until_next = (next_scan - datetime.now()).total_seconds()
                
                if seconds_until_next > 0:
                    st.sidebar.info(f"⏱️ Sonraki tarama: {int(seconds_until_next // 60)} dk {int(seconds_until_next % 60)} sn")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.rerun()
            else:
                st.rerun()

elif strategy_mode == "RSI > 50 Stratejisi":
    st.title("📊 RSI > 50 Trend Stratejisi")
    st.markdown("""
    Bu strateji **RSI (14)** indikatörünü kullanarak **yeni başlayan trendleri** yakalar:
    - **50 < RSI < 55**: 🟢 **AL Sinyali** (Trend 50'yi yeni kırmış ve güçleniyor).
    """)
    
    # Settings
    rsi_period = st.sidebar.number_input("RSI Periyodu", min_value=7, max_value=30, value=14)
    # show_only_buy removed as we filter strictly for 50-55
    
    # Auto Scan for RSI
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 Otomatik Tarama")
    auto_scan = st.sidebar.toggle("Otomatik Tarama Aktif", value=st.session_state.auto_scan_enabled, key="rsi_50_auto")
    st.session_state.auto_scan_enabled = auto_scan
    
    manual_scan = st.sidebar.button("🔍 RSI Analizi Yap")
    
    # Scan Logic
    if manual_scan or (auto_scan and st.session_state.last_scan_time is None):
        st.write(f"{len(BIST_100_SYMBOLS)} hisse taranıyor...", )
        progress_bar = st.progress(0)
        results = []
        
        for i, symbol in enumerate(BIST_100_SYMBOLS):
            df = get_stock_data(symbol, period=period, interval=interval)
            
            if df is not None and len(df) > rsi_period:
                # RSI Calculation
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
                loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
                
                last_rsi = df['RSI'].iloc[-1]
                last_price = df['Close'].iloc[-1]
                
                # Filter specific range: 50 < RSI < 55
                if 50 < last_rsi < 55:
                    signal = "AL (Trend Başlangıcı)"
                    results.append({
                        "Symbol": symbol,
                        "Fiyat": last_price,
                        "RSI": round(last_rsi, 2),
                        "Sinyal": signal
                    })
            
            progress_bar.progress((i + 1) / len(BIST_100_SYMBOLS))
            
        progress_bar.empty()
        
        if results:
            st.success(f"✅ {len(results)} hisse bulundu!")
            
            # Formatting for dataframe
            df_res = pd.DataFrame(results)
            
            # Simple styling helper
            def color_signal(val):
                color = 'green' if val == 'AL' else 'red'
                return f'color: {color}; font-weight: bold'
            
            st.dataframe(
                df_res.style.applymap(color_signal, subset=['Sinyal']), 
                use_container_width=True
            )
            
            # Interactivity: Chart
            sel_stock = st.selectbox("Grafik için hisse seçin:", df_res['Symbol'])
            if sel_stock:
                 df_gr = get_stock_data(sel_stock, period=period, interval=interval)
                 # Re-calc RSI for visual
                 delta = df_gr['Close'].diff()
                 gain = (delta.where(delta > 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
                 loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
                 rs = gain / loss
                 df_gr['RSI'] = 100 - (100 / (1 + rs))
                 
                 fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], vertical_spacing=0.05, shared_xaxes=True)
                 
                 # Price
                 fig.add_trace(go.Candlestick(x=df_gr.index, open=df_gr['Open'], high=df_gr['High'], low=df_gr['Low'], close=df_gr['Close'], name='Fiyat'), row=1, col=1)
                 
                 # RSI
                 fig.add_trace(go.Scatter(x=df_gr.index, y=df_gr['RSI'], name='RSI', line=dict(color='purple')), row=2, col=1)
                 # RSI 50 Line
                 fig.add_shape(type='line', x0=df_gr.index[0], y0=50, x1=df_gr.index[-1], y1=50, line=dict(color='gray', dash='dash'), row=2, col=1)
                 
                 fig.update_layout(title=f"{sel_stock} RSI Analizi", height=600, xaxis_rangeslider_visible=False)
                 st.plotly_chart(fig, use_container_width=True)
                 
        else:
            st.warning("Kriterlere uyan hisse bulunamadı.")

elif strategy_mode == "RSI V3 (Kar Optimizasyonu)":
    st.title("🚀 RSI V3: Kar Optimizasyonu Strategy")
    st.markdown("""
    Bu gelişmiş strateji karı maksimize etmeye odaklanır:
    1. **Trend Filtresi**: EMA 21 > EMA 55 (Yükselen trend)
    2. **Trend Gücü**: ADX > 25 (Güçlü bir trendin varlığı)
    3. **Momentum**: RSI'nin 55'i yukarı kesmesi (Güç teyidi)
    4. **Çıkış**: İz süren stop (ATR bazlı) ve RSI < 42
    """)
    
    manual_scan = st.sidebar.button("🔍 V3 Taraması Başlat")
    
    if manual_scan:
        st.write(f"{len(BIST_100_SYMBOLS)} hisse taranıyor... Lütfen bekleyin.")
        progress_bar = st.progress(0)
        results = []
        
        for i, symbol in enumerate(BIST_100_SYMBOLS):
            df = get_stock_data(symbol, period=period, interval=interval)
            if df is not None:
                res = check_rsi_strategy_v3(df)
                if res['signal']:
                    results.append({
                        "Symbol": symbol,
                        "Price": res['last_price'],
                        "Details": res['details']
                    })
            progress_bar.progress((i + 1) / len(BIST_100_SYMBOLS))
        
        progress_bar.empty()
        
        if results:
            st.success(f"✅ {len(results)} hisse bulundu!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("⚠️ Kriterlere uyan hisse bulunamadı.")
            
    # Show cached logic (Brief version for speed, can be expanded strictly like the Main Strategy)

