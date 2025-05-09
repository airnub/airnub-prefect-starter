# airnub_prefect_starter/core/artifact_creators.py
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse

from prefect.artifacts import create_markdown_artifact
from ..common.utils import sanitize_filename, generate_sha256_hash_from_string # Ensure these are correct

logger = logging.getLogger(__name__)

def _clean_for_artifact_key(name_part: str, default_name: str = "item") -> str:
    """
    Cleans a string part to be valid for a Prefect artifact key.
    Lowercase, numbers, and dashes only.
    """
    if not name_part:
        name_part = default_name
    cleaned = name_part.lower().replace(' ', '-').replace('_', '-')
    cleaned = ''.join(c for c in cleaned if c.isalnum() or c == '-')
    while '--' in cleaned: # Collapse multiple dashes
        cleaned = cleaned.replace('--', '-')
    cleaned = cleaned.strip('-')
    return cleaned if cleaned else default_name

async def _create_artifact_from_manifest(
    key_prefix: str, # e.g., "file-dl-manifest" or "scraped-page-manifest"
    data_source_name: str,
    identifier_for_key: str, # e.g., sanitized original filename or page name
    unique_id_for_key: str, # e.g., short hash or timestamp
    markdown_summary_lines: list,
    worker_manifest_path_str: Optional[str],
    artifact_description: str
) -> None:
    """
    Helper to create a Prefect Markdown artifact, optionally including manifest content.
    """
    key_ds_name = _clean_for_artifact_key(data_source_name, "datasource")
    key_identifier = _clean_for_artifact_key(identifier_for_key, "item")
    key_unique_id = _clean_for_artifact_key(unique_id_for_key, "id")

    artifact_key = f"{key_prefix}-{key_ds_name}-{key_identifier}-{key_unique_id}"
    max_key_length = 200 # Prefect's practical limit can be around 255, stay safe
    if len(artifact_key) > max_key_length:
        artifact_key = artifact_key[:max_key_length]
        logger.warning(f"Artifact key was truncated to: {artifact_key}")

    final_markdown_lines = list(markdown_summary_lines) # Copy

    if worker_manifest_path_str:
        final_markdown_lines.append(f"- **Worker Manifest JSON Path:** `{worker_manifest_path_str}`")
        try:
            manifest_path_obj = Path(worker_manifest_path_str)
            if manifest_path_obj.is_file():
                with open(manifest_path_obj, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                manifest_content_str = json.dumps(manifest_data, indent=2)
                
                max_manifest_display_len = 2000 # Characters
                display_content = manifest_content_str
                if len(manifest_content_str) > max_manifest_display_len:
                    display_content = manifest_content_str[:max_manifest_display_len] + "\n... (manifest truncated in artifact)"

                final_markdown_lines.extend([
                    "\n#### Local Manifest Content (from worker):",
                    "```json",
                    display_content,
                    "```"
                ])
            else:
                logger.warning(f"Manifest file not found at path for inclusion in artifact: {worker_manifest_path_str}")
                final_markdown_lines.append(f"\n*Local manifest file content could not be read (File not found at worker path: `{worker_manifest_path_str}`).*")
        except Exception as e_read:
            logger.error(f"Error reading manifest file {worker_manifest_path_str} for artifact: {e_read}", exc_info=True)
            final_markdown_lines.append(f"\n*Error reading local manifest content: {str(e_read)}*")
    else:
        final_markdown_lines.append("\n*No worker manifest path provided to include its content.*")

    try:
        logger.info(f"Attempting to create markdown artifact with key: {artifact_key}")
        await create_markdown_artifact(
            key=artifact_key,
            markdown="\n".join(final_markdown_lines),
            description=artifact_description
        )
        logger.info(f"Successfully created markdown artifact: {artifact_key}")
    except Exception as e:
        logger.error(f"Failed to create markdown artifact with key '{artifact_key}': {e}", exc_info=True)
        raise # Re-raise to fail the calling task

async def core_create_file_download_artifact(
    processing_result: Dict[str, Any]
) -> None:
    """
    Core logic to create a Prefect Markdown artifact for a processed file,
    including content from its locally stored JSON manifest.
    """
    if not processing_result or processing_result.get("status") != "SUCCESS":
        logger.warning("Skipping file artifact: missing or failed processing metadata.")
        return

    original_filename = processing_result.get('original_filename', 'N/A')
    data_source_name = processing_result.get('data_source_name', 'unknown_ds')
    file_hash_short = processing_result.get('content_hash_sha256', 'nohash')[:8]
    worker_manifest_path_str = processing_result.get('worker_manifest_path')

    timestamp_utc_iso = processing_result.get('download_timestamp_utc')
    if isinstance(timestamp_utc_iso, datetime): # Ensure it's ISO format string
        timestamp_utc_iso_display = timestamp_utc_iso.isoformat() + "Z"
    elif isinstance(timestamp_utc_iso, str): # If already string
        timestamp_utc_iso_display = timestamp_utc_iso
    else:
        timestamp_utc_iso_display = datetime.utcnow().isoformat() + "Z" # Fallback

    summary_lines = [
        f"### File Downloaded & Manifested: **{original_filename}**",
        f"- **Data Source:** `{data_source_name}`",
        f"- **Original URL:** `{processing_result.get('url', 'N/A')}`",
        f"- **Download Timestamp (UTC):** `{timestamp_utc_iso_display}`",
        f"- **Content Hash (SHA256):** `{processing_result.get('content_hash_sha256', 'N/A')}`",
        f"- **Worker Document Path:** `{processing_result.get('worker_storage_path', 'N/A')}`",
        # Manifest path and content will be added by _create_artifact_from_manifest
        f"- **File Size (bytes):** `{processing_result.get('file_size_bytes', 'N/A')}`",
        f"- **Content-Type (from headers):** `{processing_result.get('http_headers', {}).get('content-type', 'N/A')}`",
    ]
    summary_lines.append("\n*This artifact summarizes the file download. The file and its JSON manifest are stored within the worker container's local structure.*")


    await _create_artifact_from_manifest(
        key_prefix="file-dl-manifest",
        data_source_name=data_source_name,
        identifier_for_key=Path(original_filename).stem if original_filename != 'N/A' else "file",
        unique_id_for_key=file_hash_short,
        markdown_summary_lines=summary_lines,
        worker_manifest_path_str=worker_manifest_path_str,
        artifact_description=f"Manifest and details for downloaded file: {original_filename}"
    )

def save_scraped_page_manifest_locally(
    scrape_result: Dict[str, Any],
    target_base_dir: Path,
    data_source_id: str
) -> Optional[Path]:
    """
    Saves the scrape_result as a JSON manifest file locally.
    Returns the path to the saved manifest file or None.
    """
    if not scrape_result or scrape_result.get("status") != "SUCCESS":
        logger.warning("Skipping save for scraped page manifest: missing/failed scrape metadata.")
        return None

    original_url = scrape_result.get('original_url')
    if not original_url:
        logger.error("Original URL missing in scrape result, cannot save manifest.")
        return None

    unique_page_hash = scrape_result.get('canonical_url_hash_sha256')
    if not unique_page_hash:
        # Fallback to hashing the canonical or original URL if hash not pre-calculated
        url_to_hash = scrape_result.get('canonical_url') or original_url
        if url_to_hash:
            unique_page_hash = generate_sha256_hash_from_string(url_to_hash)
        else:
            logger.error("Cannot generate unique page hash for manifest path.")
            return None # Should not happen if original_url is present

    # Create a filename base from the original URL's path or domain
    parsed_original_url = urlparse(original_url)
    filename_base_source = parsed_original_url.path.strip('/') if parsed_original_url.path.strip('/') else parsed_original_url.netloc
    filename_base = sanitize_filename(filename_base_source, default_name="scraped_page_data")
    if not filename_base: filename_base = "scrapedpagedata" # Ensure not empty

    try:
        # Structure: base / data_source_id / "scraped_pages_manifests" / unique_page_hash / filename_base.manifest.json
        manifest_dir = target_base_dir / sanitize_filename(data_source_id) / "scraped_pages_manifests" / unique_page_hash
        manifest_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_file_path = manifest_dir / f"{filename_base}.manifest.json"
        
        # Data to save in the JSON manifest file
        manifest_content_to_save = {
            "data_source_name": data_source_id,
            "scrape_timestamp_utc": datetime.utcnow().isoformat() + "Z", # Timestamp of this manifest creation
            "original_url": scrape_result.get('original_url'),
            "canonical_url": scrape_result.get('canonical_url'),
            "canonical_url_hash_sha256": scrape_result.get('canonical_url_hash_sha256'), # This should ideally be the unique_page_hash
            "extracted_links_count": len(scrape_result.get('extracted_links', [])),
            "extracted_links": scrape_result.get('extracted_links', []),
            "status_of_scrape": scrape_result.get("status"),
            # manifest_schema_version: "1.0.0" # Good to add
        }
        if scrape_result.get("error_message"):
             manifest_content_to_save["scrape_error_message"] = scrape_result.get("error_message")


        with open(manifest_file_path, "w", encoding="utf-8") as f:
            json.dump(manifest_content_to_save, f, indent=2)
        logger.info(f"Scraped page manifest JSON saved to: {manifest_file_path}")
        return manifest_file_path
    except Exception as e:
        logger.error(f"Failed to save scraped page manifest JSON for {original_url}: {e}", exc_info=True)
        return None

async def core_create_scraped_page_artifact(
    scrape_result: Dict[str, Any], # Output from core_parse_links_and_canonical_from_html
    data_source_name: str,
    local_manifest_path: Optional[Path] = None # Path to the saved JSON manifest for scraped data
) -> None:
    """
    Core logic to create a Prefect Markdown artifact for scraped web page links,
    including content from its locally stored JSON manifest if provided.
    """
    if not scrape_result or scrape_result.get("status") != "SUCCESS": # Check original scrape status
        logger.warning("Skipping scraped links artifact: missing or failed scrape metadata.")
        return

    original_url = scrape_result.get('original_url', 'N/A')
    # Use canonical hash if available, else original URL hash, else a default for key
    key_hash_part_source = scrape_result.get('canonical_url_hash_sha256')
    if not key_hash_part_source and original_url != 'N/A':
        key_hash_part_source = generate_sha256_hash_from_string(scrape_result.get('canonical_url') or original_url)
    elif not key_hash_part_source:
        key_hash_part_source = "unknownpage"
    
    key_hash_part = key_hash_part_source[:12] # Shorten for key

    summary_lines = [
        f"### Web Page Scrape Summary: **{original_url}**",
        f"- **Data Source:** `{data_source_name}`",
        f"- **Scrape Process Timestamp (UTC):** `{datetime.utcnow().isoformat()}Z`", # Timestamp of artifact creation
        f"- **Original URL:** `{original_url}`",
        f"- **Canonical URL:** `{scrape_result.get('canonical_url', 'Not found or same as original')}`",
        f"- **Canonical URL Hash (SHA256):** `{scrape_result.get('canonical_url_hash_sha256', 'N/A')}`",
    ]
    # Path to manifest and its content will be added by _create_artifact_from_manifest

    extracted_links = scrape_result.get('extracted_links', [])
    summary_lines.append(f"\n#### Extracted Links ({len(extracted_links)}) from page content:")
    
    if not extracted_links:
        summary_lines.append("\n_No links extracted or found on the page._")
    else:
        for link in extracted_links[:20]: # Display up to first 20 links
            summary_lines.append(f"- `{link}`")
        if len(extracted_links) > 20:
            summary_lines.append(f"- ...and {len(extracted_links) - 20} more (see manifest for full list).")
    
    summary_lines.append("\n*A JSON manifest with this scrape's details (including all links) is stored in the worker container.*")

    await _create_artifact_from_manifest(
        key_prefix="scraped-page-manifest",
        data_source_name=data_source_name,
        identifier_for_key=Path(urlparse(original_url).netloc).name + Path(urlparse(original_url).path).stem if original_url != 'N/A' else "webpage",
        unique_id_for_key=key_hash_part,
        markdown_summary_lines=summary_lines,
        worker_manifest_path_str=str(local_manifest_path) if local_manifest_path else None,
        artifact_description=f"Scrape manifest and details for page: {original_url}"
    )