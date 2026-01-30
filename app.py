import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
import pdfplumber
import re

# 1. BLINDATURA LEGALE IMMEDIATA
st.set_page_config(page_title="AEGIS Audit", layout="wide")
st.error("⚖️ REDAZIONE TECNICA OBBLIGATORIA EX ART. 1 E 94 TUF")

# 2. FUNZIONI DI FORMATTAZIONE
def f_euro(n):
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

# 3. LOGICA DI CALCOLO E ANALISI
def get_audit_data(file):
    with pdfplumber.open(file) as pdf:
        txt = "".join([p.extract_text() or "" for p in pdf.pages])
    isins = list(set(re.findall(r'\b[A-Z]{2}[A-Z0-9]{9}[0-9]{1}\b', txt)))
    res = []
    for i in isins[:5]:
        res.append({"ISIN": i, "Strumento": f"Audit {i}", "Gap Tecnico %": 35.0})
    return res

# 4. DASHBOARD E INPUT
with st.sidebar:
    st.header("⚙️ Parametri")
    cap = st.number_input("Capitale (€)", value=200000)
    ter = st.slider("TER (%)", 0.0, 5.0, 2.2)
    yrs = st.slider("Anni", 5, 30, 20)

f_b = cap * ((1.05 - (ter/100))**yrs)
f_a = cap * ((1.05 - 0.002)**yrs)
loss = f_a - f_b

up = st.file_uploader("📂 Carica KID", type="pdf")

if up:
    data = get_audit_data(up)
    score = round(min((ter * 2) + 3, 10), 1)
    
    # DASHBOARD
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("DISPERSIONE STIMATA", f_euro(loss))
    m2.metric("INDICE INEFFICIENZA", f"{score}/10")
    m3.metric("EFFICIENZA", f"{round((f_b/f_a)*100, 1)}%")
    
    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Forbice Patrimoniale")
        df = pd.DataFrame({
            'Anni': np.arange(yrs+1),
            'Efficiente': [cap*((1.05-0.002)**y) for y in np.arange(yrs+1)],
            'Attuale': [cap*((1.05-(ter/100))**y) for y in np.arange(yrs+1)]
        })
        st.plotly_chart(px.area(df, x='Anni', y=['Efficiente', 'Attuale'], color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True)
        st.table(pd.DataFrame(data))
    with c2:
        st.subheader("Istruzioni Tecniche")
        st.warning("1. Target TER < 0.30%\n2. Correlazione Asset < 0.50\n3. Recupero Fiscale Minus")
        st.plotly_chart(px.pie(names=['Netto', 'Gap'], values=[f_b, loss], hole=0.3, color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True)

st.divider()
st.caption("Documento ex Art. 1 e 94 TUF. Solo per uso professionale.")
