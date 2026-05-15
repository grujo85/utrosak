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
# 2. POMOĆNA FUNKCIJA ZA SLOVA (SIGURNOST)
# ==========================================
def s(text):
    """Vraća tekst spreman za PDF. Ako font fali, menja š,ć,č,ž u s,c,c,z"""
    if os.path.exists(FONT_FILE):
        return str(text)
    repl = {"š":"s","Š":"S","ć":"c","Ć":"C","č":"c","Č":"C","ž":"z","Ž":"Z","đ":"dj","Đ":"Dj"}
    res = str(text)
    for k, v in repl.items():
        res = res.replace(k, v)
    return res

# ==========================================
# 3. PDF KLASA I LOGIKA
# ==========================================
class ElektroPDF(FPDF):
    def header(self):
        if os.path.exists(FONT_FILE):
            self.add_font("Custom", "", FONT_FILE, uni=True)
            self.set_font("Custom", "", 14)
        else:
            self.set_font("Helvetica", "B", 14)
        
        if os.path.exists("elmar.webp"):
            self.image("elmar.webp", 10, 8, 30)
        
        self.set_text_color(49, 130, 206)
        self.cell(0, 10, "ELEKTRO-LOG BUSINESS", 0, 1, "R")
        self.set_text_color(100)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, f"Izvestaj - {datetime.now().strftime('%d.%m.%Y')}", 0, 1, "R")
        self.ln(10)

def generate_pdf_output(df):
    pdf = ElektroPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    if os.path.exists(FONT_FILE):
        pdf.add_font("Custom", "", FONT_FILE, uni=True)
        pdf.set_font("Custom", "", 10)
    else:
        pdf.set_font("Helvetica", "", 10)
    
    pdf.add_page()
    
    # Glavna tabela
    pdf.set_fill_color(44, 52, 70); pdf.set_text_color(255)
    w = [25, 35, 55, 45, 30]
    headers = ["DATUM", "ORMAN", "STAVKA", "OPIS", "KOL."]
    for col_w, h in zip(w, headers):
        pdf.cell(col_w, 10, h, 1, 0, "C", True)
    pdf.ln()

    pdf.set_text_color(0)
    for _, r in df.iterrows():
        pdf.cell(25, 8, s(r['datum']), 1, 0, "C")
        pdf.cell(35, 8, s(r['orman']), 1, 0, "C")
        pdf.cell(55, 8, s(r['tip']), 1, 0, "L")
        pdf.cell(45, 8, s(r['opis'])[:22], 1, 0, "L")
        pdf.cell(30, 8, f"{r['kol']} {r['jed']}", 1, 1, "R")

    # REKAPITULACIJA PO GRUPAMA (VRACENO SVE)
    pdf.ln(10)
    pdf.set_fill_color(44, 52, 70); pdf.set_text_color(255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(190, 10, "REKAPITULACIJA PO GRUPAMA", 0, 1, "C", True)
    
    if os.path.exists(FONT_FILE): pdf.set_font("Custom", "", 10)
    else: pdf.set_font("Helvetica", "", 10)

    rekap_full = df.groupby(['tip', 'jed'])['kol'].sum().reset_index()
    ukupno_kablovi, ukupno_regali = 0, 0
    
    for grupa, stavke in MATERIJAL_STRUKTURA.items():
        pod_rekap = rekap_full[rekap_full['tip'].isin(stavke)]
        if not pod_rekap.empty:
            if pdf.get_y() > 250: pdf.add_page()
            pdf.ln(2)
            pdf.set_fill_color(230, 235, 245); pdf.set_text_color(49, 130, 206)
            pdf.cell(190, 7, f" GRUPA: {s(grupa)}", 0, 1, "L", True)
            
            pdf.set_text_color(0)
            for _, row in pod_rekap.iterrows():
                t_up = str(row['tip']).upper()
                if any(x in t_up for x in ["PP-Y", "N2XH", "NHXH", "PP00", "SKS", "H07", "LIYCY", "P/F"]):
                    ukupno_kablovi += row['kol']
                if "REGAL" in t_up: ukupno_regali += row['kol']

                pdf.cell(140, 7, f" {s(row['tip'])} ({row['jed']})", 0, 0, "L")
                pdf.cell(50, 7, f"{row['kol']:.2f} ", 0, 1, "R")

    # TOTALI NA KRAJU
    pdf.ln(5)
    pdf.set_fill_color(240, 244, 248); pdf.cell(140, 9, " SVI REGALI ZAJEDNO (m)", 0, 0, "L", True)
    pdf.cell(50, 9, f"{ukupno_regali:.2f} m ", 0, 1, "R", True)
    pdf.set_fill_color(225, 235, 255); pdf.cell(140, 10, " UKUPNO SVIH KABLOVA (m)", 0, 0, "L", True)
    pdf.cell(50, 10, f"{ukupno_kablovi:.2f} m ", 0, 1, "R", True)

    # OUTPUT KAO BYTES (REŠAVA NONE I DOWNLOAD PROBLEM)
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# ==========================================
# 4. GLAVNI PROGRAM
# ==========================================
st.title("⚡ ELEKTRO-LOG BUSINESS")

with st.form("forma", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        u_dat = st.date_input("Datum", datetime.now()).strftime("%d.%m.%Y")
        u_orm = st.text_input("RO / Orman").upper().strip()
    with c2:
        u_kat = st.selectbox("Grupa", list(MATERIJAL_STRUKTURA.keys()))
        u_tip = st.selectbox("Materijal", MATERIJAL_STRUKTURA[u_kat])
    with c3:
        u_kol = st.number_input("Količina", min_value=0.0, step=0.1)
        u_jed = st.selectbox("Jedinica", ["m", "kom", "h"])
    with c4:
        u_opi = st.text_input("Opis/Krug")
        u_nap = st.text_input("Napomena")
        submit = st.form_submit_button("DODAJ UNOS", use_container_width=True)

if submit and u_orm:
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO radovi (datum, orman, opis, tip, kol, jed, napomena) VALUES (?,?,?,?,?,?,?)",
                 (u_dat, u_orm, u_opi, u_tip, u_kol, u_jed, u_nap))
    conn.commit(); conn.close(); st.rerun()

st.divider()

conn = sqlite3.connect(DB_NAME)
df = pd.read_sql_query("SELECT * FROM radovi ORDER BY id DESC", conn)
conn.close()

if not df.empty:
    st.subheader("📋 Pregled tabele")
    # Tabela sa fiksnom visinom da ne skroluješ dole kilometrima
    ed_df = st.data_editor(df, use_container_width=True, hide_index=True, height=400)
    
    if not ed_df.equals(df):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM radovi")
        ed_df.to_sql('radovi', conn, if_exists='append', index=False)
        conn.commit(); conn.close(); st.rerun()

    # GENERISANJE PDF-a
    pdf_final = generate_pdf_output(ed_df)
    st.download_button(
        label="📥 PREUZMI PDF IZVEŠTAJ",
        data=pdf_final,
        file_name=f"Izvestaj_{datetime.now().strftime('%d_%m_%H_%M')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# SIDEBAR (ADMIN I BACKUP)
st.sidebar.title("⚙️ Admin")
if os.path.exists(DB_NAME):
    with open(DB_NAME, "rb") as fb:
        st.sidebar.download_button("💾 Backup Baze", fb, "baza.db", use_container_width=True)

res = st.sidebar.file_uploader("Vrati bazu", type="db")
if res and st.sidebar.button("RESTAURIRAJ"):
    with open(DB_NAME, "wb") as f: f.write(res.getbuffer())
    st.rerun()
