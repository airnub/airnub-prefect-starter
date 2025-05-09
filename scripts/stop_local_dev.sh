#!/bin/bash
# scripts/stop_local_dev.sh
# Stops and removes the local Prefect development environment containers,
# networks, and volumes defined in docker-compose.yml.

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Go to the project root (assuming scripts/ is one level down)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1 # Exit if cd fails

echo "--- Stopping Local Prefect Environment ---"
echo "Project Root: $PROJECT_ROOT"

# Optional: Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "[Warning] docker-compose.yml not found in project root ($PROJECT_ROOT). Cannot stop services."
    exit 1
fi

echo "Stopping and removing Docker Compose services (Prefect Server, DB, Worker)..."
# Use docker compose command (v2 syntax preferred)
# -v removes named volumes (like the database data) - ensures clean state on next start
# --remove-orphans removes containers for services not defined in compose file (good practice)
docker compose down -v --remove-orphans

# Check the exit status
if [ $? -ne 0 ]; then
    echo "[Warning] Docker Compose down command encountered an error, but proceeding."
    # Don't exit immediately, might just be warnings or already stopped services
fi

echo ""
echo "-----------------------------------------------------"
echo "Local Prefect environment stopped and cleaned up."
echo "-----------------------------------------------------"

exit 0
