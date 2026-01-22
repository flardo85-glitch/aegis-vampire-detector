import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide", page_icon="🧛")

# --- LOGICA VAMPIRE SCORE ---
def get_vampire_level(ter, res):
    avg_gap = np.mean([item['Gap %'] for item in res]) if res else 0
    score_ter = min(ter * 2, 5) 
    score_gap = min(avg_gap / 10, 5) if avg_gap > 0 else 0
    total = round(score_ter + score_gap, 1)
    
    if total <= 3.5: return total, "PIPISTRELLO (Efficienza Buona)", "🟢"
    if total <= 6.5: return total, "VAMPIRO COMUNE (Allerta)", "🟡"
    return total, "CONTE DRACULA (Pericolo Totale)", "🔴"

# --- FUNZIONI CORE ---
def analyze_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))

def get_performance_data(isin_list):
    results = []
    bench = "SWDA.MI"
    try:
        b_data = yf.download(bench, period="5y")['Close']
        b_ret = ((b_data.iloc[-1] / b_data.iloc[0]) - 1) * 100
    except: b_ret = 60.0
    
    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin)
            name = t.info.get('longName', f"Fondo {isin}")
            h = t.history(period="5y")
            f_ret = ((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100 if not h.empty else 0
            results.append({"ISIN": isin, "Nome": name, "Gap %": round(b_ret - f_ret, 2)})
        except:
            results.append({"ISIN": isin, "Nome": "Dato Privato (Opaco)", "Gap %": 0.0})
    return results

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Vampire Detector")

# SCUDO LEGALE
with st.expander("⚖️ AVVISO LEGALE E PRIVACY"):
    st.warning("""
    **Simulatore matematico. I dati non vengono salvati.**
    1. Nessun Consiglio Finanziario: i dati sono a scopo puramente informativo.
    2. Privacy: i documenti vengono analizzati in RAM e mai salvati su disco.
    3. Precisione: verificare sempre i dati con il proprio prospetto informativo.
    """)

# SIDEBAR
st.sidebar.header("⚙️ Parametri")
cap = st.sidebar.number_input("Capitale Totale (€)", value=200000)
ter = st.sidebar.slider("Costo Annuo Banca (%)", 0.5, 5.0, 2.2)
yrs = st.sidebar.slider("Orizzonte (Anni)", 5, 30, 20)

# UPLOAD
up = st.file_uploader("Carica PDF per Analisi ISIN", type="pdf")
res = []

if up:
    isins = analyze_pdf(up)
    if isins:
        st.success(f"Rilevati {len(isins)} ISIN")
        res = get_performance_data(isins)
        st.table(pd.DataFrame(res))
        
        score, label, icon = get_vampire_level(ter, res)
        st.subheader(f"📊 Vampire Score: {score}/10")
        st.info(f"{icon} LIVELLO: {label}")

st.divider()
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b

c1, c2 = st.columns(2)
with c1:
    st.metric("PERDITA TOTALE", f"€{loss:,.0f}", delta=f"-{ter}%/anno", delta_color="inverse")
    st.write("Questo capitale è ciò che regali alla banca senza renderti conto.")

with c2:
    fig = px.pie(values=[f_b, loss], names=['Tuo Patrimonio', 'Costi Banca'], 
                 color_discrete_sequence=['#2ecc71',
