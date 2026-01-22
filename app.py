import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF
import io

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide")

# --- FUNZIONI DI BACKEND ---

def get_vix_status():
    try:
        data = yf.download('^VIX', period="2d", interval="1d", auto_adjust=True)
        if data.empty: return 20.0, "UNKNOWN", "⚪"
        vix = float(data['Close'].iloc[-1])
        if vix < 15: return vix, "LOW (Compiacenza)", "🟢"
        if vix < 25: return vix, "MEDIUM (Incertezza)", "🟡"
        return vix, "HIGH (PANICO)", "🔴"
    except:
        return 20.0, "ERRORE", "⚪"

def analyze_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    isins = list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))
    return isins

def get_isin_info(isin_list):
    results = []
    for isin in isin_list[:5]:
        try:
            ticker = yf.Ticker(isin)
            name = ticker.info.get('longName', f"Fondo Bancario ({isin})")
            results.append({"ISIN": isin, "Nome Strumento": name})
        except:
            results.append({"ISIN": isin, "Nome Strumento": "Dato non pubblico"})
    return results

def generate_pdf_report(capital, loss, years, bank_ter_perc, isins, vix_val):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "AEGIS: REPORT ANALISI PATRIMONIALE", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Capitale Analizzato: Euro {capital:,.2f}", ln=True)
    pdf.cell(200, 10, f"PERDITA STIMATA: Euro {loss:,.2f}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, "Strumenti Rilevati:", ln=True)
    for i in isins:
        pdf.cell(200, 8, f"- {i}", ln=True)
    return pdf.output()

# --- INTERFACCIA UTENTE ---

st.title("🛡️ AEGIS: Vampire Detector")

# 1. SCUDO LEGALE
with st.expander("⚖️ AVVISO LEGALE E PRIVACY"):
    st.warning("Strumento informativo. Non costituisce consulenza finanziaria. I dati non vengono salvati.")

# 2. STATUS MERCATO
vix_val, risk_level, icon = get_vix_status()
st.info(f"STATUS: {icon} {risk_level} (VIX: {vix_val:.2f})")

# 3. SIDEBAR
st.sidebar.header("⚙️ Configurazione")
capital = st.sidebar.number_input("Capitale Totale (€)", value=200000)
bank_ter_input = st.sidebar.slider("Costo Annuo Banca (%)", 0.5, 5.0, 2.2)
years = st.sidebar.slider("Anni di Investimento", 5, 30, 20)

# 4. ANALISI PDF
st.subheader("📂 Analisi Estratto Conto")
uploaded_pdf = st.file_uploader("Carica il PDF", type="pdf")

found_isins = []
if uploaded_pdf:
    found_isins = analyze_pdf(uploaded_pdf)
    if found_isins:
        st.success(f"Trovati {len(found_isins)} ISIN")
        with st.spinner("Ricerca nomi strumenti..."):
            dettagli = get_isin_info(found_isins)
            st.table(pd.DataFrame(dettagli))

# 5. CALCOLI
st.divider()
mkt_ret = 0.05
etf_ter = 0.002
final_bank = capital * ((1 + mkt_ret - (bank_ter_input/100))**years)
final_aegis = capital * ((1 + mkt_ret - etf_ter)**years)
loss = final_aegis - final_bank

col1, col2 = st.columns(2)
with col1:
    st.metric("PERDITA TOTALE", f"€{loss:,.0f}")
with col2:
    fig = px.pie(values=[final_bank, loss], names=['Tuo Patrimonio', 'Costi Banca'], 
                 color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=.3)
    st.plotly_chart(fig, use_container_width=True)

# 6. REPORT
if st.button("Genera Report Ufficiale"):
    try:
        report_data = generate_pdf_report(capital, loss, years, bank_ter_input, found_isins, vix_val)
        st.download_button(
            label="💾 SCARICA PDF",
            data=report_data,
            file_name="Analisi_AEGIS.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Errore generazione: {e}")
