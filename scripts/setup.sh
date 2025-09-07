#!/bin/bash

# Smart Lead Scoring CRM Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up Smart Lead Scoring CRM..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p models
mkdir -p data/processed
mkdir -p data/insights
mkdir -p logs

# Generate sample data
echo "📊 Generating sample data..."
python data_pipeline/lead_data_simulator.py

# Train initial model
echo "🤖 Training initial model..."
python ml_model/train_model.py

echo "✅ Setup completed successfully!"
echo ""
echo "To start the application:"
echo "1. Backend: uvicorn api.enhanced_main:app --reload --host 0.0.0.0 --port 8000"
echo "2. Frontend: cd frontend && npm start"
echo "3. Or use Docker: docker-compose up -d"
echo ""
echo "Access points:"
echo "- Frontend: http://localhost:3000"
echo "- API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
