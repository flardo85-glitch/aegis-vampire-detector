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
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide")

# --- FUNZIONI CORE ---
def get_vix_status():
    try:
        data = yf.download('^VIX', period="2d", interval="1d", auto_adjust=True)
        vix = float(data['Close'].iloc[-1])
        if vix < 15: return vix, "LOW (Compiacenza)", "🟢"
        if vix < 25: return vix, "MEDIUM (Incertezza)", "🟡"
        return vix, "HIGH (PANICO)", "🔴"
    except:
        return 20.0, "ERRORE CONNESSIONE", "⚪"

def analyze_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))

def get_performance(isin_list):
    results = []
    bench = "SWDA.MI"
    try:
        b_data = yf.download(bench, period="5y")['Close']
        b_ret = ((b_data.iloc[-1] / b_data.iloc[0]) - 1) * 100
    except:
        b_ret = 60.0 # Fallback statistico mkt
    
    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin)
            name = t.info.get('longName', f"Fondo {isin}")
            h = t.history(period="5y")
            f_ret = ((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100 if not h.empty else 0
            results.append({"ISIN": isin, "Nome": name, "Resa 5a %": round(f_ret, 2), "Gap %": round(b_ret - f_ret, 2)})
        except:
            results.append({"ISIN": isin, "Nome": "Dato Privato", "Resa 5a %": 0, "Gap %": 0})
    return results

def make_pdf(capital, loss, years, isins):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "AEGIS: ANALISI IMPATTO PATRIMONIALE", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Capitale: Euro {capital:,.2f}", ln=True)
    pdf.cell(200, 10, f"Perdita stimata: Euro {loss:,.2f}", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 5, "DISCLAIMER: Documento informativo. Non costituisce consulenza finanziaria.")
    return pdf.output()

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Vampire Detector")

with st.expander("⚖️ AVVISO LEGALE"):
    st.warning("Simulatore matematico. I dati non vengono salvati.")

vix, level, icon = get_vix_status()
st.info(f"STATUS: {icon} {level} (VIX: {vix:.2f})")

cap = st.sidebar.number_input("Capitale (€)", value=200000)
ter = st.sidebar.slider("Costo Banca (%)", 0.5, 5.0, 2.2)
yrs = st.sidebar.slider("Anni", 5, 30, 20)

up = st.file_uploader("Carica PDF", type="pdf")
isins_found = []

if up:
    isins_found = analyze_pdf(up)
    if isins_found:
        st.success(f"Trovati {len(isins_found)} ISIN")
        res = get_performance(isins_found)
        st.table(pd.DataFrame(res))

st.divider()
final_b = cap * ((1 + 0.05 - (ter/100))**yrs)
final_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = final_a - final_b

c1, c2 = st.columns(2)
c1.metric("PERDITA TOTALE", f"€{loss:,.0f}")
fig = px.pie(values=[final_b, loss], names=['Patrimonio', 'Costi'], hole=0.3)
c2.plotly_chart(fig, use_container_width=True)

if st.button("Genera Report PDF"):
    report = make_pdf(cap, loss, yrs, isins_found)
    st.download_button("💾 SCARICA PDF", data=report, file_name="AEGIS_Report.pdf")
