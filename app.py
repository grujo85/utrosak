import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF

# ==============================================================================
# 1. APPLICATION ENVIRONMENT & CONFIGURATION
# ==============================================================================
# Globalna inicijalizacija Streamlit klijentskog konteksta i renderovnih parametara.
st.set_page_config(
    page_title="ELEKTRO-LOG BUSINESS v1.1",  # Unikatni identifikator aplikacije unutar DOM-a browsera
    layout="wide",                           # Maksimizacija horizontalnog viewport-a (fluidni raspored)
    initial_sidebar_state="expanded"         # Perzistencija stanja bočne navigacione konzole
)

# Definisanje apsolutne/relativne putanje do TrueType resursa za UTF-8 mapiranje karaktera
FONT_REG = "DejaVuSans.ttf"

# ==============================================================================
# 2. DOCUMENT ARCHITECTURE & RENDER ENGINE (FPDF Wrapper)
# ==============================================================================
class PDFSpec(FPDF):
    """
    Subklasa izvedena iz FPDF jezgra, specijalizovana za strukturno formatiranje,
    generisanje repetitivnih zaglavlja (Header), podnožja (Footer) i kontrolu
    preloma stranica (Page-break boundary) kod tehničkih specifikacija.
    """
    
    def header(self):
        """
        Iscrtavanje zaglavlja dokumenta. Izvršava se automatski pri svakoj 
        alokaciji nove stranice unutar PDF generatora.
        """
        # Evaluacija prisustva i asinhroni pokušaj renderovanja korporativnog logotipa
        if os.path.exists("elmar.webp"):
            try: 
                self.image("elmar.webp", 10, 8, 33)  # Geometrijska alokacija: X=10mm, Y=8mm, W=33mm
            except Exception: 
                pass  # Fail-safe mehanizam: sprečavanje prekida niti u slučaju korumpiranog resursa
            
        # --- Hijerarhijski Nivo 1: Primarni Naslov ---
        if os.path.exists(FONT_REG):
            self.add_font("DejaVu", "", FONT_REG, uni=True)
            self.set_font("DejaVu", "", 14)
        else:
            self.set_font("Helvetica", "B", 14)  # Fallback strategija na nativni font u slučaju odsustva TTF-a
            
        self.cell(0, 10, "SPECIFIKACIJA RADOVA", ln=True, align="R")
        
        # --- Hijerarhijski Nivo 2: Sekundarni Naslov (Podnaslov) ---
        if os.path.exists(FONT_REG):
            self.set_font("DejaVu", "", 10)  
        else:
            self.set_font("Helvetica", "B", 10)
            
        self.cell(0, 8, "UTROSAK MATERIJALA", ln=True, align="R")

        # --- Hijerarhijski Nivo 3: Vremenski Metapodaci ---
        if os.path.exists(FONT_REG):
            self.set_font("DejaVu", "", 9)
        else:
            self.set_font("Helvetica", "", 9)
            
        # Dinamičko formatiranje vremenskog pečata prema ISO/IEC standardu lokalizacije (DD.MM.YYYY)
        self.cell(0, 10, f"Datum izrade: {datetime.now().strftime('%d.%m.%Y')}", ln=True, align="R")
        self.ln(10)  # Skalarni vertikalni ofset (10mm pad) pre inicijalizacije tabularnog segmenta

    def footer(self):
        """
        Iscrtavanje podnožja stranice sa zaštićenim metapodacima i pravima pristupa.
        Sadrži fiksno relativno pozicioniranje u odnosu na donju marginu (Y-offset).
        """
        self.set_y(-15)  # Pozicioniranje na marginu od -15mm u odnosu na kraj matrice stranice
        
        if os.path.exists(FONT_REG):
            self.set_font("DejaVu", "", 8)
        else:
            self.set_font("Helvetica", "I", 8)  # Tipografski stil: Kurziv (Italic) za sistemski fallback
            
        self.set_text_color(128)  # Postavljanje neutralnog sivo-tonskog kanala (Grayscale: 128)
        self.cell(0, 10, "ELMAR ELEKTRO-INSTALACIJE | DESIGN VLADE 2026", align="C")

