# search/search_utils.py

import os
from openai import AzureOpenAI
from chromadb import PersistentClient
from utils import get_env, logger, get_embedding_dim
from llm.llm_utils import embed_text    # ⬅ now using the unified wrapper


# ============================================================
# CONFIG
# ============================================================
EMBEDDING_MODEL = get_env("EMBEDDING_MODEL", "text-embedding-3-large")
CHROMA_PERSIST_DIR = get_env("CHROMA_PERSIST_DIR", "./chroma_db")

EMBEDDING_DIM = get_embedding_dim(EMBEDDING_MODEL)

# Chroma client initialization
chroma_client = PersistentClient(path=CHROMA_PERSIST_DIR)

try:
    collection = chroma_client.get_collection("ppt_slides")
except:
    collection = chroma_client.create_collection("ppt_slides")


# ============================================================
# SEMANTIC SEARCH
# ============================================================
def semantic_search(query: str, top_k: int = 5, slide_type: str = None):
    """
    Perform semantic search with optional slide_type filtering.
    
    slide_type examples:
        "Title", "Problem", "Solution", etc.
    """

    emb = embed_text(query)
    if emb is None:
        logger.error("Embedding failed in semantic_search.")
        return []

    where_filter = {}
    if slide_type:
        # metadata stored exactly as: "slide_type": "Problem"
        where_filter = {"slide_type": slide_type}

    try:
        res = collection.query(
            query_embeddings=[emb],
            n_results=top_k,
            where=where_filter if slide_type else None
        )
    except Exception as e:
        logger.exception(f"Chroma query failed: {e}")
        return []

    return _format_results(res)



# ============================================================
# STRUCTURED SEARCH (NO EMBEDDINGS)
# ============================================================
def search_by_slide_type(slide_type: str, top_k: int = 5):
    """
    Fetch slides that match a slide_type, sorted by DESC classification confidence.
    """
    try:
        res = collection.get(
            where={"slide_type": slide_type}
        )
    except Exception as e:
        logger.exception(f"Chroma get() failed: {e}")
        return []

    slides = []
    ids = res.get("ids", [])
    meta = res.get("metadatas", [])
    docs = res.get("documents", [])

    for i in range(len(ids)):
        slides.append({
            "id": ids[i],
            "ppt_name": meta[i].get("ppt_name"),
            "slide_id": meta[i].get("slide_id"),
            "slide_type": meta[i].get("slide_type"),
            "confidence": meta[i].get("slide_confidence", 0.0),
            "title": meta[i].get("title", ""),
            "raw_text": meta[i].get("raw_text", ""),
            "layout": meta[i].get("layout"),
            "tags": meta[i].get("tags", None),
            "score": None
        })

    # Sort by confidence
    slides = sorted(slides, key=lambda x: x["confidence"], reverse=True)

    return slides[:top_k]



# ============================================================
# RESULT FORMATTER
# ============================================================
def _format_results(res):
    """
    Converts Chroma query response into a clean list of dicts.
    Includes layout metadata & slide_type data.
    """

    out = []

    ids = res.get("ids", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    docs = res.get("documents", [[]])[0]
    dists = res.get("distances", [[]])[0]

    for i in range(len(ids)):
        out.append({
            "id": ids[i],
            "ppt_name": metas[i].get("ppt_name"),
            "slide_id": metas[i].get("slide_id"),
            "slide_type": metas[i].get("slide_type"),
            "confidence": metas[i].get("slide_confidence", 0.0),
            "title": metas[i].get("title"),
            "raw_text": metas[i].get("raw_text"),
            "layout": metas[i].get("layout"),            # ⭐ critical for PPT builder
            "tags": metas[i].get("tags"),
            "score": dists[i]
        })

    return out
