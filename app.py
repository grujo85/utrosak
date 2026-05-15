import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. KONFIGURACIJA I INICIJALIZACIJA ---
st.set_page_config(page_title="ELEKTRO-LOG BUSINESS", layout="wide")

DB_NAME = "elektro_baza.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS radovi 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  datum TEXT, 
                  orman TEXT, 
                  opis TEXT, 
                  tip TEXT, 
                  kol REAL, 
                  jed TEXT, 
                  napomena TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. KOMPLETNA LISTA MATERIJALA (SVIH 100+ STAVKI) ---
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

# --- 3. FUNKCIJA ZA HTML IZVEŠTAJ (IDENTIČAN TVOM DIZAJNU) ---
def generisi_html_izvestaj(df):
    rekap = df.groupby(['tip', 'jed'])['kol'].sum().reset_index()
    # Logika za sumiranje regala (bilo šta što u imenu ima 'Regal')
    total_regali = df[df['tip'].str.contains("Regal", na=False)]['kol'].sum()
    # Logika za sumiranje kablova (sve što nije regal, montaža, brezon...)
    izuzeci = "Regal|MONTAŽA|DEMONTAŽA|Brezon|šina|LR|Poklopac"
    total_kablovi = df[~df['tip'].str.contains(izuzeci, na=False) & (df['jed'] == 'm')]['kol'].sum()

    # Formiranje redova tabele
    rows = ""
    for _, r in df.iterrows():
        rows += f"""<tr>
            <td>{r['datum']}</td>
            <td><b>{r['orman']}</b></td>
            <td>{r['opis']}</td>
            <td><b>{r['tip']}</b></td>
            <td>{r['kol']} {r['jed']}</td>
            <td>{r['napomena']}</td>
        </tr>"""

    # Formiranje rekapitulacije
    rekap_rows = ""
    for _, r in rekap.iterrows():
        rekap_rows += f"<tr><td>{r['tip']} ({r['jed']})</td><td>{r['kol']:.2f}</td></tr>"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 40px; color: #2d3748; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #3182ce; padding-bottom: 10px; }}
            h1 {{ margin: 0; font-size: 24px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: center; }}
            th {{ background: #3182ce; color: white; text-transform: uppercase; font-size: 12px; }}
            tr:nth-child(even) {{ background: #fcfcfc; }}
            .sum-table {{ width: 450px; margin-left: auto; margin-top: 30px; border: 2px solid #2d3748; border-collapse: collapse; }}
            .sum-table th {{ background: #2d3748; font-size: 14px; color: white; padding: 12px; }}
            .sum-table td {{ text-align: left; }}
            .sum-table td:last-child {{ text-align: right; font-weight: bold; }}
            .group-row {{ background: #edf2f7 !important; font-weight: bold; border-top: 2px solid #2d3748; }}
            .total-row {{ background: #ebf8ff !important; font-size: 17px; font-weight: bold; color: #2b6cb0; border-top: 2px solid #2b6cb0; }}
            @media print {{ @page {{ size: A4; margin: 15mm; }} body {{ margin: 0; }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>ELEKTRO-LOG BUSINESS</h1>
            <p>Izveštaj generisan: {datetime.now().strftime('%d.%m.%Y')}</p>
        </div>
        <table>
            <thead>
                <tr><th>DATUM</th><th>ORMAN</th><th>KRUG/OPIS</th><th>TIP MATERIJALA</th><th>KOLIČINA</th><th>NAPOMENA</th></tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        <table class="sum-table">
            <thead>
                <tr><th colspan="2">ZBIRNA REKAPITULACIJA</th></tr>
            </thead>
            <tbody>
                {rekap_rows}
                <tr class="group-row">
                    <td>SVI REGALI ZAJEDNO (m)</td>
                    <td>{total_regali:.2f}</td>
                </tr>
                <tr class="total-row">
                    <td>UKUPNO SVIH KABLOVA (m)</td>
                    <td>{total_kablovi:.2f} m</td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    return html_code

# --- 4. STREAMLIT KORISNIČKI INTERFEJS (UI) ---
st.title("⚡ ELEKTRO-LOG BUSINESS")
st.write("Sistem za praćenje elektromontažerskih radova")

# Kontejner za unos
with st.container(border=True):
    st.subheader("📝 Unos novih podataka")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        v_datum = st.date_input("Datum unosa", datetime.now())
        v_orman = st.text_input("Oznaka Ormana").upper().strip()
    
    with col2:
        v_opis = st.text_input("Krug / Opis radova")
        v_tip = st.selectbox("Izaberi materijal", TIPOVI_MATERIJALA)
        
    with col3:
        v_kol = st.number_input("Količina", min_value=0.0, step=0.1)
        v_jed = st.selectbox("Jedinica mere", ["m", "kom", "h"])
        
    with col4:
        v_napomena = st.text_input("Napomena / Detalji")
        st.write("---")
        btn_snimi = st.button("💾 SAČUVAJ U BAZU", use_container_width=True)

# Logika snimanja
if btn_snimi:
    if v_orman and v_kol > 0:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO radovi (datum, orman, opis, tip, kol, jed, napomena) VALUES (?,?,?,?,?,?,?)",
                  (v_datum.strftime("%d.%m.%Y"), v_orman, v_opis, v_tip, v_kol, v_jed, v_napomena))
        conn.commit()
        conn.close()
        st.success(f"Snimljeno: {v_orman} - {v_tip}")
        st.rerun()
    else:
        st.error("Polja 'Orman' i 'Količina' moraju biti popunjena!")

# --- 5. PRIKAZ PODATAKA ---
st.markdown("---")
conn = sqlite3.connect(DB_NAME)
df_prikaz = pd.read_sql_query("SELECT * FROM radovi ORDER BY id DESC", conn)
conn.close()

if not df_prikaz.empty:
    st.subheader("📋 Pregled unetih stavki")
    # Glavni prikaz tabele u aplikaciji
    st.dataframe(df_prikaz, use_container_width=True, hide_index=True)
    
    # --- 6. AKCIJE I EXPORT ---
    st.markdown("### 🛠️ Akcije")
    c_down1, c_down2, c_down3 = st.columns(3)
    
    with c_down1:
        # Generisanje onog tvog HTML-a
        finalni_html = generisi_html_izvestaj(df_prikaz)
        st.download_button(
            label="💎 PREUZMI PROFESIONALNI IZVEŠTAJ (HTML)",
            data=finalni_html,
            file_name=f"Izvestaj_{datetime.now().strftime('%d_%m_%Y')}.html",
            mime="text/html",
            use_container_width=True
        )
        
    with c_down2:
        # Backup same SQLite baze
        with open(DB_NAME, "rb") as f:
            st.download_button(
                label="📤 BACKUP BAZE (sqlite)",
                data=f,
                file_name="elektro_baza_backup.db",
                use_container_width=True
            )
            
    with c_down3:
        # Dugme za brisanje (sa proverom)
        if st.button("🗑️ OBRIŠI SVE (RESET)", use_container_width=True, type="primary"):
            st.warning("Ovo će obrisati SVE podatke iz baze!")
            if st.checkbox("Potvrđujem brisanje"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM radovi")
                conn.commit()
                conn.close()
                st.rerun()

else:
    st.info("Baza je trenutno prazna. Unesite podatke iznad.")

# --- SIDEBAR (OPCIONO) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2906/2906206.png", width=100)
st.sidebar.title("Informacije")
st.sidebar.info("Ovo je web verzija vašeg Elektro-Log sistema. Svi podaci se čuvaju u bazi.")
