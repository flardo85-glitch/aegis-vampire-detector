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
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " EUR"

def format_euro_pdf(amount):
    val_formattata = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"EUR {val_formattata}"

# --- MOTORE PDF ---
class AegisReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'AEGIS | Audit Patrimoniale Tecnico', 0, 1, 'L')
        self.line(10, 20, 200, 20)
        self.ln(10)
    def footer(self):
        self.set_y(-25)
        self.set_font('helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        disclaimer = "ESCLUSIONE DI RESPONSABILITA' EX ART. 1, 94 TUF: Elaborazione algoritmica indipendente."
        self.cell(0, 10, disclaimer, 0, 0, 'C')

def generate_premium_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 22); pdf.set_text_color(20, 33, 61) 
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.ln(5)
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, 40, 190, 35, 'F')
    pdf.set_xy(15, 45); pdf.set_font('helvetica', 'B', 14); pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VALUTAZIONE DI EFFICIENZA: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('helvetica', '', 11); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f'STATO: {"CRITICA" if score > 6 else "MIGLIORABILE"}', 0, 1, 'L')
    pdf.set_xy(10, 80); pdf.set_font('helvetica', 'B', 12); pdf.cell(0, 10, '1. ANALISI TECNICA DELLA DISPERSIONE', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"In un orizzonte di {yrs} anni, la proiezione evidenzia una dispersione stimata di {format_euro_pdf(loss)} dovuta a inefficienze commissionali e gap di mercato.")
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255)
    pdf.cell(45, 10, ' ISIN RILEVATO', 1, 0, 'L', 1)
    pdf.cell(100, 10, ' STRUMENTO FINANZIARIO', 1, 0, 'L', 1)
    pdf.cell(45, 10, ' GAP TECNICO %', 1, 1, 'C', 1)
    pdf.set_text_color(0, 0, 0); pdf.set_font('helvetica', '', 9)
    for item in data_list:
        pdf.cell(45, 10, f" {item['ISIN']}", 1)
        pdf.cell(100, 10, f" {item['Nome'][:50]}", 1)
        pdf.cell(45, 10, f"{float(item['Gap Tecnico %'])}% ", 1, 1, 'R')
    pdf.ln(10); pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255); pdf.set_font('helvetica', 'B', 12)
    if score > 6:
        pdf.cell(0, 10, ' PROTOCOLLO DI USCITA DA STATO CRITICO', 0, 1, 'L', 1)
        pdf.set_text_color(0, 0, 0); pdf.set_font('helvetica', '', 10); pdf.ln(2)
        pdf.multi_cell(0, 6, "1. STOP ALIMENTAZIONE: Sospendere PAC.\n2. AUDIT PENALI: Verificare costi uscita.\n3. SOSTITUZIONE: Migrare verso ETF.\n4. TER TARGET: Sotto 0.30%.")
    else:
        pdf.cell(0, 10, ' CHECKLIST DI OTTIMIZZAZIONE PATRIMONIALE', 0, 1, 'L', 1)
        pdf.set_text_color(0, 0, 0); pdf.set_font('helvetica', '', 10); pdf.ln(2)
        pdf.multi_cell(0, 6, "1. FISCO: Ottimizzare efficienza fiscale.\n2. CORRELAZIONI: Verificare soglia < 0.50.\n3. S
