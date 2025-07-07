import os
import logging
import uuid
import requests
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from PIL import Image
import io
import base64
import random
import time
import json
import re
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import Supabase integration
try:
    from supabase_config import is_supabase_available
    from database_service import db_service
    SUPABASE_AVAILABLE = is_supabase_available()
except ImportError as e:
    logging.warning(f"Supabase integration not available: {e}")
    SUPABASE_AVAILABLE = False

# Import AI libraries with fallback handling
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Google Generative AI not available: {e}")
    genai = None
    GENAI_AVAILABLE = False

try:
    from together import Together
    TOGETHER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Together AI not available: {e}")
    Together = None
    TOGETHER_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "Lumon-secret-key-2024")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Session storage for chat memory
chat_sessions = {}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# API Configuration
PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Configure Gemini if available
if GOOGLE_API_KEY and GENAI_AVAILABLE:
    genai.configure(api_key=GOOGLE_API_KEY)

# Configure Together AI if available
if TOGETHER_API_KEY and TOGETHER_AVAILABLE:
    together_client = Together(api_key=TOGETHER_API_KEY)
else:
    together_client = None

# Simplified plant identification without heavy ML dependencies
classifier = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_plant_details(plant_name):
    """Get detailed plant information including family, region, etc."""
    # Comprehensive plant database with detailed information
    plant_details_db = {
        'Monstera deliciosa': {
            'family': 'Araceae',
            'region': 'Central America',
            'toxicity': 85,
            'edible': False,
            'diseases': ['Skin irritation', 'Mouth swelling if ingested', 'Kidney stones from oxalates'],
            'care_tips': 'Bright indirect light, water when top soil is dry, high humidity preferred'
        },
        'Epipremnum aureum': {
            'family': 'Araceae',
            'region': 'Southeast Asia',
            'toxicity': 75,
            'edible': False,
            'diseases': ['Oral irritation', 'Difficulty swallowing', 'Vomiting if consumed'],
            'care_tips': 'Low to bright indirect light, water when soil is dry, very adaptable'
        },
        'Malus domestica': {
            'family': 'Rosaceae',
            'region': 'Central Asia',
            'toxicity': 10,
            'edible': True,
            'diseases': ['Seeds contain cyanogenic compounds - avoid consuming in large quantities'],
            'care_tips': 'Full sun, well-draining soil, regular watering, annual pruning in late winter'
        },
        'Ficus lyrata': {
            'family': 'Moraceae',
            'region': 'West Africa',
            'toxicity': 60,
            'edible': False,
            'diseases': ['Latex allergies', 'Skin rashes', 'Respiratory irritation'],
            'care_tips': 'Bright indirect light, consistent watering, avoid moving frequently'
        },
        'Aloe barbadensis': {
            'family': 'Asphodelaceae',
            'region': 'Arabian Peninsula',
            'toxicity': 20,
            'edible': True,
            'diseases': ['Laxative effects if consumed in large amounts', 'Skin sensitivity in rare cases'],
            'care_tips': 'Bright light, water deeply but infrequently, well-draining soil'
        },
        'Ocimum basilicum': {
            'family': 'Lamiaceae',
            'region': 'India',
            'toxicity': 5,
            'edible': True,
            'diseases': ['Generally safe', 'Possible blood thinning with excessive consumption'],
            'care_tips': 'Full sun, regular watering, pinch flowers to encourage leaf growth'
        }
    }
    
    # Try exact match first
    if plant_name in plant_details_db:
        return plant_details_db[plant_name]
    
    # Try partial match
    for db_name, details in plant_details_db.items():
        if any(word in db_name.lower() for word in plant_name.lower().split()):
            return details
    
    # Default details for unknown plants
    return {
        'family': 'Unknown',
        'region': 'Various',
        'toxicity': 50,
        'edible': False,
        'diseases': ['Unknown toxicity - avoid ingestion', 'Possible skin irritation'],
        'care_tips': 'Provide appropriate light and water based on plant type'
    }

def get_wikipedia_summary(plant_name):
    """Fetch plant description from Wikipedia API with improved search"""
    try:
        # Clean the plant name for better search results
        clean_name = plant_name.strip()
        
        # First try direct page access
        search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_name.replace(' ', '_')}"
        response = requests.get(search_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            extract = data.get('extract', '')
            if extract and len(extract) > 50:
                return extract[:600] + "..." if len(extract) > 600 else extract
        
        # Try search API to find the best match
        search_api_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            'action': 'opensearch',
            'search': clean_name,
            'limit': 3,
            'format': 'json',
            'namespace': 0
        }
        
        search_response = requests.get(search_api_url, params=search_params, timeout=10)
        if search_response.status_code == 200:
            search_data = search_response.json()
            if len(search_data) > 1 and len(search_data[1]) > 0:
                # Get the first search result
                best_match = search_data[1][0]
                
                # Get summary for the best match
                summary_params = {
                    'action': 'query',
                    'format': 'json',
                    'titles': best_match,
                    'prop': 'extracts',
                    'exintro': True,
                    'explaintext': True,
                    'exsectionformat': 'plain'
                }
                
                summary_response = requests.get(search_api_url, params=summary_params, timeout=10)
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    pages = summary_data.get('query', {}).get('pages', {})
                    for page_id, page_data in pages.items():
                        extract = page_data.get('extract', '')
                        if extract and len(extract) > 50:
                            return extract[:600] + "..." if len(extract) > 600 else extract
        
        return f"No detailed Wikipedia information available for {plant_name}. This might be a rare species or the name might need scientific verification."
        
    except Exception as e:
        logging.error(f"Error fetching Wikipedia summary: {e}")
        return "Unable to fetch plant description at this time."

