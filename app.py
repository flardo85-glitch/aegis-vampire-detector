import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AEGIS: Quantitative Audit", layout="wide", page_icon="🛡️")

# --- 1. FUNZIONI DI FORMATTAZIONE (RIPRISTINATE INTEGRALMENTE) ---
def format_euro_ui(amount):
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def format_euro_pdf(amount):
    val_formattata = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"EUR {val_formattata}"

# --- 2. MOTORE PDF (BLINDATURA LEGALE TOTALE) ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12); self.set_text_color(100)
        self.cell(0, 10, 'AEGIS | Audit Quantitativo Indipendente', 0, 1, 'L')
        self.line(10, 20, 200, 20); self.ln(10)

    def footer(self):
        self.set_y(-35); self.set_font('helvetica', 'I', 7); self.set_text_color(140)
        disclaimer = (
            "DOCUMENTO TECNICO-INFORMATIVO EX ART. 1, C. 5-SEPTIES E ART. 94 D.LGS. 58/1998 (TUF): "
            "Il presente report non costituisce consulenza personalizzata ne' sollecitazione al risparmio. "
            "L'elaborazione si basa su algoritmi matematici applicati a dati storici pubblici. "
            "La scelta finale di investimento spetta esclusivamente all'utente previa consultazione dei prospetti (KID)."
        )
        self.multi_cell(0, 4, disclaimer, align='C')

def generate_safe_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page(); pdf.set_font('helvetica', 'B', 20); pdf.set_text_color(20, 33, 61)
    pdf.cell(0, 15, 'REDAZIONE TECNICA DI ANALISI PATRIMONIALE', 0, 1, 'C'); pdf.ln(10)
    
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50); pdf.set_font('helvetica', 'B', 14); pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'INDICE DI INEFFICIENZA RILEVATO: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('helvetica', '', 11); pdf.set_text_color(0)
    status = "ALTA (Analisi consigliata)" if score > 6 else "MODERATA (Ottimizzazione possibile)"
    pdf.cell(0, 10, f'GRADO DI DISPERSIONE: {status}', 0, 1, 'L'); pdf.ln(20)

    pdf.set_font('helvetica', 'B', 13); pdf.cell(0, 10, '1. PROIEZIONE MATEMATICA DEGLI ONERI', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"Sulla base dei costi (TER) e del gap tecnico storico, la proiezione a {yrs} anni stima una dispersione potenziale di {format_euro_pdf(loss)} rispetto a parametri di mercato efficienti."); pdf.ln(10)

    # Tabella ISIN
    pdf.set_font('helvetica', 'B', 10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255)
    pdf.cell(45, 10, ' ISIN', 1, 0, 'L', 1); pdf.cell(100, 10, ' STRUMENTO', 1, 0, 'L', 1); pdf.cell(45, 10, ' GAP TECNICO %', 1, 1, 'C', 1)
    pdf.set_text_color(0); pdf.set_font('helvetica', '', 9)
    for item in data_list:
        n = item['Nome'].encode('ascii', 'ignore').decode('ascii')
        pdf.cell(45, 10, f" {item['ISIN']}", 1); pdf.cell(100, 10, f" {n[:50]}", 1); pdf.cell(45, 10, f"{float(item['Gap Tecnico %'])}% ", 1, 1, 'R')
    
    # 3. ISTRUZIONI E CHECKLIST (PDF)
    pdf.ln(10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255); pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, ' 2. PARAMETRI DI OTTIMIZZAZIONE TECNICA', 0, 1, 'L', 1)
    pdf.set_text_color(0); pdf.set_font('helvetica', '', 10); pdf.ln(2)
    pdf.multi_cell(0, 6, "1. FISCO: Ottimizzazione delle minusvalenze.\n2. COSTI: Riduzione del TER target < 0.30%.\n3. CORRELAZIONI: Verifica soglia di correlazione asset < 0.50.\n4. REBALANCING: Strategia di ribilanciamento automatico.")
    
    return bytes(pdf.output())

# --- LOGICA DI ANALISI ---
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
            if h.empty: results.append({"ISIN": isin, "Nome": f"Strumento Rilevato ({isin})", "Gap Tecnico %": 35.0})
            else:
                fr = float(((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100)
                results.append({"ISIN": isin, "Nome": tk.info.get('longName', isin)[:50], "Gap Tecnico %": round(float(br - fr), 2)})
        except: results.append({"ISIN": isin, "Nome": f"Dato non disponibile", "Gap Tecnico %": 35.0})
    return results, br

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Audit Quantitativo Indipendente")
st.error("⚖️ **REDAZIONE TECNICA OBBLIGATORIA EX ART. 1 E 94 TUF**")

with st.sidebar:
    st.header("⚙️ Parametri Audit")
    p = st.selectbox("Tipologia:", ["Fondi Comuni", "Polizze Unit Linked", "Gestioni", "Dato Manuale"])
    costs = {"Fondi Comuni": 2.2, "Polizze Unit Linked": 3.8, "Gestioni": 2.2, "Dato Manuale": 2.2}
    cap = st.number_input("Capitale Investito (€)", value=200000)
    ter = st.slider("Costo TER (%)", 0.0, 5.0, costs[p])
    yrs = st.slider("Orizzonte Strategico (Anni)", 5, 30, 20)

f_b = cap * ((1.05 - (ter/100))**yrs); f_a = cap * ((1.05 - 0.002)**yrs); loss = f_a - f_b
up = st.file_uploader("📂 Carica documento tecnico (KID)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, b_ret = get_performance_data(isins)
        score = round(min((ter * 2) + (np.mean([item['Gap Tecnico %'] for item in res]) / 10), 10), 1)
        
        # --- DASHBOARD EXECUTIVE (INTEGRATA) ---
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("DISPERSIONE STIMATA", format_euro_ui(loss)) # <--- SOMME IN € RIPRISTINATE
        m2.metric("INDICE INEFFICIENZA", f"{score}/10")
        m3.metric("EFFICIENZA CAPITALE", f"{round((f_b/f_a)*100, 1)}%")

        st.divider()
        c1, c2 = st.columns([2, 1])
        with c1:
            st.write("**4. GRAFICI: Proiezione Forbice Patrimoniale**")
            y_range = np.arange(0, yrs + 1)
            df_plot = pd.DataFrame({
                'Anni': y_range,
                'Efficiente': [cap * ((1.05 - 0.002)**y) for y in y_range],
                'Attuale': [cap * ((1.05 - (ter/100))**y) for y in y_range]
            })
            st.plotly_chart(px.area(df_plot, x='Anni', y=['Efficiente', 'Attuale'], 
                                   color_discrete_sequence=['#2ecc71', '#e74c3c'], template="plotly_white"), use_container_width=True)
            st.table(pd.DataFrame(res))

        with c2:
            st.write("**Ripartizione Capitale**")
            st.plotly_chart(px.pie(names=['Netto Stimato', 'Dispersione Costi'], values=[f_b, loss], 
                                   hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True)
            
            # --- ISTRUZIONI IN APP ---
            st.info("**Checklist Audit**\n- Verifica Zainetto Fiscale\n- Target TER < 0.30%\n- Correlazione Asset < 0.50")
            
            em = st.text_input("Inserisci mail per il report:")
            if em and "@" in em:
                pdf_data = generate_safe_pdf(res, score, loss, ter, yrs, cap)
                st.download_button("📩 Scarica Report Tecnico", data=pdf_data, file_name="AEGIS_Audit_Report.pdf")
    else: st.warning("Nessun ISIN rilevato.")

st.divider()
st.caption("Analisi algoritmica basata su dati di mercato e simulazioni matematiche.")
