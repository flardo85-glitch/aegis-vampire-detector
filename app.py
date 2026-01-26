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
st.set_page_config(page_title="AEGIS: Quantitative Detector", layout="wide", page_icon="🛡️")

# --- MOTORE GENERAZIONE REPORT (AUDIT FORENSE) ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'AEGIS | Analisi Tecnica Quantitativa', 0, 1, 'L')
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.multi_cell(0, 5, "Disclaimer: Il presente report è un'elaborazione matematica di dati storici e non costituisce consulenza finanziaria.", 0, 'C')
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generate_premium_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(20, 33, 61) 
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 5, 'Rilasciato dal protocollo algoritmico AEGIS', 0, 1, 'C')
    pdf.ln(10)

    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VALUTAZIONE DI EFFICIENZA: {score}/10', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    msg = "CRITICA: Erosione strutturale severa." if score > 6 else "INEFFICIENTE: Margini di miglioramento rilevati."
    pdf.cell(0, 10, f'STATO: {msg}', 0, 1, 'L')
    pdf.ln(20)

    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 10, '1. ANALISI DEL COSTO OPPORTUNITA', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    analisi = (f"In {yrs} anni, il modello prevede una dispersione di Euro {loss:,.0f}. "
               f"Questa cifra rappresenta il trasferimento di ricchezza dal tuo capitale alla struttura bancaria.")
    pdf.multi_cell(0, 6, analisi)
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(20, 33, 61)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(35, 10, ' ISIN', 1, 0, 'L', 1)
    pdf.cell(110, 10, ' STRUMENTO', 1, 0, 'L', 1)
    pdf.cell(45, 10, ' GAP TECNICO *', 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    for item in data_list:
        pdf.cell(35, 10, f" {item['ISIN']}", 1)
        pdf.cell(110, 10, f" {item['Nome'][:55]}", 1)
        if item['Gap Tecnico %'] > 0: pdf.set_text_color(192, 57, 43)
        pdf.cell(45, 10, f"{item['Gap Tecnico %']}% ", 1, 1, 'R')
        pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'STRATEGIA DI RECUPERO', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, f"L'eliminazione delle inefficienze certificate permetterebbe un recupero potenziale di Euro {loss*0.8:,.0f}.")
    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA DATI ---
vampire_data = {"Dato Manuale": 2.2, "Benchmark Fondi": 2.2, "Benchmark Gestioni Retail": 2.8, "Benchmark Polizze": 3.5, "Benchmark Private": 1.8}

def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages: text += (page.extract_text() or "") + "\n"
        return list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))
    except: return []

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
            name = t.info.get('longName', isin) if h.empty == False else "Dato Opaco"
            results.append({"ISIN": isin, "Nome": name, "Gap Tecnico %": round(b_ret - f_ret, 2)})
        except: results.append({"ISIN": isin, "Nome": "N/D", "Gap Tecnico %": 0.0})
    return results, b_ret

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Analizzatore Tecnico di Efficienza")
st.caption("Software di misurazione quantitativa. Non costituisce consulenza finanziaria.")

with st.sidebar:
    st.header("⚙️ Parametri")
    profile = st.selectbox("Benchmark:", list(vampire_data.keys()))
    cap = st.number_input("Capitale (€)", value=200000, step=10000)
    ter = st.slider("Oneri Annui (%)", 0.5, 5.0, vampire_data[profile])
    yrs = st.slider("Anni", 5, 30, 20)

# Calcoli preventivi
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b
score = round(ter * 2, 1)

up = st.file_uploader("📂 Carica Estratto Conto (PDF)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, b_ret = get_performance_data(isins)
        st.table(pd.DataFrame(res))
        avg_gap = np.mean([item['Gap Tecnico %'] for item in res])
        score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
        st.subheader(f"📊 Vampire Score: {score}/10")
        
        # --- LEAD GENERATION WALL ---
        st.divider()
        st.markdown("### 📥 Sblocca la Perizia Tecnica Completa")
        st.write("Inserisci la tua email per scaricare l'Audit forense dettagliato.")
        u_email = st.text_input("Email", placeholder="tua@email.it")
        
        if u_email and "@" in u_email:
            pdf_bytes = generate_premium_pdf(res, score, loss, ter, yrs, cap)
            st.download_button("📩 Scarica Perizia (PDF)", pdf_bytes, f"Audit_AEGIS_{u_email}.pdf", "application/pdf")
            st.success(f"Analisi pronta per {u_email}. Clicca il tasto sopra.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.metric("EMORRAGIA PATRIMONIALE PROIETTATA", f"€{loss:,.0f}", delta=f"-{ter}% anno", delta_color="inverse")
    st.plotly_chart(px.pie(names=['Netto', 'Costi'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']))
with c2:
    st.markdown(f"### [📩 Contatta un Analista](mailto:tua_mail@esempio.com?subject=Score%20{score})")
    st.write("Se il tuo score è superiore a 5.0, il tuo patrimonio sta finanziando la banca invece del tuo futuro.")
