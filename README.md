CONTACTOR – Automated Lead Generation & Website Analysis System
Copyright (c) 2026 Michael Šindelář
All rights reserved.

Contactor je automatizovaný systém pro generování obchodních leadů pomocí Google Places API a následné analýzy firemních webových stránek pomocí LLM modelu (Ollama). Projekt je navržen jako lokálně běžící nástroj, který umožňuje vyhledat firmy podle klíčového slova a lokace, uložit jejich data do SQLite databáze, analyzovat jejich webový potenciál a exportovat vybrané výsledky do CSV souboru.

Systém funguje jako kompletní pipeline: Google Places API → lokální databáze → LLM analýza webu → aktualizace databáze → export CSV. Uživatel zadá počet firem, lokaci a klíčové slovo. Program následně stáhne přesně daný počet firem z Google Places API, uloží je do databáze leads.db se stavem analyzed = False, a poté provede analýzu webových stránek přes LLM model. Po dokončení analýzy se firma aktualizuje (skóre, kontaktní údaje, doporučení ke zlepšení) a označí se jako analyzed = True. Firmy splňující minimální lead score jsou exportovány do CSV souboru na plochu uživatele.

Hlavní funkce systému:

Vyhledávání firem přes Google Places API podle lokace a klíčového slova.

Uložení firem do SQLite databáze s kontrolou duplicit (normalizace URL).

Automatická analýza webových stránek pomocí LLM modelu běžícího lokálně přes Ollama.

Výpočet lead score a generování doporučení ke zlepšení.

Export vybraných firem do CSV podle minimální hodnoty lead score.

Detailní logging všech kroků (stahování, ukládání, analýza, export).

Kontrola internetového připojení před spuštěním batch operace.

Databáze:
Systém používá lokální SQLite databázi leads.db. Tabulka companies obsahuje mimo jiné sloupce: name, industry, website (UNIQUE), email, phone, web_score, improvement_tips a analyzed. Sloupec analyzed slouží k řízení stavu zpracování – pouze firmy s analyzed = 0 jsou analyzovány LLM modulem.

Export:
CSV soubor je generován automaticky po dokončení batch operace. Exportují se pouze firmy, které byly analyzovány a jejich web_score je vyšší nebo roven hodnotě MIN_LEAD_SCORE_FOR_CSV definované v settings.

Požadavky:

Python 3.10+

Aktivní Google Places API klíč (s povoleným Text Search a Place Details API)

Nastavený API klíč v config/settings.py

Ollama nainstalovaná a funkční pro běh LLM analýzy

Internetové připojení pro komunikaci s Google Places API

Spuštění:
Program se spouští příkazem python main.py. V CLI rozhraní lze použít příkaz "run" pro spuštění batch zpracování, "stats" pro zobrazení počtu firem v databázi, "reset-db" pro smazání databáze a "exit" pro ukončení programu.

Upozornění:
Používání Google Places API podléhá podmínkám služby společnosti Google a může být zpoplatněno podle aktuálního ceníku. Autor nenese odpovědnost za případné náklady vzniklé používáním API klíče ani za způsob, jakým je nástroj využíván.

Licence:
Tento software je chráněn autorským právem. Není dovoleno jej kopírovat, distribuovat, upravovat ani komerčně využívat bez písemného souhlasu autora.

© 2026 Michael Šindelář. Všechna práva vyhrazena.
