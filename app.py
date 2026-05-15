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
FONT_PATH = "DejaVuSans.ttf" # Proveri da li je ovaj fajl na GitHub-u!

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""CREATE TABLE IF NOT EXISTS radovi 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  datum TEXT, orman TEXT, opis TEXT, 
                  tip TEXT, kol REAL, jed TEXT, napomena TEXT)""")
    conn.commit()
    conn.close()

init_db()

# Funkcija za "čišćenje" teksta ako nema fonta (da ne puca PDF)
def clean_text(text):
    if not os.path.exists(FONT_PATH):
        replacements = {
            "š": "s", "Š": "S", "ć": "c", "Ć": "C", "č": "c", "Č": "C",
            "ž": "z", "Ž": "Z", "đ": "dj", "Đ": "Dj"
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
    return str(text)

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

# ==========================================
# 2. PDF KLASA
# ==========================================
class ElektroPDF(FPDF):
    def header(self):
        self.set_auto_page_break(auto=True, margin=15)
        if os.path.exists(FONT_PATH):
            self.add_font("CustomFont", "", FONT_PATH)
            self.set_font("CustomFont", "", 12)
        else:
            self.set_font("Helvetica", "B", 12)
        
        if os.path.exists("elmar.webp"):
            self.image("elmar.webp", 10, 8, 30)
        
        self.set_text_color(49, 130, 206)
        self.cell(0, 10, "ELEKTRO-LOG BUSINESS", 0, 1, "R")
        self.ln(5)

# ==========================================
# 3. PDF GENERACIJA
# ==========================================
def generate_pdf_bytes(df_input):
    pdf = ElektroPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("CustomFont", "", FONT_PATH)
        pdf.set_font("CustomFont", "", 10)
    else:
        pdf.set_font("Helvetica", "", 10)
    
    pdf.add_page()
    
    # Naslov tabele
    pdf.set_fill_color(44, 52, 70)
    pdf.set_text_color(255)
    w = [25, 35, 55, 45, 30]
    headers = ["DATUM", "ORMAN", "STAVKA", "OPIS", "KOL."]
    for col_w, h in zip(w, headers):
        pdf.cell(col_w, 10, h, 1, 0, "C", True)
    pdf.ln()

    # Podaci
    pdf.set_text_color(0)
    for i, r in df_input.iterrows():
        pdf.cell(25, 8, clean_text(r['datum']), 1, 0, "C")
        pdf.cell(35, 8, clean_text(r['orman']), 1, 0, "C")
        pdf.cell(55, 8, clean_text(r['tip']), 1, 0, "L")
        pdf.cell(45, 8, clean_text(r['opis'])[:20], 1, 0, "L")
        pdf.cell(30, 8, f"{r['kol']} {r['jed']}", 1, 1, "R")

    # Rekapitulacija
    pdf.ln(10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(190, 10, clean_text("ZBIRNA REKAPITULACIJA"), 1, 1, "C", True)

    rekap = df_input.groupby(['tip', 'jed'])['kol'].sum().reset_index()
    ukupno_kablovi = 0
    ukupno_regali = 0

    for _, row in rekap.iterrows():
        tip_upper = str(row['tip']).upper()
        is_kabel = any(x in tip_upper for x in ["PP-Y", "N2XH", "NHXH", "PP00", "SKS", "H07", "LIYCY", "UTP", "FTP"])
        is_regal = "REGAL" in tip_upper
        
        if is_kabel: ukupno_kablovi += row['kol']
        if is_regal: ukupno_regali += row['kol']

        pdf.cell(140, 8, f" {clean_text(row['tip'])} ({row['jed']})", 1, 0, "L")
        pdf.cell(50, 8, f"{row['kol']:.2f} ", 1, 1, "R")

    pdf.set_fill_color(240, 245, 255)
    pdf.cell(140, 9, clean_text(" SVI REGALI ZAJEDNO (m)"), 1, 0, "L", True)
    pdf.cell(50, 9, f"{ukupno_regali:.2f} m ", 1, 1, "R", True)
    
    pdf.set_fill_color(220, 235, 255)
    pdf.cell(140, 9, clean_text(" UKUPNO SVIH KABLOVA (m)"), 1, 0, "L", True)
    pdf.cell(50, 9, f"{ukupno_kablovi:.2f} m ", 1, 1, "R", True)

    return bytes(pdf.output())

# ==========================================
# 4. GLAVNA APLIKACIJA
# ==========================================
st.title("⚡ ELEKTRO-LOG BUSINESS")

with st.form("unos_forme", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        u_datum = st.date_input("Datum", datetime.now()).strftime("%d.%m.%Y")
        u_orman = st.text_input("RO / Orman").upper().strip()
    with col2:
        u_kat = st.selectbox("Grupa", list(MATERIJAL_STRUKTURA.keys()))
        u_tip = st.selectbox("Materijal", MATERIJAL_STRUKTURA[u_kat])
    with col3:
        u_kol = st.number_input("Količina", min_value=0.0, step=0.1)
        u_jed = st.selectbox("Jedinica", ["m", "kom", "h"])
    with col4:
        u_opis = st.text_input("Opis/Krug")
        u_napomena = st.text_input("Napomena")
        submit = st.form_submit_button("SAČUVAJ UNOS", use_container_width=True)

if submit and u_orman:
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO radovi (datum, orman, opis, tip, kol, jed, napomena) VALUES (?,?,?,?,?,?,?)",
                 (u_datum, u_orman, u_opis, u_tip, u_kol, u_jed, u_napomena))
    conn.commit()
    conn.close()
    st.rerun()

st.divider()

conn = sqlite3.connect(DB_NAME)
df = pd.read_sql_query("SELECT * FROM radovi ORDER BY id DESC", conn)
conn.close()

if not df.empty:
    st.subheader("📋 Lista unosa")
    edited_df = st.data_editor(df, use_container_width=True, hide_index=True, height=350)
    
    if not edited_df.equals(df):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM radovi")
        edited_df.to_sql('radovi', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        st.rerun()

    pdf_data = generate_pdf_bytes(edited_df)
    st.download_button(
        label="📥 PREUZMI PDF IZVEŠTAJ",
        data=pdf_data,
        file_name=f"Izvestaj_{datetime.now().strftime('%d_%m_%Y')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# SIDEBAR
st.sidebar.title("⚙️ Administracija")
if os.path.exists(DB_NAME):
    with open(DB_NAME, "rb") as f:
        st.sidebar.download_button("💾 Backup Baze", f, "baza.db", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Restore Podataka")
up_file = st.sidebar.file_uploader("Ubaci backup .db fajl", type="db")
if up_file and st.sidebar.button("POVRATI PODATKE"):
    with open(DB_NAME, "wb") as f:
        f.write(up_file.getbuffer())
    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ OBRIŠI SVE"):
    if st.sidebar.checkbox("Potvrđujem brisanje"):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM radovi")
        conn.commit()
        conn.close()
        st.rerun()
