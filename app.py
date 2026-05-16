import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF

# ==============================================================================
# 1. KONFIGURACIJA
# ==============================================================================
st.set_page_config(
    page_title="ELEKTRO-LOG BUSINESS v1.1",
    layout="wide",
    initial_sidebar_state="expanded"
)

FONT_REG = "DejaVuSans.ttf"

# ==============================================================================
# 2. KLASA ZA PDF
# ==============================================================================
class PDFSpec(FPDF):
    def header(self):
        if os.path.exists("elmar.webp"):
            try: self.image("elmar.webp", 10, 8, 33)
            except: pass
            
        # Provera fonta za naša slova (Š, Ć, Č, Ž, Đ)
        if os.path.exists(FONT_REG):
            self.add_font("DejaVu", "", FONT_REG, uni=True)
            self.set_font("DejaVu", "", 14)
        else:
            self.set_font("Helvetica", "B", 14)
            
        self.cell(0, 10, "SPECIFIKACIJA RADOVA", ln=True, align="R")
        self.cell(0, 10, "UTROSAK MATERIJALA", ln=True, align="R")
        
        if os.path.exists(FONT_REG):
            self.set_font("DejaVu", "", 9)
        else:
            self.set_font("Helvetica", "", 9)
            
        self.cell(0, 10, f"Datum izrade: {datetime.now().strftime('%d.%m.%Y')}", ln=True, align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        if os.path.exists(FONT_REG):
            self.set_font("DejaVu", "", 8)
        else:
            self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, "ELMAR ELEKTRO-INSTALACIJE | DESIGN VLADE 2026", align="C")

