#!/bin/bash
# Development environment setup script for noise_floor_reporter

set -e  # Exit on error

echo "=========================================="
echo "Noise Floor Reporter - Dev Setup"
echo "=========================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment
if [ -d ".venv" ]; then
    echo "⚠ Virtual environment already exists at .venv"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old virtual environment..."
        rm -rf .venv
    else
        echo "Using existing virtual environment"
    fi
fi

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null

# Ask user what to install
echo ""
echo "Select installation type:"
echo "  1) Base (RTL-SDR only)"
echo "  2) With SoapySDR support"
echo "  3) Development (includes SoapySDR)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "Installing base package..."
        pip install -e .
        ;;
    2)
        echo "Installing with SoapySDR support..."
        pip install -e ".[soapysdr]"
        ;;
    3)
        echo "Installing for development..."
        pip install -e ".[dev,soapysdr]"
        ;;
    *)
        echo "Invalid choice. Installing base package..."
        pip install -e .
        ;;
esac

echo ""
echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the tool:"
echo "  noise-floor-reporter --freq 7.0-7.3 --json"
echo ""
echo "To deactivate:"
echo "  deactivate"
echo ""
