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

# Šifarnik materijala
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
        self.set_font("DejaVu" if os.path.exists(FONT_FILE) else "Helvetica", "", 10)
        self.set_text_color(120)
        self.cell(0, 10, "ELMAR ELEKTROINSTALACIJE", align="C")

# ==========================================
# 3. PDF GENERACIJA
# ==========================================
def create_pdf_data(dataframe):
    pdf = ElektroPDF()
    has_reg, has_bold = os.path.exists(FONT_FILE), os.path.exists(FONT_FILE_BOLD)
    if has_reg:
        pdf.add_font("DejaVu", "", FONT_FILE)
        if has_bold: pdf.add_font("DejaVu", "B", FONT_FILE_BOLD)
        pdf.set_font("DejaVu", "", 10)
    
    pdf.add_page()
    
    # Glavna tabela
    pdf.set_fill_color(49, 130, 206); pdf.set_text_color(255)
    if has_bold: pdf.set_font("DejaVu", "B", 10)
    w_cols = [25, 35, 50, 45, 35]
    headers = ["DATUM", "ORMAN", "MATERIJAL", "OPIS", "KOL."]
    for w, h in zip(w_cols, headers): pdf.cell(w, 10, h, 0, 0, "C", True)
    pdf.ln()

    pdf.set_text_color(0); pdf.set_font("DejaVu" if has_reg else "Helvetica", "", 9)
    for i, r in dataframe.iterrows():
        pdf.set_fill_color(248, 248, 248) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.cell(25, 8, str(r['datum']), 0, 0, "C", True)
        pdf.cell(35, 8, str(r['orman']), 0, 0, "C", True)
        pdf.cell(50, 8, str(r['tip']), 0, 0, "C", True)
        pdf.cell(45, 8, str(r['opis'])[:22], 0, 0, "C", True)
        pdf.cell(35, 8, f"{r['kol']} {r['jed']}", 0, 1, "C", True)

    # Rekapitulacija
    if pdf.get_y() > 180: pdf.add_page()
    else: pdf.ln(10)

    pdf.set_fill_color(44, 52, 70); pdf.set_text_color(255)
    if has_bold: pdf.set_font("DejaVu", "B", 11)
    pdf.cell(190, 10, "REKAPITULACIJA PO GRUPAMA", 0, 1, "C", True)

    rekap_full = dataframe.groupby(['tip', 'jed'])['kol'].sum().reset_index()
    ukupno_regali = 0
    ukupno_kablovi = 0
    
    # Širina tabele rekapitulacije
    w_naziv, w_kol = 120, 40  # Ukupno 160mm
    total_w = w_naziv + w_kol
    offset = (190 - total_w) / 2

    for grupa, stavke in MATERIJAL_STRUKTURA.items():
        pod_rekap = rekap_full[rekap_full['tip'].isin(stavke)]
        if not pod_rekap.empty:
            visina_grupe = 7 + (len(pod_rekap) * 7)
            if pdf.get_y() + visina_grupe > 270: pdf.add_page()
            
            pdf.ln(2)
            pdf.set_x(10 + offset)
            pdf.set_fill_color(230, 235, 245); pdf.set_text_color(49, 130, 206)
            if has_bold: pdf.set_font("DejaVu", "B", 9)
            pdf.cell(total_w, 7, f" GRUPA: {grupa}", 0, 1, "L", True)
            
            pdf.set_text_color(0); pdf.set_font("DejaVu" if has_reg else "Helvetica", "", 10)
            for _, row in pod_rekap.iterrows():
                if "REGALI" in grupa or "NOSAČI" in grupa: ukupno_regali += row['kol']
                if any(x in grupa for x in ["KABLOVI", "ŽICE", "GUMIRANI", "BEZHALOGENI", "VATROOTPORNI", "NAPOJNI"]): 
                    ukupno_kablovi += row['kol']
                
                pdf.set_x(10 + offset)
                # Naziv levo, Količina desno
                pdf.cell(w_naziv, 7, f" {row['tip']} ({row['jed']})", 0, 0, "L")
                pdf.cell(w_kol, 7, f"{row['kol']:.2f} ", 0, 1, "R")

    # Totali na kraju rekapitulacije
    if pdf.get_y() > 250: pdf.add_page()
    pdf.ln(5); 
    pdf.set_x(10 + offset)
    pdf.set_fill_color(240, 244, 248); pdf.set_text_color(0)
    if has_bold: pdf.set_font("DejaVu", "B", 10)
    pdf.cell(w_naziv, 9, " SVI REGALI ZAJEDNO (m)", 0, 0, "L", True)
    pdf.cell(w_kol, 9, f"{ukupno_regali:.2f} m ", 0, 1, "R", True)
    
    pdf.set_x(10 + offset)
    pdf.set_fill_color(230, 242, 255); pdf.set_text_color(49, 130, 206)
    pdf.cell(w_naziv, 10, " UKUPNO SVIH KABLOVA (m)", 0, 0, "L", True)
    pdf.cell(w_kol, 10, f"{ukupno_kablovi:.2f} m ", 0, 1, "R", True)

    return pdf.output()

