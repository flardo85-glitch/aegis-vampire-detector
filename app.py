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
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide", page_icon="🧛")

# --- FUNZIONI CORE ---
def analyze_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))

def get_performance_data(isin_list):
    results = []
    bench = "SWDA.MI"
    try:
        b_data = yf.download(bench, period="5y", progress=False)['Close']
        b_ret = ((b_data.iloc[-1] / b_data.iloc[0]) - 1) * 100
    except: b_ret = 60.0
    
    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin)
            name = t.info.get('longName', f"Fondo {isin}")
            h = t.history(period="5y")
            f_ret = ((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100 if not h.empty else 0
            results.append({"ISIN": isin, "Nome": name, "Gap %": round(b_ret - f_ret, 2)})
        except:
            results.append({"ISIN": isin, "Nome": "Dato Privato (Opaco)", "Gap %": 0.0})
    return results, b_ret

def make_pdf(capital, loss, years, ter, res, score_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(200, 15, "AEGIS: VERDETTO PATRIMONIALE", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, f"VAMPIRE SCORE: {score_data[0]}/10 - {score_data[1]}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 8, f"Capitale: Euro {capital:,.2f}", ln=True)
    pdf.cell(200, 8, f"Costo Annuo: {ter}%", ln=True)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(200, 10, f"EMORRAGIA STIMATA: Euro {loss:,.2f}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    if res:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 8, "ISIN", 1); pdf.cell(100, 8, "NOME", 1); pdf.cell(40, 8, "GAP %", 1); pdf.ln()
        pdf.set_font("Arial", "", 8)
        for item in res:
            pdf.cell(40, 8, str(item['ISIN']), 1)
            pdf.cell(100, 8, str(item['Nome'])[:45], 1)
            pdf.cell(40, 8, str(item['Gap %']), 1); pdf.ln()
    pdf.ln(20)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "AVVISO: Simulatore matematico. Non costituisce consulenza finanziaria. I dati non vengono salvati.")
    return pdf.output()

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Vampire Detector")

with st.expander("⚖️ AVVISO LEGALE E PRIVACY"):
    st.warning("Simulatore matematico. I dati non vengono salvati. Nessun consiglio finanziario fornito.")

st.sidebar.header("⚙️ Parametri")
cap = st.sidebar.number_input("Capitale Totale (€)", value=200000)
ter = st.sidebar.slider("Costo Annuo Banca (%)", 0.5, 5.0, 2.2)
yrs = st.sidebar.slider("Orizzonte (Anni)", 5, 30, 20)

up = st.file_uploader("Carica PDF Estratto Conto", type="pdf")
res = []

if up:
    isins = analyze_pdf(up)
    if isins:
        st.success(f"Rilevati {len(isins)} ISIN")
        res, b_ret = get_performance_data(isins)
        st.table(pd.DataFrame(res))
        
        avg_gap = np.mean([item['Gap %'] for item in res])
        score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
        label = "CONTE DRACULA" if score > 6.5 else "VAMPIRO" if score > 3.5 else "PIPISTRELLO"
        st.subheader(f"📊 Vampire Score: {score}/10 - {label}")

st.divider()
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b

c1, c2 = st.columns(2)
with c1:
    st.metric("PERDITA TOTALE", f"€{loss:,.0f}", delta=f"-{ter}%/anno", delta_color="inverse")
    if st.button("💾 GENERA REPORT PDF DEFINITIVO"):
        avg_gap = np.mean([item['Gap %'] for item in res]) if res else 0
        score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
        label = "CONTE DRACULA" if score > 6.5 else "VAMPIRO" if score > 3.5 else "PIPISTRELLO"
        pdf_bytes = make_pdf(cap, loss, yrs, ter, res, (score, label))
        st.download_button("SCARICA ORA", data=bytes(pdf_bytes), file_name="Verdetto_Aegis.pdf", mime="application/pdf")

with c2:
    fig = px.pie(names=['Patrimonio', 'Costi'], values=[f_b, loss], color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

st.error("🆘 Hai scoperto un'emorragia patrimoniale? Non restare a guardare mentre la banca divora il tuo futuro.")
