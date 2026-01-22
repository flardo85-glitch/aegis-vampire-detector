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
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide", initial_sidebar_state="expanded")

# --- LOGICA DI BACKEND ---

def get_vix_status():
    """Recupera l'indice VIX con gestione robusta del formato yfinance"""
    try:
        data = yf.download('^VIX', period="2d", interval="1d", auto_adjust=True)
        if data.empty: return 20.0, "UNKNOWN", "⚪"
        vix = data['Close'].iloc[-1]
        if isinstance(vix, (pd.Series, pd.DataFrame)): vix = float(vix.iloc[0])
        else: vix = float(vix)
        
        if vix < 15: return vix, "LOW (Compiacenza)", "🟢"
        if vix < 25: return vix, "MEDIUM (Incertezza)", "🟡"
        return vix, "HIGH (PANICO)", "🔴"
    except:
        return 20.0, "ERRORE CONNESSIONE", "⚪"

def analyze_pdf_intelligence(pdf_file):
    """Estrae testo e identifica pattern finanziari (ISIN e Costi)"""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    isins = list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))
    costs = re.findall(r'(\d+[,\.]\d+)\s*%', text)
    return text, isins, costs

def calculate_impact(capital, bank_ter, years=20):
    """Calcola la differenza di patrimonio tra banca ed ETF efficiente"""
    mkt_ret = 0.05
    etf_ter = 0.002
    final_bank = capital * ((1 + mkt_ret - bank_ter)**years)
    final_aegis = capital * ((1 + mkt_ret - etf_ter)**years)
    return final_aegis, final_bank, final_aegis - final_bank

def generate_pdf_report(capital, loss, years, bank_ter_perc, isins, vix_val):
    """Genera un PDF professionale con i risultati dell'analisi"""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(200, 20, "AEGIS: VAMPIRE DETECTOR REPORT", ln=True, align='C')
    pdf.line(10, 30, 200, 30)
    pdf.ln(10)
    
    # Sezione Risultati
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, "1. SINTESI PATRIMONIALE", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"- Capitale Iniziale Analizzato: Euro {capital:,.2f}", ln=True)
    pdf.cell(200, 10, f"- Orizzonte Temporale: {years} anni", ln=True)
    pdf.cell(200, 10, f"- Costo Medio Annuo (TER): {bank_ter_perc}%", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(192, 57, 43) # Rosso
    pdf.cell(200, 10, f"PERDITA COMPOSTA STIMATA: Euro {loss:,.2f}", ln=True)
    
    # Sezione Tecnica
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, "2. ANALISI TECNICA", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"- Status Mercato al momento dell'analisi (VIX): {vix_val:.2f}", ln=True)
    pdf.cell(200, 10, f"- Strumenti (ISIN) Rilevati nel documento: {len(isins)}", ln=True)
    for i in isins[:10]: # Limita a primi 10 per spazio
        pdf.set_font("Arial", "I", 10)
        pdf.cell(200, 8, f"  > {i}", ln=True)
    
    # Footer Legale
    pdf.ln(20)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(100, 100, 100)
    disclaimer = ("DISCLAIMER: Questo report e generato automaticamente da AEGIS e ha scopo puramente "
                  "informativo. Non costituisce consulenza finanziaria personalizzata. I calcoli si "
                  "basano su stime di rendimento e costi dichiarati. Verificare sempre con un "
                  "consulente abilitato prima di ogni decisione.")
    pdf.multi_cell(0, 5, disclaimer)
    
    return pdf.output()

# --- INTERFACCIA UTENTE ---

st.title("🛡️ AEGIS: Vampire Detector")
st.markdown("### L'unica difesa contro l'inefficienza bancaria.")

# 1. DISCLAIMER
with st.expander("⚖️ AVVISO LEGALE E PRIVACY"):
    st.warning("AEGIS analizza i tuoi dati localmente. Non memorizziamo i tuoi PDF. Questo strumento è a scopo educativo e non costituisce consulenza finanziaria.")

# 2. STATUS MERCATO
vix_val, risk_level, icon = get_vix_status()
st.info(f"**SENTIMENT DI MERCATO:** {icon} {risk_level} | VIX: {vix_val:.2f}")

# 3. SIDEBAR
st.sidebar.header("⚙️ Parametri")
capital = st.sidebar.number_input("Capitale Investito (€)", value=200000, step=10000)
bank_ter_input = st.sidebar.slider("TER Annuo Stimato (%)", 0.5, 5.0, 2.2)
years = st.sidebar.slider("Anni di Investimento", 5, 30, 20)
bank_ter = bank_ter_input / 100

# 4. UPLOAD PDF
st.divider()
st.subheader("📂 Caricamento Estratto Conto")
uploaded_pdf = st.file_uploader("Trascina il PDF bancario per l'analisi OCR", type="pdf")

found_isins = []
if uploaded_pdf:
    with st.spinner("Analisi in corso..."):
        text, found_isins, found_costs = analyze_pdf_intelligence(uploaded_pdf)
        st.success(f"Analisi completata. Rilevati {len(found_isins)} codici ISIN.")
        if found_isins:
            st.write(f"Strumenti trovati: `{', '.join(found_isins)}`")

# 5. RISULTATI E GRAFICI
st.divider()
aegis_total, bank_total, loss = calculate_impact(capital, bank_ter, years)

col1, col2, col3 = st.columns(3)
col1.metric("Capitale con AEGIS", f"€{aegis_total:,.0f}")
col2.metric("Capitale in Banca", f"€{bank_total:,.0f}")
col3.metric("PERDITA TOTALE", f"€{loss:,.0f}", delta_color="inverse")

fig = px.bar(x=["Efficienza (AEGIS)", "Banca Tradizionale"], y=[aegis_total, bank_total], 
             title="Erosione del Capitale nel Tempo", color=["AEGIS", "Banca"],
             color_discrete_map={"AEGIS": "#2ecc71", "Banca": "#e74c3c"})
st.plotly_chart(fig, use_container_width=True)

# 6. GENERAZIONE REPORT PDF
st.divider()
st.subheader("📥 Ottieni Prove Schiaccianti")
if st.button("Genera Anteprima Report"):
    try:
        report_bytes = generate_pdf_report(capital, loss, years, bank_ter_input, found_isins, vix_val)
        st.download_button(
            label="💾 SCARICA REPORT PDF UFFICIALE",
            data=
