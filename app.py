import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import pdfplumber
import re
from fpdf import FPDF

# 1. SETUP AMBIENTE
st.set_page_config(page_title="AEGIS: Audit Quantitativo", layout="wide")

# 2. FUNZIONI SACRE DI FORMATTAZIONE
def f_euro(n):
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

# 3. MOTORE PDF CON BLINDATURA LEGALE
class AegisReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, 'AEGIS | Audit Quantitativo Indipendente', 0, 1, 'L')
    def footer(self):
        self.set_y(-25)
        self.set_font('helvetica', 'I', 7)
        self.multi_cell(0, 4, "DOC. TECNICO EX ART. 1 E 94 TUF: Non costituisce consulenza personalizzata.")

# 4. LOGICA ESTRAZIONE E DATI
def analyze_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for p in pdf.pages: text += (p.extract_text() or "") + "\n"
    return list(set(re.findall(r'\b[A-Z]{2}[A-Z0-9]{9}[0-9]{1}\b', text)))

def get_data(isins):
    res = []
    for i in isins[:5]:
        t = f"{i}.MI" if i.startswith("IT") else i
        tk = yf.Ticker(t)
        res.append({"ISIN": i, "Nome": tk.info.get('longName', i)[:40], "Gap %": 35.0})
    return res

# 5. INTERFACCIA E DASHBOARD (BLINDATA)
st.title("🛡️ AEGIS: Audit Quantitativo Indipendente")
st.error("⚖️ REDAZIONE TECNICA OBBLIGATORIA EX ART. 1 E 94 TUF")

# Sidebar
st.sidebar.header("Parametri")
cap = st.sidebar.number_input("Capitale (€)", value=200000)
ter = st.sidebar.slider("Costo TER (%)", 0.0, 5.0, 2.2)
yrs = st.sidebar.slider("Anni", 5, 30, 20)

# Calcoli
f_b = cap * ((1.05 - (ter/100))**yrs)
f_a = cap * ((1.05 - 0.002)**yrs)
loss = f_a - f_b

up = st.file_uploader("📂 Carica KID (PDF)", type="pdf")

if up:
    isins = analyze_pdf(up)
    if isins:
        data = get_data(isins)
        score = round(min((ter * 2) + 3, 10), 1)
        
        # --- DASHBOARD ---
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("DISPERSIONE STIMATA", f_euro(loss)) # <--- EURO
        c2.metric("INDICE INEFFICIENZA", f"{score}/10")
        c3.metric("EFFICIENZA", f"{round((f_b/f_a)*100, 1)}%")
        
        st.divider()
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("Forbice Patrimoniale")
            df = pd.DataFrame({
                'Anni': np.arange(yrs+1),
                'Efficiente': [cap*((1.05-0.002)**y) for y in np.arange(yrs+1)],
                'Attuale': [cap*((1.05-(ter/100))**y) for y in np.arange(yrs+1)]
            })
            st.plotly_chart(px.area(df, x='Anni', y=['Efficiente', 'Attuale'], color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True)
            st.table(pd.DataFrame(data))
            
        with col_right:
            st.subheader("Impatto Costi")
            st.plotly_chart(px.pie(names=['Netto', 'Gap'], values=[f_b, loss], hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True)
            st.info("**ISTRUZIONI:**\n1. Target TER < 0.30%\n2. Correlazione < 0.50\n3. Recupero Minus")
            
            if st.text_input("Email:"):
                st.download_button("📩 Scarica Audit PDF", data=b"PDF_DUMMY", file_name="AEGIS_Report.pdf")
    else:
        st.warning("Nessun ISIN trovato.")
