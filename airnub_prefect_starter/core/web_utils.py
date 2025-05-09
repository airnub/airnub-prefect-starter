# airnub_prefect_starter/core/web_utils.py
import httpx
from typing import Optional, List, Dict, Any
import logging
from bs4 import BeautifulSoup # Ensure beautifulsoup4 and lxml are in pyproject.toml
from urllib.parse import urljoin, urlparse

from ..common.utils import generate_sha256_hash_from_string # For hashing canonical URL

logger = logging.getLogger(__name__)

async def core_fetch_html_content(url: str) -> Optional[str]:
    """
    Core logic to fetch HTML content of a web page.
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            logger.info(f"Core Web: Fetching HTML from: {url}")
            # Add a common user-agent
            headers = {"User-Agent": "Mozilla/5.0 (compatible; PrefectDemoBot/1.0; +http://example.com/bot)"}
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            logger.info(f"Core Web: Successfully fetched HTML from {url}, status: {response.status_code}")
            # httpx handles encoding detection for .text, but you can specify if needed
            return response.text 
    except httpx.HTTPStatusError as e:
        logger.error(f"Core Web: HTTP error {e.response.status_code} while fetching HTML from {e.request.url!r}")
    except httpx.RequestError as e:
        logger.error(f"Core Web: Request error while fetching HTML from {e.request.url!r}: {e}")
    except Exception as e:
        logger.error(f"Core Web: An unexpected error occurred fetching HTML from {url}: {e}", exc_info=True)
    return None

def core_parse_links_and_canonical_from_html(html_content: str, original_page_url: str) -> Dict[str, Any]:
    """
    Core logic to extract all absolute HTTP/HTTPS links and the canonical URL from HTML content.
    Also hashes the canonical URL.
    """
    result_data: Dict[str, Any] = {
        "original_url": original_page_url,
        "canonical_url": None,
        "canonical_url_hash_sha256": None,
        "extracted_links": [],
        "status": "INITIATED_PARSING"
    }
    if not html_content:
        result_data["status"] = "FAILED_NO_HTML"
        result_data["error_message"] = "No HTML content provided for parsing."
        logger.warning("Core Web: No HTML content provided for parsing.")
        return result_data
    
    extracted_links_set = set()
    found_canonical_url = None
    
    try:
        # Ensure lxml is an optional dependency, or use 'html.parser' for built-in
        soup = BeautifulSoup(html_content, "lxml") 

        # Extract canonical URL
        canonical_link_tag = soup.find("link", rel="canonical", href=True)
        if canonical_link_tag and canonical_link_tag.get("href"):
            found_canonical_url_str = urljoin(original_page_url, canonical_link_tag["href"].strip())
            # Basic validation for the canonical URL
            parsed_canonical = urlparse(found_canonical_url_str)
            if parsed_canonical.scheme in ["http", "https"]:
                found_canonical_url = found_canonical_url_str
                result_data["canonical_url"] = found_canonical_url
                result_data["canonical_url_hash_sha256"] = generate_sha256_hash_from_string(found_canonical_url)
                logger.info(f"Core Web: Found canonical URL: {found_canonical_url} (Hash: {result_data['canonical_url_hash_sha256'][:8]}...)")
            else:
                logger.warning(f"Core Web: Found <link rel=canonical> but href was not a valid http/https URL: {canonical_link_tag['href']}")
        else:
            logger.info(f"Core Web: No canonical URL link tag found for {original_page_url}.")
            # As a fallback, consider the original URL as canonical if no tag is found
            result_data["canonical_url"] = original_page_url
            result_data["canonical_url_hash_sha256"] = generate_sha256_hash_from_string(original_page_url)


        # Extract all a href links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href and not href.startswith(("#", "mailto:", "javascript:")):
                absolute_url = urljoin(original_page_url, href) # Use original_page_url as base
                parsed_url = urlparse(absolute_url)
                if parsed_url.scheme in ["http", "https"]: # Only collect http/https links
                    extracted_links_set.add(absolute_url)
        
        result_data["extracted_links"] = sorted(list(extracted_links_set))
        logger.info(f"Core Web: Extracted {len(extracted_links_set)} unique links from page: {original_page_url}")
        result_data["status"] = "SUCCESS"
    except Exception as e:
        logger.error(f"Core Web: Error parsing HTML or extracting links for {original_page_url}: {e}", exc_info=True)
        result_data["status"] = "FAILED_PARSING"
        result_data["error_message"] = str(e)
        
    return result_data