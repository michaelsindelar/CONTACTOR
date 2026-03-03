import sqlite3
import csv
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from config import settings

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
desktop_path = Path.home() / "Desktop"
CSV_PATH = desktop_path / f"new_leads_{timestamp}.csv"
DB_PATH = "leads.db"

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_table()
        self.current_run_ids = []

    # -------------------------------
    # Normalizace URL (centrální logika)
    # -------------------------------
    def normalize_url(self, url: str) -> str:
        if not url:
            return ""

        url = url.strip().lower()

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)
        netloc = parsed.netloc.replace("www.", "")
        path = parsed.path.rstrip("/")

        return f"{netloc}{path}"

    # -------------------------------
    # Vytvoření tabulky DB
    # -------------------------------
    def create_table(self):
        c = self.conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            industry TEXT,
            website TEXT UNIQUE,
            decision_maker_name TEXT,
            decision_maker_position TEXT,
            email TEXT,
            phone TEXT,
            web_score INTEGER,
            improvement_tips TEXT,
            analyzed INTEGER DEFAULT 0
        )
        """)
        self.conn.commit()

    # -------------------------------
    # Přidání firmy
    # -------------------------------
    def add_company(self, company_data: dict) -> bool:
        c = self.conn.cursor()
        try:
            normalized_website = self.normalize_url(company_data.get("website"))

            c.execute("""
            INSERT INTO companies (
                name,
                industry,
                website,
                decision_maker_name,
                decision_maker_position,
                email,
                phone,
                web_score,
                improvement_tips,
                analyzed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_data.get("name"),
                company_data.get("industry"),
                normalized_website,
                company_data.get("decision_maker_name"),
                company_data.get("decision_maker_position"),
                company_data.get("email"),
                company_data.get("phone"),
                company_data.get("web_score"),
                company_data.get("improvement_tips"),
                company_data.get("analyzed", 0),  # default 0 = neanalyzováno
            ))

            self.conn.commit()
            company_id = c.lastrowid
            self.current_run_ids.append(company_id)
            return True

        except sqlite3.IntegrityError:
            return False

    # -------------------------------
    # Zkontroluje existenci firmy podle webu
    # -------------------------------
    def company_exists(self, website: str) -> bool:
        if not website:
            return False

        normalized = self.normalize_url(website)
        c = self.conn.cursor()
        c.execute("SELECT 1 FROM companies WHERE website = ?", (normalized,))
        return c.fetchone() is not None

    # -------------------------------
    # Aktualizace firmy po analýze
    # -------------------------------
    def update_company_analysis(self, website: str, web_score: int, tips: str, email: str, phone: str):
        normalized = self.normalize_url(website)
        c = self.conn.cursor()
        c.execute("""
            UPDATE companies
            SET web_score = ?, improvement_tips = ?, email = ?, phone = ?, analyzed = 1
            WHERE website = ?
        """, (web_score, tips, email, phone, normalized))
        self.conn.commit()

    # -------------------------------
    # Export nově analyzovaných firem do CSV
    # -------------------------------
    def export_new_to_csv(self):
        if not self.current_run_ids:
            print("Žádné nové firmy k exportu.")
            return

        c = self.conn.cursor()
        placeholders = ",".join(["?"] * len(self.current_run_ids))
        query = f"SELECT * FROM companies WHERE id IN ({placeholders})"
        c.execute(query, self.current_run_ids)
        rows = c.fetchall()

        Path(CSV_PATH).parent.mkdir(parents=True, exist_ok=True)

        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID",
                "Firma",
                "Obor",
                "Web",
                "Jméno decision-makera",
                "Pozice decision-makera",
                "Email",
                "Telefon",
                "Lead score",
                "Tipy na zlepšení"
            ])

            filtered_rows = [r for r in rows if (r[8] is not None and r[8] >= settings.MIN_LEAD_SCORE_FOR_CSV)]
            writer.writerows(filtered_rows)

        print(f"Exportováno {len(filtered_rows)} nových firem do {CSV_PATH}")

    # -------------------------------
    # Získání počtu firem v DB
    # -------------------------------
    def get_total_count(self) -> int:
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM companies")
        return c.fetchone()[0]

    # -------------------------------
    # Získání firem, které ještě nebyly analyzovány
    # -------------------------------
    def get_unanalyzed_companies(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM companies WHERE analyzed = 0")
        return c.fetchall()

    # -------------------------------
    # Zavření DB
    # -------------------------------
    def close(self):
        self.conn.close()
