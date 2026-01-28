import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF
import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AEGIS: Quantitative Audit", layout="wide", page_icon="🛡️")

# --- MOTORE GENERAZIONE PDF (INDISTRUTTIBILE) ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'AEGIS | Audit Patrimoniale Tecnico', 0, 1, 'L')
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.multi_cell(0, 5, "Disclaimer: Il presente report e' un'elaborazione matematica di dati storici e non costituisce consulenza finanziaria personalizzata ai sensi del TUF.", 0, 'C')
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generate_premium_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(20, 33, 61) 
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.ln(10)

    # Box Verdetto
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VALUTAZIONE DI EFFICIENZA: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    status_msg = "CRITICA: Erosione strutturale severa rilevata." if score > 6 else "MIGLIORABILE: Margini di recupero ampi."
    pdf.cell(0, 10, f'STATO: {status_msg}', 0, 1, 'L')
    pdf.ln(20)

    # Analisi Perdita
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 10, '1. IL COSTO DEL SILENZIO (ANALISI COMPOSITA)', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    analisi_psico = (
        f"Al termine di {yrs} anni, il modello matematico prevede una dispersione di Euro {float(loss):,.0f}. "
        f"Questo capitale viene sottratto alla tua disponibilita' futura a causa di oneri non giustificati."
    )
    pdf.multi_cell(0, 6, analisi_psico)
    pdf.ln(10)

    # Tabella ISIN
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 10, ' CODICE ISIN', 1, 0, 'L', 1)
    pdf.cell(105, 10, ' STRUMENTO', 1, 0, 'L', 1)
    pdf.cell(45, 10, ' GAP TECNICO *', 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
    for item in data_list:
        gap_val = float(item['Gap Tecnico %'])
        pdf.cell(40, 10, f" {item['ISIN']}", 1)
        pdf.cell(105, 10, f" {str(item['Nome'])[:50]}", 1)
        if gap_val > 0: pdf.set_text_color(192, 57, 43)
        pdf.cell(45, 10, f"{gap_val}% ", 1, 1, 'R')
        pdf.set_text_color(0, 0, 0)

    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA FILTRO MILITARE ISIN ---
def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages: text += (page.extract_text() or "") + "\n"
        
        # Regex base: 2 lettere + 10 caratteri alfanumerici
        raw_finds = re.findall(r'\b[A-Z]{2}[A-Z0-9]{10}\b', text)
        
        # FILTRO CHIRURGICO: Un ISIN deve avere almeno 2 numeri (esclude parole come ANTIRICICLAGGIO)
        valid_isins = [
            isin for isin in raw_finds 
            if sum(c.isdigit() for c in isin) >= 2
        ]
        
        return list(set(valid_isins))
    except: return []

def get_performance_data(isin_list):
    results = []
    bench = "SWDA.MI" 
    try:
        b_data = yf.download(bench, period="5y", progress=False)
        b_ret = float(((b_data['Close'].iloc[-1] / b_data['Close'].iloc[0]) - 1) * 100)
    except: b_ret = 60.0 
    for isin in isin_list[:5]:
        try:
            t = yf.Ticker(isin); h = t.history(period="5y")
            f_ret = float(((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100) if not h.empty else 0.0
            results.append({"ISIN": isin, "Nome": t.info.get('longName', isin)[:50], "Gap Tecnico %": round(float(b_ret - f_ret), 2)})
        except: pass
    return results, b_ret

# --- INTERFACCIA ---
st.title("🛡️ AEGIS: Analizzatore Tecnico di Efficienza")

# --- BLINDATURA LEGALE (REINTEGRATA) ---
with st.expander("⚠️ NOTE LEGALI E DISCLAIMER - LEGGERE PRIMA DELL'USO"):
    st.caption("""
    AEGIS è un software di calcolo matematico basato su dati storici pubblici. 
    Le elaborazioni prodotte NON costituiscono:
    1. Consulenza in materia di investimenti (ex art. 1 comma 5 septies TUF).
    2. Sollecitazione al pubblico risparmio o raccomandazione personalizzata.
    L'utente dichiara di utilizzare i dati a scopo puramente informativo.
    """)

with st.sidebar:
    st.header("⚙️ Audit Setup")
    # --- GUIDA UTENTE (REINTEGRATA) ---
    with st.expander("❓ Dove trovo i costi?"):
        st.write("""
        Cerca 'Spese Correnti' o 'TER' nel documento KIID della tua banca. 
        **Medie di settore:**
        - Fondi comuni: 1.8% - 2.5%
        - Polizze Vita: 3% - 4.5%
        - ETF efficienti: 0.05% - 0.2%
        """)
    profile = st.selectbox("Profilo Prodotto:", ["Dato Manuale", "Fondi Comuni", "Gestioni Retail", "Polizze Unit Linked", "Private Banking"])
    costs = {"Dato Manuale": 2.2, "Fondi Comuni": 2.2, "Gestioni Retail": 2.8, "Polizze Unit Linked": 3.5, "Private Banking": 1.8}
    cap = st.number_input("Capitale (€)", value=200000, step=10000)
    ter = st.slider("Oneri Annui (%)", 0.0, 5.0, costs[profile])
    yrs = st.slider("Orizzonte (Anni)", 5, 30, 20)
    st.divider()
    st.info("Algoritmo AEGIS v2.4 - Indipendente.")

# Calcoli
f_b = cap * ((1 + 0.05 - (ter/100))**yrs)
f_a = cap * ((1 + 0.05 - 0.002)**yrs)
loss = f_a - f_b

up = st.file_uploader("📂 Carica Estratto Conto / KID (PDF)", type="pdf")

if up:
    with st.spinner("Filtraggio rumore e analisi ISIN..."):
        isins = analyze_pdf(up)
        if isins:
            res, b_ret = get_performance_data(isins)
            if res:
                st.table(pd.DataFrame(res))
                avg_gap = np.mean([item['Gap Tecnico %'] for item in res])
                score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
                st.subheader(f"📊 Vampire Score: {score}/10")
                
                # --- LEAD WALL ---
                st.divider()
                st.markdown("### 📥 Sblocca la Perizia Tecnica Completa")
                email = st.text_input("Inserisci la mail per scaricare il PDF:")
                if email and "@" in email:
                    try:
                        pdf_bytes = generate_premium_pdf(res, score, loss, ter, yrs, cap)
                        st.download_button("📩 Scarica Report Audit (PDF)", pdf_bytes, f"Audit_AEGIS.pdf", "application/pdf")
                    except Exception as e:
                        st.error(f"Errore PDF: {e}")
            else:
                st.error("Dati di mercato non recuperabili.")
        else:
            st.warning("Nessun ISIN valido rilevato. Il sistema ha escluso il rumore del testo.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.metric("EMORRAGIA PATRIMONIALE", f"€{loss:,.0f}", delta=f"-{ter}% cost/anno", delta_color="inverse")
    st.plotly_chart(px.pie(names=['Netto', 'Dispersione'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']))
with c2:
    st.markdown("### [📩 Contatta Analista](mailto:tua_mail@esempio.com)")
    st.write("Se lo score supera 5.0, la banca sta incassando più di te sul tuo rischio.")
