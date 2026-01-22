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

# --- FUNZIONI DI BACKEND ---

def get_vix_status():
    try:
        data = yf.download('^VIX', period="2d", interval="1d", auto_adjust=True)
        if data.empty: return 20.0, "UNKNOWN", "⚪"
        vix = float(data['Close'].iloc[-1])
        if vix < 15: return vix, "LOW (Compiacenza)", "🟢"
        if vix < 25: return vix, "MEDIUM (Incertezza)", "🟡"
        return vix, "HIGH (PANICO)", "🔴"
    except:
        return 20.0, "ERRORE", "⚪"

def analyze_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    isins = list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))
    return isins

def get_isin_info_and_performance(isin_list):
    results = []
    benchmark_ticker = "SWDA.MI" # iShares MSCI World
    try:
        b_data = yf.download(benchmark_ticker, period="5y")['Close']
        b_ret = ((b_data.iloc[-1] / b_data.iloc[0]) - 1) * 100
    except:
        b_ret = None

    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin)
            name = t.info.get('longName', f"Fondo ({isin})")
            hist = t.history(period="5y")
            if not hist.empty:
                f_ret = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
                gap = b_ret - f_ret if b_ret else 0
                results.append({"ISIN": isin, "Nome": name, "Resa 5a (%)": round(f_ret, 2), "Gap vs Mercato (%)": round(gap, 2)})
            else:
                results.append({"ISIN": isin, "Nome": name, "Resa 5a (%)": "N/D", "Gap vs Mercato (%)": "N/D"})
        except:
            results.append({"ISIN": isin, "Nome": "Privato/Non Quotato", "Resa 5a (%)": "N/D", "Gap vs Mercato (%)": "N/D"})
    return results, b_ret

def generate_pdf_report(capital, loss, years, bank_ter_perc, isins, vix_val):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "AEGIS: REPORT ANALISI PATRIMONIALE", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Capitale Analizzato: Euro {capital:,.2f}", ln=True)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(200, 10, f"PERDITA STIMATA: Euro {loss:,.2f}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.cell(200, 10, "Strumenti Rilevati:", ln=True)
    for i in isins:
        pdf.cell(200, 8, f"- {i}", ln=True)
    pdf.ln(20)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "DISCLAIMER: Questo report ha scopo puramente informativo. Non costituisce consulenza finanziaria.")
    return pdf.output()

# --- INTERFACCIA UTENTE ---

st.title("🛡️ AEGIS: Vampire Detector")

with st.expander("⚖️ AVVISO LEGALE E PRIVACY"):
    st.warning("AEGIS e' un simulatore matematico. I dati non vengono salvati. Non e' consulenza finanziaria.")

vix_val, risk_level, icon = get_vix_status()
st.info(f"STATUS MERCATO: {icon} {risk_level} (VIX: {vix_val:.2f})")

# Sidebar
st.sidebar.header("⚙️ Configurazione")
capital = st.sidebar.number_input("Capitale Totale (€)", value=200000)
bank_ter_input = st.sidebar.slider("Costo Annuo Banca (%)", 0.5, 5.0, 2.2)
years = st.sidebar.slider("Anni", 5, 30, 20)

# Main
st.subheader("📂 Analisi Estratto Conto")
uploaded_pdf = st.file_uploader("Carica PDF bancario", type="pdf")

found_isins = []
if uploaded_pdf:
    found_isins = analyze_pdf(uploaded_pdf)
    if found_isins:
        st.success(f"Trovati {len(found_isins)} codici ISIN.")
        st.write("### 🔍 Identikit dei Vampiri e Performance")
        with st.spinner("Analisi rendimenti storici..."):
            dettagli, b_ret = get_isin_info_and_performance(found_isins)
            st.table(pd.DataFrame(dettagli))
            if b_ret:
                st.caption(f"Nota: Il benchmark MSCI World ha reso il {b_ret:.2f}% negli ultimi 5 anni.")

# Calcoli Impatto
st.divider()
mkt_ret = 0.05
etf_ter = 0.002
final_bank = capital * ((1 + mkt_ret - (bank_ter_input/100))**years)
final_aegis = capital * ((1 + mkt_ret - etf_ter)**years)
loss = final_aegis - final_bank

col1, col2 = st.columns(2)
with col1:
    st.metric("PATRIMONIO PERSO", f"€{loss:,.0f}", delta=f"-{bank_ter_input}%/anno", delta_color="inverse")
    if st.button("Genera Report Ufficiale"):
        try:
            report_data = generate_pdf_report(capital, loss, years, bank_ter_input, found_isins, vix_val)
            st.download_button(label="💾 SCARICA PDF", data=report_data, file_name="Analisi_AEGIS.pdf", mime="application/pdf")
            st.balloons()
        except Exception as e:
            st.error(f"Errore: {e}")

with col2:
    fig = px.pie(values=[final_bank, loss], names=['Tuo Patrimonio', 'Costi Banca'], 
                 color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=.3, title="Ripartizione Capitale Finale")
    st.plotly_chart(fig, use_container
