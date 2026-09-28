import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- 1. Page Setup & Styling ---
st.set_page_config(page_title="Indian Stock Analyzer", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa; border-radius: 10px; padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px;
    }
    .metric-title { font-size: 13px; color: #6c757d; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 20px; font-weight: bold; color: #212529; margin-top: 5px; }
    .zone-buy { background-color: #d1e7dd; color: #0f5132; padding: 15px; border-radius: 8px; border-left: 5px solid #198754; }
    .zone-hold { background-color: #fff3cd; color: #664d03; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107; }
    .zone-sell { background-color: #f8d7da; color: #842029; padding: 15px; border-radius: 8px; border-left: 5px solid #dc3545; }
    </style>
""", unsafe_allow_html=True)

st.title("🇮🇳 Abhishek's Advanced Market Screener")
st.markdown("Deep Technical Analysis & Price Zone Recommendations.")

# --- 2. Sidebar Search ---
st.sidebar.header("Stock Search")
popular_stocks = {
    "Reliance Industries": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS", "ICICI Bank": "ICICIBANK.NS", "Tata Motors": "TATAMOTORS.NS",
    "ITC Limited": "ITC.NS", "SBI": "SBIN.NS", "L&T": "LT.NS", "Bharti Airtel": "BHARTIARTL.NS"
}

selection_type = st.sidebar.radio("Select Input Method:", ["Quick Select", "Custom Ticker"])
if selection_type == "Quick Select":
    company = st.sidebar.selectbox("Choose a Stock:", list(popular_stocks.keys()))
    ticker = popular_stocks[company]
else:
    raw_ticker = st.sidebar.text_input("Enter Ticker (e.g., ZOMATO, SUZLON):", "RELIANCE")
    ticker = f"{raw_ticker.upper()}.NS" if not raw_ticker.endswith((".NS", ".BO")) else raw_ticker.upper()

# --- 3. Data Fetching & Calculations ---
if ticker:
    with st.spinner(f"Running deep technical analysis on {ticker}..."):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            info = stock.info
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                
                # Fundamental Data
                market_cap_cr = info.get('marketCap', 0) / 10000000 
                pe_ratio = info.get('trailingPE', 'N/A')
                pb_ratio = info.get('priceToBook', 'N/A')
                high_52 = info.get('fiftyTwoWeekHigh', hist['High'].max())
                low_52 = info.get('fiftyTwoWeekLow', hist['Low'].min())
                div_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0

                # --- ADVANCED TECHNICAL INDICATORS ---
                # 1. Moving Averages
                hist['50_MA'] = hist['Close'].rolling(window=50).mean()
                hist['200_MA'] = hist['Close'].rolling(window=200).mean()
                
                # 2. RSI (14-day)
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                hist['RSI'] = 100 - (100 / (1 + rs))
                
                # 3. MACD (Moving Average Convergence Divergence)
                ema_12 = hist['Close'].ewm(span=12, adjust=False).mean()
                ema_26 = hist['Close'].ewm(span=26, adjust=False).mean()
                hist['MACD'] = ema_12 - ema_26
                hist['Signal_Line'] = hist['MACD'].ewm(span=9, adjust=False).mean()
                
                # 4. Bollinger Bands (20-day, 2 std dev) for Price Zones
                hist['20_SMA'] = hist['Close'].rolling(window=20).mean()
                hist['20_STD'] = hist['Close'].rolling(window=20).std()
                hist['BB_Upper'] = hist['20_SMA'] + (hist['20_STD'] * 2)
                hist['BB_Lower'] = hist['20_SMA'] - (hist['20_STD'] * 2)

                # Current Indicator Values
                curr_rsi = hist['RSI'].iloc[-1]
                curr_macd = hist['MACD'].iloc[-1]
                curr_signal = hist['Signal_Line'].iloc[-1]
                curr_bb_upper = hist['BB_Upper'].iloc[-1]
                curr_bb_lower = hist['BB_Lower'].iloc[-1]
                curr_50_ma = hist['50_MA'].iloc[-1]

                # --- 4. Dashboard UI ---
                st.subheader(f"{info.get('longName', ticker)} | ₹{current_price:,.2f}")
                
                # Row 1: Fundamentals
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.markdown(f'<div class="metric-card"><div class="metric-title">Market Cap</div><div class="metric-value">₹{market_cap_cr:,.0f} Cr</div></div>', unsafe_allow_html=True)
                col2.markdown(f'<div class="metric-card"><div class="metric-title">P/E Ratio</div><div class="metric-value">{pe_ratio if isinstance(pe_ratio, str) else f"{pe_ratio:.2f}"}</div></div>', unsafe_allow_html=True)
                col3.markdown(f'<div class="metric-card"><div class="metric-title">P/B Ratio</div><div class="metric-value">{pb_ratio if isinstance(pb_ratio, str) else f"{pb_ratio:.2f}"}</div></div>', unsafe_allow_html=True)
                col4.markdown(f'<div class="metric-card"><div class="metric-title">52W High</div><div class="metric-value">₹{high_52:,.1f}</div></div>', unsafe_allow_html=True)
                col5.markdown(f'<div class="metric-card"><div class="metric-title">52W Low</div><div class="metric-value">₹{low_52:,.1f}</div></div>', unsafe_allow_html=True)

                st.write("---")
                
                # --- 5. PRICE ZONE & RECOMMENDATION ENGINE ---
                st.markdown("### 🤖 Technical Price Zone Verdict")
                
                score = 0
                reasons = []

                # Price Zone Logic (Bollinger Bands)
                if current_price <= curr_bb_lower * 1.02:
                    score += 2
                    reasons.append("✅ **Price Zone:** Excellent entry. Stock is at the bottom of its Bollinger Band (Oversold).")
                elif current_price >= curr_bb_upper * 0.98:
                    score -= 2
                    reasons.append("❌ **Price Zone:** High risk. Stock is hitting the top of its Bollinger Band (Overvalued short-term).")
                else:
                    reasons.append("➖ **Price Zone:** Neutral. Stock is trading in the middle of its normal volatility range.")

                # Momentum Logic (RSI)
                if curr_rsi < 40:
                    score += 1
                    reasons.append(f"✅ **Momentum:** RSI is {curr_rsi:.1f} (Cooling down/Oversold). Good time to accumulate.")
                elif curr_rsi > 70:
                    score -= 1
                    reasons.append(f"❌ **Momentum:** RSI is {curr_rsi:.1f} (Overbought). Profit booking might happen soon.")
                else:
                    reasons.append(f"➖ **Momentum:** RSI is {curr_rsi:.1f} (Neutral momentum).")

                # Trend Logic (MACD & MA)
                if curr_macd > curr_signal and current_price > curr_50_ma:
                    score += 1
                    reasons.append("✅ **Trend:** Bullish. MACD crossed above signal line and price is above 50-day average.")
                elif curr_macd < curr_signal and current_price < curr_50_ma:
                    score -= 1
                    reasons.append("❌ **Trend:** Bearish. MACD is dropping and price is below 50-day average.")

                # Generate Final Verdict
                if score >= 2:
                    verdict_class = "zone-buy"
                    verdict_title = "🟢 GOOD TO BUY AT THIS PRICE ZONE"
                elif score <= -1:
                    verdict_class = "zone-sell"
                    verdict_title = "🔴 BAD PRICE ZONE (WAIT / AVOID)"
                else:
                    verdict_class = "zone-hold"
                    verdict_title = "🟡 FAIR ZONE (HOLD / BUY ON DIPS)"

                # Display Verdict
                st.markdown(f'<div class="{verdict_class}"><h4>{verdict_title}</h4>', unsafe_allow_html=True)
                for r in reasons:
                    st.write(r)
                st.markdown('</div><br>', unsafe_allow_html=True)

                # --- 6. Advanced Interactive Chart ---
                st.markdown("### 📊 Advanced Technical Chart (6 Months)")
                hist_6m = hist.last('6ME')
                
                fig = go.Figure()
                
                # Candlesticks
                fig.add_trace(go.Candlestick(
                    x=hist_6m.index, open=hist_6m['Open'], high=hist_6m['High'], low=hist_6m['Low'], close=hist_6m['Close'], name='Price'
                ))
                # 50 MA
                fig.add_trace(go.Scatter(x=hist_6m.index, y=hist_6m['50_MA'], line=dict(color='blue', width=1.5), name='50-Day MA'))
                
                # Bollinger Bands
                fig.add_trace(go.Scatter(x=hist_6m.index, y=hist_6m['BB_Upper'], line=dict(color='rgba(255,0,0,0.3)', width=1, dash='dot'), name='Upper Band'))
                fig.add_trace(go.Scatter(x=hist_6m.index, y=hist_6m['BB_Lower'], line=dict(color='rgba(0,128,0,0.3)', width=1, dash='dot'), name='Lower Band', fill='tonexty', fillcolor='rgba(128,128,128,0.1)'))
                
                fig.update_layout(template='plotly_white', xaxis_rangeslider_visible=False, height=550, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error fetching data. Please ensure the ticker is correct. Details: {e}")