# ==============================================================================
# 3. DATA ACCESS LAYER & BUSINESS LOGIC ENGINE
# ==============================================================================
class ElektroProUltra:
    """
    Glavni poslovni kontroler (Controller/Service Layer).
    Enkapsulira šifarnik materijala, upravlja stanjem SQLite baze podataka,
    izvršava CRUD operacije i implementira algoritme za agregaciju i eksport podataka.
    """
    def __init__(self):
        """Inicijalizacija klase, postavljanje parametara konekcije i provera integriteta šeme."""
        self.db_name = "elektro_baza.db"  
        
        # Centralizovani šifarnik i nomenklatura artikala strukturirana po tehnološkim celinama
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
        self.kreiraj_bazu()

    def kreiraj_bazu(self):
        """
        Izvršava DDL naredbu za kreiranje relacione tabele ukoliko ona ne postoji u skladištu.
        Inicijalizuje bazični indeks i tipove podataka kolona.
        """
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS radovi 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                datum TEXT, orman TEXT, opis TEXT, tip TEXT, 
                kol REAL, jed TEXT, napomena TEXT)""")

    def sacuvaj_u_bazu(self, d):
        """
        Ubacuje novi entitet u bazu podataka primenom parametrizovanog upita.
        
        :param d: tuple koji sadrži vrednosti (datum, orman, opis, tip, kol, jed, napomena)
        :type d: tuple
        """
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("INSERT INTO radovi (datum, orman, opis, tip, kol, jed, napomena) VALUES (?,?,?,?,?,?,?)", d)

    def azuriraj_bazu(self, df_izmenjen):
        """
        Osvežava kompletno stanje baze podataka. Koristi transakcionu metodu
        brisanja celokupne tabele (Flush) i naknadnog unosa novog stanja iz DataFrame-a.
        
        :param df_izmenjen: Modifikovani podaci prosleđeni sa UI interfejsa.
        :type df_izmenjen: pandas.DataFrame
        """
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("DELETE FROM radovi")  # Kaskadni reset podataka unutar transakcije
            df_izmenjen.to_sql("radovi", conn, if_exists="append", index=False)

    def obrisi_sve(self):
        """Izvršava destruktivnu operaciju brisanja svih redova u tabeli (Truncate ekvivalent)."""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("DELETE FROM radovi")

    def generisi_pdf(self, df, tm, tk):
        """
        Glavni algoritam za transformaciju skladištenih podataka u strukturirani PDF dokument.
        Implementira logiku preloma stranica i kalkulaciju kumulativne rekapitulacije materijala.
        
        :param df: Skup podataka za generisanje specifikacije
        :param tm: Sumarna vrednost metara kabla (prosledđeno sa UI-ja)
        :param tk: Sumarna vrednost komadnih stavki kablova
        :type df: pandas.DataFrame
        :return: Binarni tok (raw bytes) generisanog PDF-a
        :rtype: bytes
        """
        pdf = PDFSpec()
        pdf.set_auto_page_break(auto=True, margin=15)  # Graničnik preloma stranice na 15mm od dna
        pdf.add_page()
        
        # Konfiguracija radnog fonta podsistema u zavisnosti od sistemskih resursa
        if os.path.exists(FONT_REG):
            pdf.add_font("DejaVu", "", FONT_REG, uni=True)
            pdf.set_font("DejaVu", "", 8)
            font_ime = "DejaVu"
        else:
            pdf.set_font("Helvetica", "", 8)
            font_ime = "Helvetica"
            
        def nacrtaj_zaglavlje_specifikacije():
            """Generiše stilizovano zaglavlje primarne tabele sa fiksnim širinama kolona (Total: 197mm)."""
            pdf.set_fill_color(49, 130, 206)  # Korporativna nijansa: Material Blue
            pdf.set_text_color(255)           # Kontrastna bela boja teksta
            if font_ime == "DejaVu":
                pdf.set_font("DejaVu", "", 9)
            else:
                pdf.set_font("Helvetica", "B", 9)
            
            cols = [("Datum", 22), ("RO", 18), ("Krug", 15), ("Tip materijala", 60), ("Kol", 15), ("Jed", 10), ("Napomena", 50)]
            for col_name, width in cols:
                pdf.cell(width, 10, col_name, border=0, align="C", fill=True)
            pdf.ln()

        # Inicijalno generisanje strukture tabele
        nacrtaj_zaglavlje_specifikacije()

        pdf.set_text_color(0)  # Vraćanje boje fonta na crnu (Grayscale: 0)
        pdf.set_font(font_ime, "", 8)
        df_clean = df.dropna(subset=['datum', 'orman', 'tip'])  # Data cleaning: uklanjanje nepotpunih redova
        
        # Sortiranje skupa podataka: Primarno po oznaci razvodnog ormana, sekundarno po nazivu artikla
        if not df_clean.empty:
            df_clean = df_clean.sort_values(
                by=['orman', 'tip'], 
                ascending=[True, True], 
                key=lambda col: col.str.lower() if col.name in ['orman', 'tip'] else col
            ).reset_index(drop=True)
        
        # Iterativno mapiranje redova iz DataFrame-a u ćelije PDF dokumenta
        for _, r in df_clean.iterrows():
            # Prediktivna provera prostora: Ako novi red (8mm) narušava marginu, vrši se alokacija nove stranice
            if pdf.get_y() + 8 > 282:
                pdf.add_page() 
                nacrtaj_zaglavlje_specifikacije()  
                pdf.set_text_color(0) 
                pdf.set_font(font_ime, "", 8) 
            
            pdf.cell(22, 8, str(r['datum']), border=0, align="C")
            pdf.cell(18, 8, str(r['orman']), border=0, align="C")
            pdf.cell(15, 8, str(r['opis']), border=0, align="C")
            pdf.cell(60, 8, str(r['tip']), border=0, align="C")
            pdf.cell(15, 8, str(r['kol']), border=0, align="C")
            pdf.cell(10, 8, str(r['jed']), border=0, align="C")
            nap = str(r['napomena']) if r['napomena'] and str(r['napomena']) != 'None' else ""
            pdf.cell(50, 8, nap, border=0, align="C")
            pdf.ln()

        # Alokacija prostora za sekundarnu tabelu (Zbirna Rekapitulacija)
        if pdf.get_y() + 60 > 282:
            pdf.add_page()
        else:
            pdf.ln(10)
        
        # ----------------------------------------------------------------------
        # REKAPITULACIONA MATRICA RADOVA I MATERIJALA
        # ----------------------------------------------------------------------
        sirina_naziv = 130  
        sirina_kol = 50     
        X_pochetna = 15     # Pomeraj udesno radi postizanja optičke simetrije na A4 formatu
        
        pdf.set_x(X_pochetna)
        pdf.set_fill_color(44, 52, 70)  # Akcentovana tamna boja (Slate Gray) za zaglavlje rekapitulacije
        pdf.set_text_color(255)
        if font_ime == "DejaVu":
            pdf.set_font("DejaVu", "", 10)
        else:
            pdf.set_font("Helvetica", "B", 10)
            
        pdf.cell(sirina_naziv + sirina_kol, 10, "ZBIRNA REKAPITULACIJA", border=0, ln=True, align="C", fill=True)
        
        pdf.set_text_color(50, 50, 50)     
        pdf.set_draw_color(230, 230, 230) # Soft-gray grid linije
        pdf.set_line_width(0.2)            
        
        ukupno_regali = 0.0
        ukupno_kablovi = 0.0
        
        if not df_clean.empty:
            # Agregacija podataka: Grupisanje i sumiranje kvantiteta po tipu i jedinici mere
            utrosak = df_clean.groupby(['tip', 'jed'])['kol'].sum().reset_index()
            utrosak = utrosak.sort_values(by='tip', ascending=True, key=lambda col: col.str.lower()).reset_index(drop=True)
            
            for _, row in utrosak.iterrows():
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
                
                # Evaluacija stringova i klasifikacija elemenata u makro-kategorije (Regali vs Kablovi)
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
                
        # --- Sumarni red 1: Zbirni kvantitet nosača kablova ---
        if pdf.get_y() + 20 > 282: 
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
        
        # --- Sumarni red 2: Zbirni kvantitet elektroprovodnika ---
        pdf.set_x(X_pochetna)
        pdf.set_fill_color(230, 242, 255) 
        pdf.set_text_color(49, 130, 206)  
        
        pdf.cell(sirina_naziv, 10, " UKUPNO SVIH KABLOVA (m)", border="B", align="L", fill=True)
        pdf.cell(sirina_kol, 10, f"{ukupno_kablovi:.2f} m ", border="B", align="R", fill=True)
        
        return pdf.output()

# ==============================================================================
# 4. PRESENTATION LAYER (Streamlit UI Execution Context)
# ==============================================================================
# Inicijalizacija poslovnog kontrolera aplikacije
app = ElektroProUltra()

# Konzola bočnog menija: Upravljanje sistemskim resursima, IO operacije i administracija baze
with st.sidebar:
    st.header("⚙️ SISTEM")
    
    # Provera postojanja skladišta za omogućavanje eksporta baze podataka
    if os.path.exists(app.db_name):
        with open(app.db_name, "rb") as f:
            st.sidebar.download_button("📥 PREUZMI BACKUP", f, file_name="elektro_baza.db", use_container_width=True)
    st.divider()
    
    # Mehanizam za uvoz eksternog SQL skladišta (Restore baze podataka)
    f_res = st.file_uploader("Restore .db", type="db")
    if f_res and st.button("⚠️ POTVRDI RESTORE", use_container_width=True):
        with open(app.db_name, "wb") as f: 
            f.write(f_res.getbuffer()) 
        st.rerun()  # Hard-refresh aplikativnog stanja (UI Thread Reset)
    st.divider()
    
    # Sigurnosni mehanizam verifikacije pre destruktivnog brisanja podataka
    if st.checkbox("Potvrda brisanja"):
        if st.button("🔴 OBRIŠI SVE", use_container_width=True):
            app.obrisi_sve()
            st.rerun()

# Korisnički interfejs za unos novih unosa (Form submission handling)
with st.expander("📝 UNOS NOVE STAVKE", expanded=True):
    c1, c2, c3 = st.columns(3)  
    dat = c1.text_input("📅 Datum", datetime.now().strftime("%d.%m.%Y")) 
    orm = c2.text_input("🏗️ RO").upper().strip()  # Normalizacija unosa (Sanitization)
    krug = c3.text_input("🔌 Krug")
    
    kat_col, tip_col = st.columns(2)  
    izab_kat = kat_col.selectbox("📁 Kategorija", options=list(app.kategorije_materijala.keys()), key="m_kat")
    tip = tip_col.selectbox("📦 Tip materijala", options=app.kategorije_materijala[izab_kat], key="m_tip")
    
    # Izolovani kontekst forme radi sprečavanja prevremenog osvežavanja UI niti (Form scope)
    with st.form("forma_podaci", clear_on_submit=True):
        c4, c5, c6 = st.columns([1, 1, 2]) 
        kol = c4.number_input("Kolicina", min_value=0.0, step=0.1)
        jed = c5.selectbox("Jedinica", ["m", "kom"])
        nap = c6.text_input("📝 Napomena")
        
        if st.form_submit_button("💾 SNIMI", use_container_width=True):
            # Validacija biznis pravila: Polja 'RO' i 'Krug' su obavezni ključevi
            if orm and krug:
                app.sacuvaj_u_bazu((dat, orm, krug, tip, kol, jed, nap))
                st.rerun()  
            else:
                st.error("Polja 'RO' i 'Krug' ne smeju biti prazna!")

# Ekstrakcija podataka iz skladišta radi prezentacije na klijentskom UI-ju
with sqlite3.connect(app.db_name) as conn:
    df_prikaz = pd.read_sql_query("SELECT * FROM radovi ORDER BY id DESC", conn)

# Uslovno renderovanje analitičke table (Dashboard) i kontrola za modifikaciju podataka
if not df_prikaz.empty:
    # --- Analitička segmentacija podataka na klijentskoj strani ---
    oprema_keywords = ("REGAL", "BREZON", "C-SINA", "LR ")
    mask = df_prikaz['tip'].str.upper().str.contains('|'.join(oprema_keywords))
    
    df_kab = df_prikaz[~mask]  # Eliminacija prateće opreme iz kalkulacije provodnika
    s_m = df_kab[df_kab['jed'] == 'm']['kol'].sum()     
    s_k = df_kab[df_kab['jed'] == 'kom']['kol'].sum()   

    # Renderovanje ključnih metričkih indikatora (KPI Widget)
    st.metric("UKUPNO METARA KABLA", f"{s_m:.2f} m")
    
    # Inicijalizacija interaktivne baze podataka sa podrškom za dinamičku manipulaciju redovima
    edited_df = st.data_editor(df_prikaz, use_container_width=True, hide_index=True, num_rows="dynamic", key="glavni_editor")
    
    if st.button("✅ SAČUVAJ IZMENE", use_container_width=True):
        app.azuriraj_bazu(edited_df)  # Perzistencija novog stanja u bazu podataka
        st.rerun()

    st.divider()
    
    # Podsistem za eksport i preuzimanje generisanog PDF izveštaja
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
        st.error(f"Sistemska greška tokom izvršavanja PDF generatora: {e}")
else:
    # Renderovanje indikatora praznog stanja sistema (Empty state UI)
    st.info("Baza podataka je prazna. Unesite parametre u formu za generisanje analitike i izveštaja.")
