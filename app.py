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

def format_euro_ui(amount):
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def format_euro_pdf(amount):
    val_formattata = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"EUR {val_formattata}"

# --- MOTORE PDF (BLINDATURA TOTALE) ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12); self.set_text_color(100)
        self.cell(0, 10, 'AEGIS | Audit Quantitativo Indipendente', 0, 1, 'L')
        self.line(10, 20, 200, 20); self.ln(10)

    def footer(self):
        self.set_y(-35); self.set_font('helvetica', 'I', 7); self.set_text_color(140)
        disclaimer = (
            "DOCUMENTO TECNICO-INFORMATIVO EX ART. 1, C. 5-SEPTIES E ART. 94 TUF: "
            "Il presente report non costituisce consulenza personalizzata ne' sollecitazione al risparmio. "
            "L'elaborazione si basa su algoritmi matematici applicati a dati storici. "
            "La scelta finale di investimento spetta esclusivamente all'utente previa consultazione dei prospetti (KID)."
        )
        self.multi_cell(0, 4, disclaimer, align='C')

def generate_safe_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page(); pdf.set_font('helvetica', 'B', 20); pdf.set_text_color(20, 33, 61)
    pdf.cell(0, 15, 'REDAZIONE TECNICA DI ANALISI PATRIMONIALE', 0, 1, 'C'); pdf.ln(10)
    
    # Box Indice Inefficienza
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50); pdf.set_font('helvetica', 'B', 14); pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'INDICE DI INEFFICIENZA RILEVATO: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('helvetica', '', 11); pdf.set_text_color(0)
    status = "ALTA (Analisi consigliata)" if score > 6 else "MODERATA (Ottimizzazione possibile)"
    pdf.cell(0, 10, f'GRADO DI DISPERSIONE: {status}', 0, 1, 'L'); pdf.ln(20)

    # Analisi Dispersione
    pdf.set_font('helvetica', 'B', 13); pdf.cell(0, 10, '1. PROIEZIONE MATEMATICA DEGLI ONERI', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"Sulla base dei costi (TER) e del gap tecnico storico, la proiezione a {yrs} anni stima una dispersione potenziale di {format_euro_pdf(loss)} rispetto a parametri di mercato efficienti."); pdf.ln(10)

    # Tabella
    pdf.set_font('helvetica', 'B', 10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255)
    pdf.cell(45, 10, ' ISIN', 1, 0, 'L', 1); pdf.cell(100, 10, ' STRUMENTO', 1, 0, 'L', 1); pdf.cell(45, 10, ' GAP TECNICO %', 1, 1, 'C', 1)
    pdf.set_text_color(0); pdf.set_font('helvetica', '', 9)
    for item in data_list:
        n = item['Nome'].encode('ascii', 'ignore').decode('ascii')
        pdf.cell(45, 10, f" {item['ISIN']}", 1); pdf.cell(100, 10, f" {n[:50]}", 1); pdf.cell(45, 10, f"{float(item['Gap Tecnico %'])}% ", 1, 1, 'R')
    
    # Parametri di Raffronto
    pdf.ln(10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255); pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, ' 2. PARAMETRI DI RAFFRONTO TECNICO', 0, 1, 'L', 1)
    pdf.set_text_color(0); pdf.set_font('helvetica', '', 10); pdf.ln(2)
    if score > 6:
        pdf.multi_cell(0, 6, "I dati indicano che l'efficienza massima teorica per questa tipologia di portafoglio si ottiene attraverso:\n- Riduzione del TER complessivo sotto lo 0.30%.\n- Verifica delle commissioni di retrocessione implicite.\n- Allineamento ai benchmark istituzionali a basso costo.")
    else:
        pdf.multi_cell(0, 6, "L'analisi suggerisce margini di miglioramento tramite:\n- Ottimizzazione dell'efficienza fiscale (minusvalenze).\n- Monitoraggio della correlazione tra gli asset (Soglia < 0.50).\n- Ribilanciamento tecnico periodico.")
    
    return bytes(pdf.output())

# --- LOGICA DI ANALISI ---
def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages: text += (page.extract_text() or "") + "\n"
        finds = re.findall(r'\b[A-Z]{2}[A-Z0-9]{9}[0-9]{1}\b', text)
        return list(set([i for i in finds if sum(c.isdigit() for c in i) >= 3]))
    except: return []

def get_performance_data(isin_list):
    results = []; bench = "SWDA.MI"
    try:
        b = yf.download(bench, period="5y", progress=False)
        br = float(((b['Close'].iloc[-1] / b['Close'].iloc[0]) - 1) * 100) if not b.empty else 65.0
    except: br = 65.0
    for isin in isin_list[:5]:
        t = f"{isin}.MI" if isin.startswith("IT") else isin
        try:
            tk = yf.Ticker(t); h = tk.history(period="5y")
            if h.empty: results.append({"ISIN": isin, "Nome": f"Strumento Rilevato ({isin})", "Gap Tecnico %": 35.0})
            else:
                fr = float(((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100)
                results.append({"ISIN": isin, "Nome": tk.info.get('longName', isin)[:50], "Gap Tecnico %": round(float(br - fr), 2)})
        except: results.append({"ISIN": isin, "Nome": f"Dato non disponibile ({isin})", "Gap Tecnico %": 35.0})
    return results, br

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Audit Quantitativo Indipendente")

with st.container():
    st.error("⚖️ **REDAZIONE TECNICA OBBLIGATORIA EX ART. 1 E 94 TUF**")
    st.caption("**NATURA DELLO STRUMENTO:** Questo algoritmo effettua analisi oggettive di costi e performance passate. Non fornisce raccomandazioni personalizzate.")

with st.sidebar:
    st.header("⚙️ Parametri Audit")
    with st.expander("📊 PARAMETRI DI COSTO MEDIO"):
        st.write("**Efficienza Alta (ETF):** 0.1% - 0.3%")
        st.write("**Efficienza Bassa (Fondi):** 1.8% - 3.5%")
    
    p = st.selectbox("Tipologia:", ["Fondi Comuni", "Polizze Unit Linked", "Gestioni", "Dato Manuale"])
    costs = {"Fondi Comuni": 2.2, "Polizze Unit Linked": 3.8, "Gestioni": 2.2, "Dato Manuale": 2.2}
    cap = st.number_input("Capitale (€)", value=200000)
    ter = st.slider("Costo (TER %)", 0.0, 5.0, costs[p])
    yrs = st.slider("Orizzonte (Anni)", 5, 30, 20)

f_b = cap * ((1.05 - (ter/100))**yrs); f_a = cap * ((1.05 - 0.002)**yrs); loss = f_a - f_b
up = st.file_uploader("📂 Carica documento tecnico (KID)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, b_ret = get_performance_data(isins)
        st.table(pd.DataFrame(res))
        score = round(min((ter * 2) + (np.mean([item['Gap Tecnico %'] for item in res]) / 10), 10), 1)
        st.subheader(f"📊 Indice Inefficienza: {score}/10")
        em = st.text_input("Inserisci mail per il report:")
        if em and "@" in em:
            pdf_data = generate_safe_pdf(res, score, loss, ter, yrs, cap)
            st.download_button("📩 Scarica Report Tecnico", data=pdf_data, file_name="AEGIS_Audit_Report.pdf")
    else: st.warning("Nessun codice identificativo rilevato.")

st.divider(); c1, c2 = st.columns(2)
with c1:
    st.metric("DISPERSIONE STIMATA", format_euro_ui(loss))
    st.plotly_chart(px.pie(names=['Netto Stimato', 'Dispersione Costi'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']))
