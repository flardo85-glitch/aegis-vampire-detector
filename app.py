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

# --- BACKEND ---
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

def generate_pdf_report(capital, loss, years, bank_ter_perc, isins, vix_val):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "AEGIS: REPORT ANALISI", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Capitale: Euro {capital:,.2f}", ln=True)
    pdf.cell(200, 10, f"Perdita stimata: Euro {loss:,.2f}", ln=True)
    pdf.cell(200, 10, f"Anni: {years}", ln=True)
    pdf.cell(200, 10, f"Costo banca: {bank_ter_perc}%", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, "ISIN Rilevati:", ln=True)
    for i in isins[:15]:
        pdf.cell(200, 8, f"- {i}", ln=True)
    return pdf.output()

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Vampire Detector")

vix_val, risk_level, icon = get_vix_status()
st.info(f"STATUS: {icon} {risk_level} (VIX: {vix_val:.2f})")

capital = st.sidebar.number_input("Capitale (€)", value=200000)
bank_ter_input = st.sidebar.slider("Costo Banca (%)", 0.5, 5.0, 2.2)
years = st.sidebar.slider("Anni", 5, 30, 20)

uploaded_pdf = st.file_uploader("Carica PDF", type="pdf")
found_isins = []
if uploaded_pdf:
    found_isins = analyze_pdf(uploaded_pdf)
    st.success(f"Trovati {len(found_isins)} ISIN")

st.divider()
# Calcoli
mkt_ret = 0.05
etf_ter = 0.002
final_bank = capital * ((1 + mkt_ret - (bank_ter_input/100))**years)
final_aegis = capital * ((1 + mkt_ret - etf_ter)**years)
loss = final_aegis - final_bank

st.metric("PERDITA TOTALE", f"€{loss:,.0f}")

# GENERAZIONE E DOWNLOAD PDF
if st.button("Prepara Report"):
    try:
        report_data = generate_pdf_report(capital, loss, years, bank_ter_input, found_isins, vix_val)
        st.download_button(
            label="💾 SCARICA PDF",
            data=report_data,
            file_name="Analisi_AEGIS.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Errore: {e}")
