# airnub_prefect_starter/core/manifest_models.py
from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

class DemoFileManifestEntry(BaseModel):
    """
    Pydantic model for a basic JSON manifest entry for a downloaded file
    to be stored alongside the file in a local CAS-like structure for the demo.
    """
    # === Identity & Source ===
    data_source_name: str                       # From your old Document model
    original_filename: str                      # The sanitized filename used for storage
    source_url: HttpUrl                         # Direct download URL (was original_download_url)
    source_page_url: Optional[HttpUrl] = None   # URL where the link was found (if different) - from Document
    link_title: Optional[str] = None            # Text of the link (if applicable) - from DocumentVersion

    # === Content Identity ===
    content_hash_sha256: str                    # The SHA256 hash of the file content
    hash_algorithm: str = "sha256"              # Explicitly state the hash algorithm

    # === Storage Details (for this demo) ===
    worker_storage_path: str                    # Full path within the worker where the file is stored
    storage_type: str = "local_cas_demo"        # Indicates it's in our local demo CAS

    # === File & Download Metadata ===
    download_timestamp_utc: datetime = Field(default_factory=datetime.utcnow)
    file_size_bytes: Optional[int] = None
    content_type: Optional[str] = None          # e.g., 'application/pdf', from headers
    http_headers: Optional[Dict[str, str]] = None # Store relevant headers (e.g., ETag, Last-Modified)

    # === For Template ===
    manifest_schema_version: str = "1.0.0"      # Version of this manifest Pydantic model

    model_config = ConfigDict(
        extra='ignore', # Ignore extra fields if loading from a dict that has more
        arbitrary_types_allowed=True, # For Path if it were used directly as a field type
        json_encoders={
            Path: str, 
            datetime: lambda dt: dt.isoformat() + "Z" # Ensure UTC 'Z'
        }
    )

class DemoScrapedPageManifestEntry(BaseModel):
    """
    Pydantic model for a basic JSON manifest entry for a scraped web page
    to be stored locally for the demo.
    """
    # === Identity & Source ===
    data_source_name: str
    original_url: HttpUrl                       # The URL that was scraped
    
    # === Scrape Details ===
    scrape_timestamp_utc: datetime = Field(default_factory=datetime.utcnow)
    canonical_url: Optional[HttpUrl] = None
    canonical_url_hash_sha256: Optional[str] = None # Hash of the canonical_url string
    hash_algorithm: str = "sha256"              # For the canonical_url_hash

    # === Content (Optional for demo - could be just links) ===
    # page_content_hash_sha256: Optional[str] = None # If you were to store/hash the HTML content

    # === Extracted Data ===
    extracted_links_count: int = 0
    extracted_links: Optional[List[HttpUrl]] = None # Store all extracted links for the JSON file

    # === Storage Details (for this demo) ===
    # Path within the worker where this JSON manifest for the scrape is stored
    worker_manifest_path: str 

    # === For Template ===
    manifest_schema_version: str = "1.0.0"

    model_config = ConfigDict(
        extra='ignore',
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat() + "Z"
        }
    )