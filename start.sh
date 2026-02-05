#!/bin/bash

# AI Email Auto-Reply System Startup Script

echo "Starting AI Email Auto-Reply System..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating from example..."
    cp .env.example .env
    echo "Please edit .env file with your GEMINI_API_KEY"
fi

# Start backend
echo "Starting backend server..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt --quiet

echo "Backend starting on http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# Start frontend
echo "Starting frontend server..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Frontend starting on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "============================================"
echo "AI Email Auto-Reply System is running!"
echo "============================================"
echo "Frontend: http://localhost:5173"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
