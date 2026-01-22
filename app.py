import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF
import io

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide", page_icon="🧛")

# --- DATABASE VAMPIRI ---
vampire_data = {
    "Inserimento Manuale": 2.2,
    "Fondi Comuni Bancari (Media 2.2%)": 2.2,
    "Gestioni Patrimoniali Retail (Media 2.8%)": 2.8,
    "Polizze Unit Linked (Media 3.5%)": 3.5,
    "Private Banking (Media 1.8%)": 1.8
}

# --- FUNZIONI ---
def analyze_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))

def get_performance_data(isin_list):
    results = []
    bench = "SWDA.MI" 
    try:
        b_data = yf.download(bench, period="5y", progress=False)
        b_ret = ((b_data['Close'].iloc[-1] / b_data['Close'].iloc[0]) - 1) * 100
    except: b_ret = 60.0
    
    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin)
            h = t.history(period="5y")
            f_ret = ((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100 if not h.empty else 0
            results.append({"ISIN": isin, "Nome": t.info.get('longName', isin), "Gap %": round(b_ret - f_ret, 2)})
        except:
            results.append({"ISIN": isin, "Nome": "Dato Opaco", "Gap %": 0.0})
    return results, b_ret

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Vampire Detector")
st.markdown("### Rivela quanto ti costa realmente la tua banca.")

# Sidebar
bank_profile = st.sidebar.selectbox("Chi gestisce i tuoi soldi?", list(vampire_data.keys()))
cap = st.sidebar.number_input("Capitale Totale (€)", value=200000)
ter = st.sidebar.slider("Costo Annuo (%)", 0.5, 5.0, vampire_data[bank_profile])
yrs = st.sidebar.slider("Anni", 5, 30, 20)

up = st.file_uploader("Carica PDF Estratto Conto", type="pdf")
res = []

if up:
    isins = analyze_pdf(up)
    if isins:
        st.success(f"Rilevati {len(isins)} ISIN")
        res, b_ret = get_performance_data(isins)
        st.table(pd.DataFrame(res))
        
        avg_gap = np.mean([item['Gap %'] for item in res])
        score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
        st.subheader(f"📊 Vampire Score: {score}/10")
        if score > 6.5: st.error("⚠️ LIVELLO: CONTE DRACULA (Pericolo Totale)")
        elif score > 3.5: st.warning("🟡 LIVELLO: VAMPIRO (Allerta)")
        else: st.success("🟢 LIVELLO: PIPISTRELLO (Efficienza)")

st.divider()

# Calcolo Impatto
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b

c1, c2 = st.columns(2)
with c1:
    st.metric("EMORRAGIA PATRIMONIALE", f"€{loss:,.0f}", delta=f"-{ter}%/anno", delta_color="inverse")
    st.markdown(f"**Questo capitale (€{loss:,.0f}) viene sottratto al tuo futuro per alimentare la struttura commerciale della banca.**")
    st.markdown(f"[👉 **FERMA L'EMORRAGIA ORA**](mailto:tuamail@esempio.com?subject=Analisi%20AEGIS&body=Ho%20scoperto%20una%20perdita%20di%20{loss:,.0f}€)")

with c2:
    fig = px.pie(names=['Tuo Patrimonio', 'Regalo alla Banca'], values=[f_b, loss], 
                 color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