# ==============================================================================
# 3. GLAVNA KLASA ZA LOGIKU
# ==============================================================================
class ElektroProUltra:
    def __init__(self):
        self.db_name = "elektro_baza.db"
        self.kategorije_materijala = {
            "Nosaci i oprema": ["Brezon M8", "Brezon M10", "C-sina 30x20", "C-sina 41x21", "Regal 50", "Regal 100", "Regal 150", "Regal 200", "Regal 300", "Regal 400", "Regal 500", "Regal 600", "LR Krivina", "LR T-komad", "Poklopac regala"],
            "Instalacioni (PP-Y)": ["PP-Y 2x1.5", "PP-Y 3x1.5", "PP-Y 3x2.5", "PP-Y 3x4", "PP-Y 5x1.5", "PP-Y 5x2.5", "PP-Y 5x4", "PP-Y 5x6", "PP-Y 5x10", "PP-Y 5x16"],
            "Bezhalogeni (N2XH)": ["N2XH-J 3x1.5", "N2XH-J 3x2.5", "N2XH-J 3x4", "N2XH-J 5x1.5", "N2XH-J 5x2.5", "N2XH-J 5x4", "N2XH-J 5x6", "N2XH-J 5x10", "N2XH-J 5x16", "N2XH-J 5x25"],
            "Vatrootporni (FE180)": ["NHXH FE180 3x1.5", "NHXH FE180 3x2.5", "NHXH FE180 5x1.5", "NHXH FE180 5x2.5", "NHXH FE180 5x4", "NHXH FE180 5x6"],
            "Energetski (PP00)": ["PP00 3x1.5", "PP00 3x2.5", "PP00 4x1.5", "PP00 4x2.5", "PP00 4x4", "PP00 4x6", "PP00 4x10", "PP00 4x16", "PP00 4x25", "PP00 4x35", "PP00 4x50", "PP00 4x70", "PP00 5x1.5", "PP00 5x2.5", "PP00 5x4"],
            "Aluminijum (PP00-A)": ["PP00-A (Al) 4x16", "PP00-A 4x25", "PP00-A 4x35", "PP00-A 4x50", "PP00-A 4x70", "PP00-A 4x120", "PP00-A 4x240"],
            "Gumeni (H07RN-F)": ["H07RN-F 3x1.5", "H07RN-F 3x2.5", "H07RN-F 5x1.5", "H07RN-F 5x2.5", "H07RN-F 5x4", "H07RN-F 5x6"],
            "Signalni i P/F": ["LiYCY 2x0.75", "LiYCY 4x0.75", "P/F 0.75", "P/F 1.5", "P/F 2.5", "P/F 4", "P/F 6", "P/F 10", "P/F 16", "P 1.5", "P 2.5", "P 4"],
            "Telekom i Solarni": ["SKS 2x16", "SKS 4x16", "UTP Cat5e", "FTP Cat6", "SFTP Cat7", "Koaksijalni RG6", "Alarmni 6x0.22", "Solarni 6mm2"]
        }
        self.kreiraj_bazu()

    def kreiraj_bazu(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS radovi 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                datum TEXT, orman TEXT, opis TEXT, tip TEXT, 
                kol REAL, jed TEXT, napomena TEXT)""")

    def sacuvaj_u_bazu(self, d):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("INSERT INTO radovi (datum, orman, opis, tip, kol, jed, napomena) VALUES (?,?,?,?,?,?,?)", d)

    def azuriraj_bazu(self, df_izmenjen):
        # SIGURNIJA VARIJANTA: Brišemo stare podatke i ubacujemo nove bez rušenja tabele
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("DELETE FROM radovi")
            df_izmenjen.to_sql("radovi", conn, if_exists="append", index=False)

    def obrisi_sve(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("DELETE FROM radovi")

    def generisi_pdf(self, df, tm, tk):
        # Inicijalizacija PDF-a sa automatskim prelaskom na novu stranu (margina 15mm)
        pdf = PDFSpec()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Provera fonta
        if os.path.exists(FONT_REG):
            pdf.add_font("DejaVu", "", FONT_REG, uni=True)
            pdf.set_font("DejaVu", "", 8)
            font_ime = "DejaVu"
        else:
            pdf.set_font("Helvetica", "", 8)
            font_ime = "Helvetica"
            
        # Pomoćna funkcija koja crta plavo zaglavlje za prvu tabelu
        def nacrtaj_zaglavlje_specifikacije():
            pdf.set_fill_color(49, 130, 206) # Streamlit plava
            pdf.set_text_color(255) # Bela slova
            if font_ime == "DejaVu":
                pdf.set_font("DejaVu", "", 9)
            else:
                pdf.set_font("Helvetica", "B", 9)
            
            cols = [("Datum", 22), ("RO", 18), ("Krug", 15), ("Tip materijala", 60), ("Kol", 15), ("Jed", 10), ("Napomena", 50)]
            for col_name, width in cols:
                pdf.cell(width, 10, col_name, border=0, align="C", fill=True)
            pdf.ln()

        # Nacrtaj prvo zaglavlje na prvoj stranici
        nacrtaj_zaglavlje_specifikacije()

        # Pisanje stavki iz baze
        pdf.set_text_color(0)
        pdf.set_font(font_ime, "", 8)
        df_clean = df.dropna(subset=['datum', 'orman', 'tip'])
        
        for _, r in df_clean.iterrows():
            # --- KLJUČNA PROVERA: Da li trenutni red (visine 8mm) može da stane na trenutni list? ---
            # 297mm (A4 visina) - 15mm (donja margina) = 282mm je maksimalna visina za pisanje.
            if pdf.get_y() + 8 > 282:
                pdf.add_page() # Otvori novi list
                nacrtaj_zaglavlje_specifikacije() # Ponovo nacrtaj plave kolone na vrhu novog lista
                pdf.set_text_color(0) # Resetuj boju teksta na crnu
                pdf.set_font(font_ime, "", 8) # Resetuj font na standardni
            
            pdf.cell(22, 8, str(r['datum']), border=0, align="C")
            pdf.cell(18, 8, str(r['orman']), border=0, align="C")
            pdf.cell(15, 8, str(r['opis']), border=0, align="C")
            pdf.cell(60, 8, str(r['tip']), border=0, align="C")
            pdf.cell(15, 8, str(r['kol']), border=0, align="C")
            pdf.cell(10, 8, str(r['jed']), border=0, align="C")
            nap = str(r['napomena']) if r['napomena'] and str(r['napomena']) != 'None' else ""
            pdf.cell(50, 8, nap, border=0, align="C")
            pdf.ln()

        # Razmak između dve tabele
        # Ako je kraj prve tabele preblizu dnu (manje od 60mm slobodno za zbirnu tabelu), 
        # odmah prebaci zbirnu tabelu na ceo novi čist list.
        if pdf.get_y() + 60 > 282:
            pdf.add_page()
        else:
            pdf.ln(10)
        
        # ==============================================================================
        # TABELA 2: ZBIRNA REKAPITULACIJA (IDENTIČNA KAO SA SLIKE)
        # ==============================================================================
        sirina_naziv = 130
        sirina_kol = 50
        X_pochetna = 15 # Centriranje tabele na A4 listu
        
        pdf.set_x(X_pochetna)
        pdf.set_fill_color(44, 52, 70) # Tamno sivo-plava pozadina zaglavlja sa tvoje slike
        pdf.set_text_color(255)
        if font_ime == "DejaVu":
            pdf.set_font("DejaVu", "", 10)
        else:
            pdf.set_font("Helvetica", "B", 10)
            
        pdf.cell(sirina_naziv + sirina_kol, 10, "ZBIRNA REKAPITULACIJA", border=0, ln=True, align="C", fill=True)
        
        # Reset boja za unutrašnjost tabele
        pdf.set_text_color(50, 50, 50) 
        pdf.set_draw_color(230, 230, 230) # Tanke svetlo sive linije
        pdf.set_line_width(0.2)
        
        ukupno_regali = 0.0
        ukupno_kablovi = 0.0
        
        if not df_clean.empty:
            utrosak = df_clean.groupby(['tip', 'jed'])['kol'].sum().reset_index()
            
            for _, row in utrosak.iterrows():
                # I ovde proveravamo da li pojedinačni red sume upada na kraj stranice
                if pdf.get_y() + 9 > 282:
                    pdf.add_page()
                    # Ako pređe na novu stranu, dajemo mali podsetnik naslova
                    pdf.set_x(X_pochetna)
                    pdf.set_fill_color(44, 52, 70)
                    pdf.set_text_color(255)
                    pdf.cell(sirina_naziv + sirina_kol, 8, "ZBIRNA REKAPITULACIJA (Nastavak)", border=0, ln=True, align="C", fill=True)
                    pdf.set_text_color(50, 50, 50)
                    pdf.set_draw_color(230, 230, 230)
                
                tip_naziv = str(row['tip'])
                kolicina_val = float(row['kol'])
                jedinica_naziv = str(row['jed'])
                
                if "REGAL" in tip_naziv.upper():
                    ukupno_regali += kolicina_val
                elif any(x in tip_naziv.upper() for x in ["PP-Y", "N2XH", "FE180", "PP00", "H07RN", "LIYCY", "P/F", "SKS", "CAT"]):
                    ukupno_kablovi += kolicina_val
                
                pdf.set_x(X_pochetna)
                if font_ime == "DejaVu":
                    pdf.set_font("DejaVu", "", 9)
                else:
                    pdf.set_font("Helvetica", "", 9)
                    
                pdf.cell(sirina_naziv, 9, f" {tip_naziv} ({jedinica_naziv})", border="B", align="L")
                
                if font_ime == "DejaVu":
                    pdf.set_font("DejaVu", "", 9)
                else:
                    pdf.set_font("Helvetica", "B", 9)
                pdf.cell(sirina_kol, 9, f"{kolicina_val:.2f} ", border="B", align="R")
                pdf.ln()
                
        # --- RED 1 ZA ZBIR: SVI REGALI ZAJEDNO ---
        if pdf.get_y() + 20 > 282: # Osiguranje da oba zbira ostanu na istom listu
            pdf.add_page()
            
        pdf.set_x(X_pochetna)
        pdf.set_fill_color(240, 244, 248) 
        pdf.set_text_color(20, 30, 55)
        if font_ime == "DejaVu":
            pdf.set_font("DejaVu", "", 10)
        else:
            pdf.set_font("Helvetica", "B", 10)
            
        pdf.cell(sirina_naziv, 10, " SVI REGALI ZAJEDNO (m)", border="TB", align="L", fill=True)
        pdf.cell(sirina_kol, 10, f"{ukupno_regali:.2f} m ", border="TB", align="R", fill=True)
        pdf.ln()
        
        # --- RED 2 ZA ZBIR: UKUPNO SVIH KABLOVA ---
        pdf.set_x(X_pochetna)
        pdf.set_fill_color(230, 242, 255) # Svetlo plava sa slike
        pdf.set_text_color(49, 130, 206) # Jaka plava slova
        
        pdf.cell(sirina_naziv, 10, " UKUPNO SVIH KABLOVA (m)", border="B", align="L", fill=True)
        pdf.cell(sirina_kol, 10, f"{ukupno_kablovi:.2f} m ", border="B", align="R", fill=True)
        
        return pdf.output()

# ==============================================================================
# 4. INTERFEJS
# ==============================================================================
app = ElektroProUltra()

with st.sidebar:
    st.header("⚙️ SISTEM")
    if os.path.exists(app.db_name):
        with open(app.db_name, "rb") as f:
            st.sidebar.download_button("📥 PREUZMI BACKUP", f, file_name="elektro_baza.db", use_container_width=True)
    st.divider()
    f_res = st.file_uploader("Restore .db", type="db")
    if f_res and st.button("⚠️ POTVRDI RESTORE", use_container_width=True):
        with open(app.db_name, "wb") as f: 
            f.write(f_res.getbuffer())
        st.rerun()
    st.divider()
    if st.checkbox("Potvrda brisanja"):
        if st.button("🔴 OBRIŠI SVE", use_container_width=True):
            app.obrisi_sve()
            st.rerun()

# UNOS
with st.expander("📝 UNOS NOVE STAVKE", expanded=True):
    c1, c2, c3 = st.columns(3)
    dat = c1.text_input("📅 Datum", datetime.now().strftime("%d.%m.%Y"))
    orm = c2.text_input("🏗️ RO").upper().strip()
    krug = c3.text_input("🔌 Krug")
    kat_col, tip_col = st.columns(2)
    izab_kat = kat_col.selectbox("📁 Kategorija", options=list(app.kategorije_materijala.keys()), key="m_kat")
    tip = tip_col.selectbox("📦 Tip materijala", options=app.kategorije_materijala[izab_kat], key="m_tip")
    
    with st.form("forma_podaci", clear_on_submit=True):
        c4, c5, c6 = st.columns([1, 1, 2])
        kol = c4.number_input("Kolicina", min_value=0.0, step=0.1)
        jed = c5.selectbox("Jedinica", ["m", "kom"])
        nap = c6.text_input("📝 Napomena")
        if st.form_submit_button("💾 SNIMI", use_container_width=True):
            if orm and krug:
                app.sacuvaj_u_bazu((dat, orm, krug, tip, kol, jed, nap))
                st.rerun()
            else:
                st.error("Polja 'RO' i 'Krug' ne smeju biti prazna!")

# PRIKAZ
with sqlite3.connect(app.db_name) as conn:
    df_prikaz = pd.read_sql_query("SELECT * FROM radovi ORDER BY id DESC", conn)

if not df_prikaz.empty:
    oprema_keywords = ("REGAL", "BREZON", "C-SINA", "LR ")
    mask = df_prikaz['tip'].str.upper().str.contains('|'.join(oprema_keywords))
    df_kab = df_prikaz[~mask]
    s_m = df_kab[df_kab['jed'] == 'm']['kol'].sum()
    s_k = df_kab[df_kab['jed'] == 'kom']['kol'].sum()

    st.metric("UKUPNO METARA KABLA", f"{s_m:.2f} m")
    
    # Dodajemo ključ za stabilnost editora
    edited_df = st.data_editor(df_prikaz, use_container_width=True, hide_index=True, num_rows="dynamic", key="glavni_editor")
    
    if st.button("✅ SAČUVAJ IZMENE", use_container_width=True):
        app.azuriraj_bazu(edited_df)
        st.rerun()

    st.divider()
    
    # Generisanje stabilnog fajla preko funkcije i slanje na download dugme
    try:
        pdf_out = app.generisi_pdf(edited_df, s_m, s_k)
        if pdf_out:
            st.download_button(
                label="📄 PREUZMI PDF IZVESTAJ", 
                data=bytes(pdf_out), 
                file_name=f"izvestaj_{datetime.now().strftime('%d_%m_%Y')}.pdf", 
                mime="application/pdf",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Greška pri generisanju PDF-a: {e}")
else:
    st.info("Baza je prazna. Unesite prve stavke kako bi se prikazao izveštaj.")
