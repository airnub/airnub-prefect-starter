#!/usr/bin/env python3
# scripts/setup_prefect_blocks.py
"""
Sets up essential Prefect Blocks for the local development environment.

By default, this script focuses on:
1.  A placeholder Secret block ('example-secret') to demonstrate secret management pattern.

NOTE: Creation of the 'local-worker-infra' DockerContainer block is currently
      REMOVED from this script. This block IS REQUIRED for the deployments in
      'prefect.local.yaml' to function with the local Docker Compose setup.
      You must create it manually or restore the creation logic later.

It can be extended to create provider-specific blocks (like AWS, GCP, Azure)
by adding the necessary Prefect collection libraries (e.g., prefect-aws) and
modifying this script to include their creation logic, likely driven by
additional environment variables (e.g., SETUP_AWS_ACCESS_KEY_ID).

Requires python-dotenv: pip install python-dotenv
"""

import asyncio
import os
import sys
import traceback
from pathlib import Path
from typing import List, Optional

# --- Add python-dotenv ---
try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed. .env file will not be loaded.")
    print("Run 'pip install python-dotenv'")
    load_dotenv = None
# --- End Add ---

# --- Prefect Imports ---
try:
    from prefect.blocks.core import Block
    # Import Secret block type
    from prefect.blocks.system import Secret
    # !! DockerContainer import REMOVED !!
    # from prefect.infrastructure import DockerContainer
    from prefect.exceptions import ObjectNotFound
    from prefect.client.orchestration import get_client
except ImportError as e:
    print(f"FATAL ERROR: Failed to import Prefect modules: {e}")
    print("Ensure Prefect is installed correctly.")
    sys.exit(1)
except Exception as e:
    print(f"FATAL ERROR: Unexpected error during Prefect imports: {e}")
    sys.exit(1)
# --- End Prefect Imports ---


# --- Load .env file ---
# Determine project root relative to this script's location
try:
    project_root = Path(__file__).resolve().parents[1]
except IndexError:
    project_root = Path.cwd() # Fallback if run from root
dotenv_path = project_root / '.env'
if load_dotenv:
    print(f"Attempting to load environment variables from: {dotenv_path}")
    try:
        loaded = load_dotenv(dotenv_path=dotenv_path, override=True)
        if loaded: print("Successfully loaded variables from .env file.")
        else: print("No .env file found or it was empty.")
    except Exception as e: print(f"Warning: Error loading .env file: {e}")
else: print(".env file loading skipped as python-dotenv is not installed.")
# --- End Load ---

# --- Helper Functions ---

async def block_exists(block_type_slug: str, block_name: str) -> bool:
    """Checks if a BLOCK already exists using the client."""
    try:
        async with get_client() as client:
            await client.read_block_document_by_name(name=block_name, block_type_slug=block_type_slug)
        print(f"  Found existing block: '{block_type_slug}/{block_name}'")
        return True
    except ObjectNotFound:
        print(f"  Block not found: '{block_type_slug}/{block_name}'")
        return False
    except Exception as e:
        print(f"Warning: Error checking block {block_type_slug}/{block_name}: {e}")
        return False # Assume it doesn't exist or cannot verify

# --- Block Creation Logic ---

# --- Docker Block Creation ---
# async def create_docker_infra_block(block_name: str, overwrite: bool):
#     """Creates the Docker Container block for local execution."""
#     print(f"\n--- Processing Docker Infrastructure Block: '{block_name}' ---")
#     slug = "docker-container"
#     exists = await block_exists(slug, block_name)
#
#     if exists and not overwrite:
#         print(f"- Block '{slug}/{block_name}' already exists. Skipping creation.")
#         return
#
#     action = "Overwriting existing" if exists else "Creating new"
#     print(f"- {action} block '{slug}/{block_name}'...")
#     try:
#         # Ensure prefect.infrastructure.DockerContainer is imported if uncommenting
#         docker_block = DockerContainer(
#             image="airnub-prefect-starter-worker:latest",
#             image_pull_policy="NEVER",
#             auto_remove=True,
#             networks=["prefect-network"],
#         )
#         await docker_block.save(name=block_name, overwrite=True)
#         print(f"- Saved/Updated Block: '{slug}/{block_name}' (DockerContainer)")
#     except Exception as e:
#          print(f"ERROR saving block '{slug}/{block_name}': {e}")
#          traceback.print_exc()
# --- End Docker Block ---


