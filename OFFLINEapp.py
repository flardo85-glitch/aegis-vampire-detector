import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AEGIS: Quantitative Detector", layout="wide", page_icon="🛡️")

# --- DATABASE MEDIE DI MERCATO ---
vampire_data = {
    "Dato Manuale": 2.2,
    "Benchmark Fondi Comuni": 2.2,
    "Benchmark Gestioni Retail": 2.8,
    "Benchmark Polizze Unit Linked": 3.5,
    "Benchmark Private Banking": 1.8
}

# --- FUNZIONI CORE ---
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
    except: b_ret = 60.0 
    
    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin)
            h = t.history(period="5y")
            if not h.empty:
                f_ret = ((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100
                results.append({"ISIN": isin, "Nome": t.info.get('longName', isin), "Gap Tecnico %": round(b_ret - f_ret, 2)})
            else:
                results.append({"ISIN": isin, "Nome": "Dato Opaco/Non Censito", "Gap Tecnico %": 0.0})
        except:
            results.append({"ISIN": isin, "Nome": "N/D", "Gap Tecnico %": 0.0})
    return results, b_ret

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Analizzatore Tecnico di Efficienza")
st.subheader("Strumento di misurazione quantitativa dei costi e dei rendimenti storici")

# --- CLAUSOLA DI ESCLUSIONE DI RESPONSABILITÀ (BLINDATURA) ---
st.info("⚠️ **DISCLAIMER TECNICO OBBLIGATORIO**")
st.caption("""
AEGIS è un software di calcolo matematico. Le analisi prodotte sono elaborazioni di dati storici pubblici e non costituiscono in alcun modo:
- Consulenza in materia di investimenti (ex art. 1 comma 5 septies TUF).
- Sollecitazione al pubblico risparmio.
- Raccomandazioni personalizzate.
L'utente è invitato a verificare i dati con i prospetti informativi (KIID) e a consultare un professionista abilitato per decisioni finanziarie.
""")

# Sidebar
st.sidebar.header("⚙️ Input Dati Tecnici")
profile = st.sidebar.selectbox("Profilo di Benchmark:", list(vampire_data.keys()))
cap = st.sidebar.number_input("Capitale in Analisi (€)", value=200000, step=10000)
ter = st.sidebar.slider("Oneri Annui Dichiarati (%)", 0.5, 5.0, vampire_data[profile])
yrs = st.sidebar.slider("Orizzonte di Calcolo (Anni)", 5, 30, 20)

# Inizializzazione
score = round(ter * 2, 1)
res = []

# Main
up = st.file_uploader("📂 Carica Estratto Conto (PDF) per estrazione automatica ISIN", type="pdf")

if up:
    with st.spinner("Estrazione dati in corso..."):
        isins = analyze_pdf(up)
        if isins:
            st.success(f"Analisi completata su {len(isins)} strumenti finanziari.")
            res, b_ret = get_performance_data(isins)
            st.table(pd.DataFrame(res))
            
            avg_gap = np.mean([item['Gap Tecnico %'] for item in res])
            score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
            st.subheader(f"📊 Indice di Inefficienza (Vampire Score): {score}/10")
            if score > 6.5: st.error("⚠️ Inefficienza Elevata rilevata.")
            elif score > 3.5: st.warning("🟡 Inefficienza Moderata rilevata.")
            else: st.success("🟢 Strumenti in linea con il benchmark.")

st.divider()

# Calcolo Matematico
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b

c1, c2 = st.columns(2)
with c1:
    st.metric("COSTO OPPORTUNITÀ TOTALE", f"€{loss:,.0f}", delta=f"-{ter}% cost/anno", delta_color="inverse")
    st.write("Questo valore rappresenta la differenza matematica tra il capitale proiettato e un benchmark efficiente.")
    
    # CTA PER VENDITA REPORT O SERVIZIO
    st.markdown(f"### [📩 Ricevi la Perizia Tecnica Completa](mailto:tua_mail@esempio.com?subject=Richiesta%20Analisi%20Tecnica%20AEGIS&body=Richiedo%20approfondimento%20tecnico%20su%20score%20{score}.)")

with c2:
    fig = px.pie(names=['Patrimonio Netto Proiettato', 'Oneri e Inefficienze'], values=[f_b, loss], 
                 color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
