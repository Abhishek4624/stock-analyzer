import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Setup the Website Layout
st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📈 Tickertape Clone: Stock Analyzer & Recommender")

# 2. Create a Sidebar for User Input
st.sidebar.header("Search for a Stock")
st.sidebar.write("Use symbols like AAPL for Apple, TSLA for Tesla, or RELIANCE.NS for Indian stocks.")
ticker = st.sidebar.text_input("Enter Stock Ticker:", "AAPL")

if ticker:
    st.write(f"Fetching live data for **{ticker}**...")
    
    # 3. Fetch Live Data from Yahoo Finance
    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo")
    
    if not hist.empty:
        # 4. Calculate Math for the Recommendation
        current_price = hist['Close'].iloc[-1]
        previous_price = hist['Close'].iloc[-2]
        price_change = current_price - previous_price
        pct_change = (price_change / previous_price) * 100
        
        # Calculate a 50-day moving average (average price over last 50 days)
        hist['50_MA'] = hist['Close'].rolling(window=50).mean()
        ma_50 = hist['50_MA'].iloc[-1]
        
        # 5. Recommendation Engine Logic
        if current_price > (ma_50 * 1.05):
            recommendation = "🟢 STRONG BUY"
            reason = "The stock is surging 5% above its 50-day average. Strong upward momentum."
        elif current_price > ma_50:
            recommendation = "🟡 HOLD / ACCUMULATE"
            reason = "The stock is stable and slightly above its 50-day average."
        else:
            recommendation = "🔴 SELL"
            reason = "The stock has dropped below its 50-day average. Downward trend detected."
            
        # 6. Build the Dashboard UI
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"${current_price:.2f}", f"{pct_change:.2f}%")
        col2.metric("50-Day Average", f"${ma_50:.2f}")
        col3.metric("AI Recommendation", recommendation)
        
        st.info(f"**Analysis:** {reason}")
        
        # 7. Draw an Interactive Chart
        st.subheader("Interactive Price Chart")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name="Daily Price", line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['50_MA'], name="50-Day Average", line=dict(color='orange', dash='dash')))
        fig.update_layout(xaxis_title="Date", yaxis_title="Price", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        # 8. Show Company Info
        with st.expander("About the Company"):
            st.write(stock.info.get('longBusinessSummary', 'No description available.'))
    else:
        st.error("Could not find that stock symbol. Please try another one.")