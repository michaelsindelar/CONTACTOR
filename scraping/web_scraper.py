# scraping/web_scraper.py
import requests
from urllib.parse import urlparse


def prepare_url(url: str) -> str:
    """
    Připraví URL pro requests:
    - odstraní whitespace
    - doplní https, pokud chybí
    - ověří, že vznikne validní URL
    """
    if not url:
        raise ValueError("Empty URL")

    url = url.strip()

    # pokud chybí schéma → přidej https
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    # znovu naparsovat po úpravě
    parsed = urlparse(url)

    if not parsed.netloc:
        raise ValueError(f"Invalid URL after normalization: {url}")

    return url


def fetch_website(url):
    """Stáhne HTML stránky s bezpečným User-Agent."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    try:
        url = prepare_url(url)
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code == 200:
            return resp.text
        else:
            return None
    except Exception as e:
        print(f"Chyba při stahování {url}: {e}")
        return None
