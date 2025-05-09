#!/bin/bash
# scripts/build_deployments.sh
# Applies Prefect deployments using YAML definitions (--all) for local
# or specific CLI commands for aws.
# Usage: ./scripts/build_deployments.sh [local|aws]
# Default: local

# --- Configuration ---
TARGET_ENV=${1:-local} # Default to 'local' if no argument provided
AWS_WORK_POOL_NAME="your-aws-pool-name" # !!! REPLACE with your actual AWS work pool name !!!
# --- End Configuration ---

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Go to the project root
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1 # Exit if cd fails

echo "--- Building and Applying Prefect Deployments (Target: $TARGET_ENV) ---"
echo "Project Root: $PROJECT_ROOT"

# Validate Target Environment
if [[ "$TARGET_ENV" != "local" && "$TARGET_ENV" != "aws" ]]; then
  echo "[Error] Invalid target environment '$TARGET_ENV'. Please use 'local' or 'aws'."
  exit 1
fi

# Activate virtual environment
if [ -d ".venv" ] && [ -z "$VIRTUAL_ENV" ]; then
  echo "Activating virtual environment..."
  source .venv/bin/activate || { echo "[Error] Failed to activate virtual environment."; exit 1; }
fi

# Verify prefect command
if ! command -v prefect &> /dev/null; then
    echo "[Error] 'prefect' command could not be found."
    exit 1
fi

# --- Deployment Logic ---
EXIT_CODE=0 # Initialize exit code

if [ "$TARGET_ENV" == "local" ]; then
  # --- Local Deployment using prefect.local.yaml and --all ---
  YAML_FILE="prefect.local.yaml"
  echo "Using LOCAL configuration from $YAML_FILE."
  echo "NOTE: Ensure $YAML_FILE fully defines all desired local deployments correctly."

  # Check if YAML file exists
  if [ ! -f "$YAML_FILE" ]; then
      echo "[Error] Configuration file '$YAML_FILE' not found."
      exit 1
  fi

  # Apply all deployments defined in the YAML file
  echo "Applying all deployments defined in $YAML_FILE..."
  prefect deploy --prefect-file "$YAML_FILE" --all \
    || echo "[Error] Failed to apply local deployments from $YAML_FILE."
  EXIT_CODE=$? # Capture exit code

else # aws
  # --- AWS Deployment using prefect.yaml and CLI overrides ---
  YAML_FILE="prefect.yaml"
  WORK_POOL_NAME="$AWS_WORK_POOL_NAME"
  DEPLOYMENT_SUFFIX=" - AWS" # Add suffix to differentiate deployment names
  echo "Using AWS configuration from $YAML_FILE with CLI overrides."
  echo "NOTE: Ensure $YAML_FILE has build/push/pull uncommented."
  if [ "$WORK_POOL_NAME" == "your-aws-pool-name" ]; then
      echo "[Warning] AWS_WORK_POOL_NAME is set to placeholder. Please update the script."
  fi
   if [ ! -f "$YAML_FILE" ]; then
      echo "[Error] Configuration file '$YAML_FILE' not found."
      exit 1
  fi

  echo "Targeting Work Pool: $WORK_POOL_NAME"
  echo "Targeting Work Queue: default" # Assuming default queue for AWS pool too

  # Apply specific deployments using CLI overrides for AWS
  echo "Deploying Department A (AWS)..."
  prefect deploy --prefect-file "$YAML_FILE" flows/department_a/flow_dept_a.py:scrape_dept_a_flow \
    -n "Dept A Scraper$DEPLOYMENT_SUFFIX" \
    -p "$WORK_POOL_NAME" \
    -q default \
    || echo "[Error] Failed to deploy Dept A (AWS)."
  EXIT_CODE=$? # Capture exit code of the first deployment attempt

  if [ $EXIT_CODE -eq 0 ]; then # Only proceed if first succeeded
      echo "Deploying Department B (AWS)..."
      prefect deploy --prefect-file "$YAML_FILE" flows/department_b/flow_dept_b.py:scrape_dept_b_flow \
        -n "Dept B Scraper$DEPLOYMENT_SUFFIX" \
        -p "$WORK_POOL_NAME" \
        -q default \
        || echo "[Error] Failed to deploy Dept B (AWS)."
      EXIT_CODE=$? # Capture exit code of the second deployment attempt
  fi
  # Add more flows for AWS target here...
fi
# --- End Deployment Logic ---


echo ""
echo "-----------------------------------------------------"
echo "Prefect deployments applied (or attempted) for '$TARGET_ENV' environment."
echo "Check the Prefect UI (Deployments tab)."
echo "Target Server API URL: ${PREFECT_API_URL:-Not Set (uses default)}"
echo "-----------------------------------------------------"

exit $EXIT_CODE # Exit with the status of the last command run