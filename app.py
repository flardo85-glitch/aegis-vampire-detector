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

# --- FORMATTAZIONE CONTABILE ITALIANA (STILE BANCARIO) ---
def format_euro_ui(amount):
    """Visualizzazione nell'interfaccia Streamlit"""
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def format_euro_pdf(amount):
    """Visualizzazione nel PDF (Standard EUR per compatibilità font)"""
    val_formattata = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"EUR {val_formattata}"

# --- MOTORE PDF (BLINDATURA E COMPLIANCE) ---
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
        disclaimer = (
            "ESCLUSIONE DI RESPONSABILITA' EX ART. 1, 94 TUF: Il presente report e' un'elaborazione algoritmica di dati storici pubblici. "
            "Non costituisce sollecitazione al pubblico risparmio ne' consulenza personalizzata. "
            "AEGIS declina ogni responsabilita' per decisioni basate su questo documento."
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
    pdf.cell(0, 10, f'STATO: {"CRITICA" if score > 6 else "MIGLIORABILE"}', 0, 1, 'L')
    pdf.ln(20)

    # Analisi Perdita
    loss_txt = format_euro_pdf(loss)
    pdf.set_font('helvetica', 'B', 13); pdf.cell(0, 10, '1. ANALISI TECNICA DELLA DISPERS
