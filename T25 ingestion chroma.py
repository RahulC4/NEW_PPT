# ingestion_chroma.py

import os
import json
import uuid
from typing import List

import chromadb
from chromadb.utils import embedding_functions

from utils import (
    logger,
    get_env,
    ensure_dir
)

# ------------------------------------------------------------------
# Chroma setup (UNCHANGED)
# ------------------------------------------------------------------
CHROMA_DIR = get_env("CHROMA_DIR", default="chroma_db")
COLLECTION_NAME = get_env("CHROMA_COLLECTION", default="ppt_slides")

ensure_dir(CHROMA_DIR)

embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
    model_name=get_env("EMBEDDING_MODEL", required=True),
    api_key=get_env("OPENAI_API_KEY", required=True)
)

client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False
    )
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_fn
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def chunk_text(text: str, chunk_size=800, overlap=100) -> List[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap

    return chunks


# ------------------------------------------------------------------
# MAIN INGESTION FUNCTION
# ------------------------------------------------------------------
def process_blob(
    ppt_name: str,
    extracted_slides: List[dict]
):
    """
    extracted_slides: List of dicts like:
    {
        "slide_index": int,
        "slide_id": str,
        "title": str,
        "text": str
    }
    """

    logger.info(f"Ingesting PPT into Chroma: {ppt_name}")

    all_documents = []
    all_metadatas = []
    all_ids = []

    for slide in extracted_slides:
        slide_text = slide.get("text", "").strip()
        if not slide_text:
            continue

        slide_index = slide.get("slide_index")
        slide_id = slide.get("slide_id")
        slide_title = slide.get("title", "")

        chunks = chunk_text(slide_text)

        for i, chunk in enumerate(chunks):
            doc_id = str(uuid.uuid4())

            all_documents.append(chunk)

            # 🔑 METADATA — THIS IS THE ONLY ADDITION
            all_metadatas.append({
                "ppt_name": ppt_name,
                "slide_id": slide_id,              # ✅ exact slide retrieval
                "slide_index": slide_index,        # ✅ exact slide retrieval
                "slide_title": slide_title,        # helpful for debugging
                "chunk_index": i
            })

            all_ids.append(doc_id)

    if not all_documents:
        logger.warning("No slide text found to ingest.")
        return

    collection.add(
        documents=all_documents,
        metadatas=all_metadatas,
        ids=all_ids
    )

    client.persist()

    logger.info(
        f"Chroma ingestion complete: {len(all_documents)} chunks added "
        f"from {len(extracted_slides)} slides"
    )
