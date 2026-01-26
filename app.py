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

# --- CLASSE REPORT PDF (MOTORE PSICOLOGICO) ---
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
        self.multi_cell(0, 5, "Disclaimer: Il presente report è un'elaborazione matematica di dati storici e non costituisce consulenza finanziaria personalizzata ai sensi del TUF.", 0, 'C')
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
    status_msg = "CRITICA: Il patrimonio è soggetto a un'erosione strutturale severa." if score > 6 else "INEFFICIENTE: Margini di miglioramento rilevati."
    pdf.cell(0, 10, f'STATO: {status_msg}', 0, 1, 'L')
    pdf.ln(20)

    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 10, '1. IL COSTO DEL SILENZIO (ANALISI COMPOSITA)', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    analisi_psico = (
        f"Al termine di {yrs} anni, il modello matematico prevede una dispersione di Euro {loss:,.0f}. "
        f"Questa non è una 'spesa di servizio', ma un trasferimento di ricchezza netto. "
        f"Mentre il mercato globale cresce, una quota del {ter}% annuo agisce come un freno costante."
    )
    pdf.multi_cell(0, 6, analisi_psico)
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, '2. DETTAGLIO ANALITICO DEGLI STRUMENTI', 0, 1, 'L')
    pdf.set_fill_color(20, 33, 61)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(35, 10, ' CODICE ISIN', 1, 0, 'L', 1)
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
    pdf.cell(0, 10, 'STRATEGIA DI RECUPERO PATRIMONIALE', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    conclusione = (
        "La soluzione non risiede nel 'prevedere il mercato', ma nell'eliminare le inefficienze certificate. "
        f"Il recupero potenziale sul tuo capitale è di circa Euro {loss*0.8:,.0f}."
    )
    pdf.multi_cell(0, 6, conclusione)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA CORE ---
vampire_data = {
    "Dato Manuale": 2.2,
    "Benchmark Fondi Comuni": 2.2,
    "Benchmark Gestioni Retail": 2.8,
    "Benchmark Polizze Unit Linked": 3.5,
    "Benchmark Private Banking": 1.8
}

def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
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
            if not h.empty:
                f_ret = ((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100
                results.append({"ISIN": isin, "Nome": t.info.get('longName', isin), "Gap Tecnico %": round(b_ret - f_ret, 2)})
            else:
                results.append({"ISIN": isin, "Nome": "Dato Opaco", "Gap Tecnico %": 0.0})
        except:
            results.append({"ISIN": isin, "Nome": "N/D", "Gap Tecnico %": 0.0})
    return results, b_ret

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Analizzatore Tecnico di Efficienza")
st.info("⚠️ **DISCLAIMER TECNICO OBBLIGATORIO**")
st.caption("AEGIS è un software di calcolo matematico. Non costituisce consulenza finanziaria.")

st.sidebar.header("⚙️ Input Dati Tecnici")
profile = st.sidebar.selectbox("Profilo di Benchmark:", list(vampire_data.keys()))
cap = st.sidebar.number_input("Capitale in Analisi (€)", value=200000, step=10000)
ter = st.sidebar.slider("Oneri Annui Dichiarati (%)", 0.5, 5.0, vampire_data[profile])
yrs = st.sidebar.slider("Orizzonte di Calcolo (Anni)", 5, 30, 20)

# Calcolo Matematico Preventivo
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b
score = round(ter * 2, 1)
res = []

up = st.file_uploader("📂 Carica Estratto Conto (PDF)", type="pdf")

if up:
    with st.spinner("Analisi in corso..."):
        isins = analyze_pdf(up)
        if isins:
            res, b_ret = get_performance_data(isins)
            st.table(pd.DataFrame(res))
            avg_gap = np.mean([item['Gap Tecnico %'] for item in res])
            score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
            
            st.subheader(f"📊 Vampire Score: {score}/10")
            
            # GENERAZIONE PDF
            pdf_bytes = generate_premium_pdf(res, score, loss, ter, yrs, cap)
            st.download_button(
                label="📩 Scarica Perizia Tecnica Ufficiale (PDF)",
                data=pdf_bytes,
                file_name=f"Analisi_AEGIS_{datetime.date.today()}.pdf",
                mime="application/pdf"
            )

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.metric("COSTO OPPORTUNITÀ TOTALE", f"€{loss:,.0f}", delta=f"-{ter}% cost/anno", delta_color="inverse")
    st.markdown(f"### [📩 Richiedi Intervento](mailto:tua_mail@esempio.com?subject=Analisi%20AEGIS&body=Score%20rilevato:%20{score})")

with c2:
    fig = px.pie(names=['Patrimonio Netto', 'Oneri e Inefficienze'], values=[f_b, loss], 
                 color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
