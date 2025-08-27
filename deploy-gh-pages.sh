#!/bin/bash

echo "🚀 VCT Survivor - GitHub Pages Deployment"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Git repository not found. Please initialize git first."
    exit 1
fi

echo "✅ Git repository found"

# Check if we have changes to commit
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Changes detected, committing..."
    git add .
    git commit -m "🚀 Deploy to GitHub Pages - $(date)"
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin main

echo ""
echo "🎉 Deployment initiated!"
echo "📱 Your app will be available at:"
echo "   https://Ominousx.github.io/final-man-standing"
echo ""
echo "⏳ It may take 2-5 minutes for changes to appear."
echo "💡 Check the Actions tab in your GitHub repo for deployment status."
