import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF

st.set_page_config(page_title="AEGIS: Quantitative Audit", layout="wide")

def f_euro(n): return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " EUR"
def f_pdf(n): return f"EUR {f_euro(n).replace(' EUR', '')}"

class AegisReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12); self.set_text_color(100)
        self.cell(0, 10, 'AEGIS | Audit Patrimoniale Tecnico', 0, 1, 'L')
        self.line(10, 20, 200, 20); self.ln(10)
    def footer(self):
        self.set_y(-20); self.set_font('helvetica', 'I', 7)
        self.cell(0, 10, "EX ART. 1, 94 TUF: Audit algoritmico indipendente.", 0, 0, 'C')

def generate_pdf(res, score, loss, yrs):
    pdf = AegisReport()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 20); pdf.cell(0, 15, 'AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.set_fill_color(240); pdf.rect(10, 40, 190, 30, 'F')
    pdf.set_xy(15, 45); pdf.set_font('helvetica', 'B', 14); pdf.set_text_color(190, 50, 40)
    pdf.cell(0, 10, f'SCORE EFFICIENZA: {score}/10', 0, 1, 'L')
    pdf.set_font('helvetica', '', 11); pdf.set_text_color(0)
    pdf.cell(0, 10, f'STATO: {"CRITICA" if score > 6 else "MIGLIORABILE"}', 0, 1, 'L')
    pdf.set_xy(10, 75); pdf.set_font('helvetica', 'B', 12); pdf.cell(0, 10, '1. DISPERSIONE STIMATA', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"In {yrs} anni, la dispersione stimata e' di {f_pdf(loss)} per costi e gap tecnico.")
    pdf.ln(5)
    # Tabella
    pdf.set_font('helvetica', 'B', 9); pdf.set_fill_color(20, 30, 60); pdf.set_text_color(255)
    pdf.cell(40, 8, ' ISIN', 1, 0, 'L', 1); pdf.cell(110, 8, ' STRUMENTO', 1, 0, 'L', 1); pdf.cell(40, 8, ' GAP %', 1, 1, 'C', 1)
    pdf.set_text_color(0); pdf.set_font('helvetica', '', 8)
    for i in res:
        n = i['Nome'].encode('ascii', 'ignore').decode('ascii')
        pdf.cell(40, 8, f" {i['ISIN']}", 1); pdf.cell(110, 8, f" {n[:45]}", 1); pdf.cell(40, 8, f"{i['Gap Tecnico %']}%", 1, 1, 'C')
    # Protocolli
    pdf.ln(10); pdf.set_font('helvetica', 'B', 11); pdf.set_fill_color(20, 30, 60); pdf.set_text_color(255)
    if score > 6:
        pdf.cell(0, 10, ' PROTOCOLLO USCITA (CRITICO)', 0, 1, 'L', 1); pdf.set_text_color(0); pdf.set_font('helvetica', '', 10)
        pdf.multi_cell(0, 6, "1. STOP ALIMENTAZIONE: Sospendere PAC.\n2. AUDIT PENALI: Verificare costi riscatto.\n3. SWITCH: Migrare verso ETF (TER < 0.3%).")
    else:
        pdf.cell(0, 10, ' CHECKLIST OTTIMIZZAZIONE', 0, 1, 'L', 1); pdf.set_text_color(0); pdf.set_font('helvetica', '', 10)
        pdf.multi_cell(0, 6, "1. FISCO: Ottimizzare zainetto fiscale.\n2. RISCHIO: Verificare correlazione < 0.50.\n3. REBALANCING: Ribilanciamento periodico.")
    return bytes(pdf.output())

def get_data(isins):
    r = []
    try:
        b = yf.download("SWDA.MI", period="5y", progress=False)
        br = float(((b['Close'].iloc[-1]/b['Close'].iloc[0])-1)*100) if not b.empty else 65.0
    except: br = 65.0
    for i in isins[:5]:
        try:
            t = yf.Ticker(f"{i}.MI" if i.startswith("IT") else i); h = t.history(period="5y")
            if h.empty: r.append({"ISIN": i, "Nome": f"Fondo {i}", "Gap Tecnico %": 35.0})
            else:
                fr = float(((h['Close'].iloc[-1]/h['Close'].iloc[0])-1)*100)
                r.append({"ISIN": i, "Nome": t.info.get('longName', i), "Gap Tecnico %": round(br-fr, 2)})
        except: r.append({"ISIN": i, "Nome": f"Audit {i}", "Gap Tecnico %": 35.0})
    return r

st.title("🛡️ AEGIS: Analizzatore Tecnico")
st.error("⚖️ AVVISO EX ART. 1 E 94 TUF: No consulenza personalizzata.")

with st.sidebar:
    p = st.selectbox("Prodotto:", ["Fondi", "Polizze", "Retail", "Private"])
    cs = {"Fondi": 2.2, "Polizze": 3.8, "Retail": 2.8, "Private": 1.8}
    cap = st.number_input("Capitale (EUR)", 200000); t_cost = st.slider("TER (%)", 0.0, 5.0, cs[p])
    yrs = st.slider("Anni", 5, 30, 20)

loss = (cap * ((1.048 - 0.002)**yrs)) - (cap * ((1.048 - (t_cost/100))**yrs))
up = st.file_uploader("Carica PDF KID", type="pdf")

if up:
    with pdfplumber.open(up) as pdf:
        txt = "".join([p.extract_text() or "" for p in pdf.pages])
    isins = list(set(re.findall(r'\b[A-Z]{2}[A-Z0-9]{9}[0-9]\b', txt)))
    if isins:
        res = get_data(isins)
        st.table(pd.DataFrame(res))
        score = round(min((t_cost * 2) + (np.mean([x['Gap Tecnico %'] for x in res])/10), 10), 1)
        st.subheader(f"Vampire Score: {score}/10")
        em = st.text_input("Email per scaricare:")
        if em and "@" in em:
            pdf_b = generate_pdf(res, score, loss, yrs)
            st.download_button("📩 Scarica Perizia", pdf_b, "Perizia_AEGIS.pdf")
    else: st.warning("ISIN non trovati.")

st.divider(); st.metric("DISPERSIONE STIMATA", f_euro(loss))
st.plotly_chart(px.pie(names=['Netto', 'Dispersione'], values=[cap, loss], hole=0.4))
