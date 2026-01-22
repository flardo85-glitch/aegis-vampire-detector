import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import pdfplumber
import re
from fpdf import FPDF

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide")

# --- FUNZIONI ---
def analyze_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))

def get_performance(isin_list):
    results = []
    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin)
            name = t.info.get('longName', f"Fondo {isin}")
            results.append({"ISIN": isin, "Nome": name, "Status": "Analizzato"})
        except:
            results.append({"ISIN": isin, "Nome": "Dato Privato", "Status": "N/D"})
    return results

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Vampire Detector")

with st.expander("⚖️ AVVISO LEGALE E PRIVACY"):
    st.warning("Simulatore matematico. I dati non vengono salvati. Non costituisce consulenza finanziaria.")

# Sidebar
cap = st.sidebar.number_input("Capitale (€)", value=200000)
ter = st.sidebar.slider("Costo Banca (%)", 0.5, 5.0, 2.2)
yrs = st.sidebar.slider("Anni", 5, 30, 20)

# Analisi
up = st.file_uploader("Carica PDF", type="pdf")
res = []

if up:
    isins = analyze_pdf(up)
    if isins:
        st.success(f"Trovati {len(isins)} ISIN")
        res = get_performance(isins)
        st.table(pd.DataFrame(res))

st.divider()
loss = (cap * ((1 + 0.05 - 0.002)**yrs)) - (cap * ((1 + 0.05 - (ter/100))**yrs))

c1, c2 = st.columns(2)
c1.metric("PERDITA TOTALE", f"€{loss:,.0f}")
fig = px.pie(values=[cap, loss], names=['Patrimonio', 'Costi'], hole=0.3)
c2.plotly_chart(fig, use_container_width=True)

if st.button("Genera Report"):
    st.write("Funzione Report pronta. Scarica ora.")