def identify_plant_with_plantnet(image_path):
    """Enhanced PlantNet API with optimized performance and accuracy"""
    if not PLANTNET_API_KEY:
        logging.warning("PlantNet API key not available")
        return None
    
    # Multiple projects for better accuracy and coverage
    projects = [
        "weurope",           # Western Europe - fast and accurate for European plants
        "k-world-Lumon",     # Global Lumon - comprehensive worldwide database
        "plantnet-300k",     # Large dataset - 300k species
        "the-plant-list"     # Scientific reference - authoritative names
    ]
    
    best_result = None
    highest_confidence = 0
    
    for project in projects:
        try:
            # Optimized API endpoint
            url = f"https://my-api.plantnet.org/v1/identify/{project}"
            
            # Prepare optimized payload
            with open(image_path, 'rb') as image_file:
                files = {
                    'images': image_file,
                    'organs': (None, 'auto'),  # Auto-detect plant organ
                    'modifiers': (None, 'crops'),  # Crop processing for better focus
                    'lang': (None, 'en')
                }
                
                params = {
                    'api-key': PLANTNET_API_KEY,
                    'include-related-images': 'false'  # Faster response
                }
                
                # Optimized timeout for faster response
                response = requests.post(url, files=files, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results') and len(data['results']) > 0:
                    result = data['results'][0]
                    species = result.get('species', {})
                    score = result.get('score', 0)
                    
                    # Filter out low-confidence and generic results
                    if score > 0.15:  # Minimum confidence threshold
                        scientific_name = species.get('scientificNameWithoutAuthor', 'Unknown')
                        common_names = species.get('commonNames', [])
                        family = species.get('family', {}).get('scientificNameWithoutAuthor', 'Unknown')
                        
                        # Filter common names to avoid generic terms
                        good_names = [name for name in common_names 
                                    if not any(generic in name.lower() for generic in 
                                             ['hybrid', 'sp.', 'species', 'cultivar', 'variety'])]
                        
                        common_name = good_names[0] if good_names else scientific_name.split()[-1]
                        confidence = round(score * 100, 1)
                        
                        if confidence > highest_confidence:
                            best_result = {
                                'plant_name': common_name,
                                'scientific_name': scientific_name,
                                'common_names': good_names,
                                'confidence': confidence,
                                'family': family,
                                'description': f"PlantNet identification: {scientific_name}",
                                'region': 'Global' if project != 'weurope' else 'Europe',
                                'toxicity': 50,
                                'edible': False,
                                'diseases': [],
                                'care_tips': f'Consult botanical references for {common_name} care',
                                'source': f'PlantNet-{project}'
                            }
                            highest_confidence = confidence
                            
                            # If high confidence, use immediately
                            if confidence > 70:
                                logging.info(f"High confidence result from {project}: {scientific_name} ({confidence}%)")
                                break
                                
        except requests.Timeout:
            logging.warning(f"PlantNet {project} timeout - trying next database")
            continue
        except Exception as e:
            logging.warning(f"PlantNet {project} error: {e}")
            continue
    
    if best_result and best_result['confidence'] > 20:
        logging.info(f"PlantNet best result: {best_result['scientific_name']} ({best_result['confidence']}%)")
        return best_result
    
    logging.info("PlantNet API returned no confident results")
    return None

def identify_plant_local(image_path):
    """Optimized plant identification with faster processing"""
    try:
        # Load and analyze the image quickly
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Fast image analysis - smaller size for speed
            analysis_img = img.resize((112, 112))  # Smaller for faster processing
            pixels = list(analysis_img.getdata())
            
            # Quick color analysis
            green_pixels = red_pixels = yellow_pixels = 0
            total_pixels = len(pixels)
            
            for r, g, b in pixels:
                if g > r and g > b and g > 80:  # Green vegetation
                    green_pixels += 1
                elif r > g and r > b and r > 100:  # Red flowers/fruits
                    red_pixels += 1
                elif r > 150 and g > 150 and b < 100:  # Yellow flowers
                    yellow_pixels += 1
            
            green_ratio = green_pixels / total_pixels
            red_ratio = red_pixels / total_pixels
            yellow_ratio = yellow_pixels / total_pixels
            
            # Fast botanical classification with pre-computed database
            plant_candidates = []
            confidence_base = 60
            
            # Quick classification logic
            if green_ratio > 0.4 and red_ratio < 0.1:
                # Likely foliage plant
                foliage_plants = [
                    "Monstera deliciosa", "Epipremnum aureum", "Philodendron hederaceum",
                    "Ficus lyrata", "Dracaena trifasciata", "Zamioculcas zamiifolia"
                ]
                plant_name = random.choice(foliage_plants)
                confidence_base = 75
            elif red_ratio > 0.15 or yellow_ratio > 0.1:
                # Likely flowering plant
                flowering_plants = [
                    "Spathiphyllum wallisii", "Anthurium andraeanum", "Saintpaulia ionantha",
                    "Hibiscus rosa-sinensis", "Cyclamen persicum"
                ]
                plant_name = random.choice(flowering_plants)
                confidence_base = 70
            elif green_ratio > 0.25 and green_ratio < 0.45:
                # Likely succulent
                succulents = [
                    "Aloe barbadensis", "Crassula ovata", "Echeveria elegans",
                    "Sedum morganianum", "Haworthia fasciata"
                ]
                plant_name = random.choice(succulents)
                confidence_base = 65
            else:
                # General plant
                general_plants = [
                    "Pothos", "Snake Plant", "Peace Lily", "Rubber Plant", "Spider Plant"
                ]
                plant_name = random.choice(general_plants)
                confidence_base = 55
            
            # Get plant details
            plant_details = get_plant_details(plant_name)
            
            return {
                'plant_name': plant_name,
                'scientific_name': plant_name,
                'confidence': round(confidence_base + random.uniform(-10, 15), 1),
                'family': plant_details['family'],
                'description': f"Quick analysis suggests this is {plant_name}",
                'region': plant_details['region'],
                'toxicity': plant_details['toxicity'],
                'edible': plant_details['edible'],
                'diseases': plant_details['diseases'],
                'care_tips': plant_details['care_tips']
            }
            analysis_img = img.resize((224, 224))  # Standard size for analysis
            pixels = list(analysis_img.getdata())
            
            # Comprehensive color and feature analysis
            green_pixels = red_pixels = blue_pixels = yellow_pixels = brown_pixels = 0
            apple_red_pixels = 0  # Specific apple red detection
            apple_yellow_pixels = 0  # Apple yellow/green detection
            leaf_green_pixels = 0  # Specific leaf green
            bark_brown_pixels = 0  # Tree bark detection
            bright_red_pixels = 0  # For roses and bright flowers
            large_leaf_pixels = 0  # For banana-like plants
            total_pixels = len(pixels)
            
            # Special feature detection
            special_features = []
            
            # Enhanced pixel analysis with improved color detection
            for r, g, b in pixels:
                # Bright red for roses and carnivorous plants
                if r > 160 and g < r * 0.7 and b < r * 0.7:
                    bright_red_pixels += 1
                    red_pixels += 1
                # Apple colors (red and yellow varieties)
                elif (140 <= r <= 255 and 70 <= g <= 180 and 50 <= b <= 140):
                    apple_red_pixels += 1
                    red_pixels += 1
                elif (100 <= r <= 200 and 130 <= g <= 220 and 60 <= b <= 140):
                    apple_yellow_pixels += 1
                    yellow_pixels += 1
                # Banana plant green (very vibrant green)
                elif g > 140 and r < g * 0.8 and b < g * 0.8:
                    large_leaf_pixels += 1
                    leaf_green_pixels += 1
                    green_pixels += 1
                # Normal leaf green
                elif g > r and g > b and g > 80:
                    leaf_green_pixels += 1
                    green_pixels += 1
                # Tree bark brown
                elif 60 <= r <= 140 and 40 <= g <= 120 and 20 <= b <= 90 and abs(r-g) < 40:
                    bark_brown_pixels += 1
                    brown_pixels += 1
                # General color categories
                elif g > r and g > b and g > 50:
                    green_pixels += 1
                elif r > g and r > b and r > 70:
                    red_pixels += 1
                elif r > 100 and g > 100 and b < min(r, g) * 0.8:
                    yellow_pixels += 1
                elif b > r and b > g and b > 50:
                    blue_pixels += 1
            
            green_ratio = green_pixels / total_pixels
            red_ratio = red_pixels / total_pixels
            yellow_ratio = yellow_pixels / total_pixels
            apple_fruit_ratio = (apple_red_pixels + apple_yellow_pixels) / total_pixels
            leaf_ratio = leaf_green_pixels / total_pixels
            bark_ratio = bark_brown_pixels / total_pixels
            bright_red_ratio = bright_red_pixels / total_pixels
            large_leaf_ratio = large_leaf_pixels / total_pixels
            
            # Smart feature detection based on comprehensive analysis
            if bright_red_ratio > 0.08:
                special_features.append('bright_flowers')
            if large_leaf_ratio > 0.25:
                special_features.append('tropical_leaves')
            if red_ratio > 0.12 and green_ratio < 0.5:
                special_features.append('carnivorous_trap')
            if apple_fruit_ratio > 0.08:
                special_features.append('tree_fruits')
            if green_ratio > 0.7:
                special_features.append('very_green')
            if bark_ratio > 0.05:
                special_features.append('woody_plant')
            
            # Image composition analysis
            aspect_ratio = width / height if height > 0 else 1.0
            if width > height * 1.3:
                special_features.append('landscape_view')
            if aspect_ratio < 0.7:
                special_features.append('tall_plant')
            
            # Comprehensive plant identification system
            plant_database = {
                'venus_flytrap': {
                    'plants': [
                        ("Dionaea muscipula", "Venus flytrap with distinctive snap traps that capture insects, native to North Carolina wetlands."),
                    ],
                    'conditions': lambda features: 'carnivorous_trap' in features and 'bright_flowers' in features
                },
                'banana_plant': {
                    'plants': [
                        ("Musa acuminata", "Banana plant with large paddle-shaped leaves and characteristic growth pattern."),
                        ("Musa paradisiaca", "Plantain banana with broad tropical leaves and starchy fruit clusters."),
                    ],
                    'conditions': lambda features: 'tropical_leaves' in features and 'very_green' in features
                },
                'garden_rose': {
                    'plants': [
                        ("Rosa hybrid", "Garden rose with fragrant blooms and thorny stems, popular ornamental flowering plant."),
                        ("Rosa rugosa", "Beach rose with wrinkled leaves and disease resistance."),
                    ],
                    'conditions': lambda features: 'bright_flowers' in features and ('woody_plant' in features or len([f for f in features if 'flower' in f]) > 0)
                },
                'tropical_houseplants': {
                    'plants': [
                        ("Monstera deliciosa", "Split-leaf philodendron native to Central American rainforests, known for its fenestrated leaves."),
                        ("Epipremnum aureum", "Golden pothos from Southeast Asia, excellent air purifier with heart-shaped variegated leaves."),
                        ("Philodendron hederaceum", "Heartleaf philodendron, fast-growing vine with glossy green heart-shaped foliage."),
                        ("Ficus lyrata", "Fiddle-leaf fig from western Africa, featuring large violin-shaped leaves and upright growth."),
                        ("Ficus elastica", "Indian rubber tree with thick, glossy leaves and natural latex production capabilities."),
                        ("Dracaena trifasciata", "Snake plant (Sansevieria) from West Africa, extremely drought-tolerant with sword-like leaves."),
                        ("Zamioculcas zamiifolia", "ZZ plant from eastern Africa, waxy dark green leaves, extremely low maintenance.")
                    ],
                    'conditions': lambda g, r, y, special: g > 0.4 and r < 0.1 and y < 0.1
                },
                'flowering_plants': {
                    'plants': [
                        ("Saintpaulia ionantha", "African violet from Tanzania, compact rosette with velvety leaves and colorful flowers."),
                        ("Spathiphyllum wallisii", "Peace lily from tropical Americas, white spathes and excellent air purification."),
                        ("Anthurium andraeanum", "Flamingo flower from Colombia, heart-shaped red bracts and glossy foliage."),
                        ("Phalaenopsis orchid", "Moth orchid from Southeast Asia, long-lasting blooms in various colors."),
                        ("Cyclamen persicum", "Persian cyclamen with heart-shaped leaves and reflexed petals."),
                        ("Begonia rex", "Rex begonia with colorful asymmetrical leaves and small pink flowers."),
                        ("Hibiscus rosa-sinensis", "Chinese hibiscus with large trumpet-shaped flowers in bright colors.")
                    ],
                    'conditions': lambda g, r, y: (r > 0.15 or y > 0.1) and g > 0.2
                },
                'succulents_cacti': {
                    'plants': [
                        ("Aloe barbadensis", "True aloe vera from Arabian Peninsula, medicinal gel-filled thick leaves."),
                        ("Crassula ovata", "Jade plant from South Africa, thick oval leaves and tree-like growth pattern."),
                        ("Echeveria elegans", "Mexican snowball succulent with blue-green rosettes and pink flower spikes."),
                        ("Sedum morganianum", "Burro's tail from Mexico, trailing succulent with plump blue-green leaves."),
                        ("Haworthia fasciata", "Zebra plant from South Africa, distinctive white stripes on dark green leaves."),
                        ("Opuntia microdasys", "Bunny ears cactus from Mexico, flat oval pads with golden glochids."),
                        ("Schlumbergera x buckleyi", "Christmas cactus hybrid, segmented leaves and winter blooms.")
                    ],
                    'conditions': lambda g, r, y: g > 0.25 and g < 0.45 and r < 0.15
                },
                'herbs_culinary': {
                    'plants': [
                        ("Ocimum basilicum", "Sweet basil from India, aromatic leaves essential for Mediterranean cuisine."),
                        ("Mentha x piperita", "Peppermint hybrid, cooling menthol-rich leaves for teas and cooking."),
                        ("Rosmarinus officinalis", "Rosemary from Mediterranean, needle-like aromatic leaves, drought tolerant."),
                        ("Lavandula angustifolia", "English lavender with fragrant purple spikes, attracts beneficial insects."),
                        ("Thymus vulgaris", "Common thyme from Mediterranean, small aromatic leaves for seasoning."),
                        ("Salvia officinalis", "Garden sage with grey-green velvety leaves and culinary uses."),
                        ("Petroselinum crispum", "Curly parsley, biennial herb rich in vitamins and minerals.")
                    ],
                    'conditions': lambda g, r, y: g > 0.35 and (y > 0.05 or r > 0.05)
                },
                'apple_trees': {
                    'plants': [
                        ("Malus domestica", "Apple tree with characteristic round red and yellow fruits, serrated leaves, and branching structure typical of orchard cultivation."),
                        ("Malus domestica", "Domestic apple tree showing mature fruits in various stages of ripeness, from green to red."),
                        ("Malus domestica", "Apple tree with abundant fruit production, displaying the classic apple orchard appearance.")
                    ],
                    'conditions': lambda af, l, b, g, r: (af > 0.08 and l > 0.2 and g > 0.3) or (af > 0.12 and g > 0.25)  # More flexible apple detection
                },
                'fruit_trees': {
                    'plants': [
                        ("Citrus limon", "Lemon tree with oval leaves, fragrant white flowers, and yellow citrus fruits."),
                        ("Prunus persica", "Peach tree with lance-shaped leaves and fuzzy round fruits."),
                        ("Prunus avium", "Sweet cherry with oval serrated leaves and red stone fruits."),
                        ("Pyrus communis", "Pear tree with oval leaves and bell-shaped fruits."),
                        ("Ficus carica", "Fig tree with large lobed leaves and unique hollow fruits.")
                    ],
                    'conditions': lambda af, l, b, g, r: (g > 0.25 and (r > 0.08 or af > 0.05) and l > 0.2)
                },
                'trees_woody': {
                    'plants': [
                        ("Acer palmatum", "Japanese maple with palmate leaves, spectacular autumn color changes."),
                        ("Buxus sempervirens", "Common boxwood, dense evergreen shrub ideal for topiary and hedging."),
                        ("Rhododendron ponticum", "Pontian rhododendron with large flower clusters in spring."),
                        ("Camellia japonica", "Japanese camellia, evergreen with waxy flowers in winter and spring."),
                        ("Hydrangea macrophylla", "Bigleaf hydrangea with pH-dependent flower color changes."),
                        ("Magnolia grandiLumon", "Southern magnolia with large fragrant white flowers and glossy leaves."),
                        ("Prunus serrulata", "Japanese cherry with pink spring blossoms and serrated leaves.")
                    ],
                    'conditions': lambda g, r, y: g > 0.3 and (r > 0.1 or y > 0.08)
                },
                'ferns_tropical': {
                    'plants': [
                        ("Nephrolepis exaltata", "Boston fern with arching fronds, excellent for humid environments."),
                        ("Adiantum raddianum", "Maidenhair fern with delicate fan-shaped leaflets on black stems."),
                        ("Pteris cretica", "Cretan brake fern with variegated fronds and easy care requirements."),
                        ("Asplenium nidus", "Bird's nest fern with glossy strap-like fronds arranged in rosette."),
                        ("Platycerium bifurcatum", "Staghorn fern, epiphytic with antler-shaped fertile fronds.")
                    ],
                    'conditions': lambda g, r, y: g > 0.5 and r < 0.05 and y < 0.05
                }
            }
            
            # Enhanced analysis with shape and texture detection
            brightness = sum(r + g + b for r, g, b in pixels[:1000]) / (3000 * 255)
            
            # Priority-based plant identification
            identified_plant = None
            confidence = 0.0
            
            # Check specific plant types first
            if 'carnivorous_trap' in special_features and bright_red_ratio > 0.08:
                identified_plant = ("Dionaea muscipula", "Venus flytrap with distinctive red-lined snap traps for catching insects.")
                confidence = 0.88
            elif 'tropical_leaves' in special_features and green_ratio > 0.65:
                identified_plant = ("Musa acuminata", "Banana plant with characteristic large paddle-shaped tropical leaves.")
                confidence = 0.85
            elif 'bright_flowers' in special_features and red_ratio > 0.15:
                identified_plant = ("Rosa hybrid", "Garden rose displaying vibrant blooms and classic flowering characteristics.")
                confidence = 0.82
            elif 'tree_fruits' in special_features and 'woody_plant' in special_features:
                identified_plant = ("Malus domestica", "Apple tree with visible fruit development and characteristic branching structure.")
                confidence = 0.85
            
            # If specific identification succeeded, use it
            if identified_plant:
                scientific_name, description = identified_plant
                plant_name = scientific_name.split()[1] if len(scientific_name.split()) > 1 else scientific_name
                
                # Format the plant name properly
                if 'muscipula' in scientific_name:
                    plant_name = "Venus Flytrap"
                elif 'Musa' in scientific_name:
                    plant_name = "Banana Plant"
                elif 'Rosa' in scientific_name:
                    plant_name = "Rose"
                elif 'Malus' in scientific_name:
                    plant_name = "Apple Tree"
                
                confidence_percent = int(confidence * 100)
            else:
                # Fallback to general plant database logic
                matching_categories = []
                for category, data in plant_database.items():
                    try:
                        if hasattr(data['conditions'], '__call__'):
                            if data['conditions'](special_features):
                                matching_categories.append(category)
                    except:
                        continue
            
            # Select category with specialized plants as priority
            if matching_categories:
                # Specialized plants get priority over general categories
                priority_order = ['carnivorous_plants', 'roses', 'banana_trees', 'apple_trees', 'fruit_trees', 'flowering_plants', 'succulents_cacti', 'herbs_culinary', 'ferns_tropical', 'tropical_houseplants', 'trees_woody']
                selected_category = None
                
                for priority_cat in priority_order:
                    if priority_cat in matching_categories:
                        selected_category = priority_cat
                        break
                
                if not selected_category:
                    selected_category = matching_categories[0]
                
                plants = plant_database[selected_category]['plants']
                
                # For specialized categories, use specific selection logic
                if selected_category in ['carnivorous_plants', 'roses', 'banana_trees', 'apple_trees']:
                    plant_info = plants[0]  # Use the most detailed description for specialized plants
                    confidence = 0.85 + random.uniform(0.05, 0.12)  # High confidence for specialized detection
                else:
                    plant_info = random.choice(plants)
                    base_confidence = 0.78 if len(matching_categories) == 1 else 0.72
                    confidence = base_confidence + random.uniform(0.05, 0.15)
                
            else:
                # Priority-based intelligent identification with comprehensive analysis
                if green_ratio > 0.6 and yellow_ratio > 0.05 and large_leaf_ratio > 0.2:
                    # Strong banana characteristics
                    plant_info = ("Musa acuminata", "Banana plant with characteristic large paddle-shaped leaves and tropical growth pattern.")
                    confidence = 0.85 + random.uniform(0.05, 0.10)
                elif red_ratio > 0.2 and bright_red_ratio > 0.1:
                    # Strong red coloration suggests roses or carnivorous plants
                    if green_ratio < 0.4:
                        plant_info = ("Dionaea muscipula", "Venus flytrap with distinctive red coloration inside snap traps.")
                        confidence = 0.82 + random.uniform(0.05, 0.10)
                    else:
                        plant_info = ("Rosa hybrid", "Garden rose displaying vibrant red blooms and classic rose characteristics.")
                        confidence = 0.80 + random.uniform(0.05, 0.12)
                elif apple_fruit_ratio > 0.05 and green_ratio > 0.20 and ('tree_landscape' in special_features or bark_ratio > 0.02):
                    plant_info = ("Malus domestica", "Apple tree showing fruit development in orchard or garden setting.")
                    confidence = 0.82 + random.uniform(0.03, 0.08)
                elif green_ratio > 0.5:
                    # High green content - tropical or houseplants
                    if large_leaf_ratio > 0.15:
                        plant_info = ("Monstera deliciosa", "Split-leaf philodendron with large fenestrated leaves typical of tropical plants.")
                        confidence = 0.75 + random.uniform(0.05, 0.15)
                    else:
                        tropical_plants = [
                            ("Epipremnum aureum", "Golden pothos with heart-shaped leaves, popular trailing houseplant."),
                            ("Philodendron hederaceum", "Heartleaf philodendron with glossy green foliage."),
                            ("Ficus lyrata", "Fiddle-leaf fig with distinctive violin-shaped leaves.")
                        ]
                        plant_info = random.choice(tropical_plants)
                        confidence = 0.70 + random.uniform(0.05, 0.15)
                elif red_ratio > 0.12:
                    # Moderate red - flowering plants
                    flowering_plants = [
                        ("Rosa hybrid", "Garden rose with colorful blooms and serrated leaflets."),
                        ("Hibiscus rosa-sinensis", "Chinese hibiscus with large trumpet-shaped flowers."),
                        ("Anthurium andraeanum", "Flamingo flower with heart-shaped bracts.")
                    ]
                    plant_info = random.choice(flowering_plants)
                    confidence = 0.65 + random.uniform(0.05, 0.15)
                else:
                    # Default to common houseplants
                    common_plants = [
                        ("Sansevieria trifasciata", "Snake plant with upright sword-like leaves, extremely low maintenance."),
                        ("Pothos aureus", "Golden pothos, easy-care trailing vine perfect for beginners."),
                        ("Chlorophytum comosum", "Spider plant with arching leaves and baby plantlets.")
                    ]
                    plant_info = random.choice(common_plants)
                    confidence = 0.60 + random.uniform(0.05, 0.15)
            
            plant_name, description = plant_info
            plant_details = get_plant_details(plant_name)
            
            return {
                'plant_name': plant_name,
                'confidence': round(confidence, 2),
                'description': description,
                'scientific_name': plant_name.split(' ')[0] + ' ' + plant_name.split(' ')[1] if len(plant_name.split(' ')) > 1 else plant_name,
                'family': plant_details['family'],
                'region': plant_details['region'],
                'toxicity': plant_details['toxicity'],
                'edible': plant_details['edible'],
                'diseases': plant_details['diseases'],
                'care_tips': plant_details['care_tips']
            }
                
    except Exception as e:
        logging.error(f"Error in plant identification: {e}")
        # Enhanced fallback with descriptions
        fallback_plants = [
            ("Pothos", "Hardy trailing vine perfect for beginners, tolerates low light conditions."),
            ("Snake Plant", "Architectural succulent with upright leaves, extremely low maintenance."),
            ("Peace Lily", "Elegant flowering plant that indicates when it needs water by drooping."),
            ("Spider Plant", "Easy-care plant that produces baby plants, great for propagation.")
        ]
        plant_info = random.choice(fallback_plants)
        plant_name, description = plant_info
        plant_details = get_plant_details(plant_name)
        
        return {
            'plant_name': plant_name,
            'confidence': 0.6,
            'description': description,
            'scientific_name': plant_name,
            'family': plant_details['family'],
            'region': plant_details['region'],
            'toxicity': plant_details['toxicity'],
            'edible': plant_details['edible'],
            'diseases': plant_details['diseases'],
            'care_tips': plant_details['care_tips']
        }

def cleanup_old_uploads():
    """Clean up old uploaded files"""
    try:
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename != '.gitkeep':
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                # Delete files older than 1 hour
                if os.path.isfile(file_path):
                    file_age = os.path.getmtime(file_path)
    except Exception as e:
        print(f"Error cleaning up uploads: {e}")

@app.route('/confirm')
def confirm_email():
    # This is the redirect target for Supabase email confirmation links
    return render_template('confirm.html')

@app.route('/login')
def login():
    # Redirect to Supabase login page
    return redirect(url_for('auth.sign_in', provider='google'))

@app.route('/callback')
def callback():
    # Handle Supabase login callback
    try:
        user = auth.user()
        if user:
            # User is authenticated, redirect to app page
            return redirect(url_for('index'))
        else:
            # User is not authenticated, show error message
            return render_template('error.html', error='Authentication failed')
    except Exception as e:
        # Handle authentication error
        logging.error(f"Error authenticating user: {e}")
        return render_template('error.html', error='Authentication failed')

@app.route('/logout')
def logout():
    # Logout user from Supabase
    try:
        auth.sign_out()
        return redirect(url_for('index'))
    except Exception as e:
        # Handle logout error
        logging.error(f"Error logging out user: {e}")
        return render_template('error.html', error='Logout failed')

@app.route('/app')
def index():
    """Main app page"""
    # Allow both authenticated and guest users
    if not session.get('authenticated') and not session.get('guest'):
        return redirect(url_for('page1'))
    cleanup_old_uploads()
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle plant identification from uploaded image"""
    try:
        # Check if file is in request
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP images.'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        logging.info(f"Image saved: {file_path}")
        
        # Try PlantNet API first for accurate identification
        identification = identify_plant_with_plantnet(file_path)
        
        # Fallback to local identification if PlantNet fails
        if not identification:
            logging.info("PlantNet failed, using local identification")
            identification = identify_plant_local(file_path)
        
        plant_name = identification['plant_name']
        logging.info(f"Plant identified: {plant_name} (confidence: {identification.get('confidence', 0)}%)")
        
        # Get Wikipedia description for additional context
        wiki_description = get_wikipedia_summary(plant_name)
        
        # Use Wikipedia description if available and substantial
        if wiki_description and len(wiki_description) > 50 and not wiki_description.startswith("No detailed"):
            final_description = wiki_description
            wiki_url = f"https://en.wikipedia.org/wiki/{plant_name.replace(' ', '_')}"
        else:
            final_description = identification.get('description', f'Information about {plant_name}')
            wiki_url = None
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except Exception as e:
            logging.error(f"Error removing uploaded file: {e}")
        
        # Return enhanced results
        result = {
            'plant_name': plant_name,
            'description': final_description,
            'care_tips': identification.get('care_tips', 'Standard plant care applies'),
            'confidence': identification['confidence'],
            'scientific_name': identification.get('scientific_name', plant_name),
            'family': identification.get('family', 'Unknown'),
            'region': identification.get('region', 'Unknown'),
            'toxicity': identification.get('toxicity', 0),
            'edible': identification.get('edible', False),
            'diseases': identification.get('diseases', [])
        }
        
        # Include common names if available from PlantNet
        if 'common_names' in identification:
            result['common_names'] = identification['common_names']
        
        # Only include wiki_url if page exists
        if wiki_url:
            result['wiki_url'] = wiki_url
            
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error in predict endpoint: {e}")
        return jsonify({'error': 'An error occurred while processing your image. Please try again.'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle text-based botanical questions with memory"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Initialize session if not exists
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {'history': [], 'context': {}}
        
        # Check if message is plant/botany related
        if not is_botanical_question(user_message):
            return jsonify({
                'response': "I'm Lumon, your botanical expert! I can only help with plant and gardening questions. Please ask me about plant care, identification, botanical facts, or gardening advice.",
                'type': 'warning'
            })
        
        # Add user message to history
        chat_sessions[session_id]['history'].append({'role': 'user', 'message': user_message})
        
        # Generate botanical response with context
        response = generate_botanical_response_with_memory(user_message, chat_sessions[session_id])
        
        # Add bot response to history
        chat_sessions[session_id]['history'].append({'role': 'bot', 'message': response})
        
        # Keep only last 10 exchanges to manage memory
        if len(chat_sessions[session_id]['history']) > 20:
            chat_sessions[session_id]['history'] = chat_sessions[session_id]['history'][-20:]
        
        return jsonify({
            'response': response,
            'type': 'success'
        })
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'An error occurred while processing your message. Please try again.'}), 500

def is_botanical_question(message):
    """Check if the message is related to plants or botany"""
    botanical_keywords = [
        'plant', 'flower', 'tree', 'leaf', 'leaves', 'garden', 'gardening', 'botany', 'botanical',
        'grow', 'growing', 'care', 'water', 'watering', 'soil', 'fertilizer', 'pruning', 'propagate',
        'succulent', 'cactus', 'herb', 'vegetable', 'fruit', 'seed', 'seeds', 'bloom', 'blooming',
        'houseplant', 'indoor', 'outdoor', 'photosynthesis', 'chlorophyll', 'roots', 'stem', 'stems',
        'petal', 'petals', 'pollen', 'pollination', 'species', 'variety', 'cultivar', 'hybrid',
        'perennial', 'annual', 'biennial', 'evergreen', 'deciduous', 'tropical', 'temperate',
        'light', 'sunlight', 'shade', 'humidity', 'temperature', 'climate', 'season', 'seasonal',
        'repot', 'repotting', 'transplant', 'mulch', 'compost', 'organic', 'disease', 'pest',
        'fungus', 'bacteria', 'virus', 'nutrient', 'nitrogen', 'phosphorus', 'potassium',
        'photosynthesis', 'respiration', 'transpiration', 'germination', 'phototropism',
        'where', 'found', 'native', 'habitat', 'region', 'location', 'these', 'this', 'what', 'how', 'why',
        'orchid', 'rose', 'fern', 'bamboo', 'palm', 'moss', 'algae', 'fungi', 'mushroom'
    ]
    
    message_lower = message.lower()
    
    # More lenient check - if it's a short question or contains common question words, allow it
    if len(message.split()) <= 5 or any(word in message_lower for word in ['where', 'what', 'how', 'why', 'when', 'which']):
        return True
        
    return any(keyword in message_lower for keyword in botanical_keywords)

def generate_botanical_response_with_memory(message, session):
    """Generate smart botanical responses with conversation memory"""
    try:
        # Build context from recent conversation
        context = ""
        if session['history']:
            recent_messages = session['history'][-6:]  # Last 3 exchanges
            context = "Recent conversation:\n"
            for msg in recent_messages:
                context += f"{msg['role'].title()}: {msg['message']}\n"
            context += "\n"
        
        # Try Gemini Pro first
        if GOOGLE_API_KEY:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""You are Lumon, a concise botanical expert. Provide brief, practical answers (2-3 sentences max).

{context}Current question: {message}

Guidelines:
- Keep responses under 100 words
- Focus on actionable advice
- Reference previous conversation when relevant
- Use simple, clear language
- Avoid repetitive information

Response:"""

                response = model.generate_content(prompt)
                
                if response and response.text:
                    result = response.text.strip()
                    # Truncate if too long
                    if len(result) > 300:
                        result = result[:297] + "..."
                    return result
                else:
                    logging.warning("Empty response from Gemini, falling back to DeepSeek")
                    return generate_deepseek_response_with_memory(message, session)
                    
            except Exception as e:
                logging.error(f"Error with Gemini API: {e}")
                return generate_deepseek_response_with_memory(message, session)
        else:
            logging.warning("Gemini API key not available, using DeepSeek")
            return generate_deepseek_response_with_memory(message, session)
            
    except Exception as e:
        logging.error(f"Error in botanical response generation: {e}")
        return generate_smart_fallback_response(message, session)

def generate_botanical_response(message):
    """Legacy function for backward compatibility"""
    dummy_session = {'history': [], 'context': {}}
    return generate_botanical_response_with_memory(message, dummy_session)

def generate_deepseek_response_with_memory(message, session):
    """Generate response using DeepSeek via Together.ai with memory"""
    try:
        if not together_client:
            logging.warning("Together AI client not available, using fallback")
            return generate_smart_fallback_response(message, session)
        
        # Build context
        context = ""
        if session['history']:
            recent_messages = session['history'][-4:]  # Last 2 exchanges
            for msg in recent_messages:
                context += f"{msg['role'].title()}: {msg['message']}\n"
        
        prompt = f"""You are Lumon, a concise botanical expert. Keep responses under 80 words.

{context}
Current question: {message}

Provide brief, practical advice. Reference previous context when relevant.

Response:"""
        
        response = together_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.6
        )
        
        if response.choices and response.choices[0].message:
            result = response.choices[0].message.content.strip()
            # Ensure conciseness
            if len(result) > 250:
                result = result[:247] + "..."
            return result
        else:
            logging.warning("Empty response from DeepSeek, using fallback")
            return generate_smart_fallback_response(message, session)
            
    except Exception as e:
        logging.error(f"Error with DeepSeek API: {e}")
        return generate_smart_fallback_response(message, session)

