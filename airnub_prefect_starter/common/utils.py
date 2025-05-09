# airnub_prefect_starter/common/utils.py
import hashlib
from pathlib import Path
import logging
from typing import Optional
import re # For sanitize_filename

# It's good practice for library/core code to use standard logging.
# Prefect's logger will capture these if this code is called from a Prefect task/flow.
logger = logging.getLogger(__name__)

def generate_sha256_hash_from_bytes(content: bytes) -> str:
    """Calculates the SHA256 hash for a byte string."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    hex_digest = sha256_hash.hexdigest()
    logger.debug(f"Generated SHA256 hash from bytes: {hex_digest[:8]}...")
    return hex_digest

def generate_sha256_hash_from_string(text_content: str, encoding: str = 'utf-8') -> str:
    """Calculates the SHA256 hash for a string."""
    return generate_sha256_hash_from_bytes(text_content.encode(encoding))

def generate_sha256_for_file(file_path: Path) -> Optional[str]:
    """
    Calculates the SHA256 hash for a file on disk.
    """
    if not file_path or not file_path.is_file():
        logger.error(f"File not found or is not a file for hashing: {file_path}")
        return None
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read and update hash string value in blocks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        hex_digest = sha256_hash.hexdigest()
        logger.info(f"Calculated SHA256 for {file_path.name}: {hex_digest[:8]}...")
        return hex_digest
    except IOError as e: # More specific exception for file operations
        logger.error(f"IOError calculating SHA256 for {file_path}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error calculating SHA256 for {file_path}: {e}", exc_info=True)
    return None

def sanitize_filename(filename: str, default_name: str = "downloaded_file") -> str:
    """
    Basic filename sanitization to make it safe for use in file paths.
    Removes directory traversal components and problematic characters.
    """
    if not filename:
        return default_name
    
    # Take only the basename to prevent directory traversal
    filename = Path(filename).name
    
    # Replace spaces and common separators with underscore
    s1 = re.sub(r'[\s\-/\\&:,|]+', '_', filename)
    # Remove characters that are not alphanumeric, underscore, hyphen, or period
    s2 = re.sub(r'[^\w.\-_]', '', s1)
    # Collapse multiple underscores or hyphens
    s3 = re.sub(r'_+', '_', s2)
    s4 = re.sub(r'-+', '-', s3)
    # Remove leading/trailing problematic characters (underscores, periods, hyphens, spaces)
    s5 = s4.strip('._- ')
    
    # Ensure filename is not empty after sanitization
    return s5 if s5 else default_name

# You can add other truly generic utilities here as your template evolves.
# For example, a helper for robustly getting a string value from a nested dictionary.