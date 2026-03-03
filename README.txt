CONTACTOR
Automatizovaný nástroj pro vyhledávání potenciálních B2B klientů, analýzu jejich webových stránek a ukládání výsledků do CSV databáze.

============================================================

ÚČEL PROJEKTU

Contactor slouží k:

získávání firem (aktuálně pomocí mock dat),

stažení jejich webových stránek,

automatické analýze kvality webu,

generování skóre a doporučení na zlepšení,

ukládání všech výsledků do CSV souboru.

Projekt je navržen modulárně tak, aby bylo možné v budoucnu:

přidat Google Places API,

integrovat lokální LLM modul (např. Ollama),

případně využít externí AI API.

============================================================

STRUKTURA PROJEKTU

contactor/

main.py
Hlavní soubor programu, řídí celý proces.

leads.db
Výstupní databáze firem.

logger_config.py

mock_companies

data/
database.py
Správa ukládání dat a export do CSV.

analysis/
llm_analyzer.py
Modul pro analýzu webových stránek.

scraping/
web_scraper.py
Modul pro stahování HTML obsahu webů.

config/
settings.py

============================================================

JAK PROGRAM FUNGUJE (PIPELINE)

Získání firem

Aktuálně mock data reálných firem

Do budoucna Google Places API

Stažení webu

web_scraper stáhne HTML obsah stránky

Analýza webu

llm_analyzer vyhodnocuje:

délku textu

strukturu (H1, H2)

počet obrázků

počet odkazů

indikaci aktuálnosti

Výstupem je:

web_score (0–100)

improvement_tips

Uložení dat

database.py uloží data

CSV soubor se automaticky aktualizuje

============================================================

CSV SOUBOR

Výstupní soubor se nachází zde:

data/leads.csv

Obsahuje například tyto sloupce:

name

website

web_score

improvement_tips

email

phone

============================================================

SPUŠTĚNÍ PROGRAMU

Otevři terminál ve složce contactor

Spusť příkaz:

python main.py

Výsledky najdeš v souboru data/leads.csv

============================================================

AKTUÁLNÍ STAV

Funkční pipeline s mock daty

Automatický export do CSV

Lokální heuristická analýza webů

Ošetření chyb při nefunkčních URL

============================================================

PLÁNOVANÝ VÝVOJ

FÁZE 1:

Vylepšení analyzátoru

Extrakce emailu a telefonu z webu

Stabilizace systému

FÁZE 2:

Integrace lokálního LLM modulu (např. Ollama)

Generování pokročilých a inteligentních výstupů

Marketingové a UX hodnocení webů

FÁZE 3:

Integrace Google Places API

Automatické získávání reálných firem

============================================================

POZNÁMKA

Projekt je navržen modulárně.
Analytický modul lze kdykoli nahradit pokročilejším LLM řešením bez nutnosti měnit ostatní části systému.