# ==========================================
# 4. STREAMLIT APLIKACIJA
# ==========================================
st.title("ELEKTRO-LOG BUSINESS ⚡")

with st.form("glavna_forma", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        u_datum = st.date_input("Datum", datetime.now()).strftime("%d.%m.%Y")
        u_orman = st.text_input("RO / Orman").upper().strip()
    with c2:
        kat_izbor = st.selectbox("Grupa", list(MATERIJAL_STRUKTURA.keys()))
        u_tip = st.selectbox("Stavka", MATERIJAL_STRUKTURA[kat_izbor])
    with c3:
        u_kol = st.number_input("Količina", min_value=0.0, step=0.1)
        u_jed = st.selectbox("Jedinica", ["m", "kom", "h"])
    with c4:
        u_opis = st.text_input("Krug / Opis")
        u_napomena = st.text_input("Napomena")
        submit = st.form_submit_button("💾 SAČUVAJ", use_container_width=True)

if submit and u_orman:
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO radovi (datum, orman, opis, tip, kol, jed, napomena) VALUES (?,?,?,?,?,?,?)",
                 (u_datum, u_orman, u_opis, u_tip, u_kol, u_jed, u_napomena))
    conn.commit(); conn.close(); st.rerun()

st.divider()

conn = sqlite3.connect(DB_NAME)
df = pd.read_sql_query("SELECT * FROM radovi ORDER BY orman ASC, id DESC", conn)
conn.close()

if not df.empty:
    st.subheader("📋 Pregled unosa")
    edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")
    
    if not edited_df.equals(df):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM radovi")
        edited_df.to_sql('radovi', conn, if_exists='append', index=False)
        conn.commit(); conn.close(); st.rerun()

    # 1. Generiši PDF sadržaj
    pdf_output = create_pdf_data(edited_df)
    
    # 2. Pretvori u bajtove ako već nisu (rešava "None" i greške enkodinga)
    if isinstance(pdf_output, str):
        pdf_bytes = pdf_output.encode('latin-1')
    else:
        pdf_bytes = pdf_output

    # 3. Dugme za preuzimanje
    st.download_button(
        label="📥 PREUZMI PDF IZVEŠTAJ",
        data=pdf_bytes,
        file_name=f"Izvestaj_{datetime.now().strftime('%d_%m_%Y')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# ==========================================
# 5. SIDEBAR (BACKUP, RESTORE, DELETE)
# ==========================================
st.sidebar.title("⚙️ Administracija")

if os.path.exists(DB_NAME):
    with open(DB_NAME, "rb") as f:
        st.sidebar.download_button("💾 Backup Baze", f, "backup.db", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Restore Podataka")
up_file = st.sidebar.file_uploader("Ubaci backup.db fajl", type="db")
if up_file is not None:
    if st.sidebar.button("POVRATI PODATKE"):
        with open(DB_NAME, "wb") as f:
            f.write(up_file.getbuffer())
        st.sidebar.success("Podaci su uspesno vraceni!")
        st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ OBRIŠI SVE"):
    if st.sidebar.checkbox("Potvrđujem brisanje"):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM radovi")
        conn.commit(); conn.close(); st.rerun()
