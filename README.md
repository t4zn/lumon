# Flora - Plant Identification App 🌱

Flora is a sophisticated plant identification web application that combines AI-powered plant recognition with an intelligent botanical chatbot. Built with Flask and modern web technologies, Flora provides users with accurate plant identification and comprehensive plant care advice.

## ✨ Features

### 🔍 Plant Identification
- **PlantNet API Integration**: Highly accurate plant identification using the world's largest botanical database
- **Local AI Fallback**: Advanced image analysis with comprehensive botanical database
- **Multi-format Support**: JPG, PNG, GIF image uploads
- **Intelligent Detection**: Specialized algorithms for carnivorous plants, roses, fruit trees, and more

### 🤖 AI Botanical Assistant
- **Smart Chatbot**: Powered by Google Gemini Pro with DeepSeek fallback
- **Contextual Responses**: Understands botanical context and provides relevant advice
- **Plant Care Guidance**: Specific care instructions for identified plants
- **Wikipedia Integration**: Accurate plant information from trusted sources

### 📱 Modern Interface
- **Progressive Web App**: Mobile-first design with offline capabilities
- **Dark Theme**: Clean, modern dark interface optimized for readability
- **3D Animations**: Three.js-powered botanical animations and particles
- **Responsive Design**: Seamless experience across all devices

### 🔧 Technical Features
- **RESTful API**: Clean endpoints for plant identification and chat
- **Image Processing**: Advanced color analysis and botanical feature detection
- **Service Worker**: Offline functionality and caching
- **Health Monitoring**: Built-in health check endpoints

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/t4zn/flora.git
   cd flora
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file with your API keys:
   ```env
   PLANTNET_API_KEY=your_plantnet_api_key
   GEMINI_API_KEY=your_gemini_api_key
   TOGETHER_API_KEY=your_together_api_key
   SESSION_SECRET=your_session_secret
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access Flora**
   Open your browser to `http://localhost:5000`

## 📁 Project Structure

```
flora/
├── app.py                 # Main Flask application
├── main.py               # Application entry point
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── static/               # Static assets
│   ├── style.css        # Main styles
│   ├── script.js        # Main JavaScript
│   ├── landing.js       # Landing page animations
│   └── icons/           # App icons
├── templates/            # HTML templates
│   ├── landing.html     # Landing page
│   ├── index.html       # Main app interface
│   └── auth.html        # Authentication page
├── flora-android/        # Android app source
└── uploads/             # Temporary image uploads
```

## 🔌 API Endpoints

### Plant Identification
```http
POST /predict
Content-Type: multipart/form-data

# Upload plant image for identification
```

### Chat Interface
```http
POST /chat
Content-Type: application/json

{
  "message": "How do I care for my monstera?"
}
```

### Health Check
```http
GET /health
```

## 🛠️ Technology Stack

### Backend
- **Flask**: Python web framework
- **Gunicorn**: WSGI HTTP Server
- **Pillow**: Image processing
- **Requests**: HTTP library for API calls

### Frontend
- **Vanilla JavaScript**: No framework dependencies
- **Three.js**: 3D animations and particles
- **CSS3**: Modern styling with grid and flexbox
- **Service Worker**: PWA functionality

### APIs & Services
- **PlantNet API**: Botanical identification
- **Google Gemini Pro**: AI conversational assistant
- **Together.ai**: Fallback AI responses
- **Wikipedia API**: Plant information retrieval

## 🌍 Deployment

### Replit Deployment
Flora is optimized for Replit deployment with automatic configuration:

1. Import the repository to Replit
2. Add your API keys to Secrets
3. Run the application

The `.replit` file includes all necessary configuration for automatic deployment.

### Manual Deployment
For custom deployments:

```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PLANTNET_API_KEY` | PlantNet API key for plant identification | Yes |
| `GEMINI_API_KEY` | Google Gemini Pro API key | Yes |
| `TOGETHER_API_KEY` | Together.ai API key for fallback | Yes |
| `SESSION_SECRET` | Flask session secret key | Yes |
| `DATABASE_URL` | PostgreSQL database URL | No |

## 📱 Mobile App

Flora includes a native Android application built with Capacitor:

```bash
cd flora-android
npx cap sync android
npx cap run android
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PlantNet**: For providing the world-class plant identification API
- **Google Gemini**: For powering the intelligent botanical assistant
- **Three.js Community**: For the amazing 3D graphics library
- **Flask Team**: For the excellent Python web framework

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/t4zn/flora/issues) page
2. Create a new issue with detailed information
3. Provide steps to reproduce any bugs

---

**Flora** - Bringing nature closer through technology 🌿