import re
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from config import settings

MAX_CHARS = 20000  # omezení délky textu posílaného do LLM

# -------------------------------------------------
# HTML stažení
# -------------------------------------------------
def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print(f"Chyba při stahování {url}: {e}")
    return None

# -------------------------------------------------
# Textová extrakce
# -------------------------------------------------
def extract_text_blocks(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    blocks = []

    # --- STRUCTURAL CONTENT ---
    tags = [
        "h1","h2","h3","h4","h5","h6",
        "p","li","button","label",
    ]

    for tag in tags:
        for el in soup.find_all(tag):
            text = el.get_text(strip=True)
            if text:
                blocks.append(f"[{tag}] {text}")

    # --- LINKS ---
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        if text:
            abs_url = urljoin(base_url, a["href"])
            blocks.append(f"[link] {text} ({abs_url})")

    # --- IMAGES ---
    for img in soup.find_all("img"):
        alt = img.get("alt")
        if alt:
            blocks.append(f"[img_alt] {alt}")

    # --- META SEO SIGNALS ---
    for meta in soup.find_all("meta"):

        if meta.get("name") == "description":
            content = meta.get("content")
            if content:
                blocks.append(f"[meta_description] {content}")

        if meta.get("name") == "robots":
            content = meta.get("content")
            if content:
                blocks.append(f"[meta_robots] {content}")

        if meta.get("name") == "viewport":
            blocks.append("[meta_viewport] present")

        if meta.get("property") in ["og:title", "og:description"]:
            content = meta.get("content")
            if content:
                blocks.append(f"[{meta.get('property')}] {content}")

    # --- FOOTER SIGNALS ---
    footer = soup.find("footer")

    if footer:
        footer_text = footer.get_text(" ", strip=True)

        emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", footer_text)
        for email in set(emails):
            blocks.append(f"[footer_email] {email}")

        phones = re.findall(r"\+?\d[\d\s\-]{7,}\d", footer_text)
        for phone in set(phones):
            blocks.append(f"[footer_phone] {phone}")

        ico_matches = re.findall(r"IČO[:\s]*\d+", footer_text)
        for ico in ico_matches:
            blocks.append(f"[footer_ico] {ico}")

        if any(x in footer_text.lower() for x in ["s.r.o", "a.s", "ltd", "gmbh"]):
            blocks.append("[footer_company_type] present")

        socials_found = set()
        for a in footer.find_all("a", href=True):
            href = a["href"].lower()

            if "facebook.com" in href:
                socials_found.add("facebook")
            elif "instagram.com" in href:
                socials_found.add("instagram")
            elif "linkedin.com" in href:
                socials_found.add("linkedin")
            elif "youtube.com" in href:
                socials_found.add("youtube")

        for social in socials_found:
            blocks.append(f"[footer_social] {social}")

        footer_links = footer.find_all("a")
        blocks.append(f"[footer_link_count] {len(footer_links)}")

    return blocks

# -------------------------------------------------
# LLM volání
# -------------------------------------------------
def call_ollama(prompt: str):
    from config.settings import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "temperature": 0.1,  # nízká teplota
        "max_tokens": 1200,
        "stream": False,
        "format": "json"
    }
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        response_text = data.get("response", "")
        return response_text
    except Exception as e:
        print(f"Chyba při volání LLM: {e}")
        return None

# -------------------------------------------------
# Hlavní analýza webu
# -------------------------------------------------
def analyze_web(url, max_subpages=5):
    html_main = fetch_html(url)
    if not html_main:
        return {"lead_score": 404, "improvement_tips": ["The website is not available!"], "email": "", "phone": ""}

    main_blocks = extract_text_blocks(html_main, url)

    # přidat podstránky
    soup = BeautifulSoup(html_main, "html.parser")
    domain = urlparse(url).netloc
    links = []
    for a in soup.find_all("a", href=True):
        abs_url = urljoin(url, a["href"])
        if urlparse(abs_url).netloc == domain and abs_url != url:
            if abs_url not in links:
                links.append(abs_url)
        if len(links) >= max_subpages:
            break

    for link in links[:max_subpages]:
        html_sub = fetch_html(link)
        if html_sub:
            main_blocks += extract_text_blocks(html_sub, link)

    # omezit délku textu
    text_for_llm = "\n".join(main_blocks)
    text_for_llm = text_for_llm[:MAX_CHARS]

    prompt = f"""
You are a UX and conversion optimization expert.
Analyze the following website content and evaluate its business potential for redesign or new website development.
Return ONLY valid JSON. Do not include any explanation or markdown.

Lead score (integer 0-100) represents business potential for website redesign or new website development:
0–20 = professionally designed, modern, conversion optimized
21–49 = minor improvements possible
50–60 = clear UX and structure weaknesses (potential client)
61–80 = outdated design and missing conversion elements (potential client)
81–100 = severely outdated or broken structure (potential client)

Evaluate the website using these criteria:
1. Visual design quality (0–20)
2. Mobile responsiveness indicators (0–20)
3. Content clarity and structure (0–20)
4. Conversion elements (CTA, contact visibility) (0–20)
5. Trust signals (references, testimonials, certifications) (0–20)
Calculate total score = sum of all categories.

IMPORTANT RULES:
- Do not invent email or phone number.
- Don't confuse the phone number with dates, etc.
- Only use information clearly visible in the website content.
- If any design, UX, or technical element is not explicitly visible in the content, do not assume its existence.
- If something is unclear or missing, return an empty string.
- If the website appears outdated, minimal, or has poor content, assign higher lead_score.
- Generate score and improvement tips strictly based on the website content.
- Be critical and analytical.

Follow this process:
1. List factual observations.
2. Identify structural weaknesses.
3. Evaluate 5 scoring categories (0–20 each).
4. Sum the total.
5. Generate improvement tips only for identified weaknesses.
6. Do not assume anything not visible.
7. Do not be generous with scoring.

When searching for email and phone, prioritize the decision-maker's contact if it is mentioned.

Required format:
{{
  "lead_score": 0-100,
  "summary": "short summary of the website condition",
  "improvement_tips": ["list of concrete improvement recommendations based on the website content"],
  "email": "if found",
  "phone": "if found"
}}

If the content is insufficient for evaluation or missing, return exactly:
{{
  "lead_score": 404,
  "summary": "",
  "improvement_tips": [],
  "email": "",
  "phone": ""
}}

Website content (Remember that this is a fraction of the website text with a maximum of {MAX_CHARS} characters):
{text_for_llm}
"""

    response = call_ollama(prompt)
    if not response:
        return {"lead_score": 500, "improvement_tips": ["AI is not responding! The website is probably overloaded and cluttered."], "email": "", "phone": ""}

    # převod na dictionary
    try:
        result = json.loads(response)
        return result
    except:
        return {
            "lead_score": 502,
            "improvement_tips": ["LLM returned an invalid response!"],
            "email": "",
            "phone": ""
        }
