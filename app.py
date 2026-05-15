import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
import pdfkit
from datetime import datetime

# ==========================================
# 1. KONFIGURACIJA I INICIJALIZACIJA
# ==========================================
st.set_page_config(page_title="ELEKTRO-LOG BUSINESS", layout="wide")

# Funkcija za logo u aplikaciji i PDF-u
def get_base64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

logo_base64 = get_base64_image("elmar.webp")

# BAZA PODATAKA
def init_db():
    conn = sqlite3.connect('elektro_baza.db')
    conn.execute("""CREATE TABLE IF NOT EXISTS radovi 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  datum TEXT, 
                  orman TEXT, 
                  opis TEXT, 
                  tip TEXT, 
                  kol REAL, 
                  jed TEXT, 
                  napomena TEXT)""")
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
# 3. INTERFEJS - ZAGLAVLJE I UNOS
# ==========================================
col_l, col_r = st.columns([1, 4])
with col_l:
    if logo_base64:
        st.markdown(f'<img src="data:image/webp;base64,{logo_base64}" width="150">', unsafe_allow_html=True)
with col_r:
    st.title("ELEKTRO-LOG BUSINESS v1.0 ⚡")
    st.write(f"Vreme pristupa: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

with st.form("unos_podataka", clear_on_submit=True):
    st.subheader("➕ Unos nove stavke u dnevnik")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        u_datum = st.date_input("Datum", datetime.now()).strftime("%d.%m.%Y")
        u_orman = st.text_input("Oznaka (RO)").upper().strip()
    with c2:
        u_opis = st.text_input("Strujni krug / Opis")
        u_tip = st.selectbox("Materijal", TIPOVI_MATERIJALA)
    with c3:
        u_kol = st.number_input("Količina", min_value=0.0, step=0.1)
        u_jed = st.selectbox("Jedinica", ["m", "kom", "h"])
    with c4:
        u_napomena = st.text_input("Napomena")
        st.write("---")
        btn_snimi = st.form_submit_button("💾 SNIMI U BAZU", use_container_width=True)

if btn_snimi:
    if u_orman and u_kol > 0:
        conn = sqlite3.connect('elektro_baza.db')
        conn.execute("INSERT INTO radovi (datum, orman, opis, tip, kol, jed, napomena) VALUES (?,?,?,?,?,?,?)",
                     (u_datum, u_orman, u_opis, u_tip, u_kol, u_jed, u_napomena))
        conn.commit()
        conn.close()
        st.success(f"Uspešno sačuvano: {u_orman} | {u_tip}")
        st.rerun()
    else:
        st.error("Polja 'Oznaka' i 'Količina' moraju biti popunjena!")

# ==========================================
# 4. PRIKAZ TABELE I EDITOVANJE
# ==========================================
st.divider()
conn = sqlite3.connect('elektro_baza.db')
df = pd.read_sql_query("SELECT * FROM radovi ORDER BY id DESC", conn)
conn.close()

if not df.empty:
    st.subheader("📋 Pregled unetih radova")
    edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")
    
    # Detekcija promena/brisanja
    if len(edited_df) < len(df):
        conn = sqlite3.connect('elektro_baza.db')
        conn.execute("DELETE FROM radovi")
        edited_df.to_sql('radovi', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        st.rerun()

    # ==========================================
    # 5. GENERISANJE PDF-A (PUN DIZAJN)
    # ==========================================
    st.write("---")
    if st.button("📄 GENERIŠI FINALNI PDF IZVEŠTAJ", use_container_width=True):
        
        redovi_html = ""
        for _, r in df.iterrows():
            redovi_html += f"""
            <tr>
                <td>{r['datum']}</td>
                <td style="font-weight: bold;">{r['orman']}</td>
                <td>{r['opis']}</td>
                <td><b>{r['tip']}</b></td>
                <td>{r['kol']} {r['jed']}</td>
                <td style="text-align: left;">{r['napomena']}</td>
            </tr>
            """

        rekap = df.groupby(['tip', 'jed'])['kol'].sum().reset_index()
        rekap_rows = "".join([f"<tr><td>{r['tip']} ({r['jed']})</td><td>{r['kol']:.2f}</td></tr>" for _, r in rekap.iterrows()])
        
        suma_regali = df[df['tip'].str.contains("Regal", na=False)]['kol'].sum()
        suma_kablova = df[df['jed'] == 'm']['kol'].sum()

        html_final = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, sans-serif; padding: 30px; color: #2d3748; }}
                .header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #3182ce; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background: #3182ce; color: white; padding: 10px; font-size: 11px; }}
                td {{ border: 1px solid #e2e8f0; padding: 8px; text-align: center; font-size: 12px; }}
                .rekap-tab {{ width: 400px; margin-left: auto; margin-top: 30px; border: 2px solid #2d3748; }}
                .rekap-tab th {{ background: #2d3748; color: white; padding: 10px; }}
                .group-row {{ background: #edf2f7; font-weight: bold; }}
                .total-row {{ background: #ebf8ff; font-size: 16px; font-weight: bold; color: #2b6cb0; border-top: 2px solid #2b6cb0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div>
                    <img src="data:image/webp;base64,{logo_base64}" width="120">
                    <h1 style="margin-top:10px;">ELEKTRO-LOG BUSINESS</h1>
                </div>
                <div style="text-align: right;">
                    <p>Datum izveštaja: {datetime.now().strftime('%d.%m.%Y')}</p>
                </div>
            </div>
            <table>
                <thead>
                    <tr><th>DATUM</th><th>ORMAN</th><th>OPIS</th><th>TIP MATERIJALA</th><th>KOLIČINA</th><th>NAPOMENA</th></tr>
                </thead>
                <tbody>{redovi_html}</tbody>
            </table>
            <table class="rekap-tab">
                <thead><tr><th colspan="2">ZBIRNA REKAPITULACIJA</th></tr></thead>
                <tbody>
                    {rekap_rows}
                    <tr class="group-row"><td>SVI REGALI ZAJEDNO (m)</td><td>{suma_regali:.2f}</td></tr>
                    <tr class="total-row"><td>UKUPNO SVIH KABLOVA (m)</td><td>{suma_kablova:.2f} m</td></tr>
                </tbody>
            </table>
        </body>
        </html>
        """
        
        # Konverzija
        options = {'enable-local-file-access': None, 'encoding': "UTF-8"}
        pdf_bin = pdfkit.from_string(html_final, False, options=options)
        
        st.download_button(
            label="📥 KLIKNI OVDE DA PREUZMEŠ PDF",
            data=pdf_bin,
            file_name=f"Specifikacija_{datetime.now().strftime('%d_%m_%Y')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# ==========================================
# 6. SIDEBAR - ADMINISTRACIJA
# ==========================================
st.sidebar.title("⚙️ Administracija")
if st.sidebar.button("📥 Preuzmi bazu (Backup)"):
    with open("elektro_baza.db", "rb") as f:
        st.sidebar.download_button("Download DB", f, "elektro_baza.db")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ RESETUJ CELU BAZU", type="primary"):
    if st.sidebar.checkbox("Potvrđujem brisanje svih unosa"):
        conn = sqlite3.connect('elektro_baza.db')
        conn.execute("DELETE FROM radovi")
        conn.commit()
        conn.close()
        st.rerun()

if df.empty:
    st.info("Baza je prazna. Unesite podatke koristeći formu iznad.")
