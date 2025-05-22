# scripts/generators/utils.py
import re

def sanitize_identifier(name: str, suffix: str = "") -> str:
    """
    Converts a string to a safe snake_case identifier, optionally adding a suffix.
    - Handles CamelCase to snake_case.
    - Converts to lowercase.
    - Replaces common separators (space, -, /, \, &) with underscores.
    - Removes any other non-alphanumeric characters (keeps underscores).
    - Collapses multiple underscores into single underscores.
    - Strips leading/trailing underscores.
    - Adds a suffix if provided and not already present.
    - Returns a default ('default' or 'default_identifier') if the name is empty after sanitization.
    """
    if not name: # Handle empty input name early
        name_processed = "default"
    else:
        s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        # Replace common separators like space, hyphen, slash, backslash, ampersand with underscore
        s3 = re.sub(r'[\s\-/\&]+', '_', s2)
        # Remove any character that is not a word character (alphanumeric or underscore)
        # \W is equivalent to [^a-zA-Z0-9_]. So this step correctly keeps underscores.
        s3_cleaned = re.sub(r'[^\w_]+', '', s3)
        # Collapse multiple underscores and strip leading/trailing ones
        s4 = re.sub(r'_+', '_', s3_cleaned).strip('_')
        name_processed = s4 if s4 else "default"

    # Add suffix only if provided and not already present
    if suffix:
        if name_processed == "default" and not name_processed.endswith(suffix): # e.g. default_task
             # Ensure default combined with suffix makes sense, e.g. "default_task"
            if suffix.startswith("_"):
                name_processed += suffix
            else:
                name_processed = f"default{suffix}" # Fallback if name was empty
        elif not name_processed.endswith(suffix):
            name_processed += suffix
    
    if not name_processed: # Final check if empty
        name_processed = "default_identifier"

    return name_processed
