# search/search_utils.py

from openai import AzureOpenAI
from chromadb import PersistentClient
from utils import get_env, logger, get_embedding_dim

# ============================================================
# AZURE OPENAI CLIENT (EMBEDDINGS ONLY)
# ============================================================
embedding_client = AzureOpenAI(
    azure_endpoint=get_env("OPENAI_API_BASE", required=True),
    api_key=get_env("OPENAI_API_KEY", required=True),
    api_version=get_env("OPENAI_API_VERSION", required=True),
)

EMBEDDING_MODEL = get_env("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIM = get_embedding_dim(EMBEDDING_MODEL)

# ============================================================
# CHROMA
# ============================================================
CHROMA_PERSIST_DIR = get_env("CHROMA_PERSIST_DIR", "./chroma_db")

chroma_client = PersistentClient(path=CHROMA_PERSIST_DIR)

try:
    collection = chroma_client.get_collection("ppt_slides")
except Exception:
    collection = chroma_client.create_collection("ppt_slides")

# ============================================================
# EMBEDDING
# ============================================================
def get_embedding(text: str):
    """
    Generate embedding using Azure OpenAI.
    """
    try:
        resp = embedding_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return resp.data[0].embedding
    except Exception as e:
        logger.exception(f"Embedding failed: {e}")
        return None


# ============================================================
# SEMANTIC SEARCH
# ============================================================
def semantic_search(query: str, top_k: int = 5):
    """
    Search slides semantically from Chroma.
    """
    query_emb = get_embedding(query)
    if query_emb is None:
        return []

    try:
        res = collection.query(
            query_embeddings=[query_emb],
            n_results=top_k
        )

        results = []
        for i in range(len(res["ids"][0])):
            results.append({
                "id": res["ids"][0][i],
                "document": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i],
            })

        return results

    except Exception as e:
        logger.exception(f"Chroma query failed: {e}")
        return []
