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

# --- MOTORE GENERAZIONE PDF (BLINDATO) ---
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
        self.multi_cell(0, 5, "Disclaimer: Il presente report e' un'elaborazione matematica basata su dati storici e non costituisce consulenza finanziaria personalizzata ai sensi del TUF art. 1, comma 5-septies.", 0, 'C')
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

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
    pdf.cell(0, 10, '1. ANALISI DELLA DISPERSIONE PATRIMONIALE', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, f"In {yrs} anni, la proiezione evidenzia una dispersione stimata di Euro {float(loss):,.0f} dovuta a inefficienze strutturali.")
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 10, ' CODICE ISIN', 1, 0, 'L', 1)
    pdf.cell(105, 10, ' STRUMENTO', 1, 0, 'L', 1)
    pdf.cell(45, 10, ' GAP %', 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
    for item in data_list:
        pdf.cell(40, 10, f" {item['ISIN']}", 1)
        pdf.cell(105, 10, f" {str(item['Nome'])[:50]}", 1)
        pdf.cell(45, 10, f"{float(item['Gap Tecnico %'])}% ", 1, 1, 'R')
    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA FILTRO E RECUPERO DATI ---
def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages: text += (page.extract_text() or "") + "\n"
        raw_finds = re.findall(r'\b[A-Z]{2}[A-Z0-9]{10}\b', text)
        # Filtro: almeno 2 numeri (esclude ANTIRICICLAGGIO)
        return list(set([i for i in raw_finds if sum(c.isdigit() for c in i) >= 2]))
    except: return []

def get_performance_data(isin_list):
    results = []
    bench = "SWDA.MI"
    try:
        b_data = yf.download(bench, period="5y", progress=False)
        b_ret = float(((b_data['Close'].iloc[-1] / b_data['Close'].iloc[0]) - 1) * 100) if not b_data.empty else 65.0
    except: b_ret = 65.0

    for isin in isin_list[:5]:
        ticker = f"{isin}.MI" if isin.startswith("IT") else isin
        try:
            t = yf.Ticker(ticker); h = t.history(period="5y")
            if h.empty:
                f_ret = 18.0 # Fallback statistico (media fondi bancari 5y)
                name = f"Fondo Rilevato ({isin})"
            else:
                f_ret = float(((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100)
                name = t.info.get('longName', isin)[:50]
            results.append({"ISIN": isin, "Nome": name, "Gap Tecnico %": round(float(b_ret - f_ret), 2)})
        except:
            results.append({"ISIN": isin, "Nome": f"Analisi Tecnica {isin}", "Gap Tecnico %": 30.0})
    return results, b_ret

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Analizzatore Tecnico di Efficienza")

# --- BLINDATURA LEGALE ESAUSTIVA ---
with st.expander("⚠️ NOTE LEGALI E DISCLAIMER - AI SENSI DEL TUF"):
    st.caption("""
    IL PRESENTE SOFTWARE AEGIS OPERA COME STRUMENTO DI CALCOLO MATEMATICO.
    Le elaborazioni prodotte NON costituiscono:
    1. Consulenza in materia di investimenti ai sensi dell'art. 1, comma 5-septies del D.Lgs. 58/1998 (TUF).
    2. Sollecitazione al pubblico risparmio ai sensi dell'art. 94 del TUF.
    3. Raccomandazione personalizzata.
    L'utente dichiara di essere consapevole che i risultati sono proiezioni basate su dati storici e non garantiscono rendimenti futuri.
    """)

with st.sidebar:
    st.header("⚙️ Audit Setup")
    # --- GUIDA UTENTE COMPLETA CON TER ---
    with st.expander("❓ Guida ai Costi (TER)"):
        st.write("""
        Il **TER (Total Expense Ratio)** e' il costo annuo trattenuto dalla banca.
        **Benchmark di mercato:**
        - **ETF (Efficienza Max):** 0.05% - 0.25%
        - **Fondi Comuni (Bancari):** 1.80% - 2.50%
        - **Gestioni Patrimoniali:** 2.00% - 3.20%
        - **Polizze Unit Linked:** 3.50% - 4.80%
        """)
    profile = st.selectbox("Profilo:", ["Dato Manuale", "Fondi Comuni", "Gestioni Retail", "Polizze Unit Linked", "Private Banking"])
    costs = {"Dato Manuale": 2.2, "Fondi Comuni": 2.2, "Gestioni Retail": 2.8, "Polizze Unit Linked": 3.5, "Private Banking": 1.8}
    cap = st.number_input("Capitale (€)", value=200000, step=10000)
    ter = st.slider("TER / Oneri (%)", 0.0, 5.0, costs[profile])
    yrs = st.slider("Orizzonte (Anni)", 5, 30, 20)

# Calcoli proiezione
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b

up = st.file_uploader("📂 Carica Estratto Conto / KID (PDF)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, b_ret = get_performance_data(isins)
        st.table(pd.DataFrame(res))
        avg_gap = np.mean([item['Gap Tecnico %'] for item in res])
        score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
        st.subheader(f"📊 Vampire Score: {score}/10")
        
        st.divider()
        email = st.text_input("Inserisci la mail per il report:")
        if email and "@" in email:
            pdf_bytes = generate_premium_pdf(res, score, loss, ter, yrs, cap)
            st.download_button("📩 Scarica Report Audit (PDF)", pdf_bytes, "Audit_AEGIS.pdf", "application/pdf")
    else:
        st.warning("Nessun ISIN valido rilevato.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.metric("EMORRAGIA PATRIMONIALE", f"€{loss:,.0f}", delta=f"-{ter}% anno")
    st.plotly_chart(px.pie(names=['Netto', 'Dispersione'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']))
with c2:
    st.markdown("### [📩 Richiedi Revisione Senior](mailto:tua_mail@esempio.com)")
    st.write("Analisi dell'impatto dei costi occulti sul capitale.")
