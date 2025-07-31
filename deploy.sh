#!/bin/bash
# Funda App Deployment Script

echo "🚀 Starting Funda App Deployment..."

# Create and activate virtual environment
echo "🔧 Setting up Python virtual environment..."
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📂 Creating directories..."
mkdir -p uploads resources

# Initialize database
echo "💾 Initializing database..."
flask db upgrade

# Create admin user
echo "👤 Creating admin user..."
python create_admin.py

echo "✨ Deployment complete!"
echo "To start the application, run: flask run"
echo "Access the app at: http://localhost:5000"