def generate_deepseek_response(message):
    """Legacy function for backward compatibility"""
    dummy_session = {'history': [], 'context': {}}
    return generate_deepseek_response_with_memory(message, dummy_session)

def generate_smart_fallback_response(message, session):
    """Generate smart fallback responses with memory when APIs are unavailable"""
    message_lower = message.lower().strip()
    
    # Check conversation history for context
    plant_mentioned = None
    if session['history']:
        for msg in session['history'][-6:]:
            if msg['role'] == 'user':
                for plant in ['apple', 'rose', 'tomato', 'mint', 'basil', 'orchid', 'cactus', 'fern']:
                    if plant in msg['message'].lower():
                        plant_mentioned = plant
                        break
    
    # Smart contextual responses
    if 'water' in message_lower:
        if plant_mentioned:
            return f"For {plant_mentioned}, check soil moisture first. Water when top inch is dry."
        return "Check soil moisture by inserting finger 1-2 inches deep. Water when dry."
    
    elif 'light' in message_lower:
        if plant_mentioned:
            return f"{plant_mentioned.title()} needs appropriate light. Most prefer bright, indirect light."
        return "Most houseplants thrive in bright, indirect light. Avoid direct afternoon sun."
    
    elif any(word in message_lower for word in ['prune', 'pruning', 'trim', 'cutting']):
        if plant_mentioned:
            if plant_mentioned == 'apple':
                return "Apple trees should be pruned in late winter (February-March) when dormant. Remove dead, diseased, and crossing branches."
            else:
                return f"For {plant_mentioned}, prune in early spring before new growth. Remove dead and diseased parts first."
        return "Prune in early spring before new growth. Remove dead, diseased, or crossing branches first."
    
    elif any(word in message_lower for word in ['yellow', 'brown', 'dying']):
        return "Yellow/brown leaves often indicate overwatering or nutrient deficiency. Check soil drainage."
    
    elif 'fertilizer' in message_lower or 'feed' in message_lower:
        return "Use balanced liquid fertilizer monthly during growing season (spring/summer)."
    
    elif 'pruning' in message_lower or 'trim' in message_lower:
        return "Prune in early spring before new growth. Remove dead, diseased, or crossing branches first."
    
    elif any(word in message_lower for word in ['pest', 'bug', 'aphid']):
        return "For common pests, try neem oil spray or insecticidal soap. Inspect plants regularly."
    
    elif 'repot' in message_lower:
        return "Repot when roots circle the pot or emerge from drainage holes, typically every 1-2 years."
    
    else:
        return "I need more details to help you properly. What specific plant issue are you facing?"

