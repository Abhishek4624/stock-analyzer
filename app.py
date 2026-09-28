import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. Page Setup & Custom Styling ---
st.set_page_config(page_title="Indian Stock Analyzer", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa; border-radius: 10px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px;
    }
    .metric-title { font-size: 14px; color: #6c757d; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 24px; font-weight: bold; color: #212529; margin-top: 5px; }
    .pass-badge { background-color: #d1e7dd; color: #0f5132; padding: 5px 10px; border-radius: 5px; font-weight: bold; font-size: 14px;}
    .fail-badge { background-color: #f8d7da; color: #842029; padding: 5px 10px; border-radius: 5px; font-weight: bold; font-size: 14px;}
    </style>
""", unsafe_allow_html=True)

# App Header
st.title("🇮🇳 Abhishek's Indian Financial Dashboard")
st.markdown("Analyze Stocks, Mutual Funds, and ETFs in real-time.")

# Create Tabs for the UI
tab1, tab2 = st.tabs(["📊 Stock Analyzer", "🏦 Mutual Funds & ETFs"])

# ==========================================
# TAB 1: STOCK ANALYZER
# ==========================================
with tab1:
    st.sidebar.header("Stock Search")
    popular_stocks = {
        "Reliance Industries": "RELIANCE.NS",
        "Tata Consultancy Services": "TCS.NS",
        "HDFC Bank": "HDFCBANK.NS",
        "Infosys": "INFY.NS",
        "ICICI Bank": "ICICIBANK.NS",
        "Tata Motors": "TATAMOTORS.NS"
    }
    
    selection_type = st.sidebar.radio("Select Input Method:", ["Quick Select", "Custom Ticker"])
    if selection_type == "Quick Select":
        company = st.sidebar.selectbox("Choose a Stock:", list(popular_stocks.keys()))
        ticker = popular_stocks[company]
    else:
        raw_ticker = st.sidebar.text_input("Enter Ticker (e.g., ITC, SBIN):", "RELIANCE")
        ticker = f"{raw_ticker.upper()}.NS" if not raw_ticker.endswith((".NS", ".BO")) else raw_ticker.upper()

    if ticker:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            info = stock.info
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                pct_change = ((current_price - prev_close) / prev_close) * 100
                market_cap_cr = info.get('marketCap', 0) / 10000000 
                
                # Technicals
                hist['50_MA'] = hist['Close'].rolling(window=50).mean()
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                hist['RSI'] = 100 - (100 / (1 + rs))
                
                # Scorecard UI
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f'<div class="metric-card"><div class="metric-title">Price</div><div class="metric-value">₹{current_price:,.2f}</div><div style="color: {"green" if pct_change > 0 else "red"}; font-weight: bold;">{pct_change:+.2f}%</div></div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div class="metric-card"><div class="metric-title">Market Cap</div><div class="metric-value">₹{market_cap_cr:,.0f} Cr</div></div>', unsafe_allow_html=True)
                with col3:
                    pe_ratio = info.get('trailingPE', 'N/A')
                    st.markdown(f'<div class="metric-card"><div class="metric-title">P/E Ratio</div><div class="metric-value">{pe_ratio if isinstance(pe_ratio, str) else f"{pe_ratio:.2f}"}</div></div>', unsafe_allow_html=True)
                with col4:
                    div_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                    st.markdown(f'<div class="metric-card"><div class="metric-title">Dividend Yield</div><div class="metric-value">{div_yield:.2f}%</div></div>', unsafe_allow_html=True)

                # Chart
                st.markdown("### Technical Chart (6 Months)")
                hist_6m = hist.last('6ME')
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=hist_6m.index, open=hist_6m['Open'], high=hist_6m['High'], low=hist_6m['Low'], close=hist_6m['Close'], name='Price'))
                fig.add_trace(go.Scatter(x=hist_6m.index, y=hist_6m['50_MA'], line=dict(color='orange', width=2), name='50-Day MA'))
                fig.update_layout(template='plotly_white', xaxis_rangeslider_visible=False, height=450, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)

        except Exception:
            st.error("Error fetching stock data.")

# ==========================================
# TAB 2: MUTUAL FUNDS & ETFs
# ==========================================
with tab2:
    st.subheader("Explore Indian Index Funds & Sector ETFs")
    
    # Mapping popular Indian ETFs to their Yahoo Finance symbols
    etf_dict = {
        "Nippon India Nifty 50 (Large Cap)": "NIFTYBEES.NS",
        "Nippon India Bank Nifty (Banking)": "BANKBEES.NS",
        "Nippon India IT (Tech Sector)": "ITBEES.NS",
        "Nippon India Gold (Commodity)": "GOLDBEES.NS",
        "Motilal Oswal Nasdaq 100 (US Tech)": "MON100.NS",
        "SBI Nifty Next 50 (Mid Cap)": "SETFNIF50.NS"
    }
    
    selected_etf_name = st.selectbox("Select a Fund/ETF to Analyze:", list(etf_dict.keys()))
    etf_ticker = etf_dict[selected_etf_name]
    
    if etf_ticker:
        with st.spinner("Calculating historical returns..."):
            etf_data = yf.Ticker(etf_ticker)
            etf_hist = etf_data.history(period="1y")
            
            if not etf_hist.empty:
                current_nav = etf_hist['Close'].iloc[-1]
                
                # Calculate Returns (1M, 6M, 1Y)
                try:
                    price_1m_ago = etf_hist['Close'].iloc[-22] # Approx 22 trading days in a month
                    ret_1m = ((current_nav - price_1m_ago) / price_1m_ago) * 100
                except IndexError:
                    ret_1m = 0
                    
                try:
                    price_6m_ago = etf_hist['Close'].iloc[-126] # Approx 126 trading days in 6 months
                    ret_6m = ((current_nav - price_6m_ago) / price_6m_ago) * 100
                except IndexError:
                    ret_6m = 0
                    
                price_1y_ago = etf_hist['Close'].iloc[0]
                ret_1y = ((current_nav - price_1y_ago) / price_1y_ago) * 100

                st.markdown(f"### Current NAV: **₹{current_nav:.2f}**")
                
                # Return Metrics UI
                r_col1, r_col2, r_col3 = st.columns(3)
                r_col1.metric("1-Month Return", f"{ret_1m:.2f}%", f"{ret_1m:.2f}%")
                r_col2.metric("6-Month Return", f"{ret_6m:.2f}%", f"{ret_6m:.2f}%")
                r_col3.metric("1-Year Return", f"{ret_1y:.2f}%", f"{ret_1y:.2f}%")
                
                # ETF Growth Chart
                st.markdown("### 1-Year Growth Trajectory")
                fig_etf = go.Figure()
                fig_etf.add_trace(go.Scatter(
                    x=etf_hist.index, y=etf_hist['Close'], 
                    fill='tozeroy', mode='lines', 
                    line=dict(color='blue', width=2),
                    name='NAV'
                ))
                fig_etf.update_layout(template='plotly_white', height=400, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_etf, use_container_width=True)
