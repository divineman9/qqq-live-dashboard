import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(
    page_title='QQQ Live Dashboard',
    layout='wide',
    page_icon='📈',
    initial_sidebar_state='collapsed',
)

st.markdown("""
<style>
/* ── Page shell ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1rem 2rem 2rem 2rem; max-width: 1400px; }

/* ── Top header bar ── */
.dash-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.dash-title { font-size: 1.35rem; font-weight: 800; color: #0f172a; letter-spacing: -.4px; }
.dash-sub   { font-size: .75rem; color: #64748b; margin-top: 2px; }
.market-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: .8rem;
    font-weight: 700;
    letter-spacing: .3px;
}
.pill-open   { background: #dcfce7; color: #16a34a; }
.pill-closed { background: #f1f5f9; color: #64748b; }
.dot { width: 7px; height: 7px; border-radius: 50%; }
.dot-open { background: #22c55e; animation: pulse 1.8s infinite; }
.dot-closed { background: #94a3b8; }
@keyframes pulse {
    0%,100% { opacity:1; } 50% { opacity:.3; }
}
.et-time { font-size: .8rem; color: #475569; font-weight: 500; }

/* ── KPI cards ── */
.kpi-row { display: flex; gap: 1rem; margin-bottom: 1.25rem; }
.kpi-card {
    flex: 1;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: .9rem 1.1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.kpi-label { font-size: .7rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: .8px; }
.kpi-value { font-size: 1.4rem; font-weight: 800; color: #0f172a; margin: 2px 0; }
.kpi-sub   { font-size: .72rem; color: #64748b; }
.kpi-gain  { color: #16a34a; }
.kpi-loss  { color: #dc2626; }

/* ── Table wrapper ── */
.table-wrap {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    overflow: hidden;
}
table.holdings {
    width: 100%;
    border-collapse: collapse;
    font-size: .82rem;
    font-family: 'Inter', system-ui, sans-serif;
}
table.holdings thead tr {
    background: #f8fafc;
    border-bottom: 2px solid #e2e8f0;
}
table.holdings thead th {
    padding: 10px 14px;
    text-align: left;
    font-size: .68rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: .7px;
    white-space: nowrap;
}
table.holdings tbody tr {
    border-bottom: 1px solid #f1f5f9;
    transition: background .15s;
}
table.holdings tbody tr:hover { background: #f8fafc; }
table.holdings tbody tr:last-child { border-bottom: none; }
table.holdings td {
    padding: 10px 14px;
    white-space: nowrap;
    vertical-align: middle;
}

/* ── Cell helpers ── */
.rank-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px; height: 24px;
    border-radius: 6px;
    background: #f1f5f9;
    color: #64748b;
    font-size: .72rem;
    font-weight: 700;
}
.sym { font-weight: 800; color: #0f172a; font-size: .88rem; }
.co  { font-size: .68rem; color: #94a3b8; display: block; margin-top: 1px; }
.price { font-family: monospace; font-weight: 700; color: #0f172a; }
.gain  { color: #16a34a; font-weight: 700; font-family: monospace; }
.loss  { color: #dc2626; font-weight: 700; font-family: monospace; }
.neut  { color: #94a3b8; font-family: monospace; }
.vol   { font-family: monospace; color: #475569; font-size: .8rem; }

.rv-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 9999px;
    font-size: .72rem;
    font-weight: 700;
    font-family: monospace;
}
.rv-low    { background: #f1f5f9; color: #94a3b8; }
.rv-normal { background: #eff6ff; color: #2563eb; }
.rv-high   { background: #fff7ed; color: #ea580c; }
.rv-spike  { background: #fef2f2; color: #dc2626; }

/* ── Footer ── */
.dash-footer {
    text-align: center;
    font-size: .7rem;
    color: #94a3b8;
    margin-top: 1.2rem;
    padding-top: .8rem;
    border-top: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────
SYMBOLS = ['NVDA','AAPL','MSFT','AMZN','META','AVGO','TSLA','GOOGL','GOOG','COST',
           'SPY','IWM','QQQ','SMH','XLF']

NAMES = {
    'NVDA':'NVIDIA Corp','AAPL':'Apple Inc','MSFT':'Microsoft Corp','AMZN':'Amazon.com',
    'META':'Meta Platforms','AVGO':'Broadcom Inc','TSLA':'Tesla Inc','GOOGL':'Alphabet A',
    'GOOG':'Alphabet C','COST':'Costco Wholesale','SPY':'SPDR S&P 500 ETF',
    'IWM':'iShares Russell 2000','QQQ':'Invesco QQQ Trust','SMH':'VanEck Semi ETF',
    'XLF':'Financial Select SPDR',
}

AVG_DAILY_VOL = {
    'NVDA':159244689,'AAPL':64858913,'MSFT':47342671,'AMZN':60644120,'META':18556928,
    'TSLA':46501658,'GOOGL':39804999,'GOOG':27153391,'AVGO':36637496,'COST':2472245,
    'SPY':80000000,'IWM':35000000,'QQQ':45000000,'SMH':8000000,'XLF':40000000,
}

RANKS = {s:i+1 for i,s in enumerate(SYMBOLS)}

# ── Helpers ────────────────────────────────────────────────────────────────
def get_et():
    return datetime.now(pytz.timezone('America/New_York'))

def market_status():
    et = get_et()
    if et.weekday() >= 5: return 'Closed', False
    o = et.replace(hour=9,minute=30,second=0,microsecond=0)
    c = et.replace(hour=16,minute=0,second=0,microsecond=0)
    if et < o: return 'Pre-Market', False
    if et >= c: return 'After Hours', False
    return 'Open', True

def elapsed_fraction():
    et = get_et()
    if et.weekday() >= 5: return 1.0
    o = et.replace(hour=9,minute=30,second=0,microsecond=0)
    c = et.replace(hour=16,minute=0,second=0,microsecond=0)
    if et <= o: return 0.01
    if et >= c: return 1.0
    return (et-o).seconds / (390*60)

def pre_elapsed_fraction():
    et = get_et()
    if et.weekday() >= 5: return 1.0
    pre_start = et.replace(hour=4, minute=0, second=0, microsecond=0)
    pre_end   = et.replace(hour=9, minute=30, second=0, microsecond=0)
    if et <= pre_start: return 0.01
    if et >= pre_end:   return 1.0
    return (et - pre_start).seconds / (330 * 60)

def ah_elapsed_fraction():
    et = get_et()
    if et.weekday() >= 5: return 1.0
    ah_start = et.replace(hour=16, minute=0, second=0, microsecond=0)
    ah_end   = et.replace(hour=20, minute=0, second=0, microsecond=0)
    if et <= ah_start: return 0.01
    if et >= ah_end:   return 1.0
    return (et - ah_start).seconds / (240 * 60)

def fmt_vol(v):
    if v >= 1_000_000: return f'{v/1_000_000:.1f}M'
    if v >= 1_000: return f'{v/1_000:.0f}K'
    return str(v)

def pct_html(v, suffix='%'):
    if v > 0: return f'<span class="gain">▲ {v:+.2f}{suffix}</span>'
    if v < 0: return f'<span class="loss">▼ {v:.2f}{suffix}</span>'
    return f'<span class="neut">— 0.00{suffix}</span>'

def rv_html(rv):
    label = f'{rv:.2f}x'
    if rv >= 2.0:   css = 'rv-spike'
    elif rv >= 1.5: css = 'rv-high'
    elif rv >= 0.8: css = 'rv-normal'
    else:           css = 'rv-low'
    return f'<span class="rv-badge {css}">{label}</span>'

# ── Data fetch ─────────────────────────────────────────────────────────────
ET_TZ = pytz.timezone('America/New_York')

def _safe_tz_convert(idx):
    if idx.tz is None:
        return idx.tz_localize('UTC').tz_convert(ET_TZ)
    return idx.tz_convert(ET_TZ)

def _min_of_day(idx):
    return idx.hour * 60 + idx.minute

@st.cache_data(ttl=30)
def fetch_quotes():
    elapsed = elapsed_fraction()
    rows = []
    tickers = yf.Tickers(' '.join(SYMBOLS))
    for sym in SYMBOLS:
        try:
            t    = tickers.tickers[sym]
            info = t.fast_info
            h35  = t.history(period='35d', interval='1d')
            h1d  = t.history(period='2d', interval='1m', prepost=True)

            price = float(info.last_price or 0)
            prev  = float(info.previous_close or price)

            pre_chg = ah_chg = 0.0
            pre_vol = ah_vol = volume = 0

            if not h1d.empty:
                h1d.index = _safe_tz_convert(h1d.index)       # bug-fix: handle tz-naive
                today     = get_et().date()
                mins      = _min_of_day(h1d.index)
                # Fall back to most recent available trading day so data shows when markets are closed
                avail_dates = sorted(set(h1d.index.date))
                ref_date    = avail_dates[-1] if avail_dates else today
                is_ref      = pd.Series(h1d.index.date == ref_date, index=h1d.index)

                pre_bars = h1d[is_ref & (mins <  9*60+30)]  # 04:00-09:29
                reg_bars = h1d[is_ref & (mins >= 9*60+30) & (mins < 16*60)]  # 09:30-15:59
                ah_bars  = h1d[is_ref & (mins >= 16*60)]    # 16:00-20:00

                if not pre_bars.empty:
                    pre_vol = int(pre_bars['Volume'].sum())
                    pre_chg = round((float(pre_bars['Close'].iloc[-1]) - prev) / prev * 100, 2) if prev else 0

                volume = int(reg_bars['Volume'].sum()) if not reg_bars.empty else 0

                if not ah_bars.empty:
                    ah_vol  = int(ah_bars['Volume'].sum())
                    ah_chg  = round((float(ah_bars['Close'].iloc[-1]) - prev) / prev * 100, 2) if prev else 0

            avg         = AVG_DAILY_VOL.get(sym, 1)
            # If ref_date is a past completed session, use full elapsed (1.0); else live fraction
            is_live_today = ('ref_date' in dir() and ref_date == get_et().date())
            reg_e = elapsed if is_live_today else 1.0
            pre_e = pre_elapsed_fraction() if is_live_today else 1.0
            ah_e  = ah_elapsed_fraction()  if is_live_today else 1.0
            rel_vol     = volume / (avg * reg_e) if reg_e > 0 else 0
            pre_rel_vol = round(pre_vol / (avg * pre_e) if pre_e > 0 else 0, 2)
            ah_rel_vol  = round(ah_vol  / (avg * ah_e)  if ah_e  > 0 else 0, 2)
            wk = mo = 0.0
            if not h35.empty and len(h35) >= 6:
                wk = round((price - float(h35['Close'].iloc[-6])) / float(h35['Close'].iloc[-6]) * 100, 2)
                mo = round((price - float(h35['Close'].iloc[0]))  / float(h35['Close'].iloc[0])  * 100, 2)
            rows.append({
                'rank': RANKS.get(sym,99), 'symbol': sym,
                'price': price, 'chg_pct': round((price-prev)/prev*100,2) if prev else 0,
                'pre_chg': pre_chg, 'pre_vol': pre_vol,
                'ah_chg':  ah_chg,  'ah_vol':  ah_vol,
                'volume': volume, 'rel_vol': round(rel_vol,2),
                'pre_rel_vol': pre_rel_vol, 'ah_rel_vol': ah_rel_vol,
                'elapsed': elapsed,                            # carry elapsed to avoid drift
                'wk': wk, 'mo': mo,
            })
        except Exception:
            rows.append({'rank':RANKS.get(sym,99),'symbol':sym,'price':0,'chg_pct':0,
                         'pre_chg':0,'pre_vol':0,'ah_chg':0,'ah_vol':0,
                         'volume':0,'rel_vol':0,'pre_rel_vol':0,'ah_rel_vol':0,'elapsed':elapsed,'wk':0,'mo':0})
    return sorted(rows, key=lambda r: r['rank'])

# ── Auto-refresh ───────────────────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30_000, key='qqq_refresh')
except ImportError:
    pass

# ── Data ───────────────────────────────────────────────────────────────────
rows   = fetch_quotes()
status, is_open = market_status()
et_now = get_et()

# ── Header ─────────────────────────────────────────────────────────────────
pill_cls = 'pill-open' if is_open else 'pill-closed'
dot_cls  = 'dot-open'  if is_open else 'dot-closed'
st.markdown(f"""
<div class="dash-header">
  <div>
    <div class="dash-title">📈 QQQ Top Holdings</div>
    <div class="dash-sub">Live market dashboard · 15 symbols · auto-refreshes every 30s</div>
  </div>
  <div style="display:flex;align-items:center;gap:1.2rem;">
    <span class="et-time">🕐 {et_now.strftime('%I:%M:%S %p ET')}</span>
    <span class="market-pill {pill_cls}">
      <span class="dot {dot_cls}"></span>{status}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI cards ──────────────────────────────────────────────────────────────
gainers    = sorted(rows, key=lambda r: r['chg_pct'],  reverse=True)
pre_movers = sorted(rows, key=lambda r: r['pre_chg'],  reverse=True)
ah_movers  = sorted(rows, key=lambda r: r['ah_chg'],   reverse=True)
best, worst    = gainers[0], gainers[-1]
pre_best  = next((r for r in pre_movers if r['pre_chg'] != 0), pre_movers[0])
pre_worst = next((r for r in reversed(pre_movers) if r['pre_chg'] != 0), pre_movers[-1])
ah_best   = next((r for r in ah_movers  if r['ah_chg']  != 0), ah_movers[0])
avg_rv = sum(r['rel_vol'] for r in rows) / len(rows)
spikes = sum(1 for r in rows if r['rel_vol'] >= 2.0)

def cls(v): return 'kpi-gain' if v > 0 else 'kpi-loss'

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Market Status</div>
    <div class="kpi-value" style="font-size:1.1rem;">{'🟢 ' if is_open else '⚫ '}{status}</div>
    <div class="kpi-sub">{et_now.strftime('%A, %b %d %Y')}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Top Gainer</div>
    <div class="kpi-value {cls(best['chg_pct'])}">{best['symbol']}</div>
    <div class="kpi-sub {cls(best['chg_pct'])}">{best['chg_pct']:+.2f}% today</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Top Loser</div>
    <div class="kpi-value {cls(worst['chg_pct'])}">{worst['symbol']}</div>
    <div class="kpi-sub {cls(worst['chg_pct'])}">{worst['chg_pct']:+.2f}% today</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Pre-Mkt Leader</div>
    <div class="kpi-value {cls(pre_best['pre_chg'])}">{pre_best['symbol']}</div>
    <div class="kpi-sub {cls(pre_best['pre_chg'])}">{pre_best['pre_chg']:+.2f}% pre-mkt</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Pre-Mkt Laggard</div>
    <div class="kpi-value {cls(pre_worst['pre_chg'])}">{pre_worst['symbol']}</div>
    <div class="kpi-sub {cls(pre_worst['pre_chg'])}">{pre_worst['pre_chg']:+.2f}% pre-mkt</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">After-Hours Leader</div>
    <div class="kpi-value {cls(ah_best['ah_chg'])}">{ah_best['symbol']}</div>
    <div class="kpi-sub {cls(ah_best['ah_chg'])}">{ah_best['ah_chg']:+.2f}% AH</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Avg Rel Vol</div>
    <div class="kpi-value">{avg_rv:.2f}x</div>
    <div class="kpi-sub">{spikes} spiking ≥ 2x</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────
def color_pct(val):
    if pd.isna(val) or val == 0: return 'color: #94a3b8'
    return 'color: #16a34a; font-weight:700' if val > 0 else 'color: #dc2626; font-weight:700'

def color_rv(val):
    if val >= 2.0:   return 'color: #dc2626; font-weight:700; background:#fef2f2; border-radius:4px'
    if val >= 1.5:   return 'color: #ea580c; font-weight:700; background:#fff7ed; border-radius:4px'
    if val >= 0.8:   return 'color: #2563eb; font-weight:700; background:#eff6ff; border-radius:4px'
    return 'color: #94a3b8'

# ── Session selector + Rel Vol filter ──────────────────────────────────────
ctrl_col, filt_col = st.columns([2, 1])
with ctrl_col:
    session = st.segmented_control(
        'Session', ['🌅 Pre-Market', '📈 Live', '🌙 After Hours'],
        default='📈 Live', label_visibility='collapsed'
    )
with filt_col:
    min_rv = st.selectbox('Min Rel Vol', [0.0, 0.5, 1.0, 1.5, 2.0], index=0,
                          format_func=lambda x: f'Rel Vol >= {x}x' if x > 0 else 'All Symbols')

if min_rv > 0:
    if session == '🌅 Pre-Market':
        filtered = [r for r in rows if r['pre_rel_vol'] >= min_rv]
    elif session == '🌙 After Hours':
        filtered = [r for r in rows if r['ah_rel_vol'] >= min_rv]
    else:
        filtered = [r for r in rows if r['rel_vol'] >= min_rv]
else:
    filtered = rows

# ── Build view per session ──────────────────────────────────────────────────
if session == '🌅 Pre-Market':
    data = sorted(filtered, key=lambda r: abs(r['pre_chg']), reverse=True)
    df = pd.DataFrame([{
        'Symbol':   r['symbol'], 'Name': NAMES.get(r['symbol'], r['symbol']),
        'Pre Chg%': r['pre_chg'], 'Pre Vol': round(r['pre_vol']/1e6, 2),
        'Rel Vol':  r['pre_rel_vol'],
        'Price':    r['price'],   'Day Chg%': r['chg_pct'],
        'Week %':   r['wk'],      'Month %':  r['mo'],
    } for r in data])
    styled = (df.style
        .map(color_pct, subset=['Pre Chg%', 'Day Chg%', 'Week %', 'Month %'])
        .map(color_rv,  subset=['Rel Vol'])
        .format({'Pre Chg%':'{:+.2f}%','Pre Vol':'{:.2f}M','Rel Vol': lambda v: f'{v:.1f}x' if v > 0 else '—',
                 'Price':'${:,.2f}','Day Chg%':'{:+.2f}%','Week %':'{:+.2f}%','Month %':'{:+.2f}%'}))
    col_cfg = {
        'Symbol':   st.column_config.TextColumn('Symbol',    width=70),
        'Name':     st.column_config.TextColumn('Name',      width=160),
        'Pre Chg%': st.column_config.TextColumn('Pre Chg%', width=90),
        'Pre Vol':  st.column_config.TextColumn('Pre Vol',  width=82),
        'Rel Vol':  st.column_config.TextColumn('Rel Vol',   width=76),
        'Price':    st.column_config.TextColumn('Price',     width=88),
        'Day Chg%': st.column_config.TextColumn('Day Chg%', width=88),
        'Week %':   st.column_config.TextColumn('Wk %',      width=76),
        'Month %':  st.column_config.TextColumn('Mo %',      width=76),
    }

elif session == '🌙 After Hours':
    data = sorted(filtered, key=lambda r: abs(r['ah_chg']), reverse=True)
    df = pd.DataFrame([{
        'Symbol':  r['symbol'], 'Name': NAMES.get(r['symbol'], r['symbol']),
        'AH Chg%': r['ah_chg'], 'AH Vol': round(r['ah_vol']/1e6, 2),
        'Rel Vol': r['ah_rel_vol'],
        'Price':   r['price'],  'Day Chg%': r['chg_pct'],
        'Week %':  r['wk'],     'Month %':  r['mo'],
    } for r in data])
    styled = (df.style
        .map(color_pct, subset=['AH Chg%', 'Day Chg%', 'Week %', 'Month %'])
        .map(color_rv,  subset=['Rel Vol'])
        .format({'AH Chg%':'{:+.2f}%','AH Vol':'{:.2f}M','Rel Vol': lambda v: f'{v:.1f}x' if v > 0 else '—',
                 'Price':'${:,.2f}','Day Chg%':'{:+.2f}%','Week %':'{:+.2f}%','Month %':'{:+.2f}%'}))
    col_cfg = {
        'Symbol':  st.column_config.TextColumn('Symbol',    width=70),
        'Name':    st.column_config.TextColumn('Name',      width=160),
        'AH Chg%': st.column_config.TextColumn('AH Chg%',  width=90),
        'AH Vol':  st.column_config.TextColumn('AH Vol',    width=82),
        'Rel Vol': st.column_config.TextColumn('Rel Vol',   width=76),
        'Price':   st.column_config.TextColumn('Price',     width=88),
        'Day Chg%':st.column_config.TextColumn('Day Chg%',  width=88),
        'Week %':  st.column_config.TextColumn('Wk %',      width=76),
        'Month %': st.column_config.TextColumn('Mo %',      width=76),
    }

else:  # Live
    data = filtered
    _va = [r['rel_vol'] for r in data]
    df = pd.DataFrame([{
        'Symbol':   r['symbol'], 'Name': NAMES.get(r['symbol'], r['symbol']),
        'Price':    r['price'],  'Day Chg%': r['chg_pct'],
        'Vol (M)':  round(r['volume']/1e6, 2),
        'Rel Vol':  r['rel_vol'],
        'Week %':   r['wk'],    'Month %': r['mo'],
    } for r in data])
    va_series = pd.Series(_va, index=df.index)
    styled = (df.style
        .map(color_pct, subset=['Day Chg%', 'Week %', 'Month %'])
        .map(color_rv,  subset=['Rel Vol'])
        .format({'Price':'${:,.2f}','Day Chg%':'{:+.2f}%','Vol (M)':'{:.2f}M',
                 'Rel Vol': lambda v: f'{v:.1f}x' if v > 0 else '—','Week %':'{:+.2f}%','Month %':'{:+.2f}%'})
        .apply(lambda col: ['color: #16a34a; font-weight:700' if va_series.iloc[i] >= 1.0
                            else 'color: #dc2626; font-weight:700' for i in range(len(col))],
               subset=['Vol (M)'], axis=0))
    col_cfg = {
        'Symbol':   st.column_config.TextColumn('Symbol',    width=70),
        'Name':     st.column_config.TextColumn('Name',      width=160),
        'Price':    st.column_config.TextColumn('Price',     width=88),
        'Day Chg%': st.column_config.TextColumn('Day Chg%', width=88),
        'Vol (M)':  st.column_config.TextColumn('Vol',       width=76),
        'Rel Vol':  st.column_config.TextColumn('Rel Vol',   width=76),
        'Week %':   st.column_config.TextColumn('Wk %',      width=76),
        'Month %':  st.column_config.TextColumn('Mo %',      width=76),
    }

st.dataframe(styled, use_container_width=True, hide_index=True, height=560, column_config=col_cfg)

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-footer">
  Data via Yahoo Finance · Last fetched {datetime.now().strftime('%H:%M:%S')} ·
  Rel Vol = today's volume ÷ (avg daily vol × elapsed market fraction)
</div>
""", unsafe_allow_html=True)
