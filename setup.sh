#!/bin/bash
# Quick setup script for Terraform K8s Agent

set -e

echo "🤖 Terraform K8s Agent - Setup"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION found"

# Check pip
echo ""
echo "Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Installing..."
    python3 -m ensurepip --upgrade
fi
echo "✅ pip found"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
echo "✅ Dependencies installed"

# Check Terraform
echo ""
echo "Checking Terraform..."
if ! command -v terraform &> /dev/null; then
    echo "⚠️  Terraform not found"
    echo "   Install from: https://www.terraform.io/downloads"
else
    TERRAFORM_VERSION=$(terraform --version | head -1)
    echo "✅ $TERRAFORM_VERSION found"
fi

# Check kubectl
echo ""
echo "Checking kubectl..."
if ! command -v kubectl &> /dev/null; then
    echo "⚠️  kubectl not found"
    echo "   Install from: https://kubernetes.io/docs/tasks/tools/"
else
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null || kubectl version --client)
    echo "✅ kubectl found"
fi

# Create .env if not exists
echo ""
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✅ .env created from .env.example"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and configure your LLM provider!"
    echo "   For quick start (local/free):"
    echo "   1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   2. Pull a model: ollama pull llama2"
    echo "   3. Keep LLM_PROVIDER=ollama in .env"
else
    echo "✅ .env already exists"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p output data
echo "✅ Directories created"

# Make main.py executable
chmod +x main.py

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your LLM provider in .env"
echo "2. Run: python main.py (interactive mode)"
echo "   Or: python main.py --help (see all options)"
echo ""
echo "Quick test:"
echo "  python main.py create --platform k3s --nodes 1 --no-monitoring"
echo "=========================================="
