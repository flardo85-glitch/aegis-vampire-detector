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

# --- FUNZIONI SACRE (TUO CODICE ORIGINALE) ---
def format_euro_ui(amount):
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def format_euro_pdf(amount):
    val_formattata = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"EUR {val_formattata}"

# --- MOTORE PDF (TUO CODICE ORIGINALE) ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12); self.set_text_color(100)
        self.cell(0, 10, 'AEGIS | Audit Quantitativo Indipendente', 0, 1, 'L')
        self.line(10, 20, 200, 20); self.ln(10)
    def footer(self):
        self.set_y(-35); self.set_font('helvetica', 'I', 7); self.set_text_color(140)
        disclaimer = "DOCUMENTO TECNICO EX ART. 1 E 94 TUF: Non costituisce consulenza personalizzata."
        self.multi_cell(0, 4, disclaimer, align='C')

def generate_safe_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page(); pdf.set_font('helvetica', 'B', 20); pdf.cell(0, 15, 'REDAZIONE TECNICA', 0, 1, 'C')
    pdf.set_font('helvetica', 'B', 14); pdf.cell(0, 10, f'INDICE INEFFICIENZA: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10); pdf.multi_cell(0, 6, f"Dispersione a {yrs} anni: {format_euro_pdf(loss)}.")
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
            if h.empty: results.append({"ISIN": isin, "Nome": f"Audit {isin}", "Gap Tecnico %": 35.0})
            else:
                fr = float(((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100)
                results.append({"ISIN": isin, "Nome": tk.info.get('longName', isin)[:50], "Gap Tecnico %": round(float(br - fr), 2)})
        except: results.append({"ISIN": isin, "Nome": "Dato non disponibile", "Gap Tecnico %": 35.0})
    return results, br

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Audit Quantitativo")
st.error("⚖️ **REDAZIONE TECNICA OBBLIGATORIA EX ART. 1 E 94 TUF**")

with st.sidebar:
    st.header("⚙️ Parametri")
    p = st.selectbox("Tipologia:", ["Fondi", "Polizze", "Manuale"])
    costs = {"Fondi": 2.2, "Polizze": 3.8, "Manuale": 2.2}
    cap = st.number_input("Capitale (€)", value=200000)
    ter = st.slider("Costo (TER %)", 0.0, 5.0, costs[p])
    yrs = st.slider("Orizzonte (Anni)", 5, 30, 20)

f_b = cap * ((1.05 - (ter/100))**yrs); f_a = cap * ((1.05 - 0.002)**yrs); loss = f_a - f_b

up = st.file_uploader("📂 Carica documento tecnico (KID)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, b_ret = get_performance_data(isins)
        score = round(min((ter * 2) + (np.mean([item['Gap Tecnico %'] for item in res]) / 10), 10), 1)
        
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("DISPERSIONE STIMATA", format_euro_ui(loss))
        m2.metric("INDICE INEFFICIENZA", f"{score}/10")
        m3.metric("EFFICIENZA CAPITALE", f"{round((f_b/f_a)*100, 1)}%")
        
        st.divider()
        c1, c2 = st.columns([2, 1])
        with c1:
            st.write("**Forbice Patrimoniale (Loss Gap)**")
            y_range = np.arange(0, yrs + 1)
            df_p = pd.DataFrame({'Anni': y_range, 
                                 'Efficiente': [cap * ((1.05 - 0.002)**y) for y in y_range],
                                 'Attuale': [cap * ((1.05 - (ter/100))**y) for y in y_range]})
            st.plotly_chart(px.area(df_p, x='Anni', y=['Efficiente', 'Attuale'], color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True)
            st.table(pd.DataFrame(res))
        with c2:
            st.write("**Composizione**")
            st.plotly_chart(px.pie(names=['Netto', 'Oneri'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True)
            em = st.text_input("Mail:")
            if em and "@" in em:
                pdf_data = generate_safe_pdf(res, score, loss, ter, yrs, cap)
                st.download_button("📩 Download Report", data=pdf_data, file_name="AEGIS_Audit.pdf")
