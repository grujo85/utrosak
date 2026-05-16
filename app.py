import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF

# ==============================================================================
# 1. KONFIGURACIJA STREAMLIT APLIKACIJE
# ==============================================================================
# Postavljamo osnovna podešavanja stranice u veb brauzeru
st.set_page_config(
    page_title="ELEKTRO-LOG BUSINESS v1.1",  # Naslov koji piše na tabu brauzera
    layout="wide",                           # Široki prikaz (iskorišćava ceo ekran)
    initial_sidebar_state="expanded"         # Bočni meni (sidebar) je otvoren pri pokretanju
)

# Definisanje naziva fajla za font koji podržava naša slova (Š, Ć, Č, Ž, Đ)
FONT_REG = "DejaVuSans.ttf"

# ==============================================================================
# 2. KLASA ZA PDF GENERISANJE (Podklasa FPDF-a)
# ==============================================================================
class PDFSpec(FPDF):
    # Automatska funkcija koja se izvršava na početku SVAKE nove stranice PDF-a
    def header(self):
        # Ako logo "elmar.webp" postoji u folderu, ubaci ga u gornji levi ugao
        if os.path.exists("elmar.webp"):
            try: self.image("elmar.webp", 10, 8, 33) # Pozicija X=10, Y=8, širina=33mm
            except: pass                             # Ako slika ima grešku, ignoriši i nastavi
            
        # Provera i učitavanje fonta za ispravan prikaz naših specifičnih slova
        if os.path.exists(FONT_REG):
            self.add_font("DejaVu", "", FONT_REG, uni=True) # Registrovanje UTF-8 fonta
            self.set_font("DejaVu", "", 14)                # Postavljanje fonta na veličinu 14
        else:
            self.set_font("Helvetica", "B", 14)             # Ako fonta nema, koristi standardni Helvetica Bold
            
        # Desno poravnati naslovi u zaglavlju dokumenta
        self.cell(0, 10, "SPECIFIKACIJA RADOVA", ln=True, align="R")
        self.cell(0, 8, "UTROSAK MATERIJALA", ln=True, align="R")
        
        # Smanjujemo font za datum izrade
        if os.path.exists(FONT_REG):
            self.set_font("DejaVu", "", 9)
        else:
            self.set_font("Helvetica", "", 9)
            
        # Ispisivanje trenutnog datuma u gornjem desnom uglu
        self.cell(0, 10, f"Datum izrade: {datetime.now().strftime('%d.%m.%Y')}", ln=True, align="R")
        self.ln(10) # Pravimo prazan prostor od 10mm pre nego što počne tabela

    # Automatska funkcija koja se izvršava na dnu SVAKE stranice PDF-a
    def footer(self):
        self.set_y(-15) # Pozicioniranje na 15mm od dna stranice
        if os.path.exists(FONT_REG):
            self.set_font("DejaVu", "", 8)
        else:
            self.set_font("Helvetica", "I", 8) # Italika (iskošena slova) za standardni font
        self.set_text_color(128) # Postavljanje sive boje teksta
        # Centralno poravnat potpis na dnu
        self.cell(0, 10, "ELMAR ELEKTRO-INSTALACIJE | DESIGN VLADE 2026", align="C")

