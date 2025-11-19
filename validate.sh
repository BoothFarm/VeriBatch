#!/bin/bash
# Quick validation script - checks if the code structure is valid

echo "🔍 Validating OriginStack setup..."

# Check if OpenOriginJSON exists
if [ ! -d "../OpenOriginJSON/ooj_client" ]; then
    echo "❌ OpenOriginJSON not found in parent directory"
    echo "   Please ensure OpenOriginJSON is at ../OpenOriginJSON/"
    exit 1
fi

echo "✅ OpenOriginJSON found"

# Check Python files for syntax errors
echo "🐍 Checking Python syntax..."

cd backend

for file in $(find app -name "*.py"); do
    python3 -m py_compile "$file" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Syntax error in $file"
        exit 1
    fi
done

echo "✅ All Python files valid"

echo ""
echo "✨ Structure looks good!"
echo ""
echo "Next steps:"
echo "1. Set up PostgreSQL database (see backend/README.md)"
echo "2. Install dependencies: cd backend && pip install -r requirements.txt"
echo "3. Run the app: uvicorn app.main:app --reload"
