#!/bin/bash
# Start the Report Generator (Backend + Frontend)

echo "🚀 Starting Report Generator..."
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the report-generator directory"
    exit 1
fi

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

# Install frontend dependencies if needed
if [ ! -d "web/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd web
    npm install
    cd ..
fi

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "Starting servers..."
echo "  📡 Backend API: http://localhost:8000"
echo "  🌐 Frontend UI: http://localhost:3000"
echo ""

# Start backend in background
source venv/bin/activate
python -m uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend in background
cd web
npm run dev &
FRONTEND_PID=$!

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '👋 Goodbye!'; exit 0" SIGINT SIGTERM

echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

wait
