import subprocess
import requests
import time
import socket
import sys
from config.settings import OLLAMA_MODEL, OLLAMA_URL

PORT = 11434


def is_port_open(host="127.0.0.1", port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0


def is_ollama_api_alive():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return r.status_code == 200
    except:
        return False


def start_ollama_server():
    print("Ollama neběží! | Spouštím server...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_for_server(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open() and is_ollama_api_alive():
            print("Ollama API je připraveno.")
            return True
        time.sleep(1)
    return False


def ensure_model_installed():
    r = requests.get(f"{OLLAMA_URL}/api/tags")
    models = r.json().get("models", [])
    model_names = [m["name"] for m in models]

    if OLLAMA_MODEL not in model_names:
        print(f"Model {OLLAMA_MODEL} není nainstalován. Stahuji...")
        subprocess.run(["ollama", "pull", OLLAMA_MODEL], check=True)


def ensure_ollama_ready():
    if not is_ollama_api_alive():
        start_ollama_server()

        if not wait_for_server():
            print("Nepodařilo se spustit Ollama server.")
            sys.exit(1)

    ensure_model_installed()
