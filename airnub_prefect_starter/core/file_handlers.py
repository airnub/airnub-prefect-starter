# airnub_prefect_starter/core/file_handlers.py
import httpx
from pathlib import Path
import tempfile
import shutil
from typing import Optional, Tuple, Dict, Any
import logging
import re
from urllib.parse import urlparse
import json # For writing JSON manifest
from datetime import datetime

from ..common.utils import generate_sha256_for_file, sanitize_filename
from .manifest_models import DemoFileManifestEntry # Import your Pydantic model

logger = logging.getLogger(__name__)

async def _download_to_temporary_file(url: str) -> Optional[Tuple[Path, str, Dict[str, str], int]]:
    """
    Downloads content from a URL into a temporary file.
    The temporary file is NOT automatically deleted; caller must manage or move it.
    Returns: (temp_file_path, original_filename, headers_dict, file_size_bytes) or None.
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=180.0) as client: # Increased timeout for potentially large files
            logger.info(f"Core File: Starting download from: {url}")
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                
                headers = dict(response.headers)
                content_disposition = headers.get("Content-Disposition")
                raw_filename_from_url = Path(urlparse(url).path).name
                
                original_filename = raw_filename_from_url
                if content_disposition:
                    disp_fn_match = re.search(r'filename="?([^"]+)"?', content_disposition, re.IGNORECASE)
                    if disp_fn_match:
                        original_filename = disp_fn_match.group(1)
                
                # Sanitize filename after determining it
                safe_original_filename = sanitize_filename(original_filename if original_filename else "unknown_download")
                
                # Create a named temporary file, ensure it's not deleted immediately
                with tempfile.NamedTemporaryFile(delete=False, prefix="prefDL_", suffix=f"_{safe_original_filename}") as tmpfile:
                    temp_file_path = Path(tmpfile.name)
                    file_size = 0
                    async for chunk in response.aiter_bytes(chunk_size=8192 * 4): # Use a decent chunk size
                        tmpfile.write(chunk)
                        file_size += len(chunk)
                
                logger.info(f"Core File: '{safe_original_filename}' ({file_size} bytes) downloaded to temp: {temp_file_path}")
                return temp_file_path, safe_original_filename, headers, file_size
    except httpx.HTTPStatusError as e:
        logger.error(f"Core File: HTTP error {e.response.status_code} downloading {e.request.url!r}")
    except httpx.RequestError as e:
        logger.error(f"Core File: Request error downloading {e.request.url!r}: {e}")
    except Exception as e:
        logger.error(f"Core File: Unexpected error downloading {url}: {e}", exc_info=True)
    return None

def _store_file_and_its_manifest_locally(
    source_temp_file_path: Path,
    target_cas_base_dir: Path, # e.g., /app/local_demo_artifacts/downloads
    data_source_name_for_path: str,
    file_content_hash: str,
    sanitized_original_filename: str,
    manifest_model_instance: DemoFileManifestEntry
) -> Optional[Tuple[Path, Path]]:
    """
    Moves the downloaded file to a CAS-like structure and saves its JSON manifest alongside.
    Cleans up the source_temp_file_path.
    Returns (path_to_document, path_to_manifest) or (None, None).
    """
    if not all([source_temp_file_path, target_cas_base_dir, data_source_name_for_path, 
                file_content_hash, sanitized_original_filename, manifest_model_instance]):
        logger.error("Core File Store: Missing required arguments.")
        if source_temp_file_path and source_temp_file_path.exists(): source_temp_file_path.unlink(missing_ok=True)
        return None, None
    if not source_temp_file_path.is_file():
        logger.error(f"Core File Store: Source temp path is not a file: {source_temp_file_path}")
        return None, None
        
    final_doc_path: Optional[Path] = None
    final_manifest_path: Optional[Path] = None
    try:
        # CAS structure: target_base_dir / data_source_name / hash / filename
        cas_content_dir = target_cas_base_dir / sanitize_filename(data_source_name_for_path) / file_content_hash
        cas_content_dir.mkdir(parents=True, exist_ok=True)
        
        final_doc_path = cas_content_dir / sanitized_original_filename
        shutil.move(str(source_temp_file_path), final_doc_path) # source_temp_file_path is now moved
        logger.info(f"Core File Store: Document moved to CAS location: {final_doc_path}")

        # Update manifest model with the final worker storage path
        manifest_model_instance.worker_storage_path = str(final_doc_path)

        manifest_filename = f"{sanitized_original_filename}.manifest.json"
        final_manifest_path = cas_content_dir / manifest_filename
        with open(final_manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest_model_instance.model_dump_json(indent=2)) # Pydantic V2
        logger.info(f"Core File Store: Manifest JSON saved to: {final_manifest_path}")
        
        return final_doc_path, final_manifest_path
    except Exception as e:
        logger.error(f"Core File Store: Error storing file/manifest for {sanitized_original_filename}: {e}", exc_info=True)
    finally:
        # Ensure temporary file is cleaned up if it somehow still exists (e.g., move failed before unlink)
        if source_temp_file_path and source_temp_file_path.exists():
            try:
                source_temp_file_path.unlink(missing_ok=True)
            except OSError as unlink_err:
                logger.error(f"Core File Store: Error final cleanup temp file {source_temp_file_path}: {unlink_err}")
    return final_doc_path, final_manifest_path # One or both might be None if an error occurred after partial success

async def core_process_scheduled_file_download(
    url: str, 
    data_source_name: str, # For path and manifest
    local_cas_target_base_dir: Path, # Base for CAS, e.g., /app/local_demo_artifacts/
    # target_subdirectory: Optional[str] = "scheduled_files" # To organize within base_dir
) -> Dict[str, Any]:
    """
    Orchestrates downloading, hashing, storing (CAS-like), and preparing manifest data
    for a file from a URL.
    This is the main function the "Download File" Prefect task wrapper will call.
    """
    logger.info(f"Core File Process: Starting for URL: {url} (DataSource: {data_source_name})")
    processing_metadata: Dict[str, Any] = {
        "status": "INITIATED", 
        "url": url, 
        "data_source_name": data_source_name,
        "download_timestamp_utc": datetime.utcnow() # Record start of attempt
    }
    
    download_attempt_result = await _download_to_temporary_file(url)
    if not download_attempt_result:
        processing_metadata["status"] = "FAILED_DOWNLOAD"
        processing_metadata["error_message"] = "Download operation failed."
        return processing_metadata
    
    temp_file_path, original_filename, headers, file_size_bytes = download_attempt_result
    processing_metadata.update({
        "original_filename": original_filename,
        "http_headers": headers,
        "file_size_bytes": file_size_bytes,
        "content_type": headers.get("content-type")
    })

    content_hash = generate_sha256_for_file(temp_file_path) # From common.utils
    if not content_hash:
        processing_metadata["status"] = "FAILED_HASHING"
        processing_metadata["error_message"] = "Could not generate hash for the downloaded file."
        if temp_file_path.exists(): temp_file_path.unlink(missing_ok=True)
        return processing_metadata
    processing_metadata["content_hash_sha256"] = content_hash
    processing_metadata["hash_algorithm"] = "sha256"

    # Create Pydantic model instance for the manifest
    manifest_entry = DemoFileManifestEntry(
        data_source_name=data_source_name,
        original_filename=original_filename,
        source_url=url,
        download_timestamp_utc=processing_metadata["download_timestamp_utc"], # Use earlier timestamp
        content_hash_sha256=content_hash,
        worker_storage_path="placeholder", # Will be updated
        file_size_bytes=file_size_bytes,
        http_headers=headers,
        content_type=headers.get("content-type")
    )

    # Store file and its manifest
    # The target_subdirectory can be part of local_cas_target_base_dir if desired
    # e.g. local_cas_target_base_dir = Path("/app/local_demo_artifacts/scheduled_files")
    stored_doc_path, stored_manifest_path = _store_file_and_its_manifest_locally(
        temp_file_path, local_cas_target_base_dir, data_source_name, 
        content_hash, original_filename, manifest_entry
    )
    # temp_file_path is handled (deleted) by _store_file_and_its_manifest_locally

    if not stored_doc_path or not stored_manifest_path:
        processing_metadata["status"] = "FAILED_STORAGE"
        processing_metadata["error_message"] = "Local CAS storage or manifest JSON saving failed."
        if stored_doc_path: processing_metadata["worker_storage_path"] = str(stored_doc_path) # It might have stored the doc
        return processing_metadata

    processing_metadata["worker_storage_path"] = str(stored_doc_path)
    processing_metadata["worker_manifest_path"] = str(stored_manifest_path)
    processing_metadata["status"] = "SUCCESS"
    logger.info(f"Core File Process: Successfully processed, stored, and prepared manifest for {original_filename}")
    
    return processing_metadata