# utils.py

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# ============================================================
# LOAD ENV
# ============================================================
load_dotenv()

# ============================================================
# LOGGING
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("ai-ppt-generator")


# ============================================================
# ENV HELPERS
# ============================================================
def get_env(name: str, default=None, required: bool = False):
    """
    Safely read environment variables.
    """
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        logger.error(f"Missing required environment variable: {name}")
        raise EnvironmentError(f"Missing env var: {name}")
    return val


# ============================================================
# FILESYSTEM
# ============================================================
def ensure_dir(path: str):
    """
    Create directory if it does not exist.
    """
    os.makedirs(path, exist_ok=True)


# ============================================================
# TIME
# ============================================================
def now_ts() -> str:
    """
    Returns UTC timestamp in ISO format.
    """
    return datetime.utcnow().isoformat() + "Z"


# ============================================================
# JSON SAFETY
# ============================================================
def safe_json_load(text: str):
    """
    Attempts to extract and parse JSON from an LLM response.
    Safely ignores non-JSON leading/trailing text.
    """
    if not text:
        return None

    text = text.strip()
    starts = [text.find("{"), text.find("[")]
    starts = [s for s in starts if s != -1]

    if not starts:
        return None

    try:
        return json.loads(text[min(starts):])
    except Exception as e:
        logger.warning(f"safe_json_load failed: {e}")
        return None


# ============================================================
# EMBEDDING DIMENSION
# ============================================================
def get_embedding_dim(model_name: str = None) -> int:
    """
    Returns embedding dimension.
    Reads from env EMBEDDING_DIM if present.
    """
    try:
        return int(get_env("EMBEDDING_DIM", 1536))
    except Exception:
        return 1536
