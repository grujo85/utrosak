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

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""CREATE TABLE IF NOT EXISTS radovi 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  datum TEXT, orman TEXT, opis TEXT, 
                  tip TEXT, kol REAL, jed TEXT, napomena TEXT)""")
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. KOMPLETNA LISTA MATERIJALA
# ==========================================
TIPOVI_MATERIJALA = [
    "Brezon M8", "Brezon M10", "C-šina 30x20", "C-šina 41x21", 
    "Regal 50", "Regal 100", "Regal 150", "Regal 200", "Regal 300", "Regal 400", "Regal 500", "Regal 600",
    "LR Krivina", "LR T-komad", "Poklopac regala",
    "PP-Y 2x1.5", "PP-Y 3x1.5", "PP-Y 3x2.5", "PP-Y 3x4", "PP-Y 4x1.5", "PP-Y 4x2.5", "PP-Y 4x4",
    "PP-Y 5x1.5", "PP-Y 5x2.5", "PP-Y 5x4", "PP-Y 5x6", "PP-Y 5x10", "PP-Y 5x16",
    "N2XH-J 3x1.5", "N2XH-J 3x2.5", "N2XH-J 3x4", "N2XH-J 5x1.5", "N2XH-J 5x2.5", "N2XH-J 5x4",
    "N2XH-J 5x6", "N2XH-J 5x10", "N2XH-J 5x16", "N2XH-J 5x25", "N2XH-J 5x35", "N2XH-J 5x50",
    "NHXH FE180 3x1.5", "NHXH FE180 3x2.5", "NHXH FE180 5x1.5", "NHXH FE180 5x2.5", "NHXH FE180 5x4", "NHXH FE180 5x6",
    "PP00 3x1.5", "PP00 3x2.5", "PP00 4x1.5", "PP00 4x2.5", "PP00 4x4", "PP00 4x6", "PP00 4x10",
    "PP00 4x16", "PP00 4x25", "PP00 4x35", "PP00 4x50", "PP00 4x70", "PP00 4x95", "PP00 4x120",
    "PP00 4x150", "PP00 4x185", "PP00 4x240", "PP00 5x1.5", "PP00 5x2.5", "PP00 5x4", "PP00 5x6",
    "PP00 5x10", "PP00 5x16", 
    "PP00-A (Al) 4x16", "PP00-A 4x25", "PP00-A 4x35", "PP00-A 4x50", 
    "PP00-A 4x70", "PP00-A 4x95", "PP00-A 4x120", "PP00-A 4x150", "PP00-A 4x240",
    "H07RN-F (GG/J) 3x1.5", "H07RN-F 3x2.5", "H07RN-F 5x1.5", "H07RN-F 5x2.5", "H07RN-F 5x4", 
    "H07RN-F 5x6", "H07RN-F 5x10", "H07RN-F 5x16", 
    "LiYCY 2x0.75", "LiYCY 3x0.75", "LiYCY 4x0.75", "LiYCY 5x0.75", "LiYCY 7x0.75", "LiYCY 12x0.75",
    "P/F (H07V-K) 0.75", "P/F 1.5", "P/F 2.5", "P/F 4", "P/F 6", "P/F 10", "P/F 16", "P/F 25", "P/F 35", "P/F 50",
    "P (H07V-U) 1.5", "P 2.5", "P 4", "P 6", 
    "SKS 2x16", "SKS 4x16", "SKS 4x25", "UTP Cat5e", "FTP Cat6", "SFTP Cat7", "Koaksijalni RG6", "Koaksijalni RG11",
    "Alarmni 4x0.22", "Alarmni 6x0.22", "Alarmni 8x0.22", "JH(St)H 2x2x0.8", "JH(St)H 4x2x0.8",
    "Solarni 4mm2", "Solarni 6mm2", "MONTAŽA", "DEMONTAŽA"
]

# ==========================================
# 3. PDF KLASA (Podržava srpska slova)
# ==========================================
class ElektroPDF(FPDF):
    def header(self):
        # Registracija fonta unutar klase
        if os.path.exists(FONT_FILE):
            self.add_font("DejaVu", "", FONT_FILE)
            self.set_font("DejaVu", "", 16)
        else:
            self.set_font("Helvetica", "B", 16)

        # Logo
        if os.path.exists("elmar.webp"):
            self.image("elmar.webp", 10, 8, 35)
            
        self.set_text_color(49, 130, 206)
        self.cell(0, 10, "ELEKTRO-LOG BUSINESS", ln=True, align="R")
        
        # Podnaslov sa datumom
        self.set_text_color(100)
        if os.path.exists(FONT_FILE):
            self.set_font("DejaVu", "", 10)
        else:
            self.set_font("Helvetica", "I", 10)
        self.cell(0, 5, f"Izveštaj o utrošku materijala - {datetime.now().strftime('%d.%m.%Y')}", ln=True, align="R")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        if os.path.exists(FONT_FILE):
            self.set_font("DejaVu", "", 8)
        else:
            self.set_font("Helvetica", "I", 8)
        self.set_text_color(150)
        self.cell(0, 10, f"ELMAR Elektro-instalacije | Strana {self.page_no()}", align="C")

# ==========================================
# 4. FORMULAR ZA UNOS
# ==========================================
st.title("ELEKTRO-LOG BUSINESS ⚡")

with st.form("glavna_forma", clear_on_submit=True):
    st.subheader("➕ Novi unos")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        u_datum = st.date_input("Datum", datetime.now()).strftime("%d.%m.%Y")
        u_orman = st.text_input("RO / Orman").upper().strip()
    with c2:
        u_opis = st.text_input("Krug / Opis")
        u_tip = st.selectbox("Materijal", TIPOVI_MATERIJALA)
    with c3:
        u_kol = st.number_input("Količina", min_value=0.0, step=0.1)
        u_jed = st.selectbox("Jedinica", ["m", "kom", "h"])
    with c4:
        u_napomena = st.text_input("Napomena")
        st.write("---")
        submit = st.form_submit_button("💾 SAČUVAJ", use_container_width=True)

if submit and u_orman:
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO radovi (datum, orman, opis, tip, kol, jed, napomena) VALUES (?,?,?,?,?,?,?)",
                 (u_datum, u_orman, u_opis, u_tip, u_kol, u_jed, u_napomena))
    conn.commit()
    conn.close()
    st.rerun()

# ==========================================
# 5. TABELA I PDF GENERACIJA
# ==========================================
st.divider()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql_query("SELECT * FROM radovi ORDER BY id DESC", conn)
conn.close()

if not df.empty:
    st.subheader("📋 Pregled unosa")
    edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")
    
    # Detekcija brisanja redova
    if len(edited_df) < len(df):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM radovi")
        edited_df.to_sql('radovi', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        st.rerun()

    st.write("---")
    if st.button("📄 GENERIŠI PDF IZVEŠTAJ", use_container_width=True):
        if not os.path.exists(FONT_FILE):
            st.error(f"GREŠKA: Fajl {FONT_FILE} nije pronađen na GitHub-u! PDF ne može imati srpska slova.")
        
        pdf = ElektroPDF()
        if os.path.exists(FONT_FILE):
            pdf.add_font("DejaVu", "", FONT_FILE)
            pdf.set_font("DejaVu", "", 10)
        
        pdf.add_page()
        
        # Zaglavlje tabele
        pdf.set_fill_color(49, 130, 206)
        pdf.set_text_color(255)
        pdf.cell(25, 10, "DATUM", border=1, align="C", fill=True)
        pdf.cell(30, 10, "ORMAN", border=1, align="C", fill=True)
        pdf.cell(45, 10, "OPIS", border=1, align="C", fill=True)
        pdf.cell(55, 10, "MATERIJAL", border=1, align="C", fill=True)
        pdf.cell(35, 10, "KOLIČINA", border=1, align="C", fill=True)
        pdf.ln()

        # Podaci iz baze
        pdf.set_text_color(0)
        for _, r in df.iterrows():
            pdf.cell(25, 8, str(r['datum']), border=1, align="C")
            pdf.cell(30, 8, str(r['orman']), border=1, align="C")
            pdf.cell(45, 8, str(r['opis'])[:25], border=1, align="L")
            pdf.cell(55, 8, str(r['tip']), border=1, align="L")
            pdf.cell(35, 8, f"{r['kol']} {r['jed']}", border=1, align="C")
            pdf.ln()

        # Rekapitulacija materijala
        pdf.ln(10)
        pdf.set_font("DejaVu" if os.path.exists(FONT_FILE) else "Helvetica", "B", 12)
        pdf.cell(0, 10, "ZBIRNA REKAPITULACIJA:", ln=True)
        
        pdf.set_font("DejaVu" if os.path.exists(FONT_FILE) else "Helvetica", "", 10)
        rekap = df.groupby(['tip', 'jed'])['kol'].sum().reset_index()
        for _, r in rekap.iterrows():
            pdf.cell(100, 7, f"- {r['tip']}:", border="B")
            pdf.cell(40, 7, f"{r['kol']:.2f} {r['jed']}", border="B", align="R", ln=True)

        pdf_bytes = pdf.output()
        st.download_button("📥 PREUZMI PDF", data=pdf_bytes, file_name="Izvestaj.pdf", mime="application/pdf")

# ==========================================
# 6. SIDEBAR (BACKUP & RESTORE)
# ==========================================
st.sidebar.title("⚙️ Administracija")

# Backup
if os.path.exists(DB_NAME):
    with open(DB_NAME, "rb") as f:
        st.sidebar.download_button("💾 Backup Baze", f, "backup.db", use_container_width=True)

# Restore
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Restore")
up_file = st.sidebar.file_uploader("Vrati bazu iz fajla", type="db")
if up_file:
    if st.sidebar.button("POVRATI PODATKE", use_container_width=True):
        with open(DB_NAME, "wb") as f:
            f.write(up_file.getbuffer())
        st.rerun()

# Brisanje
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ OBRIŠI SVE", use_container_width=True):
    if st.sidebar.checkbox("Potvrđujem brisanje"):
        conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM radovi"); conn.commit(); conn.close()
        st.rerun()
