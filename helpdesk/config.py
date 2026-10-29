import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOCS_DIR = ROOT / "data" / "docs"
CSV_DIR = ROOT / "data" / "csv"
CHROMA_DIR = ROOT / "chroma_db"
LOG_DIR = ROOT / "logs"
UNANSWERED_LOG = LOG_DIR / "unanswered.csv"

OLLAMA_BASE = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
CHAT_MODEL = os.environ.get("HELPDESK_MODEL", "ollama_chat/qwen3:8b")
EMBED_MODEL = os.environ.get("HELPDESK_EMBED_MODEL", "nomic-embed-text")

LLM_TIMEOUT = int(os.environ.get("HELPDESK_LLM_TIMEOUT", "300"))  # seconds per model call

COLLECTION = "academic_docs"
CHUNK_SIZE = 900      # characters
CHUNK_OVERLAP = 150
TOP_K = 4

# Cosine distance above which a chunk is considered irrelevant.
# Tune this on your own documents; it is what makes out-of-scope questions refuse.
MAX_DISTANCE = float(os.environ.get("HELPDESK_MAX_DISTANCE", "0.32"))

os.environ.setdefault("OLLAMA_API_BASE", OLLAMA_BASE)
