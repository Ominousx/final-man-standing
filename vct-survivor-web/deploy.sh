#!/bin/bash

echo "🚀 VCT Survivor - Deployment Script"
echo "=================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the app
echo "🔨 Building the application..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
else
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📥 Installing Vercel CLI..."
    npm install -g vercel
fi

echo "🌐 Deploying to Vercel..."
echo "📝 Note: You'll need to login to Vercel if this is your first time."
echo ""

# Deploy to Vercel
vercel --prod

echo ""
echo "🎉 Deployment complete!"
echo "🌍 Your app should now be live at the URL provided above."
echo ""
echo "📱 Share the URL with your friends to start playing!"
echo ""
echo "💡 Tip: Every time you push to GitHub, your app will automatically update!"
