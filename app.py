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

# --- FORMATTAZIONE CONTABILE ITALIANA ---
def format_euro_ui(amount):
    """Visualizzazione nell'interfaccia Streamlit"""
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def format_euro_pdf(amount):
    """Visualizzazione nel PDF (Standard EUR per compatibilità font)"""
    val_formattata = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"EUR {val_formattata}"

# --- MOTORE PDF (BLINDATURA E PROTOCOLLI) ---
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
        disclaimer = (
            "ESCLUSIONE DI RESPONSABILITA' EX ART. 1, 94 TUF: Elaborazione algoritmica di dati storici pubblici. "
            "Non costituisce consulenza personalizzata. AEGIS declina ogni responsabilita' per decisioni basate su questo documento."
        )
        self.multi_cell(0, 4, disclaimer, align='C')

def generate_premium_pdf(data_list, score, loss, ter, yrs, cap):
    pdf = AegisReport()
    pdf.add_page()
    
    # 1. TESTATA E VERDETTO
    pdf.set_font('helvetica', 'B', 22); pdf.set_text_color(20, 33, 61) 
    pdf.cell(0, 15, 'CERTIFICATO DI AUDIT PATRIMONIALE', 0, 1, 'C')
    pdf.ln(5)
    
    # Box Verdetto
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, 40, 190, 35, 'F')
    pdf.set_xy(15, 45); pdf.set_font('helvetica', 'B', 14); pdf.set_text_color(192, 57, 43) 
    pdf.cell(0, 10, f'VALUTAZIONE DI EFFICIENZA: {float(score)}/10', 0, 1, 'L')
    pdf.set_font('helvetica', '', 11); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f'STATO: {"CRITICA" if score > 6 else "MIGLIORABILE"}', 0, 1, 'L')
    
    # 2. ANALISI DISPERSIONE
    pdf.set_xy(10, 80); pdf.set_font('helvetica', 'B', 12); pdf.cell(0, 10, '1. ANALISI TECNICA DELLA DISPERSIONE', 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    loss_txt = format_euro_pdf(loss)
    pdf.multi_cell(0, 6, f"In un orizzonte di {yrs} anni, la proiezione evidenzia una dispersione stimata di {loss_txt} dovuta a inefficienze commissionali e gap di mercato rispetto al benchmark di riferimento.")
    pdf.ln(5)

    # 3. TABELLA ASSET ANALIZZATI
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
    
    # 4. PROTOCOLLI STRATEGICI (LOGICA CONDIZIONALE)
    pdf.ln(10)
    pdf.set_fill_color(20, 33, 61); pdf.set_text_color(255, 255, 255)
    pdf.set_font('helvetica', 'B', 12)
    
    if score > 6:
        pdf.cell(0, 10, ' PROTOCOLLO DI USCITA DA STATO CRITICO', 0, 1, 'L', 1)
        pdf.set_text_color(0, 0, 0); pdf.set_font('helvetica', '', 10); pdf.ln(2)
        protocollo = (
            "1. STOP ALIMENTAZIONE: Sospendere immediatamente versamenti ricorrenti (PAC) su questo strumento.\n"
            "2. AUDIT PENALI: Verificare l'esistenza di costi di uscita o commissioni di retrocessione.\n"
            "3. SOSTITUZIONE EFFICIENTE: Migrare verso strumenti a gestione passiva (ETF) per recuperare il gap tecnico.\n"
            "4. MONITORAGGIO TER: Non accettare strumenti con costi di gestione superiori allo 0.30% annuo."
        )
        pdf.multi_cell(0, 6, protocollo)
    else:
        pdf.cell(0, 10, ' CHECKLIST DI OTTIMIZZAZIONE PATRIMONIALE', 0, 1, 'L', 1)
        pdf.set_text_color(0, 0, 0); pdf.set_font('helvetica', '', 10); pdf.ln(2)
        checklist = (
            "1. EFFICIENTAMENTO FISCALE: Valutare se il regime fiscale attuale penalizza i rendimenti netti.\n"
            "2. ANALISI CORRELAZIONI: Verificare che la correlazione tra gli asset non superi la soglia di rischio 0.50.\n"
            "3. OTTIMIZZAZIONE SPREAD: Ridurre i costi di negoziazione scegliendo mercati a maggiore liquidita'.\n"
            "4. RE-BALANCING: Impostare una strategia di ribilanciamento automatico del portafoglio."
        )
        pdf.multi_cell(0, 6, checklist)
    
    return bytes(pdf.output())

# --- LOGICA DI ANALISI ---
def analyze_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for
