# storage/azure_blob_utils.py

import os
import tempfile
from azure.storage.blob import BlobServiceClient
from utils import get_env, logger


# ============================================================
# ENVIRONMENT CONFIG
# ============================================================
BLOB_CONN = get_env("AZURE_BLOB_CONN", required=True)

# Dataset container (sample PPT decks)
SOURCE_CONTAINER = get_env("AZURE_BLOB_CONTAINER", "ppt-dataset")

# Output container (generated PPTs)
GENERATED_CONTAINER = get_env("GENERATED_CONTAINER", "generated-presentations")


# ============================================================
# INTERNAL HELPER
# ============================================================
def _get_container_client(container_name: str):
    blob_service = BlobServiceClient.from_connection_string(BLOB_CONN)
    container_client = blob_service.get_container_client(container_name)
    try:
        container_client.create_container()
    except Exception:
        pass
    return container_client


# ============================================================
# 1. UPLOAD — Generated PPTs
# ============================================================
def upload_ppt_to_blob(file_path, file_name):
    container_client = _get_container_client(GENERATED_CONTAINER)
    with open(file_path, "rb") as data:
        container_client.upload_blob(name=file_name, data=data, overwrite=True)
    logger.info(f"Uploaded generated PPT → {GENERATED_CONTAINER}/{file_name}")
    return f"{GENERATED_CONTAINER}/{file_name}"


def upload_json_to_blob(json_bytes, blob_name):
    container_client = _get_container_client(GENERATED_CONTAINER)
    container_client.upload_blob(name=blob_name, data=json_bytes, overwrite=True)
    logger.info(f"Uploaded JSON log → {GENERATED_CONTAINER}/{blob_name}")
    return f"{GENERATED_CONTAINER}/{blob_name}"


def list_generated_presentations():
    try:
        client = _get_container_client(GENERATED_CONTAINER)
        return [b.name for b in client.list_blobs()]
    except Exception as e:
        logger.warning(f"Failed to list generated PPTs: {e}")
        return []


# ============================================================
# 2. UPLOAD — Sample PPT Decks (Templates)
# ============================================================
def upload_source_ppt_to_blob(file_bytes, blob_name: str):
    container_client = _get_container_client(SOURCE_CONTAINER)
    container_client.upload_blob(name=blob_name, data=file_bytes, overwrite=True)
    logger.info(f"Uploaded SOURCE PPT → {SOURCE_CONTAINER}/{blob_name}")
    return f"{SOURCE_CONTAINER}/{blob_name}"


# ============================================================
# 3. LIST — Sample Decks
# ============================================================
def list_source_ppt_blobs():
    try:
        container_client = _get_container_client(SOURCE_CONTAINER)
        return [
            b.name for b in container_client.list_blobs()
            if b.name.lower().endswith(".pptx")
        ]
    except Exception as e:
        logger.warning(f"Failed to list source PPTs: {e}")
        return []


# ============================================================
# 4. DELETE — Sample Deck
# ============================================================
def delete_source_ppt_from_blob(blob_name: str):
    try:
        container_client = _get_container_client(SOURCE_CONTAINER)
        container_client.delete_blob(blob_name)
        logger.info(f"Deleted SOURCE PPT → {SOURCE_CONTAINER}/{blob_name}")
    except Exception as e:
        logger.exception(f"Failed to delete PPT: {blob_name}")
        raise e


# ============================================================
# 5. DOWNLOAD — (NEW) Retrieve PPT locally
# ============================================================
def download_source_ppt(blob_name: str) -> str:
    """
    Downloads a PPT from Azure Blob to a local tmp path.
    Used by ingestion_chroma and template-based engines.
    Returns the local file path.
    """

    try:
        container_client = _get_container_client(SOURCE_CONTAINER)

        download_path = os.path.join(
            tempfile.gettempdir(),
            f"download_{blob_name.replace('/', '_')}"
        )

        with open(download_path, "wb") as f:
            container_client.download_blob(blob_name).readinto(f)

        logger.info(f"Downloaded PPT locally: {download_path}")
        return download_path

    except Exception as e:
        logger.exception(f"Failed to download PPT: {blob_name}")
        return None