async def create_placeholder_secret_block(block_name: str, overwrite: bool):
    """Creates a placeholder Secret block."""
    print(f"\n--- Processing Placeholder Secret Block: '{block_name}' ---")
    slug = "secret"
    exists = await block_exists(slug, block_name)

    if exists and not overwrite:
        print(f"- Block '{slug}/{block_name}' already exists. Skipping creation.")
        return

    action = "Overwriting existing" if exists else "Creating new"
    print(f"- {action} block '{slug}/{block_name}'...")
    try:
        # Use a placeholder value - DO NOT commit real secrets here
        secret_block = Secret(value="replace-with-real-secret-value-in-ui-or-via-cli")
        await secret_block.save(name=block_name, overwrite=True) # Use overwrite=True as we've checked
        print(f"- Saved/Updated Block: '{slug}/{block_name}' (Secret)")
        print(f"  NOTE: Value is a placeholder. Update it with real secrets via Prefect UI/CLI.")
    except Exception as e:
        print(f"ERROR saving block '{slug}/{block_name}': {e}")
        traceback.print_exc()


async def create_all_blocks():
    """Main async function to create all needed blocks."""
    print("Starting block setup...")
    overwrite = os.environ.get("PREFECT_BLOCK_OVERWRITE", "false").lower() == "true"
    print(f"Overwrite existing blocks (PREFECT_BLOCK_OVERWRITE): {overwrite}")

    # Define block names
    # docker_infra_block_name = "local-worker-infra" # Name if Docker block were created
    secret_block_name = "example-secret" # Placeholder secret

    # --- Docker Block Creation Call REMOVED ---
    # print("\nINFO: Docker infrastructure block creation ('local-worker-infra') is currently disabled in this script.")
    # print("      This block IS REQUIRED for 'prefect.local.yaml' deployments to work.")
    # print("      Uncomment the relevant sections in the script or create it manually if needed.")
    # # await create_docker_infra_block(docker_infra_block_name, overwrite)
    # --- End Docker Block REMOVED ---


    # Create Placeholder Secret Block (Demonstration)
    await create_placeholder_secret_block(secret_block_name, overwrite)

    # --- REMOVED AWS Block Creation ---

    print("\nBlock setup script finished.")


# --- Main Execution Block ---
if __name__ == "__main__":
    api_url = os.environ.get("PREFECT_API_URL")
    api_key = os.environ.get("PREFECT_API_KEY")
    if not api_url:
        print("\nERROR: PREFECT_API_URL environment variable not set.")
        print("Please set it directly or via the .env / setup.env file.")
        sys.exit(1)
    if "prefect.cloud" in api_url and not api_key:
        print("\nWARNING: PREFECT_API_URL looks like Prefect Cloud, but PREFECT_API_KEY is not set.")

    print(f"\nTargeting Prefect API: {api_url}")
    print("Script will attempt to create/update:")
    # print(" - Docker Container block: 'local-worker-infra'  <-- DISABLED IN SCRIPT") # Updated print statement
    print(" - Placeholder Secret block: 'example-secret'")
    print("Set PREFECT_BLOCK_OVERWRITE=true env var to force updates to existing blocks.")
    print("\nWARNING: Automatic creation of 'local-worker-infra' DockerContainer block is disabled.")
    print("         Deployments in 'prefect.local.yaml' require this block to run.")
    print("Starting block creation...\n")

    try:
        asyncio.run(create_all_blocks())
    except Exception as e:
        print(f"\nCRITICAL ERROR during script execution: {e}")
        traceback.print_exc()

    print("\nScript finished.")