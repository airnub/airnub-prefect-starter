#!/bin/bash
# scripts/run_local_dev.sh
# Builds and starts the local Prefect development environment using Docker Compose.
# This includes Prefect server, UI, Postgres DB, and the custom worker.

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Go to the project root (assuming scripts/ is one level down)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1 # Exit if cd fails

echo "--- Starting Local Prefect Environment ---"
echo "Project Root: $PROJECT_ROOT"

echo "Checking Docker daemon status..."
docker ps > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[Error] Docker daemon is not running. Please start Docker and try again."
    exit 1
else
    echo "Docker daemon is running."
fi

# Optional: Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "[Error] docker-compose.yml not found in project root ($PROJECT_ROOT)."
    exit 1
fi

echo "Stopping existing containers (if any) to ensure a clean start..."
# Use docker compose command (v2 syntax preferred)
docker compose down -v --remove-orphans

echo "Building worker image (if needed) and starting services..."
# Use --build to ensure the worker image is updated if Dockerfile or code changed
# Use -d to run in detached mode
docker compose up --build -d

# Check the exit status of docker compose up
if [ $? -ne 0 ]; then
    echo "[Error] Docker Compose failed to start services. Check logs above or run 'docker compose logs'."
    exit 1
fi

echo ""
echo "-----------------------------------------------------"
echo "Local Prefect environment started successfully!"
echo ""
echo "Access Prefect UI at: http://127.0.0.1:4200"
echo "Worker container 'prefect-custom-worker' is running and polling the 'default' pool."
echo ""
echo "Next steps:"
echo " - Activate your virtual environment: source .venv/bin/activate"
echo " - Build and apply deployments: ./scripts/build_deployments.sh"
echo " - Trigger flow runs via the UI or CLI."
echo ""
echo "To view logs: docker compose logs -f worker"
echo "To stop services: ./scripts/stop_local_dev.sh"
echo "-----------------------------------------------------"

exit 0
