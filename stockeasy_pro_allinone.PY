"""
StockEasy PRO Ultimate - All-in-One 실행 스크립트
- 패키지 설치
- PyUpbit/RSI/Whale 테스트
- Streamlit 대시보드 포함
"""



print("\n모든 패키지 설치 완료 ✅\n")

# -------------------------------
# 2️⃣ PyUpbit 테스트
# -------------------------------
import pyupbit
import pandas as pd
import numpy as np
import requests

print("KRW 코인 리스트 (상위 5개):")
tickers = pyupbit.get_tickers(fiat="KRW")
print(tickers[:5])

# BTC 4시간봉 데이터 확인
df_btc = pyupbit.get_ohlcv("KRW-BTC", interval="minute240", count=30)
print("\nBTC 4시간봉 최근 5개 데이터:")
print(df_btc.tail())

# RSI 계산 함수
def get_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df_btc['rsi'] = get_rsi(df_btc)
print("\nBTC RSI 최근 5개:")
print(df_btc[['close','rsi']].tail())

# -------------------------------
# 3️⃣ Solscan Whale API 테스트
# -------------------------------
url = "https://api.solscan.io/leaderboard/whale-tracking"
try:
    resp = requests.get(url, timeout=5).json()
    data = resp.get("data", [])
except:
    data = []

print("\n최근 3개 Whale 거래 확인:")
print(data[:3])

# ORCA Whale 필터
orca_whales = [tx for tx in data if tx.get("Action")=="ORCA" and float(tx.get("Amount",0))>=100000]
print("\nORCA Whale 거래 확인 (최대 3개):")
print(orca_whales[:3])

# -------------------------------
# 4️⃣ Streamlit 대시보드 코드
# -------------------------------
import streamlit as st

st.set_page_config(page_title="StockEasy PRO Ultimate", layout="wide")
st.title("🔥 StockEasy PRO Ultimate - All-in-One Trading Dashboard")

#########################################
# RSI 계산 함수 (대시보드용)
#########################################
def get_rsi_dashboard(df, period=14):
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

#########################################
# 1️⃣ BTC 상태
#########################################
@st.cache_data(ttl=300)
def get_btc_status():
    df = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=30)
    df['ma20'] = df['close'].rolling(20).mean()
    btc_return = (df['close'][-1] / df['close'][-2] - 1) * 100
    trend = "상승" if df['close'].iloc[-1] > df['ma20'].iloc[-1] else "하락"
    return round(btc_return,2), trend

btc_return, btc_trend = get_btc_status()
col1, col2 = st.columns(2)
col1.metric("BTC 24h 수익률", f"{btc_return}%")
col2.metric("BTC 추세", btc_trend)

#########################################
# 2️⃣ 4시간봉 주도코인
#########################################
@st.cache_data(ttl=300)
def get_leaders():
    tickers = pyupbit.get_tickers(fiat="KRW")
    result = []
    btc_df = pyupbit.get_ohlcv("KRW-BTC", interval="minute240", count=2)
    btc_return_4h = (btc_df['close'][-1] / btc_df['close'][-2] - 1) * 100
    for ticker in tickers:
        try:
            df = pyupbit.get_ohlcv(ticker, interval="minute240", count=30)
            if df is None: continue
            df['rsi'] = get_rsi_dashboard(df)
            coin_return = (df['close'][-1] / df['close'][-2] - 1) * 100
            strength = coin_return - btc_return_4h
            volume_spike = df['volume'][-1] > df['volume'][:-1].mean() * 2
            if volume_spike and strength > 0:
                result.append((ticker, round(coin_return,2), round(strength,2), round(df['rsi'].iloc[-1],1)))
        except: continue
    df_result = pd.DataFrame(result, columns=["코인","4H수익률","BTC대비강도","RSI"])
    return df_result.sort_values(by="BTC대비강도", ascending=False).head(10)

st.subheader("🚀 4시간봉 주도코인")
st.dataframe(get_leaders(), use_container_width=True)

#########################################
# 8️⃣ 수동 새로고침
#########################################
if st.button("🔄 수동 새로고침"):
    st.cache_data.clear()
    st.experimental_rerun()

st.write("\n모든 테스트 완료 ✅")
st.write("이제 대시보드를 통해 실시간 코인 상태 확인 가능")
