import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
from io import BytesIO
from datetime import datetime
from xhtml2pdf import pisa 

# ==========================================
# 1. KONFIGURACIJA I BAZA
# ==========================================
st.set_page_config(page_title="ELEKTRO-LOG BUSINESS", layout="wide")

DB_NAME = 'elektro_baza.db'

def get_base64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

logo_base64 = get_base64_image("elmar.webp")

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
# 3. GLAVNI INTERFEJS
# ==========================================
col_l, col_r = st.columns([1, 4])
with col_l:
    if logo_base64:
        st.markdown(f'<img src="data:image/webp;base64,{logo_base64}" width="150">', unsafe_allow_html=True)
with col_r:
    st.title("ELEKTRO-LOG BUSINESS v1.0 ⚡")

# Forma za unos
with st.form("glavna_forma", clear_on_submit=True):
    st.subheader("📝 Novi unos")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        u_datum = st.date_input("Datum", datetime.now()).strftime("%d.%m.%Y")
        u_orman = st.text_input("Oznaka (RO)").upper().strip()
    with c2:
        u_opis = st.text_input("Krug / Opis")
        u_tip = st.selectbox("Materijal", TIPOVI_MATERIJALA)
    with c3:
        u_kol = st.number_input("Količina", min_value=0.0, step=0.1)
        u_jed = st.selectbox("Jedinica", ["m", "kom", "h"])
    with c4:
        u_napomena = st.text_input("Napomena")
        st.write("---")
        btn_snimi = st.form_submit_button("💾 SNIMI", use_container_width=True)

if btn_snimi and u_orman:
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO radovi (datum, orman, opis, tip, kol, jed, napomena) VALUES (?,?,?,?,?,?,?)",
                 (u_datum, u_orman, u_opis, u_tip, u_kol, u_jed, u_napomena))
    conn.commit(); conn.close(); st.rerun()

# ==========================================
# 4. TABELA I PDF
# ==========================================
st.divider()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql_query("SELECT * FROM radovi ORDER BY id DESC", conn)
conn.close()

if not df.empty:
    st.subheader("📋 Tabela radova")
    edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")
    
    if len(edited_df) < len(df):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM radovi")
        edited_df.to_sql('radovi', conn, if_exists='append', index=False)
        conn.commit(); conn.close(); st.rerun()

    if st.button("📄 GENERIŠI PDF IZVEŠTAJ", use_container_width=True):
        redovi_html = "".join([f"<tr><td>{r.datum}</td><td><b>{r.orman}</b></td><td>{r.opis}</td><td><b>{r.tip}</b></td><td>{r.kol} {r.jed}</td><td>{r.napomena}</td></tr>" for r in df.itertuples()])
        rekap = df.groupby(['tip', 'jed'])['kol'].sum().reset_index()
        rekap_rows = "".join([f"<tr><td>{r.tip} ({r.jed})</td><td>{r.kol:.2f}</td></tr>" for r in rekap.itertuples()])
        suma_regali = df[df['tip'].str.contains("Regal", na=False)]['kol'].sum()
        suma_kablova = df[df['jed'] == 'm']['kol'].sum()

        html_sadrzaj = f"""
        <html><head><style>
            @page {{ size: a4; margin: 1cm; }}
            body {{ font-family: Helvetica, sans-serif; font-size: 10pt; color: #333; }}
            h1 {{ color: #3182ce; border-bottom: 2pt solid #3182ce; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th {{ background-color: #3182ce; color: white; padding: 8px; }}
            td {{ border: 0.5pt solid #ccc; padding: 6px; text-align: center; }}
            .rekap-tab {{ width: 350px; margin-top: 30px; border: 1.5pt solid #000; }}
            .total-row {{ background-color: #ebf8ff; font-weight: bold; }}
        </style></head><body>
            <h1>ELEKTRO-LOG BUSINESS</h1>
            <p>Datum: {datetime.now().strftime('%d.%m.%Y')}</p>
            <table><thead><tr><th>DATUM</th><th>ORMAN</th><th>OPIS</th><th>TIP</th><th>KOL.</th><th>NAPOMENA</th></tr></thead>
            <tbody>{redovi_html}</tbody></table>
            <table class="rekap-tab"><tr><th colspan="2">REKAPITULACIJA</th></tr>{rekap_rows}
            <tr class="total-row"><td>UKUPNO REGALI (m)</td><td>{suma_regali:.2f}</td></tr>
            <tr class="total-row"><td>UKUPNO KABLOVI (m)</td><td>{suma_kablova:.2f}</td></tr>
            </table></body></html>"""
        
        pdf_buffer = BytesIO()
        pisa.CreatePDF(html_sadrzaj, dest=pdf_buffer)
        st.download_button("📥 PREUZMI PDF", data=pdf_buffer.getvalue(), file_name=f"Izvestaj_{datetime.now().strftime('%d_%m')}.pdf", mime="application/pdf")

# ==========================================
# 5. SIDEBAR (BACKUP & RESTORE)
# ==========================================
st.sidebar.title("⚙️ Administracija")

# BACKUP
st.sidebar.subheader("💾 Backup podataka")
if os.path.exists(DB_NAME):
    with open(DB_NAME, "rb") as f:
        st.sidebar.download_button(
            label="Preuzmi bazu (Backup)",
            data=f,
            file_name=f"backup_elektro_{datetime.now().strftime('%d_%m_%Y')}.db",
            mime="application/x-sqlite3",
            use_container_width=True
        )

# RESTORE (Vraćanje podataka)
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Restore (Vraćanje)")
uploaded_file = st.sidebar.file_uploader("Otpremi backup (.db) fajl", type="db")

if uploaded_file is not None:
    if st.sidebar.button("POVRATI PODATKE IZ FAJLA", type="primary", use_container_width=True):
        try:
            with open(DB_NAME, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.sidebar.success("Podaci su uspešno vraćeni!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Greška pri vraćanju: {e}")

# BRISANJE
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ OBRIŠI SVE", use_container_width=True):
    if st.sidebar.checkbox("Potvrđujem brisanje"):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM radovi"); conn.commit(); conn.close(); st.rerun()
