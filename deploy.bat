@echo off
REM Deployment script for Fly.io (Windows)
echo 🚀 Deploying AI Financial Analyst to Fly.io...

REM Build frontend
echo 📦 Building frontend...
cd frontend
call npm ci
call npm run build
cd ..

REM Deploy to Fly.io
echo ☁️  Deploying to Fly.io...
flyctl deploy

echo ✅ Deployment complete!
echo 🌐 Your app should be available at: https://ai-financial-analyst.fly.dev
pause
