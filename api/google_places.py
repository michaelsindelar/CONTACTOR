# google_places.py
import requests
from config import settings
import logging
import time

logger = logging.getLogger("Contactor")

TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

def fetch_companies_from_google(location: str, keyword: str, max_results: int, db=None):
    """
    Vrátí seznam firem z Google Places API.
    :param location: město / oblast
    :param keyword: klíčové slovo
    :param max_results: maximální počet firem
    :param db: instance Database (volitelné, pokud chceš kontrolovat duplicity)
    :return: seznam dict
    """
    results = []
    next_page_token = None
    total_fetched = 0

    while total_fetched < max_results:
        params = {
            "query": f"{keyword} in {location}",
            "key": settings.GOOGLE_PLACES_API_KEY,
        }
        if next_page_token:
            params["pagetoken"] = next_page_token
            # Google Places doporučuje čekat ~2s před použitím next_page_token
            time.sleep(2)

        try:
            r = requests.get(TEXTSEARCH_URL, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.error(f"Chyba při volání Google Places API: {e}")
            break

        for place in data.get("results", []):
            firm = {
                "name": place.get("name"),
                "industry": keyword,
                "website": "",  # vyplníme níže
                "analyzed": False,
                "email": "",
                "phone": "",
                "decision_maker_name": "",
                "decision_maker_position": ""
            }

            place_id = place.get("place_id")
            if place_id:
                # zavolat Details API, abychom získali website, phone
                try:
                    details_params = {
                        "place_id": place_id,
                        "fields": "website,formatted_phone_number",
                        "key": settings.GOOGLE_PLACES_API_KEY
                    }
                    r_details = requests.get(DETAILS_URL, params=details_params, timeout=10)
                    r_details.raise_for_status()
                    details = r_details.json().get("result", {})
                    firm["website"] = details.get("website", "")
                    firm["phone"] = details.get("formatted_phone_number", "")
                except Exception as e:
                    logger.warning(f"Nelze získat detail firmy {firm['name']}: {e}")

            # pokud stále není web, použijeme adresu
            if not firm["website"]:
                firm["website"] = place.get("formatted_address", "")

            # volitelná kontrola duplicity v DB
            if db and firm.get("website") and db.company_exists(firm["website"]):
                continue

            results.append(firm)
            total_fetched += 1
            if total_fetched >= max_results:
                break

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

    return results
