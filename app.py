import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AEGIS: Quantitative Audit", layout="wide", page_icon="🛡️")

# --- FORMATTAZIONE CONTABILE ITALIANA ---
def format_euro_ui(amount):
    """Visualizzazione nell'interfaccia Streamlit con simbolo €"""
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def format_euro_pdf(amount):
    """Visualizzazione nel PDF con standard istituzionale EUR"""
    return "EUR " + f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- MOTORE PDF (BLINDATURA E FIX CARATTERI) ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'AEGIS | Audit Patrimoniale Tecnico', 0, 1, 'L')
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-30)
        self.set_font('helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        # Disclaimer pulito da caratteri speciali problematici
        disclaimer = (
            "ESCLUSIONE DI RESPONSABILITA' EX ART. 1, 94 TUF: Il presente report e' un'elaborazione algoritmica di dati storici pubblici. "
            "Non costituisce sollecitazione al pubblico risparmio ne' consulenza personalizzata. "
            "AEGIS declina ogni responsabilita' per decisioni basate su questo documento."
        )
        self.multi_cell(0, 4, disclaimer, align='C')

def generate_premium_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 22); pdf.set_text_color(20, 33, 61) 
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.ln(10)
    
    # Box Verdetto
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50); pdf.set_font('helvetica', 'B', 14); pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VALUTAZIONE DI EFFICIENZA: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('helvetica', '', 11); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f'STATO: {"CRITICA" if score > 6 else "MIGLIORABILE"}', 0, 1, 'L')
    pdf.ln(20)

    # Analisi Perdita (Accounting Style)
    loss_txt = format_euro_pdf(loss)
    pdf.set_font('helvetica', 'B', 13); pdf.cell(0, 10, '1. ANALISI TECNICA DELLA DISPERSIONE', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"In un orizzonte di {yrs} anni, la proiezione evidenzia una dispersione stimata di {loss_txt} dovuta a inefficienze commissionali e gap di mercato.")
    pdf.ln(10)

    # Tabella
    pdf.set_font('helvetica', 'B', 10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255)
    pdf.cell(45, 10, ' ISIN RILEVATO', 1, 0, 'L', 1)
    pdf.cell(100, 10, ' STRUMENTO FINANZIARIO', 1, 0, 'L', 1)
    pdf.cell(45, 10, ' GAP TECNICO %', 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font('helvetica', '', 9)
    for item in data_list:
        nome_pulito = item['Nome'].encode('ascii', 'ignore').decode('ascii')
        pdf.cell(45, 10, f" {item['ISIN']}", 1)
        pdf.cell(100, 10, f" {nome_pulito[:50]}", 1)
        pdf.cell(45, 10, f"{float(item['Gap Tecnico %'])}% ", 1, 1, 'R')
    
    return bytes(pdf.output())

# --- LOGICA FILTRO ---
def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages: text += (page.extract_text() or "") + "\n"
        raw_finds = re.findall(r'\b[A-Z]{2}[A-Z0-9]{9}[0-9]{1}\b', text)
        return list(set([i for i in raw_finds if sum(c.isdigit() for c in i) >= 3]))
    except: return []

def get_performance_data(isin_list):
    results = []
    bench = "SWDA.MI"
    try:
        b_data = yf.download(bench, period="5y", progress=False)
        b_ret = float(((b_data['Close'].iloc[-1] / b_data['Close'].iloc[0]) - 1) * 100) if not b_data.empty else 65.0
    except: b_ret =
