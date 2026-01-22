import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF
import io

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide", page_icon="🛡️")

# --- FUNZIONI CORE ---
def get_vix_status():
    try:
        data = yf.download('^VIX', period="2d", interval="1d", auto_adjust=True)
        vix = float(data['Close'].iloc[-1])
        if vix < 15: return vix, "LOW (Compiacenza)", "🟢"
        if vix < 25: return vix, "MEDIUM (Incertezza)", "🟡"
        return vix, "HIGH (PANICO)", "🔴"
    except:
        return 20.0, "DATO NON DISPONIBILE", "⚪"

def analyze_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))

def get_performance_data(isin_list):
    results = []
    bench_ticker = "SWDA.MI"
    try:
        b_data = yf.download(bench_ticker, period="5y")['Close']
        b_ret = ((b_data.iloc[-1] / b_data.iloc[0]) - 1) * 100
    except:
        b_ret = 60.0
    
    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin)
            name = t.info.get('longName', f"Fondo {isin}")
            h = t.history(period="5y")
            f_ret = ((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100 if not h.empty else 0
            results.append({
                "ISIN": isin, 
                "Nome": name, 
                "Resa 5a %": round(f_ret, 2), 
                "Gap %": round(b_ret - f_ret, 2)
            })
        except:
            results.append({"ISIN": isin, "Nome": "Dato Privato", "Resa 5a %": 0.0, "Gap %": 0.0})
    return results, b_ret

def make_pdf(capital, loss, years, bank_ter, isin_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(200, 15, "AEGIS: ANALISI IMPATTO PATRIMONIALE", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, f"Capitale Analizzato: Euro {capital:,.2f}", ln=True)
    pdf.cell(200, 10, f"Costo Annuo Stimato: {bank_ter}%", ln=True)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(200, 10, f"PERDITA STIMATA: Euro {loss:,.2f}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    if isin_data:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 8, "ISIN", 1)
        pdf.cell(100, 8, "NOME STRUMENTO", 1)
        pdf.cell(40, 8, "GAP MKT %", 1)
        pdf.ln()
        pdf.set_font("Arial", "", 8)
        for item in isin_data:
            pdf.cell(40, 8, str(item['ISIN']), 1)
            pdf.cell(100, 8, str(item['Nome'])[:50], 1)
            pdf.cell(40, 8, str(item['Gap %']), 1)
            pdf.ln()
    
    pdf.ln(20)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "Simulatore matematico. I dati non vengono salvati. Non costituisce consulenza finanziaria.")
    return pdf.output()

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Vampire Detector")

with st.expander("⚖️ AVVISO LEGALE E PRIVACY"):
    st.warning("Simulatore matematico. I dati non vengono salvati. Non costituisce consulenza finanziaria.")

vix, level, icon = get_vix_status()
st.info(f"STATUS MERCATO: {icon} {level} (VIX: {vix:.2f})")

cap = st.sidebar.number_input("Capitale Totale (€)", value=200000)
ter = st.sidebar.slider("Costo Annuo Banca (%)", 0.5, 5.0, 2.2)
yrs = st.sidebar.slider("Anni", 5, 30, 20)

up = st.file_uploader("Carica Estratto Conto PDF", type="pdf")
res = []

if up:
    isins = analyze_pdf(up)
    if isins:
        st.success(f"Trovati {len(isins)} ISIN.")
        res, b_ret = get_performance_data(isins)
        st.table(pd.DataFrame(res))

st.divider()
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b

c1, c2 = st.columns(2)
with c1:
    st.metric("PERDITA TOTALE", f"€{loss:,.0f}")
    if st.button("Genera Report PDF"):
        if res:
            try:
                out = make_pdf(cap, loss, yrs, ter, res)
                st.download_button("💾 SCARICA PDF", data=out, file_name="AEGIS_Analisi.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Errore: {e}")
        else:
            st.error("Carica un PDF per includere i dati.")

with c2:
    fig = px.pie(values=[f_b, loss], names=['Tuo Patrimonio', 'Costi Banca'], 
                 color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=0.3)
    st.plotly_chart(fig, use_container_width=True)
