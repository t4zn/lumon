# Flora Plant Identification App

## Project Overview
Flora is a plant identification web application that uses PlantNet API for accurate plant identification and AI-powered chatbot for botanical assistance.

## Recent Changes
- **June 25, 2025**: Successfully migrated from Replit Agent to Replit environment
- Integrated PlantNet API for plant identification
- Updated chatbot to use Gemini Pro with DeepSeek fallback
- Added API key management via .env file
- Fixed package dependencies and deployment configuration
- **Latest Update**: Improved chatbot with memory capabilities and concise responses
- Enhanced plant identification to correctly identify fruit trees like apple trees
- Added session-based conversation memory for contextual responses
- **Plant ID Fix**: Implemented comprehensive plant detection for all plant types
- Added specialized detection for carnivorous plants, roses, banana trees, and fruit trees
- Fixed light mode UI to be clean and smooth like dark mode
- Enhanced color analysis algorithm for accurate plant identification
- **Database Integration**: Added PostgreSQL database for persistent conversation memory
- **PlantNet API**: Integrated PlantNet API for highly accurate plant identification
- **Memory System**: Implemented context-aware chatbot that remembers previous conversations
- **UI Enhancement**: Completely removed green backgrounds from light mode interface
- **Dark Mode Only**: Removed light mode functionality completely, app now uses dark theme exclusively
- **Wikipedia API Restored**: Using Wikipedia API for accurate, specific plant information instead of standardized templates
- **Markdown Support**: Added proper markdown parsing for bold text in chat responses
- **Database Removed**: Eliminated all database/memory functionality for simpler stateless operation
- **GitHub Repository**: Prepared comprehensive project documentation and push script for GitHub deployment

## Project Architecture
- **Backend**: Flask web application
- **Plant Identification**: PlantNet API integration with local fallback
- **AI Chatbot**: Gemini Pro (primary) with Llama 3.2 via Together.ai (fallback)
- **Frontend**: Progressive Web App with mobile-first design
- **Database**: None currently (stateless application)

## API Integrations
- PlantNet API for botanical identification
- Google Gemini Pro for conversational AI
- Together.ai for fallback AI responses
- Wikipedia for plant information

## User Preferences
- Keep technical implementation details internal
- Focus on practical plant care advice
- Maintain conversational but informative tone
- Prioritize accuracy over speed for plant identification

## Deployment
- Configured for Replit environment
- Uses gunicorn WSGI server
- Binds to 0.0.0.0 for Replit compatibility
- Environment variables managed via .env file