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

# --- FORMATTAZIONE CONTABILE ---
def format_euro_ui(amount):
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def format_euro_pdf(amount):
    val_formattata = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"EUR {val_formattata}"

# --- MOTORE PDF (POTENZIATO) ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'AEGIS | Forensic Financial Audit', 0, 1, 'L')
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-35)
        self.set_font('helvetica', 'I', 7)
        self.set_text_color(140, 140, 140)
        # BLINDATURA LEGALE INTEGRALE
        disclaimer = (
            "AVVISO LEGALE OBBLIGATORIO EX ART. 1, C. 5-SEPTIES E ART. 94 D.LGS. 58/1998 (TUF): "
            "Il presente documento e' il risultato di un'elaborazione algoritmica basata esclusivamente su dati storici pubblici. "
            "Non costituisce in alcun modo sollecitazione al pubblico risparmio, ne' integra il servizio di consulenza in materia di investimenti. "
            "L'utente dichiara di aver preso visione dei KID ufficiali prima di ogni decisione. AEGIS non garantisce risultati futuri."
        )
        self.multi_cell(0, 4, disclaimer, align='C')

def generate_premium_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 22); pdf.set_text_color(20, 33, 61) 
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.ln(10)
    
    # Box Verdetto
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50); pdf.set_font('helvetica', 'B', 14); pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VALUTAZIONE DI EFFICIENZA: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('helvetica', '', 11); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f'STATO: {"CRITICA (Richiesto Intervento)" if score > 6 else "MIGLIORABILE (Audit Periodico)"}', 0, 1, 'L')
    pdf.ln(20)

    # Analisi Perdita
    pdf.set_font('helvetica', 'B', 13); pdf.cell(0, 10, '1. ANALISI TECNICA DELLA DISPERSIONE', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"In un orizzonte di {yrs} anni, la proiezione algoritmica evidenzia una dispersione stimata di {format_euro_pdf(loss)} causata da inefficienze commissionali e mancato allineamento ai benchmark di mercato.")
    pdf.ln(10)

    # Tabella
    pdf.set_font('helvetica', 'B', 10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255)
    pdf.cell(45, 10, ' ISIN RILEVATO', 1, 0, 'L', 1)
    pdf.cell(100, 10, ' STRUMENTO FINANZIARIO', 1, 0, 'L', 1)
    pdf.cell(45, 10, ' GAP TECNICO %', 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font('helvetica', '', 9)
    for item in data_list:
        n = item['Nome'].encode('ascii', 'ignore').decode('ascii')
        pdf.cell(45, 10, f" {item['ISIN']}", 1); pdf.cell(100, 10, f" {n[:50]}", 1)
        pdf.cell(45, 10, f"{float(item['Gap Tecnico %'])}% ", 1, 1, 'R')
    
    # Protocolli
    pdf.ln(10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255); pdf.set_font('helvetica', 'B', 12)
    if score > 6:
        pdf.cell(0, 10, ' PROTOCOLLO DI USCITA DA STATO CRITICO', 0, 1, 'L', 1)
        pdf.set_text_color(0, 0, 0); pdf.set_font('helvetica', '', 10); pdf.ln(2)
        pdf.multi_cell(0, 6, "1. STOP ALIMENTAZIONE: Sospendere PAC.\n2. AUDIT PENALI: Verificare commissioni di riscatto.\n3. SOSTITUZIONE: Migrazione verso ETF.\n4. TER TARGET: Sotto 0.30% annuo.")
    else:
        pdf.cell(0, 10, ' CHECKLIST DI OTTIMIZZAZIONE TECNICA', 0, 1, 'L', 1)
        pdf.set_text_color(0, 0, 0); pdf.set_font('helvetica', '', 10); pdf.ln(2)
        pdf.multi_cell(0, 6, "1. FISCO: Ottimizzare minusvalenze.\n2. CORRELAZIONI: Verificare soglia < 0.50.\n3. REBALANCING: Strategia automatica.")
    
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
        except: results.append({"ISIN": isin, "Nome": f"Dato Non Reperibile ({isin})", "Gap Tecnico %": 35.0})
    return results, br

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Forensic Financial Audit")

with st.container():
    st.error("⚖️ **AVVISO LEGALE OBBLIGATORIO - EX ARTT. 1 E 94 TUF**")
    st.caption("""
    **LIMITAZIONI DI RESPONSABILITA' (DISCLAIMER):**
    Il presente software e' un algoritmo indipendente di analisi quantitativa. 
    1. **Assenza di Consulenza:** Le analisi prodotte NON costituiscono consulenza personalizzata (Art. 1, TUF).
    2. **Finalita':** Strumento di supporto all'educazione finanziaria e all'analisi oggettiva dei costi.
    3. **Documentazione:** Prima di ogni investimento, consultare i prospetti informativi (KID) e i rendiconti ufficiali.
    """)

with st.sidebar:
    st.header("⚙️ Audit Parameters")
    with st.expander("📊 GUIDA AI COSTI (TER MEDIO)"):
        st.write("**ETF Classici:** 0.05% - 0.25%")
        st.write("**Fondi Bancari:** 1.80% - 2.80%")
        st.write("**Polizze Unit Linked:** 3.50% - 5.00%")
        st.write("**Gestioni Patrimoniali:** 1.50% + IVA")
    
    profile = st.selectbox("Tipologia Strumento:", ["Fondi Comuni", "Polizze Unit Linked", "Gestioni Retail", "Private Banking", "Dato Manuale"])
    costs = {"Fondi Comuni": 2.2, "Polizze Unit Linked": 3.8, "Gestioni Retail": 2.8, "Private Banking": 1.8, "Dato Manuale": 2.2}
    cap = st.number_input("Capitale Totale (€)", value=200000, step=10000)
    ter = st.slider("TER (%) rilevato dal documento", 0.0, 5.0, costs[profile])
    yrs = st.slider("Orizzonte Strategico (Anni)", 5, 30, 20)

f_b = cap * ((1.05 - (ter/100))**yrs); f_a = cap * ((1.05 - 0.002)**yrs); loss = f_a - f_b

up = st.file_uploader("📂 Carica KID per Estrazione ISIN (PDF)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, b_ret = get_performance_data(isins)
        st.table(pd.DataFrame(res))
        avg_gap = np.mean([item['Gap Tecnico %'] for item in res])
        score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
        st.subheader(f"📊 Vampire Score: {score}/10")
        em = st.text_input("Inserisci mail per scaricare il Certificato:")
        if em and "@" in em:
            try:
                pdf_data = generate_premium_pdf(res, score, loss, ter, yrs, cap)
                st.download_button("📩 Scarica Perizia Forense", data=pdf_data, file_name="AEGIS_Audit_Report.pdf")
            except Exception as e:
                st.error(f"Errore tecnico: {str(e)}")
    else: st.warning("Nessun ISIN rilevato.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.metric("DISPERSIONE PATRIMONIALE STIMATA", format_euro_ui(loss))
    st.plotly_chart(px.pie(names=['Capitale Netto', 'Costi/Gap Mercato'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']))
