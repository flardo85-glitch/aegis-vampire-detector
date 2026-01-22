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

# --- LOGICA DI BACKEND ---

def get_vix_status():
    """Recupera il VIX per misurare la paura del mercato"""
    try:
        data = yf.download('^VIX', period="2d", interval="1d", auto_adjust=True)
        vix = float(data['Close'].iloc[-1])
        if vix < 15: return vix, "LOW (Compiacenza)", "🟢"
        if vix < 25: return vix, "MEDIUM (Incertezza)", "🟡"
        return vix, "HIGH (PANICO)", "🔴"
    except:
        return 20.0, "ERRORE CONNESSIONE", "⚪"

def analyze_pdf(pdf_file):
    """Estrae codici ISIN univoci dal PDF"""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))

def get_performance_data(isin_list):
    """Confronta rendimenti ISIN vs MSCI World (Benchmark)"""
    results = []
    bench_ticker = "SWDA.MI"
    try:
        b_data = yf.download(bench_ticker, period="5y")['Close']
        b_ret = ((b_data.iloc[-1] / b_data.iloc[0]) - 1) * 100
    except:
        b_ret = 60.0 # Fallback storico medio 5 anni
    
    for isin in isin_list[:5]: # Limitiamo a 5 per performance
        try:
            t = yf.Ticker(isin)
            name = t.info.get('longName', f"Fondo {isin}")
            h = t.history(period="5y")
            if not h.empty:
                f_ret = ((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100
                gap = b_ret - f_ret
                results.append({
                    "ISIN": isin, 
                    "Nome": name, 
                    "Resa 5a %": round(f_ret, 2), 
                    "Gap %": round(gap, 2)
                })
            else:
                results.append({"ISIN": isin, "Nome": name, "Resa 5a %": 0.0, "Gap %": 0.0})
        except:
            results.append({"ISIN": isin, "Nome": "Dato Privato/Bancario", "Resa 5a %": 0.0, "Gap %": 0.0})
    return results, b_ret

def make_pdf(capital, loss, years, bank_ter, isin_data):
    """Genera Report PDF Professionale"""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(200, 20, "AEGIS: REPORT IMPATTO PATRIMONIALE", ln=True, align='C')
    pdf.ln(10)
    
    # Sintesi Costi
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, "1. ANALISI DEI COSTI DI GESTIONE", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 8, f"Capitale Analizzato: Euro {capital:,.2f}", ln=True)
    pdf.cell(200, 8, f"Costo Annuo Stimato: {bank_ter}%", ln=True)
    pdf.cell(200, 8, f"Orizzonte Temporale: {years} anni", ln=True)
    
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(200, 12, f"PERDITA DI CAPITALE STIMATA: Euro {loss:,.2f}", ln=True)
    pdf.ln(10)
    
    # Tabella Intelligence
    if isin_data:
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(200, 10, "2. DETTAGLIO STRUMENTI E GAP DI RENDIMENTO", ln=True)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(35, 8, "ISIN", 1)
        pdf.cell(90, 8, "NOME STRUMENTO", 1)
        pdf.cell(30, 8, "RESA 5A %", 1)
        pdf.cell(30, 8, "GAP MKT %", 1)
        pdf.ln()
        
        pdf.set_font("Arial", "", 8)
        for item in isin_data:
            pdf.cell(35, 8, str(item['ISIN']), 1)
            nome = (str(item['Nome'])[:40] + '..') if len(str(item['Nome'])) > 40 else str(item['Nome'])
