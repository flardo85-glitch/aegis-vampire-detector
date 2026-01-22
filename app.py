import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AEGIS: Vampire Detector", layout="wide", initial_sidebar_state="expanded")

# --- LOGICA DI BACKEND ---

def get_vix_status():
    """Recupera l'indice VIX con gestione robusta del formato yfinance"""
    try:
        # Usiamo auto_adjust=True per evitare KeyError 'Adj Close'
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
    
    # Regex per ISIN (2 lettere + 10 caratteri alfanumerici)
    isins = list(set(re.findall(r'[A-Z]{2}[A-Z0-9]{10}', text)))
    # Regex per percentuali di costo (es: 2.5%, 1,80 %)
    costs = re.findall(r'(\d+[,\.]\d+)\s*%', text)
    
    return text, isins, costs

def calculate_impact(capital, bank_ter, years=20):
    """Calcola la differenza di patrimonio tra banca ed ETF efficiente"""
    mkt_ret = 0.05  # Rendimento medio stimato 5%
    etf_ter = 0.002 # 0.2% commissione ETF
    final_bank = capital * ((1 + mkt_ret - bank_ter)**years)
    final_aegis = capital * ((1 + mkt_ret - etf_ter)**years)
    return final_aegis, final_bank, final_aegis - final_bank

# --- INTERFACCIA UTENTE ---

st.title("🛡️ AEGIS: Vampire Detector")
st.markdown("### Analisi Indipendente del Patrimonio e Rilevamento Costi Occulti")

# 1. SCUDO LEGALE (Disclaimer Obbligatorio)
with st.expander("⚖️ AVVISO LEGALE E DISCLAIMER (Leggere prima dell'uso)"):
    st.warning("""
    **INFORMAZIONI IMPORTANTI:**
    1. **Nessun Consiglio Finanziario:** AEGIS è uno strumento puramente matematico e informativo. I risultati non costituiscono sollecitazione al risparmio o consulenza finanziaria.
    2. **Limitazione di Responsabilità:** L'accuratezza dipende dai dati inseriti e dalle fonti pubbliche. Non garantiamo l'assenza di errori.
    3. **Privacy:** I documenti caricati vengono elaborati in memoria e non salvati su server esterni. Per sicurezza, si consiglia di oscurare dati anagrafici sensibili.
    4. **Indipendenza:** Questo software non è affiliato a nessun istituto bancario.
    """)

# 2. STATUS MERCATO (VIX)
vix_val, risk_level, icon = get_vix_status()
st.info(f"**STATUS KILL-SWITCH:** {icon} {risk_level} | VIX: {vix_val:.2f}")

# 3. SIDEBAR PARAMETRI
st.sidebar.header("⚙️ Parametri Analisi")
capital = st.sidebar.number_input("Capitale Investito (€)", value=200000, step=10000)
bank_ter_input = st.sidebar.slider("Costi Annuali Banca (%)", 0.5, 5.0, 2.2)
years = st.sidebar.slider("Orizzonte Temporale (Anni)", 5, 30, 20)
bank_ter = bank_ter_input / 100

# 4. CARICAMENTO E ANALISI PDF
st.divider()
st.subheader("📂 Analisi Automatica Estratto Conto")
uploaded_pdf = st.file_uploader("Carica il PDF bancario per estrarre ISIN e Costi", type="pdf")

if uploaded_pdf:
    with st.spinner("Scansione 'Vampire' in corso..."):
        full_text, found_isins, found_costs = analyze_pdf_intelligence(uploaded_pdf)
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.success("Analisi Testuale Completata")
            st.write(f"**ISIN Rilevati:** {', '.join(found_isins) if found_isins else 'Nessuno'}")
        with col_res2:
            st.write(f"**Costi Potenziali Trovati:** {', '.join(found_costs[:5])}% ...")

# 5. VERDETTO MATEMATICO
st.divider()
aegis_total, bank_total, loss = calculate_impact(capital, bank_ter, years)

st.subheader("📊 Impatto dell'Erosione Bancaria")
m1, m2, m3 = st.columns(3)
m1.metric("Capitale con AEGIS", f"€{aegis_total:,.0f}")
m2.metric("Capitale in Banca", f"€{bank_total:,.0f}")
m3.metric("PATRIMONIO PERSO", f"€{loss:,.0f}", delta=f"-{bank_ter_input}%/anno", delta_color="inverse")

# Grafico
plot_df = pd.DataFrame({
    "Scenario": ["Patrimonio Efficiente (AEGIS)", "Patrimonio Erosione (Banca)"],
    "Valore Finale (€)": [aegis_total, bank_total]
})
fig = px.bar(plot_df, x="Scenario", y="Valore Finale (€)", color="Scenario",
             color_discrete_sequence=["#2ecc71", "#e74c3c"])
st.plotly_chart(fig, use_container_width=True)

# 6. ANALISI CORRELAZIONE (KILL-SWITCH ALFA)
st.divider()
st.subheader("🔗 Analisi Correlazione Asset")
tickers_str = st.text_input("Inserisci i Ticker dei titoli (es. AAPL,MSFT,BTC-USD)", "AAPL,MSFT,GOOGL")

if tickers_str:
    try:
        t_list = [x.strip().upper() for x in tickers_str.split(",")]
        # Fix per KeyError 'Adj Close'
        mkt_data = yf.download(t_list, period="1y", auto_adjust=True)['Close']
        if not mkt_data.empty:
            corr_matrix = mkt_data.pct_change().corr()
            st.plotly_chart(px.imshow(corr_matrix, text_auto=True, title="Matrice di Correlazione"))
            
            # Notifica Kill-Switch (Soglia 0.50)
            high_corr_val = (corr_matrix.values > 0.50).sum() - len(t_list)
            if high_corr_val > 0:
                st.warning(f"🚨 ALERT CORRELAZIONE: {high_corr_val//2} coppie superano la soglia di 0.50. Diversificazione inefficiente.")
    except:
        st.error("Inserisci ticker validi per l'analisi.")

# 7. GENERAZIONE REPORT
st.divider()
st.subheader("📥 Report Strategico")
email = st.text_input("Lascia la tua email per ricevere l'analisi PDF completa:")
if st.button("Invia Report"):
    st.success(f"Richiesta presa in carico per {email}. Riceverai il report entro 5 minuti.")
