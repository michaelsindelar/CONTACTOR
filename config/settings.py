# settings.py

# Minimální skóre, nad kterým firma bude považována za relevantní lead
MIN_LEAD_SCORE_FOR_CSV = 50  # čím vyšší, tím větší obchodní šance

# Maximální počet podstránek, které se analyzují pro jeden web
MAX_SUBPAGES = 2

# LLaMA/Ollama konfigurace
OLLAMA_MODEL = "llama2:7b"
OLLAMA_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 120  # timeout pro volání LLM v sekundách

GOOGLE_PLACES_API_KEY = "---"
