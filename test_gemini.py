"""Quick test: can this computer talk to Google Gemini with the key in .streamlit/secrets.toml?
Run:  python test_gemini.py
"""
import re
from pathlib import Path

from google import genai

# Read the key from .streamlit/secrets.toml (never print it)
secrets = Path(__file__).parent / ".streamlit" / "secrets.toml"
match = re.search(r'GEMINI_API_KEY\s*=\s*"([^"]+)"', secrets.read_text())
if not match or match.group(1) == "paste-your-key-here":
    raise SystemExit("❌ No key found in .streamlit/secrets.toml")

client = genai.Client(api_key=match.group(1))

# Find the available 'flash' models (fast + free-tier friendly)
flash_models = [m.name for m in client.models.list() if "flash" in m.name and "image" not in m.name]
print("✅ Key works. Flash models available:", flash_models[:6])

import re as _re
from google.genai import errors


def version(name):
    """'models/gemini-3.5-flash' -> (3, 5) so we can sort newest first."""
    m = _re.search(r"gemini-(\d+)(?:\.(\d+))?", name)
    return (int(m.group(1)), int(m.group(2) or 0)) if m else (0, 0)


# Newest stable 'flash' first (skip 'lite' and 'preview' unless nothing else works)
candidates = sorted(flash_models, key=lambda n: ("lite" in n or "preview" in n, tuple(-x for x in version(n))))

print("Trying in this order:", [c.replace("models/", "") for c in candidates])
for model in candidates:
    try:
        reply = client.models.generate_content(
            model=model,
            contents="In one short sentence, say hello to Afrina and wish her luck rebuilding her YUTP donor dashboard.",
        )
        print(f"🤖 Gemini ({model}) says:", reply.text)
        print(f"👉 Use this model name in the project: {model.replace('models/', '')}")
        break
    except errors.APIError as e:  # 404 not found, 429 quota, 503 busy -> try next
        print(f"⚠️  {model} not available ({e.code}), trying next...")
else:
    print("❌ None of the flash models worked - send this output to Claude.")
