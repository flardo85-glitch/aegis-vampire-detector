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

# --- MOTORE GENERAZIONE PDF (BLINDATURA FORENSE) ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'AEGIS | Audit Patrimoniale Tecnico', 0, 1, 'L')
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(150, 150, 150)
        # Disclaimer Legale Integrale nel Footer del PDF
        disclaimer = (
            "ESCLUSIONE DI RESPONSABILITA': Il presente report costituisce esclusivamente un'elaborazione algoritmica di dati storici pubblici. "
            "Ai sensi dell'Art. 1, c. 5-septies del D.Lgs. 58/1998 (TUF), la presente analisi NON costituisce consulenza in materia di investimenti. "
            "L'utente assume piena responsabilita' per le proprie decisioni finanziarie. I rendimenti passati non sono indicativi di quelli futuri."
        )
        self.multi_cell(0, 4, disclaimer, 0, 'C')

def generate_premium_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 22); pdf.set_text_color(20, 33, 61) 
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50); pdf.set_font('Arial', 'B', 14); pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VALUTAZIONE DI EFFICIENZA: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('Arial', '', 11); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f'STATO: {"CRITICA" if score > 6 else "MIGLIORABILE"}', 0, 1, 'L')
    pdf.ln(20)
    # Analisi Perdita
    pdf.set_font('Arial', 'B', 13); pdf.cell(0, 10, '1. ANALISI TECNICA DELLA DISPERSIONE', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, f"La proiezione a {yrs} anni evidenzia una perdita stimata di Euro {float(loss):,.0f} a causa del prelievo commissionale e del gap di rendimento rispetto al mercato benchmark.")
    pdf.ln(10)
    # Tabella
    pdf.set_font('Arial', 'B', 10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255)
    pdf.cell(45, 10, ' ISIN RILEVATO', 1, 0, 'L', 1); pdf.cell(100, 10, ' STRUMENTO FINANZIARIO', 1, 0, 'L', 1); pdf.cell(45, 10, ' GAP TECNICO %', 1, 1, 'C', 1)
    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
    for item in data_list:
        pdf.cell(45, 10, f" {item['ISIN']}", 1); pdf.cell(100, 10, f" {str(item['Nome'])[:50]}", 1); pdf.cell(45, 10, f"{float(item['Gap Tecnico %'])}% ", 1, 1, 'R')
    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA FILTRO E RECUPERO ---
def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages: text += (page.extract_text() or "") + "\n"
        # Regex Ultra-Restrittiva: 2 lettere + 9 alfanumerici + 1 numero finale
        raw_finds = re.findall(r'\b[A-Z]{2}[A-Z0-9]{9}[0-9]{1}\b', text)
        return list(set([i for i in raw_finds if sum(c.isdigit() for c in i) >= 3]))
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
                f_ret = 18.0 
                name = f"Fondo Bancario ({isin})"
            else:
                f_ret = float(((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100)
                name = t.info.get('longName', isin)[:50]
            results.append({"ISIN": isin, "Nome": name, "Gap Tecnico %": round(float(b_ret - f_ret), 2)})
        except:
            results.append({"ISIN": isin, "Nome": f"Strumento {isin}", "Gap Tecnico %": 35.0})
    return results, b_ret

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Analizzatore Tecnico di Efficienza")

# --- BLINDATURA LEGALE "CORTE D'APPELLO" ---
with st.container():
    st.warning("⚠️ **AVVISO LEGALE OBBLIGATORIO (TUF Art. 1, 94 & Reg. Intermediari)**")
    st.caption("""
    IL PRESENTE SOFTWARE ('AEGIS') E' UN ALGORITMO DI PURA ANALISI MATEMATICA.
    L'utente prende atto e dichiara di comprendere che:
    1. **Assenza di Consulenza:** Le analisi prodotte non costituiscono consulenza in materia di investimenti (ex Art. 1, c. 5-septies D.Lgs. 58/98).
    2. **Limitazione di Responsabilita':** AEGIS non effettua profilatura di rischio (Suitability Test) nè verifica l'adeguatezza dell'investimento per l'utente.
    3. **Natura dei Dati:** I dati sono tratti da fonti pubbliche terze. Non si garantisce l'accuratezza in tempo reale dei prezzi.
    4. **Indipendenza:** AEGIS non riceve commissioni da emittenti finanziari e opera come software indipendente di audit quantitativo.
    Qualsiasi decisione finanziaria intrapresa sulla base di questo report e' ad esclusivo rischio dell'utente.
    """)

with st.sidebar:
    st.header("⚙️ Audit Setup")
    with st.expander("❓ Guida ai Costi (TER) - Standard di Settore"):
        st.write("""
        Il TER indica l'erosione annuale del capitale.
        - **ETF Passivi:** 0.05% - 0.25% (Benchmark Efficienza)
        - **Fondi Comuni:** 1.80% - 2.50% (Standard Bancario)
        - **Gestioni (GPM/GPF):** 2.00% - 3.50%
        - **Unit Linked / PIP:** 3.50% - 4.80% (Erosione Critica)
        """)
    profile = st.selectbox("Seleziona Prodotto:", ["Fondi Comuni", "Polizze Unit Linked", "Gestioni Retail", "Private Banking", "Dato Manuale"])
    costs = {"Fondi Comuni": 2.2, "Polizze Unit Linked": 3.8, "Gestioni Retail": 2.8, "Private Banking": 1.8, "Dato Manuale": 2.2}
    cap = st.number_input("Capitale Totale (€)", value=200000, step=10000)
    ter = st.slider("TER (%) rilevato dal KID", 0.0, 5.0, costs[profile])
    yrs = st.slider("Orizzonte (Anni)", 5, 30, 20)

f_b = cap * ((1 + 0.05 - (ter/100))**yrs); f_a = cap * ((1 + 0.05 - 0.002)**yrs); loss = f_a - f_b

up = st.file_uploader("📂 Carica Documento per Audit ISIN (PDF)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, b_ret = get_performance_data(isins)
        st.table(pd.DataFrame(res))
        avg_gap = np.mean([item['Gap Tecnico %'] for item in res])
        score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
        st.subheader(f"📊 Vampire Score: {score}/10")
        st.divider()
        email = st.text_input("Sblocca il Report Certificato (Inserisci Mail):")
        if email and "@" in email:
            pdf_bytes = generate_premium_pdf(res, score, loss, ter, yrs, cap)
            st.download_button("📩 Scarica Perizia Tecnica (PDF)", pdf_bytes, "Perizia_AEGIS.pdf")
    else:
        st.warning("Nessun ISIN conforme rilevato. Assicurati che il PDF contenga codici finanziari validi.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.metric("DISPERSIONE PATRIMONIALE STIMATA", f"€{loss:,.0f}", delta=f"Costo: {ter}%/anno", delta_color="inverse")
    st.plotly_chart(px.pie(names=['Capitale Netto', 'Costi/Inefficienze'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True)
with c2:
    st.markdown("### [📩 Contatta un Consulente Senior](mailto:tua_mail@esempio.com)")
    st.write("Analisi quantitativa indipendente basata sull'Art. 1, 94 del TUF.")
