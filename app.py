import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF
import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AEGIS: Quantitative Audit", layout="wide", page_icon="🛡️")

# --- MOTORE GENERAZIONE PDF ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'AEGIS | Audit Patrimoniale Tecnico', 0, 1, 'L')
        self.line(10, 20, 200, 20)
        self.ln(10)
    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.multi_cell(0, 5, "Disclaimer: Analisi matematica basata su dati storici pubblici. Non costituisce consulenza finanziaria.", 0, 'C')

def generate_premium_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(20, 33, 61) 
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VALUTAZIONE DI EFFICIENZA: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f'STATO: {"CRITICA" if score > 6 else "MIGLIORABILE"}', 0, 1, 'L')
    pdf.ln(20)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 10, 'ANALISI DELLA DISPERSIONE', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, f"La proiezione a {yrs} anni evidenzia una perdita stimata di Euro {float(loss):,.0f}.")
    pdf.ln(10)
    # Tabella
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 10, ' ISIN', 1, 0, 'L', 1)
    pdf.cell(105, 10, ' STRUMENTO', 1, 0, 'L', 1)
    pdf.cell(45, 10, ' GAP %', 1, 1, 'C', 1)
    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
    for item in data_list:
        pdf.cell(40, 10, f" {item['ISIN']}", 1)
        pdf.cell(105, 10, f" {str(item['Nome'])[:50]}", 1)
        pdf.cell(45, 10, f"{float(item['Gap Tecnico %'])}% ", 1, 1, 'R')
    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA FILTRO ISIN MILITARE ---
def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        
        # 1. Trova pattern ISIN (2 lettere + 10 cifre/lettere)
        potential_isins = re.findall(r'\b[A-Z]{2}[A-Z0-9]{10}\b', text)
        
        # 2. Blacklist parole comuni nei KID che sembrano ISIN
        blacklist = ["INFORMATIVA", "SOTTOSCRIZION", "CONSERVAZION", "ANTIRICICLAG", "COOPERAZIONE", "REGOLAMENTO", "INTERNET"]
        
        valid_isins = []
        for isin in potential_isins:
            # Deve avere almeno 2 numeri (un ISIN reale li ha quasi sempre)
            # Non deve essere nella blacklist
            if sum(c.isdigit() for c in isin) >= 2:
                if not any(word in isin for word in blacklist):
                    valid_isins.append(isin)
        
        return list(set(valid_isins))
    except: return []

def get_performance_data(isin_list):
    results = []
    bench = "SWDA.MI" 
    try:
        b_data = yf.download(bench, period="5y", progress=False)
        b_ret = float(((b_data['Close'].iloc[-1] / b_data['Close'].iloc[0]) - 1) * 100)
    except: b_ret = 60.0 
    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin); h = t.history(period="5y")
            f_ret = float(((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100) if not h.empty else 0.0
            name = t.info.get('longName', isin)
            results.append({"ISIN": isin, "Nome": name, "Gap Tecnico %": round(float(b_ret - f_ret), 2)})
        except: pass
    return results, b_ret

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Analizzatore Tecnico di Efficienza")

with st.expander("⚠️ NOTE LEGALI E DISCLAIMER"):
    st.caption("Software di calcolo matematico. Non costituisce consulenza finanziaria.")

with st.sidebar:
    st.header("⚙️ Audit Setup")
    with st.expander("❓ Guida Oneri"):
        st.write("Fondi comuni: 1.8%-2.5% | Polizze: 3%-4.5%")
    cap = st.number_input("Capitale (€)", value=200000, step=10000)
    ter = st.slider("Oneri Annui (%)", 0.0, 5.0, 2.2)
    yrs = st.slider("Anni", 5, 30, 20)

f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b

up = st.file_uploader("📂 Carica KID Eurizon (PDF)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, b_ret = get_performance_data(isins)
        if res:
            st.table(pd.DataFrame(res))
            avg_gap = np.mean([item['Gap Tecnico %'] for item in res])
            score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
            st.subheader(f"📊 Vampire Score: {score}/10")
            
            st.divider()
            email = st.text_input("Inserisci la mail per scaricare l'Audit:")
            if email and "@" in email:
                pdf_bytes = generate_premium_pdf(res, score, loss, ter, yrs, cap)
                st.download_button("📩 Scarica Report Audit (PDF)", pdf_bytes, "Audit_AEGIS.pdf")
        else:
            st.error("Dati di mercato non disponibili per questi codici.")
    else:
        st.warning("Nessun ISIN valido rilevato. Il filtro ha escluso il rumore del documento.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.metric("EMORRAGIA PATRIMONIALE", f"€{loss:,.0f}")
    st.plotly_chart(px.pie(names=['Netto', 'Costi'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']))
with c2:
    st.write("Se lo score supera 5, la banca sta drenando la tua ricchezza.")