# ==============================================================================
# 3. GLAVNA KLASA ZA LOGIKU I RAD SA BAZOM PODATAKA
# ==============================================================================
class ElektroProUltra:
    def __init__(self):
        self.db_name = "elektro_baza.db" # Naziv SQLite fajla baze podataka
        
        # Veliki rečnik (Dictionary) sa strukturiranim materijalima po kategorijama
        self.kategorije_materijala = {
            "Nosaci i oprema": [
                "Regal 50", "Regal 100", "Regal 150", "Regal 200", "Regal 300", "Regal 400", "Regal 500", "Regal 600",
                "Poklopac regala 50", "Poklopac regala 100", "Poklopac regala 150", "Poklopac regala 200", "Poklopac regala 300", "Poklopac regala 400",
                "Spojnica za regal", "Zglobna spojnica za regal", "LR Krivina 90", "LR T-komad", "LR X-komad", "Redukcija za regal",
                "Zidni nosac regala", "Plafonski viseci nosac", "Navojna šipka (Brezon) M6", "Brezon M8", "Brezon M10", "Brezon M12",
                "C-sina 30x20", "C-sina 41x21", "C-sina 41x41", "Matica M6", "Matica M8", "Matica M10", "Matica M12",
                "Podloška M6", "Podloška M8", "Podloška M10", "Podloška M12", "Tipl gužvajući (Mesing) M8", "Tipl gužvajući (Mesing) M10",
                "Udarni tipl 6x40", "Udarni tipl 8x60", "Anker vijak M8", "Anker vijak M10", "Sajla čelična 4mm", "Obujmica metalna sa gumom",
                "Obujmica plastična", "PVC vezice (razne)", "PVC cev kruta fi 16", "PVC cev kruta fi 20", "PVC cev kruta fi 25",
                "PVC cev kruta fi 32", "PVC cev kruta fi 40", "PVC cev kruta fi 50", "Rebrasta cev (Gibljiva) fi 16", "Rebrasta cev fi 20",
                "Rebrasta cev fi 25", "Rebrasta cev fi 32", "Rebrasta cev fi 40", "Bezhalogena (HF) rebrasta cev fi 20", "Bezhalogena (HF) kruta cev fi 20",
                "Dozna fi 60 (nizajuća)", "Dozna za gips fi 60", "Dozna 100x100", "OG kutija 80x80", "OG kutija 100x100", "OG kutija 150x110",
                "OG kutija 190x140", "OG kutija 240x190", "Uvodnica PG 13.5", "Uvodnica PG 16", "Uvodnica PG 21", "Uvodnica PG 29",
                "Uvodnica PG 36", "Metrička uvodnica M20", "Metrička uvodnica M25", "Metrička uvodnica M32", "Metrička uvodnica M40"
            ],
            "Instalacioni (PP-Y)": [
                "PP-Y 2x1.5", "PP-Y 2x2.5", "PP-Y 3x1.5", "PP-Y 3x2.5", "PP-Y 3x4", "PP-Y 3x6",
                "PP-Y 4x1.5", "PP-Y 4x2.5", "PP-Y 4x4", "PP-Y 4x6", "PP-Y 4x10", "PP-Y 4x16",
                "PP-Y 5x1.5", "PP-Y 5x2.5", "PP-Y 5x4", "PP-Y 5x6", "PP-Y 5x10", "PP-Y 5x16", "PP-Y 5x25", "PP-Y 7x1.5", "PP-Y 12x1.5"
            ],
            "Bezhalogeni (N2XH)": [
                "N2XH-O 1x16", "N2XH-O 1x25", "N2XH-O 1x35", "N2XH-O 1x50", "N2XH-O 1x70", "N2XH-O 1x95", "N2XH-O 1x120", "N2XH-O 1x150", "N2XH-O 1x240",
                "N2XH-J 2x1.5", "N2XH-J 2x2.5", "N2XH-J 3x1.5", "N2XH-J 3x2.5", "N2XH-J 3x4", "N2XH-J 3x6",
                "N2XH-J 4x1.5", "N2XH-J 4x2.5", "N2XH-J 4x4", "N2XH-J 4x6", "N2XH-J 4x10", "N2XH-J 4x16", "N2XH-J 4x25", "N2XH-J 4x35",
                "N2XH-J 5x1.5", "N2XH-J 5x2.5", "N2XH-J 5x4", "N2XH-J 5x6", "N2XH-J 5x10", "N2XH-J 5x16", "N2XH-J 5x25", "N2XH-J 5x35", "N2XH-J 5x50",
                "N2XH-J 7x1.5", "N2XH-J 7x2.5", "N2XH-J 12x1.5", "N2XH-J 19x1.5", "N2XH-J 24x1.5", "N2XH-J 37x1.5"
            ],
            "Vatrootporni (FE180)": [
                "NHXH FE180 1x16", "NHXH FE180 1x25", "NHXH FE180 1x35", "NHXH FE180 1x50", "NHXH FE180 1x70", "NHXH FE180 1x95", "NHXH FE180 1x120", "NHXH FE180 1x150", "NHXH FE180 1x185", "NHXH FE180 1x240",
                "NHXH FE180 2x1.5", "NHXH FE180 2x2.5", "NHXH FE180 2x4", "NHXH FE180 2x6",
                "NHXH FE180 3x1.5", "NHXH FE180 3x2.5", "NHXH FE180 3x4", "NHXH FE180 3x6", "NHXH FE180 3x10",
                "NHXH FE180 4x1.5", "NHXH FE180 4x2.5", "NHXH FE180 4x4", "NHXH FE180 4x6", "NHXH FE180 4x10", "NHXH FE180 4x16", "NHXH FE180 4x25", "NHXH FE180 4x35", "NHXH FE180 4x50", "NHXH FE180 4x70", "NHXH FE180 4x95", "NHXH FE180 4x120",
                "NHXH FE180 5x1.5", "NHXH FE180 5x2.5", "NHXH FE180 5x4", "NHXH FE180 5x6", "NHXH FE180 5x10", "NHXH FE180 5x16", "NHXH FE180 5x25", "NHXH FE180 5x35", "NHXH FE180 5x50",
                "NHXH FE180 7x1.5", "NHXH FE180 7x2.5", "NHXH FE180 10x1.5", "NHXH FE180 12x1.5", "NHXH FE180 12x2.5", "NHXH FE180 14x1.5", "NHXH FE180 19x1.5", "NHXH FE180 24x1.5", "NHXH FE180 30x1.5", "NHXH FE180 37x1.5",
                "JE-H(St)H FE180 E30/E90 1x2x0.8", "JE-H(St)H FE180 E30/E90 2x2x0.8", "JE-H(St)H FE180 E30/E90 3x2x0.8", "JE-H(St)H FE180 E30/E90 4x2x0.8", "JE-H(St)H FE180 E30/E90 8x2x0.8", "JE-H(St)H FE180 E30/E90 12x2x0.8",
                "Vatrootporna kutija FE (sa keramičkim klemama) 100x100", "Vatrootporna kutija FE (sa keramičkim klemama) 150x150", "Vatrootporna kutija FE (sa keramičkim klemama) 200x200",
                "Metalna uvodnica M20 (za FE kutije)", "Metalna uvodnica M25 (za FE kutije)", "Vatrootporna metalna obujmica (jednostruka)", "Vatrootporna metalna obujmica (dvostruka)",
                "Metalni tipl za beton (FE montaža)", "Vatrootporni premaz/pena za kablovske prodore"
            ],
            "Energetski (PP00)": [
                "PP00 1x16", "PP00 1x25", "PP00 1x35", "PP00 1x50", "PP00 1x70", "PP00 1x95", "PP00 1x120", "PP00 1x150", "PP00 1x185", "PP00 1x240", "PP00 1x300",
                "PP00 2x1.5", "PP00 2x2.5", "PP00 2x4", "PP00 2x6", "PP00 3x1.5", "PP00 3x2.5", "PP00 3x4", "PP00 3x6", "PP00 3x10",
                "PP00 4x1.5", "PP00 4x2.5", "PP00 4x4", "PP00 4x6", "PP00 4x10", "PP00 4x16", "PP00 4x25", "PP00 4x35", "PP00 4x50", "PP00 4x70", "PP00 4x95", "PP00 4x120", "PP00 4x150", "PP00 4x185", "PP00 4x240",
                "PP00 5x1.5", "PP00 5x2.5", "PP00 5x4", "PP00 5x6", "PP00 5x10", "PP00 5x16", "PP00 5x25", "PP00 5x35", "PP00 5x50", "PP00 5x70",
                "PP00 7x1.5", "PP00 7x2.5", "PP00 10x1.5", "PP00 12x1.5", "PP00 14x1.5", "PP00 19x1.5", "PP00 24x1.5", "PP00 30x1.5", "PP00 37x1.5"
            ],
            "Aluminijum (PP00-A)": [
                "PP00-A (Al) 1x150", "PP00-A (Al) 1x185", "PP00-A (Al) 1x240", "PP00-A (Al) 1x300", "PP00-A (Al) 1x400",
                "PP00-A 3x50", "PP00-A 3x70", "PP00-A 3x95", "PP00-A 3x120", "PP00-A 3x150", "PP00-A 3x185", "PP00-A 3x240",
                "PP00-A 4x16", "PP00-A 4x25", "PP00-A 4x35", "PP00-A 4x50", "PP00-A 4x70", "PP00-A 4x95", "PP00-A 4x120", "PP00-A 4x150", "PP00-A 4x185", "PP00-A 4x240"
            ],
            "Gumeni (H07RN-F)": [
                "H07RN-F 1x16", "H07RN-F 1x25", "H07RN-F 1x35", "H07RN-F 1x50", "H07RN-F 1x70", "H07RN-F 1x95", "H07RN-F 1x120", "H07RN-F 1x150", "H07RN-F 1x240",
                "H07RN-F 2x1.5", "H07RN-F 2x2.5", "H07RN-F 3x1.5", "H07RN-F 3x2.5", "H07RN-F 3x4", "H07RN-F 3x6",
                "H07RN-F 4x1.5", "H07RN-F 4x2.5", "H07RN-F 4x4", "H07RN-F 4x6", "H07RN-F 4x10", "H07RN-F 4x16", "H07RN-F 4x25", "H07RN-F 4x35", "H07RN-F 4x50",
                "H07RN-F 5x1.5", "H07RN-F 5x2.5", "H07RN-F 5x4", "H07RN-F 5x6", "H07RN-F 5x10", "H07RN-F 5x16", "H07RN-F 5x25", "H07RN-F 5x35",
                "H07RN-F 7x1.5", "H07RN-F 12x1.5", "H07RN-F 19x1.5", "H07RN-F 24x1.5"
            ],
            "Signalni i P/F": [
                "LiYY 2x0.75", "LiYY 3x0.75", "LiYY 4x0.75", "LiYY 5x0.75", "LiYCY 2x0.50", "LiYCY 2x0.75", "LiYCY 2x1.0", "LiYCY 2x1.5",
                "LiYCY 3x0.50", "LiYCY 3x0.75", "LiYCY 3x1.0", "LiYCY 3x1.5", "LiYCY 4x0.50", "LiYCY 4x0.75", "LiYCY 4x1.0", "LiYCY 4x1.5",
                "LiYCY 5x0.75", "LiYCY 7x0.75", "LiYCY 10x0.75", "LiYCY 12x0.75", "LiYCY 16x0.75", "LiYCY 24x0.75", "LiYCY 36x0.75",
                "P/F (H07V-K) 0.5", "P/F 0.75", "P/F 1.0", "P/F 1.5", "P/F 2.5", "P/F 4", "P/F 6", "P/F 10", "P/F 16", "P/F 25", "P/F 35",
                "P/F 50", "P/F 70", "P/F 95", "P/F 120", "P/F 150", "P/F 185", "P/F 240", "P (H07V-U kruti) 1.5", "P 2.5", "P 4", "P 6", "P 10", "P 16",
                "Gromobranska traka Zn 25x4", "Gromobranska traka Zn 30x4", "Gromobranska žica Zn Fi 8", "Bakarna traka za uzemljenje",
                "Bakarna pletenica za uzemljenje", "Sonda za uzemljenje 1.5m", "Sonda za uzemljenje 2.0m", "Ukrsni komad (JUS) traka-traka",
                "Ukrsni komad traka-žica", "Potpora za krov/zid (za Fi8)"
            ],
            "Telekom i Solarni": [
                "UTP Cat5e", "UTP Cat5e (Spoljašnji/Outdoor)", "FTP Cat6", "FTP Cat6 (Spoljašnji/Outdoor)", "SFTP Cat7", "SFTP Cat8",
                "Optički kabl SM 4FO", "Optički kabl SM 8FO", "Optički kabl SM 12FO", "Optički kabl SM 24FO", "Optički kabl SM 48FO", "Optički kabl SM 96FO",
                "Optički kabl MM 4FO", "Optički kabl MM 8FO", "Pigtail optički", "Patch cord optički", "J-Y(St)Y 1x2x0.6", "J-Y(St)Y 2x2x0.6",
                "J-Y(St)Y 4x2x0.6", "J-Y(St)Y 6x2x0.6", "J-Y(St)Y 1x2x0.8", "J-Y(St)Y 2x2x0.8", "J-Y(St)Y 3x2x0.8", "J-Y(St)Y 4x2x0.8",
                "J-Y(St)Y 5x2x0.8", "J-Y(St)Y 6x2x0.8", "J-Y(St)Y 10x2x0.8", "J-Y(St)Y 20x2x0.8", "J-Y(St)Y 30x2x0.8", "J-Y(St)Y 50x2x0.8",
                "Alarmni beli 4x0.22", "Alarmni beli 6x0.22", "Alarmni beli 8x0.22", "Alarmni beli 12x0.22", "Koaksijalni RG6", "Koaksijalni RG11",
                "Kombinovani RG59+2x0.75", "Kombinovani RG59+2x1.0", "Solarni kabl 4mm2 crni", "Solarni kabl 4mm2 crveni", "Solarni kabl 6mm2 crni",
                "Solarni kabl 6mm2 crveni", "Solarni kabl 10mm2 crni", "Solarni kabl 10mm2 crveni", "Solarni kabl 16mm2", "MC4 konektor (Set muški/ženski)",
                "SKS 2x16", "SKS 4x16", "SKS 4x25", "SKS 4x35", "SKS 4x50", "SKS 4x70", "SKS 4x16+25", "SKS 4x35+25"
            ],
            "RADOVI": [
                "MONTAŽA", "DEMONTAŽA", "POLAGANJE KABLA (Ručno)", "POLAGANJE KABLA (Mašinski)", "IZVLAČENJE STAROG KABLA",
                "MONTAŽA REGALA/C-ŠINE", "POSTAVLJANJE CEVI/BUŽIRA", "ŠEMIRANJE ORMANA", "UGRADNJA DOZNE/KUTIJE", "ŠLICOVANJE ZIDA (Opeka)",
                "ŠLICOVANJE ZIDA (Beton)", "PROBOJ ZIDA/PLOČE", "POVEZIVANJE POTROŠAČA", "POVEZIVANJE SVETILJKE", "POVEZIVANJE UTIČNICE/PREKIDAČA",
                "IZRADA UZEMLJENJA (Zabijanje sondi)", "VARENJE GROMOBRANSKE TRAKE (Kadmitsko)", "SPAJANJE OPTIKE (Splajsovanje)",
                "KONEKTOVANJE RJ45/Keystone", "ZAVRŠAVANJE KABLA (Mufiranje)", "ISPITIVANJE INSTALACIJE", "MERENJE OTPORA UZEMLJENJA", "IZDAVANJE ATESTA"
            ]
        }
        self.kreiraj_bazu() # Pri svakom pokretanju proveravamo da li tabela postoji

    # Funkcija kreira SQLite tabelu ako ona već ne postoji u fajlu
    def kreiraj_bazu(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS radovi 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                datum TEXT, orman TEXT, opis TEXT, tip TEXT, 
                kol REAL, jed TEXT, napomena TEXT)""")

    # Funkcija upisuje novu stavku (red) u bazu podataka
    def sacuvaj_u_bazu(self, d):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("INSERT INTO radovi (datum, orman, opis, tip, kol, jed, napomena) VALUES (?,?,?,?,?,?,?)", d)

    # Sigurna funkcija za sinhronizaciju izmena iz tabele na ekranu direktno u bazu
    def azuriraj_bazu(self, df_izmenjen):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("DELETE FROM radovi") # Prvo brišemo sve stare podatke
            # Zatim upisujemo kompletnu novu tabelu bez menjanja strukture tabele
            df_izmenjen.to_sql("radovi", conn, if_exists="append", index=False)

    # Funkcija za potpuno pražnjenje baze podataka
    def obrisi_sve(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("DELETE FROM radovi")

    # GLAVNA FUNKCIJA ZA KREIRANJE PDF DOKUMENTA
    def generisi_pdf(self, df, tm, tk):
        pdf = PDFSpec()
        pdf.set_auto_page_break(auto=True, margin=15) # Ako tekst pređe donju marginu (na 15mm), otvara se nova strana
        pdf.add_page() # Otvaranje prve stranice (automatski okida i funkciju header())
        
        # Podešavanje fonta unutar same tabele
        if os.path.exists(FONT_REG):
            pdf.add_font("DejaVu", "", FONT_REG, uni=True)
            pdf.set_font("DejaVu", "", 8)
            font_ime = "DejaVu"
        else:
            pdf.set_font("Helvetica", "", 8)
            font_ime = "Helvetica"
            
        # Unutrašnja funkcija koja crta plavo zaglavlje za glavnu tabelu specifikacije
        def nacrtaj_zaglavlje_specifikacije():
            pdf.set_fill_color(49, 130, 206)  # Svetlo plava boja (RGB)
            pdf.set_text_color(255)           # Bela boja teksta
            if font_ime == "DejaVu":
                pdf.set_font("DejaVu", "", 9)
            else:
                pdf.set_font("Helvetica", "B", 9)
            
            # Definisanje naziva kolona i njihovih širina u milimetrima (ukupno 197mm)
            cols = [("Datum", 22), ("RO", 18), ("Krug", 15), ("Tip materijala", 60), ("Kol", 15), ("Jed", 10), ("Napomena", 50)]
            for col_name, width in cols:
                pdf.cell(width, 10, col_name, border=0, align="C", fill=True) # fill=True boji pozadinu ćelije
            pdf.ln() # Prelazak u novi red

        # Crtamo prvo zaglavlje na samom početku dokumenta
        nacrtaj_zaglavlje_specifikacije()

        # Priprema podataka za ispisivanje stavki
        pdf.set_text_color(0) # Vraćamo boju teksta na crnu
        pdf.set_font(font_ime, "", 8)
        df_clean = df.dropna(subset=['datum', 'orman', 'tip']) # Čistimo redove koji nemaju osnovne podatke
        
        # SORTIRANJE: Prvo po Ormanu (RO), pa unutar tog ormana po Tipu materijala po azbuci
        if not df_clean.empty:
            df_clean = df_clean.sort_values(
                by=['orman', 'tip'], 
                ascending=[True, True], 
                key=lambda col: col.str.lower() if col.name in ['orman', 'tip'] else col
            ).reset_index(drop=True)
        
        # Prolazimo kroz svaki red očišćene tabele i ispisujemo ga u PDF
        for _, r in df_clean.iterrows():
            # Provera visine: ako sledeći red (visine 8mm) prelazi 282mm (visina A4 je 297mm - 15mm margina), otvori novu stranu
            if pdf.get_y() + 8 > 282:
                pdf.add_page() 
                nacrtaj_zaglavlje_specifikacije() # Na novoj strani ponovo nacrtaj plavo zaglavlje
                pdf.set_text_color(0) 
                pdf.set_font(font_ime, "", 8) 
            
            # Ispis pojedinačnih ćelija u redu
            pdf.cell(22, 8, str(r['datum']), border=0, align="C")
            pdf.cell(18, 8, str(r['orman']), border=0, align="C")
            pdf.cell(15, 8, str(r['opis']), border=0, align="C")
            pdf.cell(60, 8, str(r['tip']), border=0, align="C")
            pdf.cell(15, 8, str(r['kol']), border=0, align="C")
            pdf.cell(10, 8, str(r['jed']), border=0, align="C")
            nap = str(r['napomena']) if r['napomena'] and str(r['napomena']) != 'None' else ""
            pdf.cell(50, 8, nap, border=0, align="C")
            pdf.ln() # Prelazak u novi red za sledeću stavku

        # Provera prostora pre crtanja druge tabele (Rekapitualcije)
        if pdf.get_y() + 60 > 282:
            pdf.add_page() # Ako nema dovoljno mesta za zaglavlje i bar par redova, prebaci na novu stranu
        else:
            pdf.ln(10) # Inače napravi razmak od 10mm
        
        # ----------------------------------------------------------------------
        # TABELA 2: ZBIRNA REKAPITULACIJA PODATAKA
        # ----------------------------------------------------------------------
        sirina_naziv = 130  # Širina kolone za naziv materijala
        sirina_kol = 50     # Širina kolone za ukupnu količinu
        X_pochetna = 15     # Pomeramo tabelu malo udesno (centriranje na stranici)
        
        pdf.set_x(X_pochetna)
        pdf.set_fill_color(44, 52, 70)  # Tamno siva/teget boja pozadine zaglavlja rekapitulacije
        pdf.set_text_color(255)          # Bela boja teksta
        if font_ime == "DejaVu":
            pdf.set_font("DejaVu", "", 10)
        else:
            pdf.set_font("Helvetica", "B", 10)
            
        # Naslovni red Zbirne rekapitulacije
        pdf.cell(sirina_naziv + sirina_kol, 10, "ZBIRNA REKAPITULACIJA", border=0, ln=True, align="C", fill=True)
        
        pdf.set_text_color(50, 50, 50)     # Tamno siva boja slova za stavke
        pdf.set_draw_color(230, 230, 230) # Vrlo svetlo siva boja za horizontalne linije (border)
        pdf.set_line_width(0.2)            # Tanka linija borders-a
        
        # Promenljive u kojima ćemo sabirati ukupne količine svih regala i svih kablova
        ukupno_regali = 0.0
        ukupno_kablovi = 0.0
        
        if not df_clean.empty:
            # Grupisanje podataka: Saberi sve količine ('kol') za isti 'tip' i istu 'jed' (jedinicu mere)
            utrosak = df_clean.groupby(['tip', 'jed'])['kol'].sum().reset_index()
            # Sortiranje rekapitulacije po abecedi naziva materijala
            utrosak = utrosak.sort_values(by='tip', ascending=True, key=lambda col: col.str.lower()).reset_index(drop=True)
            
            for _, row in utrosak.iterrows():
                # Provera visine za svaki red rekapitulacije
                if pdf.get_y() + 9 > 282:
                    pdf.add_page()
                    pdf.set_x(X_pochetna)
                    pdf.set_fill_color(44, 52, 70)
                    pdf.set_text_color(255)
                    pdf.cell(sirina_naziv + sirina_kol, 8, "ZBIRNA REKAPITULACIJA (Nastavak)", border=0, ln=True, align="C", fill=True)
                    pdf.set_text_color(50, 50, 50)
                    pdf.set_draw_color(230, 230, 230)
                
                tip_naziv = str(row['tip'])
                kolicina_val = float(row['kol'])
                jedinica_naziv = str(row['jed'])
                
                # LOGIKA SABIRANJA ZA UKUPNE ZBIRE NA DNU:
                # Ako naziv sadrži reč "REGAL", dodaj u zbir regala
                if "REGAL" in tip_naziv.upper():
                    ukupno_regali += kolicina_val
                # Ako naziv sadrži neku od oznaka kablova, dodaj u zbir kablova
                elif any(x in tip_naziv.upper() for x in ["PP-Y", "N2XH", "FE180", "PP00", "H07RN", "LIYCY", "P/F", "SKS", "CAT"]):
                    ukupno_kablovi += kolicina_val
                
                pdf.set_x(X_pochetna)
                if font_ime == "DejaVu":
                    pdf.set_font("DejaVu", "", 9)
                else:
                    pdf.set_font("Helvetica", "", 9)
                    
                # Ispis naziva artikla sa donjom linijom ("B")
                pdf.cell(sirina_naziv, 9, f" {tip_naziv} ({jedinica_naziv})", border="B", align="L")
                
                # Ispis količine (formatirane na 2 decimale) sa desnim poravnanjem
                if font_ime == "DejaVu":
                    pdf.set_font("DejaVu", "", 9)
                else:
                    pdf.set_font("Helvetica", "B", 9)
                pdf.cell(sirina_kol, 9, f"{kolicina_val:.2f} ", border="B", align="R")
                pdf.ln()
                
        # --- UKUPAN RED 1: SUMA SVIH REGALA ---
        if pdf.get_y() + 20 > 282: 
            pdf.add_page()
            
        pdf.set_x(X_pochetna)
        pdf.set_fill_color(240, 244, 248) # Svetlo sivo-plava pozadina za isticanje
        pdf.set_text_color(20, 30, 55)     # Tamni tekst
        if font_ime == "DejaVu":
            pdf.set_font("DejaVu", "", 10)
        else:
            pdf.set_font("Helvetica", "B", 10)
            
        pdf.cell(sirina_naziv, 10, " SVI REGALI ZAJEDNO (m)", border="TB", align="L", fill=True) # TB = Top i Bottom border
        pdf.cell(sirina_kol, 10, f"{ukupno_regali:.2f} m ", border="TB", align="R", fill=True)
        pdf.ln()
        
        # --- UKUPAN RED 2: SUMA SVIH KABLOVA ---
        pdf.set_x(X_pochetna)
        pdf.set_fill_color(230, 242, 255) # Svetlo plava pozadina
        pdf.set_text_color(49, 130, 206)  # Plava boja teksta (podudara se sa temom aplikacije)
        
        pdf.cell(sirina_naziv, 10, " UKUPNO SVIH KABLOVA (m)", border="B", align="L", fill=True)
        pdf.cell(sirina_kol, 10, f"{ukupno_kablovi:.2f} m ", border="B", align="R", fill=True)
        
        return pdf.output() # Vraća generisani PDF kao raw bajtove spremne za preuzimanje

# ==============================================================================
# 4. KORISNIČKI INTERFEJS (STREAMLIT WEB APP)
# ==============================================================================
# Inicijalizujemo našu klasu sa logikom
app = ElektroProUltra()

# BOČNI MENI (SIDEBAR) - Za sistemske operacije (Backup i Restore baze)
with st.sidebar:
    st.header("⚙️ SISTEM")
    # Provera da li fajl baze uopšte postoji da bismo ponudili dugme za download
    if os.path.exists(app.db_name):
        with open(app.db_name, "rb") as f:
            st.sidebar.download_button("📥 PREUZMI BACKUP", f, file_name="elektro_baza.db", use_container_width=True)
    st.divider()
    
    # Polje za učitavanje (upload) eksternog .db fajla radi povratka podataka
    f_res = st.file_uploader("Restore .db", type="db")
    if f_res and st.button("⚠️ POTVRDI RESTORE", use_container_width=True):
        with open(app.db_name, "wb") as f: 
            f.write(f_res.getbuffer()) # Upisujemo bajtove učitanog fajla preko trenutne baze
        st.rerun() # Ponovo osvežavamo aplikaciju da učita nove podatke
    st.divider()
    
    # Sigurnosni checkbox pre nego što se omogući brisanje cele baze
    if st.checkbox("Potvrda brisanja"):
        if st.button("🔴 OBRIŠI SVE", use_container_width=True):
            app.obrisi_sve()
            st.rerun()

# FORMA ZA UNOS NOVE STAVKE (Korišćenjem st.expander koji može da se skuplja/širi)
with st.expander("📝 UNOS NOVE STAVKE", expanded=True):
    c1, c2, c3 = st.columns(3) # Delimo ekran na 3 kolone za osnovne podatke
    dat = c1.text_input("📅 Datum", datetime.now().strftime("%d.%m.%Y")) # Automatski nudi današnji datum
    orm = c2.text_input("🏗️ RO").upper().strip() # Automatski pretvara unos u velika slova i briše razmake
    krug = c3.text_input("🔌 Krug")
    
    kat_col, tip_col = st.columns(2) # Delimo donji deo na dve kolone za izbor materijala
    # Prvi selectbox nudi nazive kategorija (ključevi našeg rečnika)
    izab_kat = kat_col.selectbox("📁 Kategorija", options=list(app.kategorije_materijala.keys()), key="m_kat")
    # Drugi selectbox dinamički nudi samo artikle koji pripadaju izabranoj kategoriji
    tip = tip_col.selectbox("📦 Tip materijala", options=app.kategorije_materijala[izab_kat], key="m_tip")
    
    # Otvaramo formu za količinu i napomenu. Forme sprečavaju osvežavanje ekrana dok se ne klikne na dugme
    with st.form("forma_podaci", clear_on_submit=True):
        c4, c5, c6 = st.columns([1, 1, 2]) # Različite širine kolona (napomena je duplo šira)
        kol = c4.number_input("Kolicina", min_value=0.0, step=0.1)
        jed = c5.selectbox("Jedinica", ["m", "kom"])
        nap = c6.text_input("📝 Napomena")
        
        if st.form_submit_button("💾 SNIMI", use_container_width=True):
            # Validacija: Polja RO i Krug su obavezna
            if orm and krug:
                # Pozivamo funkciju za spasavanje prosleđujući joj torku (tuple) podataka
                app.sacuvaj_u_bazu((dat, orm, krug, tip, kol, jed, nap))
                st.rerun() # Osvežavamo ekran da se nova stavka odmah vidi u tabeli ispod
            else:
                st.error("Polja 'RO' i 'Krug' ne smeju biti prazna!")

# PRIKAZ I INTERAKTIVNO MENJANJE PODATAKA
with sqlite3.connect(app.db_name) as conn:
    # Čitamo sve podatke iz baze hronološki unazad (poslednje uneseno ide na vrh)
    df_prikaz = pd.read_sql_query("SELECT * FROM radovi ORDER BY id DESC", conn)

# Ako baza ima podatke, prikaži statistiku, tabelu i PDF dugme
if not df_prikaz.empty:
    # --- LOGIKA ZA GLAVNI METRIC NA EKRANU ---
    # Definišemo ključne reči koje označavaju prateću opremu (a ne kablove)
    oprema_keywords = ("REGAL", "BREZON", "C-SINA", "LR ")
    # Pravimo filter masku koja pronalazi sve redove gde se u nazivu nalazi neka od tih reči
    mask = df_prikaz['tip'].str.upper().str.contains('|'.join(oprema_keywords))
    
    # Izbacujemo opremu (uzimamo inverziju maske pomoću ~) da nam ostanu samo kablovi
    df_kab = df_prikaz[~mask]
    # Sumiramo količinu svih kablova čija je jedinica mere "m"
    s_m = df_kab[df_kab['jed'] == 'm']['kol'].sum()
    # Sumiramo količinu svih kablova čija je jedinica mere "kom" (npr. krajevi, mufovi ukoliko postoje)
    s_k = df_kab[df_kab['jed'] == 'kom']['kol'].sum()

    # Veliki vizuelni vidžet na vrhu koji pokazuje ukupnu dužinu kablova na gradilištu
    st.metric("UKUPNO METARA KABLA", f"{s_m:.2f} m")
    
    # GLAVNA INTERAKTIVNA TABELA (Data Editor)
    # Korisnik može direktno ovde da menja bilo koje polje, briše redove ili dodaje nove
    edited_df = st.data_editor(df_prikaz, use_container_width=True, hide_index=True, num_rows="dynamic", key="glavni_editor")
    
    # Ako korisnik izmeni nešto u tabeli, mora da klikne na ovo dugme da potvrdi
    if st.button("✅ SAČUVAJ IZMENE", use_container_width=True):
        app.azuriraj_bazu(edited_df) # Šaljemo izmenjeni DataFrame na upis u bazu
        st.rerun()

    st.divider()
    
    # DUGME ZA PREUZIMANJE PDF IZVEŠTAJA
    try:
        # Generišemo PDF preko naše funkcije i smeštamo bajtove u promenljivu pdf_out
        pdf_out = app.generisi_pdf(edited_df, s_m, s_k)
        if pdf_out:
            # Otvaramo zvanično Streamlit preuzimanje fajlova u brauzeru
            st.download_button(
                label="📄 PREUZMI PDF IZVESTAJ", 
                data=bytes(pdf_out), # Pretvaramo podatke u čiste bajtove
                file_name=f"izvestaj_{datetime.now().strftime('%d_%m_%Y')}.pdf", # Dinamičko ime fajla sa današnjim datumom
                mime="application/pdf",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Greška pri generisanju PDF-a: {e}")
else:
    # Ako je baza prazna, umesto svega iznad ispiši plavu info poruku
    st.info("Baza je prazna. Unesite prve stavke kako bi se prikazao izveštaj.")
