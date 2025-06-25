#!/bin/bash

# Flora GitHub Push Script
echo "🌱 Preparing Flora project for GitHub push..."

# Add all files to git
echo "Adding files to git..."
git add .

# Commit with descriptive message
echo "Creating commit..."
git commit -m "Initial commit: Flora Plant Identification App

Features:
- PlantNet API integration for accurate plant identification
- AI-powered botanical chatbot with Gemini Pro + DeepSeek fallback
- Progressive Web App with mobile-first design
- 3D animations and dark theme interface
- Android app source code included
- Comprehensive plant care advice system"

# Push to GitHub
echo "Pushing to GitHub repository..."
git push -u origin main

echo "✅ Flora project successfully pushed to https://github.com/t4zn/flora"
echo ""
echo "Next steps:"
echo "1. Add your API keys to the repository secrets (for deployment)"
echo "2. Configure deployment settings if needed"
echo "3. Update the repository description and topics on GitHub"