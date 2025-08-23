#!/bin/bash
# Unix launcher script for Boneglaive
# Usage: ./run_boneglaive.sh [arguments]
# Example: ./run_boneglaive.sh --mode vs_ai --debug

echo "Starting Boneglaive on $(uname -s)..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ using your system package manager"
    exit 1
fi

# Check Python version
python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "WARNING: Python 3.8+ is recommended"
fi

# Set PYTHONPATH to current directory to ensure imports work
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the game with all passed arguments
python3 boneglaive/main.py "$@"

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "Game exited with error code $?"
fi