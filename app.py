import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AEGIS: Quantitative Audit", layout="wide", page_icon="🛡️")

# --- 1. FUNZIONI DI FORMATTAZIONE (SOMME IN €) ---
def format_euro_ui(amount):
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def format_euro_pdf(amount):
    val_formattata = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"EUR {val_formattata}"

# --- 2. MOTORE PDF (BLINDATURA LEGALE INTEGRALE) ---
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
            "La scelta finale di investimento spetta esclusivamente all'utente previa consultazione dei prospetti (KID)."
        )
        self.multi_cell(0, 4, disclaimer, align='C')

def generate_safe_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page(); pdf.set_font('helvetica', 'B', 20); pdf.set_text_color(20, 33, 61)
    pdf.cell(0, 15, 'REDAZIONE TECNICA DI ANALISI PATRIMONIALE', 0, 1, 'C'); pdf.ln(10)
    
    # Box Indice
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, 45, 190, 40, 'F')
    pdf.set_xy(15, 50); pdf.set_font('helvetica', 'B', 14); pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'INDICE DI INEFFICIENZA RILEVATO: {float(score)}/10', 0, 1, 'L')
    
    # Somma in € nel PDF
    pdf.set_font('helvetica', '', 11); pdf.set_text_color(0)
    pdf.cell(0, 10, f'DISPERSIONE STIMATA: {format_euro_pdf(loss)}', 0, 1, 'L'); pdf.ln(20)

    # Istruzioni Tecniche nel PDF
    pdf.set_font('helvetica', 'B', 12); pdf.cell(0, 10, 'PARAMETRI DI OTTIMIZZAZIONE TECNICA', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    instructions = "- Riduzione del TER target < 0.30%\n- Verifica soglia di correlazione asset < 0.50\n- Ottimizzazione fiscale minusvalenze"
    pdf.multi_cell(0, 6, instructions); pdf.ln(5)

    return bytes(pdf.output())

# --- 3. ANALISI DATI ---
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
            if h.empty: results.append({"ISIN": isin, "Nome": f"Strumento {isin}", "Gap Tecnico %": 35.0})
            else:
                fr = float(((h['Close'].iloc[-1] / h['Close'].iloc[0]) - 1) * 100)
                results.append({"ISIN": isin, "Nome": tk.info.get('longName', isin)[:50], "Gap Tecnico %": round(float(br - fr), 2)})
        except: results.append({"ISIN": isin, "Nome": f"Dato non disponibile", "Gap Tecnico %": 35.0})
    return results, br

# --- 4. INTERFACCIA E DASHBOARD (GRAFICI E ISTRUZIONI) ---
st.title("🛡️ AEGIS: Audit Quantitativo Indipendente")
st.error("⚖️ **REDAZIONE TECNICA OBBLIGATORIA EX ART. 1 E 94 TUF**")

with st.sidebar:
    st.header("⚙️ Parametri Audit")
    p = st.selectbox("Tipologia:", ["Fondi Comuni", "Polizze Unit Linked", "Gestioni", "Dato Manuale"])
    costs = {"Fondi Comuni": 2.2, "Polizze Unit Linked": 3.8, "Gestioni": 2.2, "Dato Manuale": 2.2}
    cap = st.number_input("Capitale (€)", value=200000)
    ter = st.slider("Costo (TER %)", 0.0, 5.0, costs[p])
    yrs = st.slider("Orizzonte (Anni)", 5, 30, 20)

# Logica matematica
f_b = cap * ((1.05 - (ter/100))**yrs); f_a = cap * ((1.05 - 0.002)**yrs); loss = f_a - f_b

up = st.file_uploader("📂 Carica documento tecnico (KID)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        res, b_ret = get_performance_data(isins)
        score = round(min((ter * 2) + (np.mean([item['Gap Tecnico %'] for item in res]) / 10), 10), 1)
        
        # --- DASHBOARD EXECUTIVE ---
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("DISPERSIONE STIMATA", format_euro_ui(loss)) # <--- SOMMA IN €
        col2.metric("INDICE INEFFICIENZA", f"{score}/10")
        col3.metric("EFFICIENZA CAPITALE", f"{round((f_b/f_a)*100, 1)}%")

        st.divider()
        c1, c2 = st.columns([2, 1])
        with c1:
            st.write("**PROIEZIONE GRAFICA: Forbice Patrimoniale**")
            y_range = np.arange(0, yrs + 1)
            df_plot = pd.DataFrame({
                'Anni': y_range,
                'Efficiente': [cap * ((1.05 - 0.002)**y) for y in y_range],
                'Attuale': [cap * ((1.05 - (ter/100))**y) for y in y_range]
            })
            st.plotly_chart(px.area(df_plot, x='Anni', y=['Efficiente', 'Attuale'], 
                                   color_discrete_sequence=['#2ecc71', '#e74c3c'], template="plotly_white"), use_container_width=True) # <--- GRAFICO AREA
            st.table(pd.DataFrame(res))

        with c2:
            st.write("**IMPATTO COSTI**")
            st.plotly_chart(px.pie(names=['Netto', 'Costi/Gap'], values=[f_b, loss], 
                                   hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True) # <--- GRAFICO TORTA
            
            st.info("**ISTRUZIONI TECNICHE:**\n1. Riduci TER < 0.30%\n2. Verifica Correlazione < 0.50\n3. Recupero Minusvalenze")
            
            em = st.text_input("Inserisci mail per il report:")
            if em and "@" in em:
                pdf_data = generate_safe_pdf(res, score, loss, ter, yrs, cap)
                st.download_button("📩 Scarica Perizia Tecnico-Legale", data=pdf_data, file_name="AEGIS_Audit.pdf")
    else: st.warning("Nessun ISIN rilevato.")

st.divider(); st.caption("Analisi eseguita ex Art. 1 e 94 TUF.")
