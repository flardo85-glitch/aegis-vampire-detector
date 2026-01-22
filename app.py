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
    pdf.set_text_color(200, 0, 0)
    pdf.cell(200, 10, f"PERDITA STIMATA: Euro {loss:,.2f}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.cell(200, 10, f"Orizzonte: {years} anni | Costo Banca: {bank_ter_perc}%", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "Strumenti Rilevati (Vampiri):", ln=True)
    pdf.set_font("Arial", "", 10)
    for i in isins:
        pdf.cell(200, 8, f"- {i}", ln=True)
    pdf.ln(20)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "DISCLAIMER LEGALE: Questo report ha scopo puramente informativo e matematico. Non costituisce consulenza finanziaria personalizzata ai sensi della normativa vigente.")
    return pdf.output()

# --- INTERFACCIA UTENTE ---

st.title("🛡️ AEGIS: Vampire Detector")

# 1. LO SCUDO LEGALE (Sempre visibile)
with st.expander("⚖️ AVVISO LEGALE E DISCLAIMER (LEGGERE ATTENTAMENTE)"):
    st.warning("""
    **ATTENZIONE:** AEGIS è un simulatore matematico. 
    1. I risultati non sono consigli di investimento. 
    2. I dati OCR possono contenere errori: verifica sempre i codici ISIN. 
    3. Non carichiamo né salviamo i tuoi dati sensibili sui nostri server.
    """)

# 2. STATUS MERCATO
vix_val, risk_level, icon = get_vix_status()
st.info(f"STATUS: {icon} {risk_level} (VIX: {vix_val:.2f})")

# 3. SIDEBAR PARAMETRI
st.sidebar.header("⚙️ Configurazione")
capital = st.sidebar.number_input("Capitale Totale (€)", value=200000)
bank_ter_input = st.sidebar.slider("Costo Annuo Banca (%)",
