import requests
import json


OLLAMA_BASE_URL = "http://localhost:11434"


def is_ollama_available() -> bool:
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def run_prompt(prompt: str, model: str = "llama3") -> str:
    """Send a prompt to Ollama and return the full response text."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "").strip()
