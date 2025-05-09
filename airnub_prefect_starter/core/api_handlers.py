# airnub_prefect_starter/core/api_handlers.py
import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def core_fetch_json_from_api(url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Core logic to fetch JSON data from a given API endpoint.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            logger.info(f"Core: Fetching JSON from API: {url} with params: {params}")
            response = await client.get(url, params=params)
            response.raise_for_status()
            logger.info(f"Core: Successfully fetched JSON from {url}, status: {response.status_code}")
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Core: HTTP error {e.response.status_code} while requesting {e.request.url!r}. Response: {e.response.text[:500]}")
    except httpx.RequestError as e: # Covers network errors, timeouts, etc.
        logger.error(f"Core: Request error while requesting {e.request.url!r}: {e}")
    except json.JSONDecodeError as e: # If response is not valid JSON
        logger.error(f"Core: Failed to decode JSON from {url}: {e}")
    except Exception as e:
        logger.error(f"Core: An unexpected error occurred fetching JSON from {url}: {e}", exc_info=True)
    return None

def core_parse_api_response_for_demo(response_data: Dict[str, Any], primary_key: str = "fact") -> Optional[Dict[str, Any]]:
    """
    Core logic for a very simple parser for demo API responses.
    Extracts a specific key or returns a small part of the response.
    """
    if not response_data or not isinstance(response_data, dict):
        logger.warning("Core: Invalid or empty API response_data provided for parsing.")
        return None

    parsed_result = {"data_retrieved": True} # Base for successful parsing attempt
    if primary_key in response_data:
        extracted_value = response_data[primary_key]
        logger.info(f"Core: Extracted primary key '{primary_key}': {str(extracted_value)[:100]}...")
        parsed_result[primary_key] = extracted_value
        # Example: try to get another common field if available from demo APIs
        if "length" in response_data: # Specific to catfact.ninja
             parsed_result["length"] = response_data["length"]
        elif "activity" in response_data: # Specific to boredapi.com
             parsed_result["activity_type"] = response_data.get("type")
             parsed_result["participants"] = response_data.get("participants")
    else:
        # Fallback: return a small part of the response or a specific message
        snippet = {k: v for i, (k, v) in enumerate(response_data.items()) if i < 3} # Get first 3 items
        logger.info(f"Core: Primary key '{primary_key}' not found. Returning snippet: {snippet}")
        parsed_result["message"] = f"Primary key '{primary_key}' not found in response."
        parsed_result["response_snippet"] = snippet
    
    return parsed_result