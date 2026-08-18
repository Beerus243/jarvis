"""Paramètres centralisés de JARVIS."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MEMORY_FILE = DATA_DIR / "user.json"
CONVERSATION_FILE = DATA_DIR / "conversation.json"
HISTORY_FILE = DATA_DIR / "history.json"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSION = 384
SEMANTIC_THRESHOLD = 0.35
MAX_MEMORY_RESULTS = 3

# Pondérations du ranking hybride. Elles totalisent 1 avant les bonus/malus.
SEMANTIC_WEIGHT = 0.45
LEXICAL_WEIGHT = 0.20
CATEGORY_WEIGHT = 0.15
SPECIFICITY_WEIGHT = 0.20

MODEL = "openai/gpt-oss-120b"
