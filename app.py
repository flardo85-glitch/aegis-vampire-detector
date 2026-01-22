import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re

# --- CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="AEGIS Vampire Detector", layout="wide", initial_sidebar_state="expanded")

# Custom CSS per un look professionale e "brutale"
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGICA DI BACKEND ---

def get_vix_status():
    """Recupera l'indice VIX con gestione errori MultiIndex"""
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
    """Estrae testo e cerca ISIN e costi potenziali"""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    
    # Ricerca Codici ISIN (Standard Internazionale)
    isins = list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))
    # Ricerca costi (numeri seguiti da %)
    costs = re.findall(r'(\d+[,\.]\d+)\s*%', text)
    
    return text, isins, costs

def calculate_impact(capital, bank_ter, years=20):
    """Calcola la differenza tra gestione bancaria ed efficiente"""
    mkt_ret = 0.05  # Ritorno annuo stimato 5%
    etf_ter = 0.002 # 0.2%
    final_bank = capital * ((1 + mkt_ret - bank_ter)**years)
    final_aegis = capital * ((1 + mkt_ret - etf_ter)**years)
    return final_aegis, final_bank, final_aegis - final_bank

# --- INTERFACCIA PRINCIPALE ---

st.title("🛡️ AEGIS: Vampire Detector")
st.subheader("Analisi Quantitativa Indipendente per Professionisti")

# 1. STATUS MERCATO
vix_val, risk_level, icon = get_vix_status()
st.info(f"**SENTIMENT DI MERCATO:** {icon} {risk_level} | VIX attuale: {vix_val:.2f}")

# 2. INPUT SIDEBAR
st.sidebar.header("⚙️ Configurazione")
capital = st.sidebar.number_input("Capitale Totale (€)", value=200000, step=10000)
bank_ter_input = st.sidebar.slider("Costo Annuo Banca (TER %)", 0.5, 5.0, 2.2)
years = st.sidebar.slider("Orizzonte (Anni)", 5, 30, 20)
bank_ter = bank_ter_input / 100

# 3. AREA UPLOAD E OCR
st.divider()
st.write("### 📂 Fase 1: Caricamento Documentazione")
uploaded_pdf = st.file_uploader("Trascina qui il tuo estratto conto titoli (PDF)", type="pdf")

if uploaded_pdf:
    with st.spinner("L'IA sta scansionando i costi occulti..."):
        full_text, found_isins, found_costs = analyze_pdf_intelligence(uploaded_pdf)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.success("Analisi Completata")
            st.write(f"**ISIN Rilevati:** {', '.join(found_isins) if found_isins else 'Nessuno'}")
        with col_b:
            st.write(f"**Costi Potenziali Trovati:** {', '.join(found_costs[:5])}% ...")

# 4. IL VERDETTO (CALCOLI)
st.divider()
aegis_total, bank_total, loss = calculate_impact(capital, bank_ter, years)

st.write("### 📊 Fase 2: Il Verdetto della Verità")
c1, c2, c3 = st.columns(3)
c1.metric("Capitale con AEGIS", f"€{aegis_total:,.0f}")
c2.metric("Capitale in Banca", f"€{bank_total:,.0f}")
c3.metric("PATRIMONIO DISTRUTTO", f"€{loss:,.0f}", delta=f"-{bank_ter_input}%/anno", delta_color="inverse")

# Grafico di crescita
plot_df = pd.DataFrame({
    "Scenario": ["Patrimonio Efficiente (AEGIS)", "Patrimonio Erosione (Banca)"],
    "Valore Finale (€)": [aegis_total, bank_total]
})
fig = px.bar(plot_df, x="Scenario", y="Valore Finale (€)", color="Scenario",
             color_discrete_sequence=["#00CC96", "#EF553B"])
st.plotly_chart(fig, use_container_width=True)

# 5. CORRELAZIONE E KILL-SWITCH
st.divider()
st.write("### 🔗 Fase 3: Analisi Correlazione (Kill-Switch)")
tickers_str = st.text_input("Verifica Asset Specifici (inserisci ticker separati da virgola)", "AAPL,MSFT,BTC-USD,GLD")

if tickers_str:
    try:
        t_list = [x.strip().upper() for x in tickers_str.split(",")]
        # Fix per KeyError 'Adj Close' con auto_adjust=True
        mkt_data = yf.download(t_list, period="1y", auto_adjust=True)['Close']
        if not mkt_data.empty:
            corr_matrix = mkt_data.pct_change().corr()
            st.plotly_chart(px.imshow(corr_matrix, text_auto=True, title="Mappa della Falsa Diversificazione"))
            
            # Alert se correlazione > 0.50
            danger_links = (corr_matrix.values > 0.50).sum() - len(t_list)
            if danger_links > 0:
                st.error(f"🚨 KILL-SWITCH ALERT: Trovate {danger_links//2} sovrapposizioni pericolose. Il tuo rischio è concentrato.")
    except:
        st.warning("Inserisci ticker validi per l'analisi di mercato.")

# 6. LEAD GENERATION
st.divider()
st.write("### ✉️ Ottieni il Report Strategico")
user_email = st.text_input("Inserisci la tua email per ricevere l'analisi dettagliata (PDF)")
if st.button("Genera Report e Invia"):
    if user_email:
        st.success(f"Analisi prioritaria in coda per: {user_email}")
    else:
        st.error("Inserisci un'email valida.")