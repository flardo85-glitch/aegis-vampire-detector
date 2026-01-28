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
        self.multi_cell(0, 5, "Analisi matematica basata su dati storici. Non costituisce sollecitazione al pubblico risparmio.", 0, 'C')
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generate_premium_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page()
    
    # Titolo
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(20, 33, 61) 
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.ln(10)

    # Box Verdetto
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, 40, 190, 35, 'F')
    pdf.set_xy(15, 45)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VAMPIRE SCORE: {score}/10', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    status = "CRITICO: Forte erosione in corso." if score > 6 else "INEFFICIENTE: Margini di recupero ampi."
    pdf.cell(0, 10, f"STATO: {status}", 0, 1, 'L')
    pdf.ln(15)

    # Analisi Perdita
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 10, '1. IMPATTO DEI COSTI COMPOSTI', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    analisi = (f"La proiezione a {yrs} anni evidenzia una dispersione patrimoniale di Euro {loss:,.0f}. "
               f"Questo capitale viene sottratto alla tua disponibilità futura a causa di oneri non giustificati.")
    pdf.multi_cell(0, 6, analisi)
    pdf.ln(10)

    # Tabella ISIN
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(20, 33, 61)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(35, 10, ' ISIN', 1, 0, 'L', 1)
    pdf.cell(110, 10, ' STRUMENTO', 1, 0, 'L', 1)
    pdf.cell(45, 10, ' GAP TECNICO *', 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    for item in data_list:
        pdf.cell(35, 10, f" {item['ISIN']}", 1)
        pdf.cell(110, 10, f" {item['Nome'][:50]}", 1)
        if item['Gap Tecnico %'] > 0: 
            pdf.set_text_color(192, 57, 43)
        pdf.cell(45, 10, f"{item['Gap Tecnico %']}% ", 1, 1, 'R')
        pdf.set_text_color(0, 0, 0)
    
    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA DATI ---
vampire_data = {
    "Dato Manuale": 2.2, 
    "Fondi Comuni": 2.2, 
    "Gestioni Patrimoniali": 2.8, 
    "Polizze Unit Linked": 3.5, 
    "Private Banking": 1.8
}

def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages: 
                text += (page.extract_text() or "") + "\n"
        return list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))
    except: 
        return []

def get_performance_data(isin_list):
    results = []
    bench = "SWDA.MI" 
    try:
        b_data = yf.download(bench, period="5y", progress=False)
        b_ret = ((b_data['Close'].iloc[-1] / b_data['Close'].iloc[0]) - 1) * 100
    except: 
        b_ret = 60.0 
    
    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin)
            h = t.history(period="5y")
            if not h.empty:
                f_ret = ((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100
                name = t.info.get('longName', isin)[:50]
                results.append({"ISIN": isin, "Nome": name, "Gap Tecnico %": round(b_ret - f_ret, 2)})
            else:
                results.append({"ISIN": isin, "Nome": "Dato Opaco", "Gap Tecnico %": 0.0})
        except: 
            results.append({"ISIN": isin, "Nome": "N/D", "Gap Tecnico %": 0.0})
    return results, b_ret

# --- INTERFACCIA UTENTE ---
st.title("🛡️ AEGIS: Analizzatore Tecnico di Efficienza")

with st.sidebar:
    st.header("⚙️ Parametri di Audit")
    with st.expander("❓ Guida agli Oneri"):
        st.write("""
        **Dove trovo i costi?**
        Cerca nel KIID o nell'estratto conto 'Oneri annui' o 'Spese correnti'.
        - Fondi bancari: 1.8% - 2.5%
        - Polizze: 3% - 4.5%
        - ETF: 0.05% - 0.2%
        """)
    profile = st.selectbox("Benchmark Profilo:", list(vampire_data.keys()))
    cap = st.number_input("Capitale Investito (€)", value=200000, step=10000)
    ter = st.slider("Oneri Annui Dichiarati (%)", 0.0, 5.0, vampire_data[profile])
    yrs = st.slider("Orizzonte (Anni)", 5, 30, 20)

# Calcoli Proiezione
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b
score_base = round(ter * 2, 1)

up = st.file_uploader("📂 Carica Estratto Conto per Audit ISIN (PDF)", type="pdf")

if up:
    with st.spinner("Analisi dei parassiti in corso..."):
        isins = analyze_pdf(up)
        if isins:
            res, b_ret = get_performance_data(isins)
            st.table(pd.DataFrame(res))
            avg_gap = np.mean([item['Gap Tecnico %'] for item in res])
            score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
            st.subheader(f"📊 Vampire Score: {score}/10")
            
            # --- LEAD WALL ---
            st.divider()
            st.markdown("### 📥 Sblocca la Perizia Tecnica Completa")
            email = st.text_input("Inserisci la tua email per il download:")
            if email and "@" in email:
                pdf_bytes = generate_premium_pdf(res, score, loss, ter, yrs, cap)
                st.download_button(
                    label="📩 Scarica Report Audit (PDF)",
                    data=pdf_bytes,
                    file_name=f"Audit_AEGIS_{datetime.date.today()}.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("Nessun ISIN rilevato. Prova con un PDF differente o inserisci dati manuali.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.metric("DISPERSIONE PATRIMONIALE", f"€{loss:,.0f}", delta=f"-{ter}% cost/anno", delta_color="inverse")
    fig = px.pie(names=['Capitale Finale Netto', 'Oneri e Inefficienze'], 
                 values=[f_b, loss], 
                 hole=0.4, 
                 color_discrete_sequence=['#2ecc71', '#e74c3c'])
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown("### 📢 Analisi del Rischio")
    if score_base > 5:
        st.error(f"Attenzione: i costi del {ter}% stanno distruggendo il tuo interesse composto.")
    else:
        st.success("Costi sotto controllo, ma verifica sempre il Gap Tecnico degli strumenti.")
    st.write("Questo strumento utilizza algoritmi quantitativi per evidenziare ciò che i rendiconti bancari spesso omettono.")
    st.markdown(f"**[📩 Contatta un esperto per un'analisi manuale](mailto:tua_mail@esempio.com?subject=Richiesta%20Audit%20AEGIS)**")
