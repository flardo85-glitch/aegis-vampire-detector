import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide", page_icon="🧛")

# --- DATABASE VAMPIRI (MEDIE DI SETTORE) ---
vampire_data = {
    "Inserimento Manuale": 2.2,
    "Fondi Comuni Bancari (Media 2.2%)": 2.2,
    "Gestioni Patrimoniali Retail (Media 2.8%)": 2.8,
    "Polizze Unit Linked / Fondi di Fondi (Media 3.5%)": 3.5,
    "Private Banking High Net Worth (Media 1.8%)": 1.8
}

# --- FUNZIONI CORE ---
def analyze_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
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

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Vampire Detector")

with st.expander("⚖️ AVVISO LEGALE E PRIVACY"):
    st.warning("Simulatore matematico. I dati non vengono salvati. Nessun consiglio finanziario fornito.")

# Sidebar Strategica
st.sidebar.header("⚙️ Profilo di Costo")
bank_profile = st.sidebar.selectbox("Chi gestisce i tuoi soldi?", list(vampire_data.keys()))
default_ter = vampire_data[bank_profile]

cap = st.sidebar.number_input("Capitale Totale (€)", value=200000, step=10000)
ter = st.sidebar.slider("Costo Annuo Stimato (%)", 0.5, 5.0, default_ter)
yrs = st.sidebar.slider("Orizzonte (Anni)", 5, 30, 20)

# Main
up = st.file_uploader("📂 Carica Estratto Conto PDF per Analisi ISIN", type="pdf")
res = []

if up:
    isins = analyze_pdf(up)
    if isins:
        st.success(f"Rilevati {len(isins)} codici ISIN.")
        res, b_ret = get_performance_data(isins)
        st.table(pd.DataFrame(res))
        
        avg_gap = np.mean([item['Gap %'] for item in res])
        v_score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
        v_label = "CONTE DRACULA" if v_score > 6.5 else "VAMPIRO" if v_score > 3.5 else "PIPISTRELLO"
        st.subheader(f"📊 Vampire Score: {v_score}/10")
        st.info(f"LIVELLO: {v_label} - Rendimento perso vs Mercato: {avg_gap:.1f}% (ultimi 5 anni)")

st.divider()

# Calcolo
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b

col1, col2 = st.columns(2)
with col1:
    st.metric("EMORRAGIA PATRIMONIALE", f"€{loss:,.0f}", delta=f"-{ter}%/anno", delta_color="inverse")
    
    # CTA AGGRESSIVA
    st.markdown(f"""
    ### 🚨 Non restare a guardare!
    L'analisi mostra che il tuo patrimonio è sotto attacco. 
    **€{loss:,.0f}** non sono solo numeri, è il costo della tua inazione.
    
    [👉 **RICHIEDI CHECK-UP PROFESSIONALE**](mailto:tua_mail@esempio.com?subject=Analisi%20AEGIS%20-%20Score%20{v_score}&body=Ho%20analizzato%20il%20mio%20portafoglio%20con%20AEGIS.%20Risultato:%20Score%20{v_score},%20Perdita%20stimata%20{loss:,.0f}€.)
    """)

with col2:
    fig = px.pie(names=['Patrimonio per Te', 'Patrimonio per la Banca'], values=[f_b, loss], 
                 color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
