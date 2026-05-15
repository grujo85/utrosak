import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
from fpdf import FPDF

# ==========================================
# 1. KONFIGURACIJA I BAZA PODATAKA
# ==========================================
st.set_page_config(page_title="ELEKTRO-LOG BUSINESS", layout="wide")
DB_NAME = 'elektro_baza.db'
FONT_FILE = "DejaVuSans.ttf"
FONT_FILE_BOLD = "DejaVuSans-Bold.ttf"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""CREATE TABLE IF NOT EXISTS radovi 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  datum TEXT, orman TEXT, opis TEXT, 
                  tip TEXT, kol REAL, jed TEXT, napomena TEXT)""")
    conn.commit()
    conn.close()

init_db()

MATERIJAL_STRUKTURA = {
    "NOSAČI I REGALI": ["Regal 50", "Regal 100", "Regal 150", "Regal 200", "Regal 300", "Regal 400", "Regal 500", "Regal 600"],
    "OPREMA ZA REGALE": ["LR Krivina", "LR T-komad", "Poklopac regala", "C-šina 30x20", "C-šina 41x21", "Brezon M8", "Brezon M10"],
    "INSTALACIONI KABLOVI (PP-Y)": ["PP-Y 2x1.5", "PP-Y 3x1.5", "PP-Y 3x2.5", "PP-Y 3x4", "PP-Y 4x1.5", "PP-Y 4x2.5", "PP-Y 4x4", "PP-Y 5x1.5", "PP-Y 5x2.5", "PP-Y 5x4", "PP-Y 5x6", "PP-Y 5x10", "PP-Y 5x16"],
    "BEZHALOGENI KABLOVI (N2XH)": ["N2XH-J 3x1.5", "N2XH-J 3x2.5", "N2XH-J 3x4", "N2XH-J 5x1.5", "N2XH-J 5x2.5", "N2XH-J 5x4", "N2XH-J 5x6", "N2XH-J 5x10", "N2XH-J 5x16", "N2XH-J 5x25", "N2XH-J 5x35", "N2XH-J 5x50"],
    "VATROOTPORNI KABLOVI (NHXH)": ["NHXH FE180 3x1.5", "NHXH FE180 3x2.5", "NHXH FE180 5x1.5", "NHXH FE180 5x2.5", "NHXH FE180 5x4", "NHXH FE180 5x6"],
    "NAPOJNI KABLOVI (PP00)": ["PP00 3x1.5", "PP00 3x2.5", "PP00 4x1.5", "PP00 4x2.5", "PP00 4x4", "PP00 4x6", "PP00 4x10", "PP00 4x16", "PP00 4x25", "PP00 4x35", "PP00 4x50", "PP00 4x70", "PP00 4x95", "PP00 4x120", "PP00 4x150", "PP00 4x185", "PP00 4x240", "PP00 5x1.5", "PP00 5x2.5", "PP00 5x4", "PP00 5x6", "PP00 5x10", "PP00 5x16"],
    "ALUMINIJUMSKI KABLOVI": ["PP00-A (Al) 4x16", "PP00-A 4x25", "PP00-A 4x35", "PP00-A 4x50", "PP00-A 4x70", "PP00-A 4x95", "PP00-A 4x120", "PP00-A 4x150", "PP00-A 4x240", "SKS 2x16", "SKS 4x16", "SKS 4x25"],
    "GUMIRANI I FLEKSIBILNI": ["H07RN-F (GG/J) 3x1.5", "H07RN-F 3x2.5", "H07RN-F 5x1.5", "H07RN-F 5x2.5", "H07RN-F 5x4", "H07RN-F 5x6", "H07RN-F 5x10", "H07RN-F 5x16", "LiYCY 2x0.75", "LiYCY 3x0.75", "LiYCY 4x0.75", "LiYCY 5x0.75", "LiYCY 7x0.75", "LiYCY 12x0.75"],
    "DOVODNE ŽICE (P / PF)": ["P/F 0.75", "P/F 1.5", "P/F 2.5", "P/F 4", "P/F 6", "P/F 10", "P/F 16", "P/F 25", "P/F 35", "P/F 50", "P 1.5", "P 2.5", "P 4", "P 6"],
    "TELEKOMUNIKACIJE": ["UTP Cat5e", "FTP Cat6", "SFTP Cat7", "RG6", "RG11", "Alarmni 4x0.22", "Alarmni 6x0.22", "JH(St)H 2x2x0.8", "Solarni 6mm2"],
    "RADOVI": ["MONTAŽA", "DEMONTAŽA"]
}

class ElektroPDF(FPDF):
    def header(self):
        self.set_auto_page_break(auto=True, margin=15)
        if os.path.exists(FONT_FILE):
            self.add_font("DejaVu", "", FONT_FILE)
            self.set_font("DejaVu", "", 14)
        else: self.set_font("Helvetica", "B", 14)
        if os.path.exists("elmar.webp"): self.image("elmar.webp", 10, 8, 30)
        self.set_text_color(49, 130, 206)
        self.cell(0, 10, "ELEKTRO-LOG BUSINESS", 0, 1, "R")
        self.set_text_color(100)
        self.set_font("DejaVu" if os.path.exists(FONT_FILE) else "Helvetica", "", 9)
        self.cell(0, 5, f"Izveštaj - {datetime.now().strftime('%d.%m.%Y')}", 0, 1, "R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu" if os.path.exists(FONT_FILE) else "Helvetica", "", 8)
        self.set_text_color(150)
        self.cell(0, 10, f"{self.page_no()}", align="C")

# ==========================================
# 4. POMOĆNE FUNKCIJE
# ==========================================
def create_pdf_data(dataframe):
    pdf = ElektroPDF()
    has_reg, has_bold = os.path.exists(FONT_FILE), os.path.exists(FONT_FILE_BOLD)
    if has_reg:
        pdf.add_font("DejaVu", "", FONT_FILE)
        if has_bold: pdf.add_font("DejaVu", "B", FONT_FILE_BOLD)
        pdf.set_font("DejaVu", "", 10)
    
    pdf.add_page()
    
    # GLAVNA TABELA
    pdf.set_fill_color(49, 130, 206); pdf.set_text_color(255)
    if has_bold: pdf.set_font("DejaVu", "B", 10)
    w_cols = [25, 35, 50, 45, 35]
    headers = ["DATUM", "ORMAN", "MATERIJAL", "OPIS", "KOL."]
    for w, h in zip(w_cols, headers): pdf.cell(w, 10, h, 0, 0, "C", True)
    pdf.ln()

    pdf.set_text_color(0); pdf.set_font("DejaVu" if has_reg else "Helvetica", "", 9)
    for i, r in dataframe.iterrows():
        # ISPRAVLJENO: Jasnije definisana boja pozadine reda
        if i % 2 == 0:
            pdf.set_fill_color(248, 248, 248)
        else:
            pdf.set_fill_color(255, 255, 2
