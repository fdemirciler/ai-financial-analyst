#!/bin/bash

# Deployment script for Fly.io
echo "🚀 Deploying AI Financial Analyst to Fly.io..."

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm ci
npm run build
cd ..

# Deploy to Fly.io
echo "☁️  Deploying to Fly.io..."
flyctl deploy

echo "✅ Deployment complete!"
echo "🌐 Your app should be available at: https://ai-financial-analyst.fly.dev"
