import subprocess
import requests
import time

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "llama2:7b"

def is_server_running():
    try:
        resp = requests.get(f"{OLLAMA_URL}/v1/models", timeout=2)
        return resp.status_code == 200
    except:
        return False

def start_ollama_server():
    print("Spouštím Ollama server...")
    subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    # počkejme, než server naběhne
    for _ in range(10):
        time.sleep(1)
        if is_server_running():
            print("Ollama server běží.")
            return True
    print("Server se nepodařilo spustit.")
    return False

def ensure_server_ready():
    if is_server_running():
        return True
    return start_ollama_server()

def call_ollama(prompt: str, temperature=0.1, max_tokens=1200):
    """
    Pošle prompt do modelu LLaMA2:7B přes Ollama API.
    """
    if not ensure_server_ready():
        return None

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("response", "")
        else:
            print(f"Ollama API error: {resp.status_code}")
    except Exception as e:
        print(f"Chyba při volání Ollama: {e}")
    return None
