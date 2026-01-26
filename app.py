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

# --- MOTORE PDF ---
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
        self.multi_cell(0, 5, "Analisi matematica basata su dati storici. Non costituisce sollecitazione al pubblico risparmio.", 0, 'C')
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
    pdf.rect(10, 40, 190, 35, 'F')
    pdf.set_xy(15, 45)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VAMPIRE SCORE: {score}/10', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    status = "CRITICO: Forte erosione in corso." if score > 6 else "INEFFICIENTE: Margini di recupero ampi."
    pdf.cell(0, 10, f"STATO: {status}", 0, 1, 'L')
    pdf.ln(15)

    # Analisi Perdita
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 10, '1. IMPATTO DEI COSTI COMPOSTI', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    analisi = (f"La proiezione a {yrs} anni evidenzia una dispersione patrimoniale di Euro {loss:,.0f}. "
               f"Questo capitale viene sottratto alla tua disponibilità futura a causa di oneri non giustificati.")
    pdf.multi_cell(0, 6, analisi)
    pdf.ln(5)

    # Tabella ISIN
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255)
    pdf.cell(35, 10, ' ISIN', 1, 0, 'L', 1)
    pdf.cell(110, 10, ' STRUMENTO', 1, 0, 'L', 1)
    pdf.cell(45, 10, ' GAP TECNICO *', 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
    for item in data_list:
        pdf.cell(35, 10, f" {item['ISIN']}", 1)
        pdf.cell(110, 1
