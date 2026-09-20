
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
import json
from datetime import datetime

st.set_page_config(
    page_title="Painel de Ações",
    page_icon="📈",
    layout="wide"
)

# Símbolos: B3 usa sufixo .SA no Yahoo Finance
DEFAULTS = {
    "PETR4.SA": {"nome": "Petrobras PN", "compra": 0, "venda": 0},
    "ITUB4.SA": {"nome": "Itaú Unibanco PN", "compra": 0, "venda": 0},
    "PSSA3.SA": {"nome": "Porto Seguro", "compra": 0, "venda": 0},
    "AAPL": {"nome": "Apple", "compra": 0, "venda": 0},
    "MSFT": {"nome": "Microsoft", "compra": 0, "venda": 0},
    "NVDA": {"nome": "NVIDIA", "compra": 0, "venda": 0},
}

st.title("📈 Painel de Ações")
st.caption("Monitoramento de mercado e alertas — não executa ordens.")

if "symbols" not in st.session_state:
    st.session_state.symbols = list(DEFAULTS)

if "targets" not in st.session_state:
    st.session_state.targets = DEFAULTS.copy()

with st.sidebar:
    st.header("Configurações")

    novo = st.text_input(
        "Adicionar ticker",
        placeholder="Ex.: VALE3.SA ou AMZN"
    ).upper().strip()

    if st.button("Adicionar ação") and novo:
        if novo not in st.session_state.symbols:
            st.session_state.symbols.append(novo)
            st.session_state.targets[novo] = {
                "nome": novo, "compra": 0, "venda": 0
            }

    st.divider()
    st.subheader("Atualização")
    intervalo = st.selectbox(
        "Atualizar a cada",
        [1, 5, 15, 30],
        index=1
    )

    st.caption(
        "Os dados podem ter atraso. "
        "Confirme preços na corretora."
    )

@st.cache_data(ttl=60)
def carregar(ticker):
    df = yf.download(
        ticker,
        period="6mo",
        interval="1d",
        progress=False,
        auto_adjust=True
    )

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna(subset=["Close"])
    df["MM20"] = df["Close"].rolling(20).mean()
    df["MM50"] = df["Close"].rolling(50).mean()

    delta = df["Close"].diff()
    ganhos = delta.clip(lower=0)
    perdas = -delta.clip(upper=0)

    media_g = ganhos.ewm(
        alpha=1/14, min_periods=14, adjust=False
    ).mean()
    media_p = perdas.ewm(
        alpha=1/14, min_periods=14, adjust=False
    ).mean()

    rs = media_g / media_p.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df

def enviar_telegram(mensagem):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": chat_id, "text": mensagem},
            timeout=10
        )
        return r.ok
    except requests.RequestException:
        return False

st.subheader("Cotações e indicadores")

for ticker in st.session_state.symbols:
    cfg = st.session_state.targets[ticker]

    with st.expander(
        f"{ticker} — {cfg.get('nome', ticker)}",
        expanded=True
    ):
        df = carregar(ticker)

        if df is None or df.empty:
            st.warning(
                f"Não foi possível obter dados para {ticker}."
            )
            continue

        atual = float(df["Close"].iloc[-1])
        anterior = (
            float(df["Close"].iloc[-2])
            if len(df) > 1 else atual
        )
        variacao = (
            (atual / anterior - 1) * 100
            if anterior else 0
        )

        rsi = df["RSI"].iloc[-1]
        mm20 = df["MM20"].iloc[-1]
        mm50 = df["MM50"].iloc[-1]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Último fechamento", f"{atual:.2f}")
        c2.metric("Variação diária", f"{variacao:.2f}%")
        c3.metric(
            "RSI (14)",
            f"{rsi:.1f}" if pd.notna(rsi) else "—"
        )
        c4.metric(
            "MM20 / MM50",
            f"{mm20:.2f} / {mm50:.2f}"
            if pd.notna(mm20) and pd.notna(mm50)
            else "—"
        )

        st.line_chart(df[["Close", "MM20", "MM50"]])

        st.markdown("**Configurar preços-alvo**")
        a, b = st.columns(2)

        compra = a.number_input(
            "Alertar se cair até",
            min_value=0.0,
            value=float(cfg.get("compra", 0)),
            key=f"buy_{ticker}"
        )
        venda = b.number_input(
            "Alertar se subir até",
            min_value=0.0,
            value=float(cfg.get("venda", 0)),
            key=f"sell_{ticker}"
        )

        st.session_state.targets[ticker]["compra"] = compra
        st.session_state.targets[ticker]["venda"] = venda

        if compra > 0 and atual <= compra:
            st.warning(f"Preço atingiu o alvo de compra: {ticker}")
        if venda > 0 and atual >= venda:
            st.warning(f"Preço atingiu o alvo de venda: {ticker}")

        if pd.notna(rsi):
            if rsi < 30:
                st.info("RSI abaixo de 30: condição frequentemente chamada de sobrevenda.")
            elif rsi > 70:
                st.info("RSI acima de 70: condição frequentemente chamada de sobrecompra.")

        if pd.notna(mm20) and pd.notna(mm50):
            if mm20 > mm50:
                st.caption("MM20 acima da MM50.")
            elif mm20 < mm50:
                st.caption("MM20 abaixo da MM50.")

st.caption(
    f"Última atualização da tela: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
)

if st.button("Atualizar agora"):
    st.cache_data.clear()
    st.rerun()
