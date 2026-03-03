import os
import logging
import socket
from data.database import Database
from analysis.business_analyzer import analyze_web
from config import settings
from ollama_bootstrap import ensure_ollama_ready
from scraping.web_scraper import prepare_url
from api.google_places import fetch_companies_from_google  # nový modul

# -------------------------------
# Logovací systém
# -------------------------------
def setup_logger():
    logger = logging.getLogger("Contactor")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    os.makedirs("logs", exist_ok=True)
    fh = logging.FileHandler("logs/contactor.log", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

logger = setup_logger()

# -------------------------------
# Kontrola internetu
# -------------------------------
def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

# -------------------------------
# Zpracování jedné firmy
# -------------------------------
def process_company(firm: dict, db: Database):
    try:
        website = firm.get("website")
        if not website:
            logger.warning(f"{firm.get('name')} nemá URL.")
            firm["web_score"] = 404
            firm["improvement_tips"] = "No website..."
            firm["email"] = ""
            firm["phone"] = ""
            db.add_company(firm)
            return

        # Připravit URL
        try:
            normalized_website = prepare_url(website)
        except Exception as e:
            logger.warning(f"{firm.get('name')} má nevalidní URL ({website}): {e}")
            firm["web_score"] = 404
            firm["improvement_tips"] = ["Invalid URL"]
            firm["email"] = ""
            firm["phone"] = ""
            db.add_company(firm)
            return

        # Uložit firmu do DB s analyzed=False
        firm["website"] = normalized_website
        if not db.company_exists(normalized_website):
            db.add_company(firm)
            logger.info(f"Přidána nová firma do DB: {firm.get('name')}")
        else:
            logger.info(f"Firma již existuje v DB: {firm.get('name')}")

    except Exception as e:
        logger.error(f"Chyba při zpracování {firm.get('name')}: {e}")

# -------------------------------
# Spuštění batch zpracování
# -------------------------------
def run_batch():
    if not check_internet():
        logger.error("Internetové připojení není dostupné. Program se ukončí.")
        return

    db = Database()

    # --- Dotaz uživatele na parametry ---
    try:
        num_companies = int(input("Kolik firem chcete stáhnout z Google Places? ").strip())
    except ValueError:
        num_companies = 10

    location = input("Zadejte město / lokaci (default: Brno): ").strip() or "Brno"
    keyword = input("Zadejte klíčové slovo (např. realitní kancelář): ").strip() or ""

    logger.info("Stahuji firmy z Google Places...")
    companies = fetch_companies_from_google(
        location=location,
        keyword=keyword,
        max_results=num_companies,
        db=db  # předáváme db pro kontrolu existujících firem
    )

    logger.info(f"Načteno {len(companies)} firem z Google Places.")
    logger.info(f"Spouštím analýzu firem, které ještě nebyly analyzovány...")

    unanalyzed = db.get_unanalyzed_companies()
    total = len(unanalyzed)
    for i, firm in enumerate(unanalyzed):
        print(f"[{i+1}/{total}] {firm[1]}")  # [1] = name
        # Analýza přes LLM
        result = analyze_web(firm[3], max_subpages=settings.MAX_SUBPAGES)  # [3] = website

        if isinstance(result, str):
            import json
            try:
                result = json.loads(result)
            except:
                result = {}

        score = result.get("lead_score", 0)
        if not isinstance(score, (int, float)):
            score = 0

        tips = result.get("improvement_tips", [])
        if isinstance(tips, list):
            tips_str = ", ".join(tips)
        elif isinstance(tips, str):
            tips_str = tips
        else:
            tips_str = ""

        email = result.get("email", "")
        phone = result.get("phone", "")

        # Aktualizace DB
        db.update_company_analysis(firm[3], score, tips_str, email, phone)

    db.export_new_to_csv()
    db.close()
    logger.info("Batch dokončen. CSV je aktualizované.")

# -------------------------------
# Příkazy
# -------------------------------
def reset_database():
    db_path = DB_PATH
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info("Databáze byla smazána.")
    else:
        logger.info("Databáze neexistuje.")

def show_stats():
    db = Database()
    total = db.get_total_count()
    db.close()
    logger.info(f"Celkový počet firem v databázi: {total}")

def show_help():
    print("""
Dostupné příkazy:

run        → spustí zpracování firem
reset-db   → smaže lifetime databázi
stats      → zobrazí počet firem v databázi
help       → zobrazí tuto nápovědu
exit       → ukončí program
""")

# -------------------------------
# Hlavní smyčka CLI
# -------------------------------
def main():
    print("\n########################################\n#                                      #\n#           CONTACTOR ready!           #\n#       © 2026 Michael Šindelář        #\n#   Napiš 'help' pro přehled příkazů.  #\n#                                      #\n########################################\n")

    while True:
        command = input(">>> ").strip().lower()
        if command == "run":
            run_batch()
        elif command == "reset-db":
            reset_database()
        elif command == "stats":
            show_stats()
        elif command == "help":
            show_help()
        elif command == "exit":
            print("Ukončuji program.")
            break
        elif command == "":
            continue
        else:
            print("Neznámý příkaz. Zadej 'help'.")


if __name__ == "__main__":
    print("Spouštění programu...")
    ensure_ollama_ready()
    main()
