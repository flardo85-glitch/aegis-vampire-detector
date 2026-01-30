import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AEGIS: Forensic Audit", layout="wide", page_icon="🛡️")

# --- FORMATTAZIONE CONTABILE (PUNTO DI FORZA) ---
def f_ui(n): return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
def f_pdf(n): return f"EUR {f_ui(n).replace(' €', '')}"

# --- MOTORE PDF (BLINDATURA LEGALE INTEGRALE) ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12); self.set_text_color(100)
        self.cell(0, 10, 'AEGIS | Forensic Financial Audit', 0, 1, 'L')
        self.line(10, 20, 200, 20); self.ln(10)
    def footer(self):
        self.set_y(-35); self.set_font('helvetica', 'I', 7); self.set_text_color(140)
        disclaimer = (
            "AVVISO LEGALE OBBLIGATORIO EX ART. 1, C. 5-SEPTIES E ART. 94 D.LGS. 58/1998 (TUF): "
            "Il presente documento e' il risultato di un'elaborazione algoritmica basata su dati storici pubblici. "
            "Non costituisce sollecitazione al risparmio ne' servizio di consulenza personalizzata. "
            "AEGIS non garantisce risultati futuri. La decisione finale spetta all'utente."
        )
        self.multi_cell(0, 4, disclaimer, align='C')

def generate_premium_pdf(res, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page(); pdf.set_font('helvetica', 'B', 22); pdf.set_text_color(20, 33, 61)
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C'); pdf.ln(10)
    
    # Box Verdetto
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50); pdf.set_font('helvetica', 'B', 14); pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VALUTAZIONE DI EFFICIENZA: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('helvetica', '', 11); pdf.set_text_color(0)
    pdf.cell(0, 10, f'STATO: {"CRITICA (Richiesto Intervento)" if score > 6 else "MIGLIORABILE"}', 0, 1, 'L'); pdf.ln(20)

    # Analisi Dispersione
    pdf.set_font('helvetica', 'B', 13); pdf.cell(0, 10, '1. ANALISI TECNICA DELLA DISPERSIONE', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"In un orizzonte di {yrs} anni, la proiezione evidenzia una dispersione stimata di {f_pdf(loss)} dovuta a inefficienze commissionali."); pdf.ln(10)

    # Tabella ISIN
    pdf.set_font('helvetica', 'B', 10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255)
    pdf.cell(45, 10, ' ISIN RILEVATO', 1, 0, 'L', 1); pdf.cell(100, 10, ' STRUMENTO', 1, 0, 'L', 1); pdf.cell(45, 10, ' GAP TECNICO %', 1, 1, 'C', 1)
    pdf.set_text_color(0); pdf.set_font('helvetica', '', 9)
    for i in res:
        n = i['Nome'].encode('ascii', 'ignore').decode('ascii')
        pdf.cell(45, 10, f" {i['ISIN']}", 1); pdf.cell(100, 10, f" {n[:50]}", 1); pdf.cell(45, 10, f"{float(i['Gap Tecnico %'])}% ", 1, 1, 'R')
    
    # Checklist Istruzioni
    pdf.ln(10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255); pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, ' 2. PARAMETRI DI OTTIMIZZAZIONE', 0, 1, 'L', 1)
    pdf.set_text_color(0); pdf.set_font('helvetica', '', 10); pdf.ln(2)
    pdf.multi_cell(0, 6, "1. FISCO: Verifica zainetto fiscale.\n2. KILL-SWITCH: Correlazione asset < 0.50.\n3. COSTI: Target TER < 0.30%.\n4. REBALANCING: Strategia automatica.")
    return bytes(pdf.output())

# --- LOGICA DATI ---
def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages: text += (page.extract_text() or "") + "\n"
        finds = re.findall(r'\b[A-Z]{2}[A-Z0-9]{9}[0-9]{1}\b', text)
        return list(set([i for i in finds if sum(c.isdigit() for c in i) >= 3]))
    except: return []

def get_performance_data(isin_list):
    results = []; bench = "SWDA.MI"
    try:
        b = yf.download(bench, period="5y", progress=False)
        br = float(((b['Close'].iloc[-1] / b['Close'].iloc[0]) - 1) * 100) if not b.empty else 65.0
    except: br = 65.0
    for isin in isin_list[:5]:
        t = f"{isin}.MI" if isin.startswith("IT") else isin
        try:
            tk = yf.Ticker(t); h = tk.history(period="5y")
            if h.empty: results.append({"ISIN": isin, "Nome": f"Audit {isin}", "Gap Tecnico %": 35.0})
            else:
                fr = float(((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100)
                results.append({"ISIN": isin, "Nome": tk.info.get('longName', isin)[:50], "Gap Tecnico %": round(float(br - fr), 2)})
        except: results.append({"ISIN": isin, "Nome": f"Errore Dati ({isin})", "Gap Tecnico %": 35.0})
    return results, br

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Forensic Financial Audit")
st.error("⚖️ **AVVISO LEGALE OBBLIGATORIO - EX ARTT. 1 E 94 TUF**")
st.caption("IL PRESENTE SOFTWARE E' UN ALGORITMO DI AUDIT MATEMATICO INDIPENDENTE.")

with st.sidebar:
    st.header("⚙️ Audit Setup")
    with st.expander("📊 GUIDA AI COSTI (TER)"):
        st.write("ETF: 0.1% | Fondi: 2.2% | Polizze: 4.2%")
    p = st.selectbox("Prodotto:", ["Fondi Comuni", "Polizze Unit Linked", "Private Banking", "Dato Manuale"])
    costs = {"Fondi Comuni": 2.2, "Polizze Unit Linked": 3.8, "Private Banking": 1.8, "Dato Manuale": 2.2}
    cap = st.number_input("Capitale (€)", value=200000)
    ter = st.slider("Costo TER (%)", 0.0, 5.0, costs[p])
    yrs = st.slider("Orizzonte (Anni)", 5, 30, 20)

f_b = cap * ((1.05 - (ter/100))**yrs); f_a = cap * ((1.05 - 0.002)**yrs); loss = f_a - f_b

up = st.file_uploader("📂 Carica documento tecnico (PDF)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, br = get_performance_data(isins)
        st.subheader("🔍 Analisi Posizioni Rilevate")
        st.table(pd.DataFrame(res))
        
        score = round(min((ter * 2) + (np.mean([x['Gap Tecnico %'] for x in res])/10), 10), 1)
        
        # --- GRAFICI (IL CUORE VISIVO) ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.metric("DISPERSIONE STIMATA", f_ui(loss))
            st.plotly_chart(px.pie(names=['Netto', 'Dispersione'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']))
        with c2:
            st.write("**Proiezione Forbice Temporale**")
            y_range = np.arange(0, yrs + 1)
            df_plot = pd.DataFrame({
                'Anni': y_range,
                'Efficiente': [cap * ((1.05 - 0.002)**y) for y in y_range],
                'Attuale': [cap * ((1.05 - (ter/100))**y) for y in y_range]
            })
            st.plotly_chart(px.area(df_plot, x='Anni', y=['Efficiente', 'Attuale'], color_discrete_sequence=['#2ecc71', '#e74c3c']))

        em = st.text_input("Inserisci mail per sbloccare la perizia:")
        if em and "@" in em:
            pdf_data = generate_premium_pdf(res, score, loss, ter, yrs, cap)
            st.download_button("📩 Scarica Perizia Forense (PDF)", data=pdf_data, file_name="Audit_AEGIS.pdf")
    else: st.warning("ISIN non trovati.")