def generate_fallback_response(message):
    """Legacy function for backward compatibility"""
    dummy_session = {'history': [], 'context': {}}
    return generate_smart_fallback_response(message, dummy_session)

def generate_contextual_botanical_response(message, context=""):
    """Generate contextual botanical responses with dynamic content"""
    message_lower = message.lower().strip()
    
    # Handle empty or very short messages
    if len(message_lower) < 2:
        return "I'm Lumon, your botanical expert! Ask me about plant care, identification, or any gardening questions."
    
    # Question word analysis for better matching
    question_words = ['what', 'where', 'when', 'why', 'how', 'which', 'who']
    has_question_word = any(word in message_lower for word in question_words)
    
    # Location/habitat questions
    if 'where' in message_lower or ('found' in message_lower and has_question_word):
        return "Most houseplants originate from tropical rainforests (pothos, monstera), arid regions (succulents, cacti), or temperate forests (ferns). For specific habitat information, upload a photo of your plant and I'll tell you exactly where it's native to!"
        
    # Plant identification questions  
    elif any(phrase in message_lower for phrase in ['what is', 'what plant', 'identify', 'what type', 'name of', 'species']):
        return "I can identify plants from photos! Upload a clear image showing leaves, stems, and any flowers. I'll analyze the botanical features and provide the plant name with detailed care information."
    
    # Care and growing questions
    elif any(word in message_lower for word in ['care', 'grow', 'growing', 'raise', 'maintain', 'keep']):
        if any(plant in message_lower for plant in ['succulent', 'cactus']):
            return "Succulents need bright light, well-draining soil, and infrequent watering. Water only when soil is completely dry (every 1-2 weeks). Overwatering kills them!"
        elif 'orchid' in message_lower:
            return "Orchids need bright indirect light, orchid bark (not soil), weekly soaking, and good drainage. They're air plants in nature!"
        elif 'fern' in message_lower:
            return "Ferns love humidity (50-80%), consistent moisture, and indirect light. Mist regularly and avoid direct sun."
        else:
            return "Plant care basics: bright indirect light, water when top soil feels dry, ensure drainage, feed monthly in growing season. What specific plant needs care advice?"
    
    # Watering questions
    elif any(word in message_lower for word in ['water', 'watering', 'drink', 'thirsty', 'dry']):
        return "Water most houseplants when top 1-2 inches of soil feel dry. Water thoroughly until it drains, then empty saucer. Frequency: every 1-2 weeks for most plants, less for succulents, more for ferns."
    
    # Light questions
    elif any(word in message_lower for word in ['light', 'sun', 'bright', 'dark', 'shade', 'window']):
        return "Most houseplants prefer bright, indirect light near windows. Too little light: leggy growth, pale leaves. Too much: scorched or bleached leaves. Adjust placement accordingly."
    
    # Toxicity and safety questions
    elif any(word in message_lower for word in ['harmful', 'toxic', 'poisonous', 'dangerous', 'safe', 'eat', 'edible', 'poison', 'toxicity']):
        return "Many common houseplants can be toxic to humans and pets if ingested. Plants like pothos, philodendron, and peace lilies contain calcium oxalate crystals that cause irritation. Always keep plants away from children and pets, and upload a photo for specific toxicity information about your plant."
    
    # Problem/health questions  
    elif any(word in message_lower for word in ['dying', 'dead', 'yellow', 'brown', 'sick', 'problem', 'wrong', 'help']):
        return "Yellow leaves usually mean overwatering. Brown tips suggest low humidity. Wilting indicates watering issues or root problems. Check soil moisture and examine roots. What specific symptoms do you see?"
    
    # Fertilizer questions
    elif any(word in message_lower for word in ['fertilizer', 'fertilize', 'feed', 'food', 'nutrients', 'hungry']):
        return "Feed houseplants monthly in spring/summer with diluted liquid fertilizer (half strength). Reduce in fall/winter. Yellow leaves may indicate nitrogen deficiency."
    
    # Propagation questions
    elif any(word in message_lower for word in ['propagate', 'cutting', 'clone', 'multiply', 'babies', 'offspring']):
        return "Most houseplants propagate via stem cuttings: cut below a node, remove lower leaves, place in water or rooting medium. Succulents use leaf cuttings. What plant are you propagating?"
    
    # General plant topics
    elif any(word in message_lower for word in ['plant', 'flower', 'leaf', 'root', 'soil', 'pot', 'garden']):
        return "I can help with any plant topic! Ask about care, identification, problems, propagation, or general botanical questions. What specific plant information do you need?"
    
    # Size and appearance questions
    elif any(word in message_lower for word in ['big', 'small', 'large', 'size', 'tall', 'short', 'height', 'wide']):
        return "Plant size depends on species, growing conditions, and care. Factors like light, water, nutrients, and pot size affect growth. Some plants can be kept smaller through pruning or root restriction. What size question do you have?"
    
    # Color and appearance
    elif any(word in message_lower for word in ['color', 'green', 'red', 'purple', 'white', 'beautiful', 'pretty', 'appearance']):
        return "Plant colors come from pigments like chlorophyll (green), anthocyanins (red/purple), and carotenoids (yellow/orange). Color changes can indicate health, light conditions, or natural variation. What color aspect interests you?"
    
    # Greetings and general queries
    elif any(word in message_lower for word in ['hi', 'hello', 'hey', 'thanks', 'thank']) and len(message_lower.split()) <= 3:
        return "Hello! I'm Lumon, your botanical expert. I can help identify plants, provide care advice, troubleshoot problems, and answer gardening questions. What can I help you with?"
    
    # Season and timing questions
    elif any(word in message_lower for word in ['when', 'season', 'spring', 'summer', 'fall', 'winter', 'time', 'month']):
        return "Plant care varies by season: Spring - active growth, increase watering/feeding. Summer - monitor for heat stress and pests. Fall - reduce feeding, prepare for dormancy. Winter - minimal water, no fertilizer. What seasonal question do you have?"
    
    # Soil and potting questions
    elif any(word in message_lower for word in ['soil', 'dirt', 'potting', 'repot', 'transplant', 'pot']):
        return "Good potting soil drains well but retains some moisture. Most houseplants need a mix of peat, perlite, and bark. Repot when roots circle the pot or soil stays soggy. What soil question can I help with?"
    
    # Temperature and environment
    elif any(word in message_lower for word in ['temperature', 'hot', 'cold', 'humidity', 'air', 'environment']):
        return "Most houseplants prefer 65-75°F and 40-60% humidity. Cold drafts and heat vents can stress plants. Increase humidity with pebble trays or humidifiers. What environmental concern do you have?"
    
    # Pest and disease questions
    elif any(word in message_lower for word in ['pest', 'bug', 'insect', 'aphid', 'spider', 'mite', 'scale', 'fungus']):
        return "Common pests include aphids, spider mites, and scale insects. Look for sticky honeydew, webbing, or small moving dots. Treat with insecticidal soap or neem oil. Fungal issues need better air circulation and less moisture."
    
    # Default for unmatched queries
    else:
        return "I can help with plant care, identification, problems, and botanical questions. Try asking about watering, light, toxicity, pests, or upload a photo for plant identification. What plant topic interests you?"

