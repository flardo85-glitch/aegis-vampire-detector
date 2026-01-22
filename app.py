import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF

# --- CONFIGURAZIONE PROFESSIONALE ---
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide", page_icon="🧛")

# --- CORE LOGIC: INTELLIGENCE ---
def analyze_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))

def get_performance_data(isin_list):
    results = []
    bench = "SWDA.MI" # MSCI World
    try:
        b_data = yf.download(bench, period="5y", progress=False)['Close']
        b_ret = ((b_data.iloc[-1] / b_data.iloc[0]) - 1) * 100
    except:
        b_ret = 60.0
    
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

# --- GENERATORE REPORT PDF ---
def generate_pdf_report(cap, loss, yrs, ter, res, score_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(200, 20, "AEGIS: VERDETTO PATRIMONIALE", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, f"VAMPIRE SCORE: {score_info[0]}/10 - {score_info[1]}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 8, f"Capitale: Euro {cap:,.2f}", ln=True)
    pdf.cell(200, 8, f"Costo Annuo Banca: {ter}%", ln=True)
    
    pdf.set_text_color(220, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 12, f"CAPITALE DIVORATO: Euro {loss:,.2f}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    if res:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(45, 8, "ISIN", 1); pdf.cell(100, 8, "NOME", 1); pdf.cell(35, 8, "GAP %", 1); pdf.ln()
        pdf.set_font("Arial", "", 8)
        for item in res:
            pdf.cell(45, 8, str(item['ISIN']), 1)
            pdf.cell(100, 8, str(item['Nome'])[:45], 1)
            pdf.cell(35, 8, str(item['Gap %']), 1); pdf.ln()
    
    pdf.ln(20)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "AVVISO LEGALE: Simulatore matematico. Non costituisce consulenza finanziaria. I dati non vengono salvati.")
    return pdf.output()

# --- INTERFACCIA UTENTE ---
st.title("🛡️ AEGIS: Vampire Detector")

with st.expander("⚖️ AVVISO LEGALE E PRIVACY"):
    st.warning("Simulatore matematico. I dati non vengono salvati. Nessun consiglio finanziario fornito.")

# Sidebar
st.sidebar.header("⚙️ Parametri Finanziari")
cap = st.sidebar.number_input("Capitale Totale (€)", value=200000, step=10000)
ter = st.sidebar.slider("Costo Annuo Banca (%)", 0.5, 5.0, 2.2)
yrs = st.sidebar.slider("Anni di detenzione", 5, 30, 20)

# Main Analysis
up = st.file_uploader("📂 Carica Estratto Conto PDF per Analisi ISIN", type="pdf")
res = []

if up:
    with st.spinner("Analisi dei parassiti in corso..."):
        isins = analyze_pdf(up)
        if isins:
            st.success(f"Rilevati {len(isins)} codici ISIN.")
            res, b_ret = get_performance_data(isins)
            st.table(pd.DataFrame(res))
            
            # Calcolo Vampire Score
            avg_gap = np.mean([item['Gap %'] for item in res])
            v_score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
            v_label = "CONTE DRACULA" if v_score > 6.5 else "VAMPIRO" if v_score > 3.5 else "PIPISTRELLO"
            st.subheader(f"📊 Vampire Score: {v_score}/10")
            st.info(f"LIVELLO: {v_label}")
            st.session_state['v_data'] = (v_score, v_label)

st.divider()

# Calcolo Matematico
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b

col1, col2 = st.columns(2)
with col1:
    st.metric("EMORRAGIA PATRIMONIALE", f"€{loss:,.0f}", delta=f"-{ter}%/anno", delta_color="inverse")
    
    if st.button("💾 GENERA VERDETTO PDF"):
        v_info = st.session_state.get('v_data', (round(ter*2, 1), "Analisi Parziale"))
        pdf_out = generate_pdf_report(cap, loss, yrs, ter, res, v_info)
        st.download_button("SCARICA ORA", data=bytes(pdf_out), file_name="Verdetto_AEGIS.pdf", mime="application/pdf")

with col2:
    fig = px.pie(names=['Patrimonio Residuo', 'Costi Bancari'], values=[f_b, loss], 
                 color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

st.error("🆘 Hai scoperto un'emorragia patrimoniale? Non restare a guardare mentre la banca divora il tuo futuro.")
