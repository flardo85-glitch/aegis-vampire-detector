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

# --- FUNZIONE FORMATTAZIONE MONETARIA (CORRETTA) ---
def format_euro_ui(amount):
    """Per la visualizzazione nell'app Streamlit"""
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

# --- MOTORE PDF (BLINDATURA E FIX EURO) ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'AEGIS | Audit Patrimoniale Tecnico', 0, 1, 'L')
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-30)
        self.set_font('helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        # Sostituzione manuale dell'apice e dei simboli per evitare crash
        disclaimer = (
            "ESCLUSIONE DI RESPONSABILITA' EX ART. 1, 94 TUF: Il presente report e' un'elaborazione algoritmica di dati storici pubblici. "
            "Non costituisce sollecitazione al pubblico risparmio ne' consulenza personalizzata. "
            "L'accuratezza dei dati dipende dalle fonti terze. AEGIS declina ogni responsabilita' per decisioni basate su questo documento."
        )
        self.multi_cell(0, 4, disclaimer, align='C')

def generate_premium_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page()
    
    # Titolo
    pdf.set_font('helvetica', 'B', 22); pdf.set_text_color(20, 33, 61) 
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.ln(10)
    
    # Box Verdetto
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50); pdf.set_font('helvetica', 'B', 14); pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VALUTAZIONE DI EFFICIENZA: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('helvetica', '', 11); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f'STATO: {"CRITICA" if score > 6 else "MIGLIORABILE"}', 0, 1, 'L')
    pdf.ln(20)

    # Analisi Perdita
    # Nota: Usiamo "EUR" come testo per massima sicurezza o il carattere latin-1 mappato
    valuta = "EUR" 
    perdita_testo = f"{float(loss):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    pdf.set_font('helvetica', 'B', 13); pdf.cell(0, 10, '1. ANALISI TECNICA DELLA DISPERSIONE', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"In un orizzonte di {yrs} anni, la proiezione evidenzia una dispersione stimata di {valuta} {perdita_testo} dovuta a inefficienze commissionali e gap di mercato.")
    pdf.ln(10)

    # Tabella
    pdf.set_font('helvetica', 'B', 10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255)
    pdf.cell(45, 10, ' ISIN RILEVATO', 1, 0, 'L', 1)
    pdf.cell(100, 10, ' STRUMENTO FINANZIARIO', 1, 0, 'L', 1)
    pdf.cell(45, 10, ' GAP TECNICO %', 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font('helvetica', '', 9)
    for item in data_list:
        nome_pulito = item['Nome'].encode('ascii', 'ignore').decode('ascii')
        pdf.cell(45, 10, f" {item['ISIN']}", 1)
        pdf.cell(100, 10, f" {nome_pulito[:50]}", 1)
        pdf.cell(45, 10, f"{float(item['Gap Tecnico %'])}% ", 1, 1, 'R')
    
    return bytes(pdf.output())

# --- LOGICA FILTRO E RECUPERO ---
def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages: text += (page.extract_text() or "") + "\n"
        raw_finds = re.findall(r'\b[A-Z]{2}[A-Z0-9]{9}[0-9]{1}\b', text)
        return list(set([i for i in raw_finds if sum(c.isdigit() for c in i) >= 3]))
    except: return []

def get_performance_data(isin_list):
    results = []
    bench = "SWDA.MI"
    try:
        b_data = yf.download(bench, period="5y", progress=False)
        b_ret = float(((b_data['Close'].iloc[-1] / b_data['Close'].iloc[0]) - 1) * 100) if not b_data.empty else 65.0
    except: b_ret = 65.0
    for isin in isin_list[:5]:
        ticker = f"{isin}.MI" if isin.startswith("IT") else isin
        try:
            t = yf.Ticker(ticker); h = t.history(period="5y")
            if h.empty:
                f_ret = 18.0 
                name = f"Fondo Bancario ({isin})"
            else:
                f_ret = float(((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100)
                name = t.info.get('longName', isin)[:50]
            results.append({"ISIN": isin, "Nome": name, "Gap Tecnico %": round(float(b_ret - f_ret), 2)})
        except:
            results.append({"ISIN": isin, "Nome": f"Strumento {isin}", "Gap Tecnico %": 35.0})
    return results, b_ret

# --- INTERFACCIA STREAMLIT ---
st.title("🛡️ AEGIS: Analizzatore Tecnico di Efficienza")

with st.container():
    st.error("⚖️ **DISCLAIMER LEGALE OBBLIGATORIO - AI SENSI DEL TUF**")
    st.caption("""
    IL PRESENTE SOFTWARE OPERA COME MERO STRUMENTO DI CALCOLO MATEMATICO.
    - **Assenza di Consulenza:** Le analisi NON costituiscono consulenza ai sensi dell'Art. 1, c. 5-septies D.Lgs. 58/98.
    - **Indipendenza:** AEGIS opera come audit indipendente. Consultare i documenti ufficiali (KID).
    """)

with st.sidebar:
    st.header("⚙️ Audit Setup")
    with st.expander("❓ Guida ai Costi (TER)"):
        st.write("Efficienza: 0.2% | Bancari: 2.2% | Polizze: 3.8%")
    profile = st.selectbox("Seleziona Prodotto:", ["Fondi Comuni", "Polizze Unit Linked", "Gestioni Retail", "Private Banking", "Dato Manuale"])
    costs = {"Fondi Comuni": 2.2, "Polizze Unit Linked": 3.8, "Gestioni Retail": 2.8, "Private Banking": 1.8, "Dato Manuale": 2.2}
    cap = st.number_input("Capitale Totale (€)", value=200000, step=10000)
    ter = st.slider("TER (%) rilevato dal KID", 0.0, 5.0, costs[profile])
    yrs = st.slider("Orizzonte (Anni)", 5, 30, 20)

f_b = cap * ((1 + 0.05 - (ter/100))**yrs); f_a = cap * ((1 + 0.05 - 0.002)**yrs); loss = f_a - f_b

up = st.file_uploader("📂 Carica Documento per Audit ISIN (PDF)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, b_ret = get_performance_data(isins)
        st.table(pd.DataFrame(res))
        avg_gap = np.mean([item['Gap Tecnico %'] for item in res])
        score = round(min((ter * 2) + (avg_gap / 10), 10), 1)
        st.subheader(f"📊 Vampire Score: {score}/10")
        st.divider()
        email = st.text_input("Inserisci Mail per scaricare l'Audit:")
        if email and "@" in email:
            try:
                pdf_data = generate_premium_pdf(res, score, loss, ter, yrs, cap)
                st.download_button(
                    label="📩 Scarica Perizia Tecnica (PDF)",
                    data=pdf_data,
                    file_name="Perizia_AEGIS.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Errore critico: {str(e)}")
    else:
        st.warning("Nessun ISIN conforme rilevato.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.metric("DISPERSIONE PATRIMONIALE STIMATA", format_euro_ui(loss))
    st.plotly_chart(px.pie(names=['Netto', 'Costi'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']))