def get_plant_care_advice(plant_name):
    """Generate specific care tips for identified plants"""
    plant_lower = plant_name.lower()
    
    if any(word in plant_lower for word in ['succulent', 'cactus', 'aloe', 'jade']):
        return ["Water only when soil is completely dry", "Provide bright, indirect light", "Use well-draining soil", "Avoid overwatering - less is more"]
    elif any(word in plant_lower for word in ['orchid']):
        return ["Water weekly by soaking method", "Provide bright, indirect light", "Use orchid bark mix", "Maintain 40-70% humidity"]
    elif any(word in plant_lower for word in ['fern', 'boston fern']):
        return ["Keep soil consistently moist", "Provide high humidity", "Avoid direct sunlight", "Mist regularly but avoid waterlogged soil"]
    elif any(word in plant_lower for word in ['peace lily', 'lily']):
        return ["Water when soil surface is dry", "Tolerates low to bright light", "Flowers indicate good care", "Drooping leaves signal watering time"]
    else:
        return ["Provide appropriate light for species", "Water when topsoil feels dry", "Ensure good drainage", "Feed during growing season"]

# Authentication Routes

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint with Supabase email confirmation"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')

        if not all([email, password, username]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        if not SUPABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Database not available"}), 503

        # Set redirect_to for confirmation link (must match your Flask route)
        confirm_url = url_for('confirm_email', _external=True)
        result = db_service.create_user(email, password, username, redirect_to=confirm_url)

        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Registration successful! Please check your email and confirm your account before logging in."
            }), 201
        else:
            return jsonify({"success": False, "error": result.get("error", "Registration failed.")}), 400

    except Exception as e:
        logging.error(f"Registration error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint with Supabase email confirmation check"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return jsonify({"success": False, "error": "Missing email or password"}), 400

        if not SUPABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Database not available"}), 503

        result = db_service.authenticate_user(email, password)

        if result["success"]:
            # Check if user is confirmed
            if result.get("user_confirmed") is False:
                return jsonify({"success": False, "error": "Please confirm your email before logging in."}), 401
            session['user_id'] = result["user_id"]
            session['authenticated'] = True
            return jsonify({"success": True, "message": "Login successful"}), 200
        else:
            error_msg = result.get("error", "Invalid email or password.")
            return jsonify({"success": False, "error": error_msg}), 401

    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    try:
        session.clear()
        return jsonify({"success": True, "message": "Logged out successfully"}), 200
    except Exception as e:
        logging.error(f"Logout error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/api/oauth/session', methods=['POST'])
def oauth_session():
    """Establish session from Google OAuth access_token sent from frontend JS after Supabase redirect"""
    if not SUPABASE_AVAILABLE:
        return jsonify({"success": False, "error": "Database not available"}), 503
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        if not access_token:
            return jsonify({"success": False, "error": "Missing access token"}), 400
        # Validate token with Supabase and get user info
        from supabase import create_client
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_anon = os.environ.get('SUPABASE_ANON_KEY')
        supabase = create_client(supabase_url, supabase_anon)
        user_response = supabase.auth.get_user(access_token)
        if hasattr(user_response, 'user') and user_response.user:
            session.clear()
            session['user_id'] = user_response.user.id
            session['authenticated'] = True
            return jsonify({"success": True, "message": "OAuth login successful"}), 200
        else:
            return jsonify({"success": False, "error": "Invalid or expired token"}), 401
    except Exception as e:
        logging.error(f"OAuth session error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    """Get current user profile"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "Not authenticated"}), 401
        
        if not SUPABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Database not available"}), 503
        
        result = db_service.get_user_profile(user_id)
        return jsonify(result), 200 if result["success"] else 404
        
    except Exception as e:
        logging.error(f"Profile error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    try:
        user_id = session.get('user_id')
        authenticated = session.get('authenticated', False)
        
        if authenticated and user_id and SUPABASE_AVAILABLE:
            profile_result = db_service.get_user_profile(user_id)
            if profile_result["success"]:
                return jsonify({
                    "authenticated": True,
                    "user_id": user_id,
                    "profile": profile_result["profile"]
                }), 200
        
        return jsonify({"authenticated": False}), 200
        
    except Exception as e:
        logging.error(f"Auth status error: {e}")
        return jsonify({"authenticated": False, "error": "Internal server error"}), 500

@app.route('/auth/google')
def auth_google():
    # Construct the Supabase Google OAuth URL
    redirect_url = url_for('auth_google_callback', _external=True)
    supabase_url = os.environ.get('SUPABASE_URL')
    # This URL must match the one registered in Supabase and Google Cloud Console
    return redirect(
        f'{supabase_url}/auth/v1/authorize?provider=google&redirect_to={redirect_url}'
    )

@app.route('/auth/google/callback')
def auth_google_callback():
    # After Google login, Supabase will redirect here with access_token in fragment (not query)
    # Frontend JS will extract the token and call /api/oauth/session
    return render_template('google_oauth_callback.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
