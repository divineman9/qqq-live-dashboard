import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title='QQQ Live Dashboard', layout='wide', page_icon='📈')

SYMBOLS = ['MSFT', 'AAPL', 'NVDA', 'AMZN', 'META', 'AVGO', 'TSLA', 'GOOGL', 'GOOG', 'COST', 'SPY', 'IWM', 'QQQ', 'SMH', 'XLF']

AVG_DAILY_VOL = {
    'NVDA': 159244689, 'AAPL': 64858913, 'MSFT': 47342671, 'AMZN': 60644120, 'META': 18556928,
    'TSLA': 46501658, 'GOOGL': 39804999, 'GOOG': 27153391, 'AVGO': 36637496, 'COST': 2472245,
    'SPY': 80000000, 'IWM': 35000000, 'QQQ': 45000000, 'SMH': 8000000, 'XLF': 40000000
}

RANKS = {
    'NVDA': 1, 'AAPL': 2, 'MSFT': 3, 'AMZN': 4, 'META': 5, 'AVGO': 6, 'TSLA': 7,
    'GOOGL': 8, 'GOOG': 9, 'COST': 10, 'SPY': 11, 'IWM': 12, 'QQQ': 13, 'SMH': 14, 'XLF': 15
}


def get_elapsed_fraction():
    et = datetime.now(pytz.timezone('America/New_York'))
    if et.weekday() >= 5:
        return 1.0
    open_time = et.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = et.replace(hour=16, minute=0, second=0, microsecond=0)
    if et <= open_time:
        return 0.01
    if et >= close_time:
        return 1.0
    return (et - open_time).seconds / (390 * 60)


def get_market_status():
    et = datetime.now(pytz.timezone('America/New_York'))
    if et.weekday() >= 5:
        return 'Closed (Weekend)'
    open_time = et.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = et.replace(hour=16, minute=0, second=0, microsecond=0)
    if et < open_time:
        return 'Closed (Pre-Market)'
    if et >= close_time:
        return 'Closed (After Hours)'
    return 'Open'


@st.cache_data(ttl=30)
def fetch_quotes():
    rows = []
    elapsed = get_elapsed_fraction()
    tickers = yf.Tickers(' '.join(SYMBOLS))
    for sym in SYMBOLS:
        try:
            t = tickers.tickers[sym]
            info = t.fast_info
            hist_30d = t.history(period='35d', interval='1d')
            hist_1d = t.history(period='1d', interval='1m')
            price = info.last_price or 0
            prev_close = info.previous_close or price
            volume = int(hist_1d['Volume'].sum()) if not hist_1d.empty else 0
            avg_vol = AVG_DAILY_VOL.get(sym, 1)
            rel_vol = volume / (avg_vol * elapsed) if elapsed > 0 else 0
            week_chg = 0
            month_chg = 0
            if not hist_30d.empty and len(hist_30d) >= 6:
                week_chg = round((price - hist_30d['Close'].iloc[-6]) / hist_30d['Close'].iloc[-6] * 100, 2)
                month_chg = round((price - hist_30d['Close'].iloc[0]) / hist_30d['Close'].iloc[0] * 100, 2)
            rows.append({
                '#': RANKS.get(sym, 99),
                'Symbol': sym,
                'Price': round(price, 2),
                'Chg %': round((price - prev_close) / prev_close * 100, 2) if prev_close else 0,
                'Volume': volume,
                'Rel Vol': round(rel_vol, 2),
                'Wk %': week_chg,
                'Mo %': month_chg,
            })
        except Exception:
            rows.append({
                '#': RANKS.get(sym, 99), 'Symbol': sym, 'Price': 0, 'Chg %': 0,
                'Volume': 0, 'Rel Vol': 0, 'Wk %': 0, 'Mo %': 0
            })
    return pd.DataFrame(rows).sort_values('#').reset_index(drop=True)


def style_pct_columns(df):
    def color_pct(val):
        if pd.isna(val) or val == 0:
            return ''
        color = '#16a34a' if val > 0 else '#dc2626'
        return f'color: {color}'

    styled = df.style.map(color_pct, subset=['Chg %', 'Wk %', 'Mo %'])
    return styled


try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(interval=30_000, key='qqq_autorefresh')
except ImportError:
    if st.button('🔄 Refresh'):
        st.cache_data.clear()
        st.rerun()

et_now = datetime.now(pytz.timezone('America/New_York'))
st.title('📈 QQQ Top Holdings — Live Dashboard')
st.subheader(f'Current Time (ET): {et_now.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")}')

last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
st.caption(f'Last updated: {last_updated}')

df = fetch_quotes()

column_config = {
    'Chg %': st.column_config.NumberColumn('Chg %', format='%.2f%%'),
    'Wk %': st.column_config.NumberColumn('Wk %', format='%.2f%%'),
    'Mo %': st.column_config.NumberColumn('Mo %', format='%.2f%%'),
    'Volume': st.column_config.NumberColumn('Volume', format='%d'),
    'Rel Vol': st.column_config.NumberColumn('Rel Vol', format='%.2fx'),
    'Price': st.column_config.NumberColumn('Price', format='$%.2f'),
}

st.dataframe(
    style_pct_columns(df),
    column_config=column_config,
    use_container_width=True,
    hide_index=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric('Total Symbols', len(SYMBOLS))
with col2:
    st.metric('Market Status', get_market_status())
with col3:
    st.metric('Last Refresh', last_updated)