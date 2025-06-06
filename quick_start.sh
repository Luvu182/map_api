#!/bin/bash
# Quick Start Script for US Cities Road Data Project

echo "🚀 US Cities Road Data Project - Quick Start"
echo "=========================================="

# Check requirements
echo "Checking requirements..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 required but not installed."; exit 1; }
command -v psql >/dev/null 2>&1 || { echo "⚠️  PostgreSQL recommended but not installed."; }

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
cat > requirements.txt << EOF
pandas>=1.3.0
geopandas>=0.10.0
shapely>=1.8.0
requests>=2.26.0
tqdm>=4.62.0
psycopg2-binary>=2.9.0
sqlalchemy>=1.4.0
EOF

pip install -r requirements.txt

# Create subdirectories
echo "Creating project structure..."
mkdir -p raw_data/shapefiles
mkdir -p processed_data/by_state
mkdir -p processed_data/by_city
mkdir -p output/by_state
mkdir -p output/by_city
mkdir -p output/metadata

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Place your paste.txt file in the scripts directory"
echo "2. cd scripts && python process_cities.py"
echo "3. Follow the guides in order:"
echo "   - CRAWL_GUIDE.md"
echo "   - PROCESSING_GUIDE.md"
echo "   - DEPLOYMENT.md"
echo ""
echo "Happy coding! 🎉"