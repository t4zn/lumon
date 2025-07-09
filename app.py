import os
import logging
import uuid
import requests
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, make_response
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
import difflib

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
app.secret_key = 'lumon-very-secret-key-2024'  # Fixed secret key for session persistence
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

# Log PlantNet API key status at startup
logging.info(f"PLANTNET_API_KEY loaded: {bool(PLANTNET_API_KEY)}")

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

def get_wikipedia_summary(plant_name, scientific_name=None):
    """Fetch plant description from Wikipedia API, prefer scientific name."""
    try:
        # Try scientific name first
        if scientific_name:
            clean_name = scientific_name.strip()
            search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_name.replace(' ', '_')}"
            response = requests.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                extract = data.get('extract', '')
                if extract and len(extract) > 50:
                    return extract[:600] + "..." if len(extract) > 600 else extract
        # Fallback to common name
        clean_name = plant_name.strip()
        search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_name.replace(' ', '_')}"
        response = requests.get(search_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            extract = data.get('extract', '')
            if extract and len(extract) > 50:
                return extract[:600] + "..." if len(extract) > 600 else extract
        return None
    except Exception as e:
        logging.error(f"Error fetching Wikipedia summary: {e}")
        return None

def extract_region_from_text(text):
    """Try to extract native region from Wikipedia or PlantNet text."""
    if not text:
        return None
    # Look for phrases like 'native to ...', 'indigenous to ...', 'originates from ...'
    match = re.search(r'(native to|indigenous to|originates from|found in|distributed in|occurs in) ([A-Z][a-zA-Z,\-\s]+)[\.,]', text, re.IGNORECASE)
    if match:
        region = match.group(2).strip()
        # Only return the first word/phrase
        return region.split(',')[0].strip()
    return None

def extract_season_from_text(text):
    """Try to extract the season or period when the plant is commonly grown from Wikipedia or PlantNet text."""
    if not text:
        return None
    # Look for phrases like 'commonly grown in ...', 'cultivated in ...', 'planted in ...', 'sown in ...', 'grows in ...', 'harvested in ...', 'season: ...', 'flowering in ...'
    match = re.search(r'(commonly grown in|cultivated in|planted in|sown in|grows in|harvested in|season:?|flowering in) ([A-Za-z,\-\s]+)[\.,]', text, re.IGNORECASE)
    if match:
        season = match.group(2).strip()
        return season.split(',')[0].strip()
    # Try to find common season words
    for season_word in ['spring', 'summer', 'autumn', 'fall', 'winter', 'rainy', 'dry']:
        if season_word in text.lower():
            return season_word.capitalize()
    return None

def get_plantnet_species_info(scientific_name):
    """Fetch and parse PlantNet species data page for region/season/edibility."""
    try:
        base_url = "https://identify.plantnet.org/prosea/species/"
        sci_url = scientific_name.replace(' ', '%20')
        url = f"{base_url}{sci_url}/data"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None, None, None
        html = resp.text
        # Edibility
        edible = None
        edible_match = re.search(r'Edible\s*[:\-]?\s*(Yes|No)', html, re.IGNORECASE)
        if edible_match:
            edible = edible_match.group(1).capitalize()
        # Region
        region = None
        region_match = re.search(r'(Native to|Indigenous to|Originates from|Found in|Distributed in|Occurs in) ([A-Z][a-zA-Z,\-\s]+)[\.,]', html, re.IGNORECASE)
        if region_match:
            region = region_match.group(2).strip().split(',')[0]
        # Season (look for growing/cultivation/planting/sowing period)
        season = None
        season_match = re.search(r'(commonly grown in|cultivated in|planted in|sown in|grows in|harvested in|season:?|flowering in) ([A-Za-z,\-\s]+)[\.,]', html, re.IGNORECASE)
        if season_match:
            season = season_match.group(2).strip().split(',')[0]
        for season_word in ['spring', 'summer', 'autumn', 'fall', 'winter', 'rainy', 'dry']:
            if season_word in html.lower():
                season = season_word.capitalize()
        return edible, region, season
    except Exception as e:
        logging.warning(f"PlantNet species info fetch failed: {e}")
        return None, None, None

def identify_plant_with_plantnet(image_path):
    """PlantNet API v2 - use only the official /v2/identify/all endpoint for best compatibility"""
    if not PLANTNET_API_KEY:
        logging.warning("PlantNet API key not available")
        return None
    url = "https://my-api.plantnet.org/v2/identify/all"
    best_result = None
    highest_confidence = 0
    last_error = None
    try:
        with open(image_path, 'rb') as image_file:
            files = {
                'images': image_file,
                'organs': (None, 'auto')
            }
            params = {
                'api-key': PLANTNET_API_KEY,
                'include-related-images': 'false'
            }
            response = requests.post(url, files=files, params=params, timeout=10)
        logging.info(f"PlantNet v2 response status: {response.status_code}")
        logging.info(f"PlantNet v2 response body: {response.text}")
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                result = data['results'][0]
                species = result.get('species', {})
                score = result.get('score', 0)
                if score > 0.15:
                    scientific_name = species.get('scientificNameWithoutAuthor', 'Unknown')
                    common_names = species.get('commonNames', [])
                    family = species.get('family', {}).get('scientificNameWithoutAuthor', 'Unknown')
                    good_names = [name for name in common_names if not any(generic in name.lower() for generic in ['hybrid', 'sp.', 'species', 'cultivar', 'variety'])]
                    common_name = good_names[0] if good_names else scientific_name.split()[-1]
                    confidence = round(score * 100, 1)
                    best_result = {
                        'plant_name': common_name,
                        'scientific_name': scientific_name,
                        'common_names': good_names,
                        'confidence': confidence,
                        'family': family,
                        'description': f"PlantNet identification: {scientific_name}",
                        'region': 'Global',
                        'toxicity': 50,
                        'edible': False,
                        'diseases': [],
                        'care_tips': f'Consult botanical references for {common_name} care',
                        'source': 'PlantNet-all'
                    }
                    highest_confidence = confidence
            else:
                last_error = data.get('message', 'No results from PlantNet')
        else:
            last_error = response.text
    except requests.Timeout:
        logging.warning(f"PlantNet v2 timeout")
        last_error = 'Timeout'
    except Exception as e:
        logging.warning(f"PlantNet v2 error: {e}")
        last_error = str(e)
    if best_result and best_result['confidence'] > 20:
        logging.info(f"PlantNet best result: {best_result['scientific_name']} ({best_result['confidence']}%)")
        return best_result
    logging.info(f"PlantNet API returned no confident results. Last error: {last_error}")
    return {'error': last_error or 'PlantNet API could not identify the plant.'}

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


@app.route('/callback')
def callback():
    # Handle Supabase login callback
    try:
        if session.get('user_id'):
            return redirect(url_for('index'))
        else:
            return render_template('error.html', error='Authentication failed')
    except Exception as e:
        # Handle authentication error
        logging.error(f"Error authenticating user: {e}")
        return render_template('error.html', error='Authentication failed')


@app.route('/app')
def index():
    """Main app page (DEV: allow all users for guest testing)"""
    # DEV: Allow any user to access /app for guest testing, no session check
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
        # Try PlantNet API only for identification
        identification = identify_plant_with_plantnet(file_path)
        if isinstance(identification, dict) and 'error' in identification:
            logging.info("PlantNet failed, returning error (no local fallback)")
            try:
                os.remove(file_path)
            except Exception as e:
                logging.error(f"Error removing uploaded file: {e}")
            return jsonify({'error': "I couldn't analyze your image. Please try a clearer photo."}), 422
        if not identification:
            logging.info("PlantNet failed, returning error (no local fallback)")
            try:
                os.remove(file_path)
            except Exception as e:
                logging.error(f"Error removing uploaded file: {e}")
            return jsonify({'error': "I couldn't analyze your image. Please try a clearer photo."}), 422
        plant_name = identification['plant_name']
        scientific_name = identification.get('scientific_name', plant_name)
        logging.info(f"Plant identified: {plant_name} (confidence: {identification.get('confidence', 0)}%)")
        wiki_description = get_wikipedia_summary(plant_name, scientific_name)
        def first_sentence(text):
            if not text:
                return ''
            s = text.split('.')
            return s[0].strip() + '.' if s and s[0].strip() else text.strip()
        wiki_url = f"https://en.wikipedia.org/wiki/{scientific_name.replace(' ', '_')}" if scientific_name else None
        def clean_description(desc):
            if desc and desc.startswith('PlantNet identification:'):
                return desc.replace('PlantNet identification:', '').strip()
            return desc
        def get_one_word_field(field, default, plant_name, field_label):
            if field and field not in ['Unknown', 'Global', 50, False, None, '', 'Various']:
                return str(field).split()[0].replace('.', '')
            try:
                ai_result = generate_deepseek_response_with_memory(f"Give only the one-word answer for the {field_label} of {plant_name}.", {'history': [], 'context': {}})
                if ai_result:
                    word = ai_result.split('.')[0].split(',')[0].split()[0].strip()
                    if word.lower() not in ['unknown', 'various', 'global', '50', 'false', 'none', '']:
                        return word
            except Exception as e:
                logging.warning(f"DeepSeek fallback failed for {field_label}: {e}")
            return None
        family = get_one_word_field(identification.get('family'), 'Unknown', plant_name, 'family')
        # Native region: try Wikipedia, then PlantNet, then DeepSeek
        region = extract_region_from_text(wiki_description)
        if not region:
            _, pn_region, _ = get_plantnet_species_info(scientific_name)
            if pn_region:
                region = pn_region
        if not region:
            region = get_one_word_field(identification.get('region'), 'Unknown', plant_name, 'native region')
        # Season: try Wikipedia, then PlantNet, then DeepSeek
        season = extract_season_from_text(wiki_description)
        if not season:
            _, _, pn_season = get_plantnet_species_info(scientific_name)
            if pn_season:
                season = pn_season
        if not season:
            season = get_one_word_field(identification.get('season'), 'Unknown', plant_name, 'growing season')
        # Edibility: try Wikipedia, then PlantNet, then DeepSeek
        edible = None
        if wiki_description:
            if re.search(r'not edible|inedible|poisonous', wiki_description, re.IGNORECASE):
                edible = 'No'
            elif re.search(r'edible', wiki_description, re.IGNORECASE):
                edible = 'Yes'
        if not edible:
            pn_edible, _, _ = get_plantnet_species_info(scientific_name)
            if pn_edible:
                edible = pn_edible
        if not edible:
            edible = get_one_word_field(identification.get('edible'), False, plant_name, 'edibility')
        if edible and edible.lower() not in ['unknown', 'various', 'global', '50', 'false', 'none', '']:
            edible = edible.capitalize()
        else:
            edible = None
        if season and season.lower() not in ['unknown', 'various', 'global', '50', 'false', 'none', '']:
            season = season.capitalize()
        else:
            season = None
        try:
            os.remove(file_path)
        except Exception as e:
            logging.error(f"Error removing uploaded file: {e}")
        result = {
            'plant_name': plant_name,
            'description': clean_description(wiki_description) if wiki_description and len(wiki_description) > 10 else clean_description(identification.get('description', f'Information about {plant_name}')),
            'short_fact': first_sentence(wiki_description) if wiki_description and len(wiki_description) > 10 else '',
            'confidence': identification['confidence'],
            'scientific_name': scientific_name
        }
        if family: result['family'] = family
        if region: result['region'] = region
        if season: result['season'] = season
        if edible: result['edible'] = edible
        if 'common_names' in identification:
            result['common_names'] = identification['common_names']
        if wiki_url:
            result['wiki_url'] = wiki_url
        session['last_plant'] = result
        session_id = request.form.get('session_id', 'default')
        summary = f"Identified plant: {result['plant_name']}" + (f" (Family: {result.get('family')}, Region: {result.get('region')})" if result.get('family') or result.get('region') else '')
        if 'chat_sessions' in globals():
            if session_id not in chat_sessions:
                chat_sessions[session_id] = {'history': [], 'context': {}}
            chat_sessions[session_id]['history'].append({'role': 'bot', 'message': summary})
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in predict endpoint: {e}")
        return jsonify({'error': "I couldn't analyze your image. Please try a clearer photo."}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle text-based botanical questions with memory and persist to DB if logged in."""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        user_id = session.get('user_id')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        # Initialize session if not exists
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {'history': [], 'context': {}}
        # Add user message to history
        chat_sessions[session_id]['history'].append({'role': 'user', 'message': user_message})
        # Save to DB if logged in
        if user_id and SUPABASE_AVAILABLE and session_id != 'default':
            save_message_to_db(session_id, user_id, 'user', user_message)
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        who_are_you = ['who are you', 'what are you', 'your name', 'who r u']
        thanks = ['thank you', 'thanks', 'thx', 'ty', 'appreciate it', 'much appreciated']
        farewells = ['bye', 'goodbye', 'see you', 'see ya', 'later', 'farewell', 'take care']
        followup_words = ['and where', 'and how', 'where', 'how', 'when', 'why', 'what about', 'and what', 'and when', 'and why']
        message_lower = user_message.lower().strip()
        # Greetings
        if any(greet in message_lower for greet in greetings) and len(message_lower.split()) <= 4:
            response = "Hello! I'm Lumon, your botanical expert. How can I help you today?"
            typing_delay = random.uniform(1, 2)
        # Who are you
        elif any(q in message_lower for q in who_are_you):
            response = "I'm Lumon, your AI-powered botanist. Ask me anything about plants, gardening, or botany!"
            typing_delay = random.uniform(1, 2)
        # Thanks
        elif any(t in message_lower for t in thanks):
            response = "You're welcome! If you have more questions about plants or gardening, just ask."
            typing_delay = random.uniform(1, 2)
        # Farewells
        elif any(f in message_lower for f in farewells):
            response = "Goodbye! Happy gardening!"
            typing_delay = random.uniform(1, 2)
        # If user asks for more detail or a follow-up, use previous context
        elif any(word in message_lower for word in ['explain', 'more', 'details', 'elaborate', 'expand', 'long', 'full', 'in depth']) or any(fw in message_lower for fw in followup_words):
            # Find last bot and user response
            prev_bot = None
            prev_user = None
            for msg in reversed(chat_sessions[session_id]['history'][:-1]):
                if not prev_bot and msg['role'] == 'bot':
                    prev_bot = msg['message']
                if not prev_user and msg['role'] == 'user':
                    prev_user = msg['message']
                if prev_bot and prev_user:
                    break
            context_message = ''
            if prev_bot:
                context_message += prev_bot + "\n"
            if prev_user:
                context_message += prev_user + "\n"
            context_message += user_message
            response = generate_botanical_response_with_memory(context_message, chat_sessions[session_id])
            typing_delay = random.uniform(1, 2)
        # Botanical question (with typo correction)
        elif is_botanical_question(user_message):
            # Try to auto-correct a single close botanical word for downstream processing
            corrected = get_corrected_botanical_word(user_message)
            if corrected and corrected not in user_message.lower():
                # Replace the closest word in the message with the corrected botanical word
                words = user_message.split()
                for i, word in enumerate(words):
                    if difflib.get_close_matches(word.lower(), [corrected], n=1, cutoff=0.8):
                        words[i] = corrected
                        break
                corrected_message = ' '.join(words)
                response = generate_botanical_response_with_memory(corrected_message, chat_sessions[session_id])
            else:
                response = generate_botanical_response_with_memory(user_message, chat_sessions[session_id])
            typing_delay = random.uniform(1, 2)
        # Irrelevant question (strict, smart, and context-aware response)
        else:
            # Large topic-to-response mapping for 1000+ general topics
            topic_responses = {
                # Existing examples
                'beard': "That's not a question for a botanist, I'm afraid. Consult a dermatologist or barber for advice on beard growth.",
                'hair': "I'm a plant expert, not a trichologist. For hair questions, consult a medical professional.",
                'dog': "I specialize in plants, not animals. For pet advice, consult a veterinarian.",
                'cat': "I specialize in plants, not animals. For pet advice, consult a veterinarian.",
                'pet': "I specialize in plants, not animals. For pet advice, consult a veterinarian.",
                'india': "That's a question about horticulture and regional agriculture, not pure botany. I can't provide specific advice on cultivation in specific countries or regions.",
                'usa': "That's a question about horticulture and regional agriculture, not pure botany. I can't provide specific advice on cultivation in specific countries or regions.",
                'china': "That's a question about horticulture and regional agriculture, not pure botany. I can't provide specific advice on cultivation in specific countries or regions.",
                'country': "That's a question about horticulture and regional agriculture, not pure botany. I can't provide specific advice on cultivation in specific countries or regions.",
                'region': "That's a question about horticulture and regional agriculture, not pure botany. I can't provide specific advice on cultivation in specific countries or regions.",
                'tech': "I'm a botanist AI, not a tech support agent. Please ask about plants, gardening, or botany.",
                'computer': "I'm a botanist AI, not a tech support agent. Please ask about plants, gardening, or botany.",
                'software': "I'm a botanist AI, not a tech support agent. Please ask about plants, gardening, or botany.",
                'app': "I'm a botanist AI, not a tech support agent. Please ask about plants, gardening, or botany.",
                'food': "I can tell you about edible plants, but for recipes or cooking advice, consult a chef or food expert.",
                'recipe': "I can tell you about edible plants, but for recipes or cooking advice, consult a chef or food expert.",
                'cook': "I can tell you about edible plants, but for recipes or cooking advice, consult a chef or food expert.",
                'eat': "I can tell you about edible plants, but for recipes or cooking advice, consult a chef or food expert.",
                'math': "I'm not a math tutor, but I can help with plant science questions!",
                'calculate': "I'm not a math tutor, but I can help with plant science questions!",
                'number': "I'm not a math tutor, but I can help with plant science questions!",
                'weather': "I can't provide weather forecasts, but I can explain how weather affects plants.",
                'forecast': "I can't provide weather forecasts, but I can explain how weather affects plants.",
                'medicine': "I can discuss plant diseases, but for human health, consult a medical professional.",
                'doctor': "I can discuss plant diseases, but for human health, consult a medical professional.",
                'disease': "I can discuss plant diseases, but for human health, consult a medical professional.",
                'news': "I'm here for plant science, not current events or sports.",
                'politics': "I'm here for plant science, not current events or sports.",
                'sports': "I'm here for plant science, not current events or sports.",
                # Add 1000+ more topics (examples below, expand as needed)
                'finance': "I'm not a financial advisor. For finance questions, consult a professional.",
                'bank': "I'm not a financial advisor. For banking questions, consult your bank.",
                'stock': "I can't provide stock advice. Please consult a financial expert.",
                'investment': "I can't provide investment advice. Please consult a financial advisor.",
                'movie': "I'm not a movie critic. For film recommendations, try a movie database or critic.",
                'music': "I'm not a music expert. For music questions, consult a musicologist or streaming service.",
                'song': "I'm not a music expert. For music questions, consult a musicologist or streaming service.",
                'artist': "I'm not an art historian. For art questions, consult an art expert.",
                'painting': "I'm not an art historian. For art questions, consult an art expert.",
                'car': "I'm not an automotive expert. For car questions, consult a mechanic or car specialist.",
                'engine': "I'm not an automotive expert. For car questions, consult a mechanic or car specialist.",
                'travel': "I'm not a travel agent. For travel advice, consult a travel professional.",
                'flight': "I'm not a travel agent. For flight information, consult an airline or travel website.",
                'hotel': "I'm not a travel agent. For hotel bookings, consult a travel website or agent.",
                'game': "I'm not a gaming expert. For game advice, consult a gaming community or expert.",
                'playstation': "I'm not a gaming expert. For PlayStation questions, consult Sony or a gaming forum.",
                'xbox': "I'm not a gaming expert. For Xbox questions, consult Microsoft or a gaming forum.",
                'nintendo': "I'm not a gaming expert. For Nintendo questions, consult Nintendo or a gaming forum.",
                'fashion': "I'm not a fashion consultant. For style advice, consult a stylist or fashion expert.",
                'clothes': "I'm not a fashion consultant. For style advice, consult a stylist or fashion expert.",
                'shoes': "I'm not a fashion consultant. For style advice, consult a stylist or fashion expert.",
                'makeup': "I'm not a beauty expert. For makeup advice, consult a beautician or makeup artist.",
                'beauty': "I'm not a beauty expert. For beauty advice, consult a beautician or dermatologist.",
                'law': "I'm not a lawyer. For legal advice, consult a legal professional.",
                'court': "I'm not a lawyer. For legal advice, consult a legal professional.",
                'crime': "I'm not a lawyer. For legal advice, consult a legal professional.",
                'history': "I'm not a historian. For history questions, consult a historian or history resource.",
                'war': "I'm not a historian. For history questions, consult a historian or history resource.",
                'space': "I'm not an astronomer. For space questions, consult an astronomer or space agency.",
                'planet': "I'm not an astronomer. For space questions, consult an astronomer or space agency.",
                'star': "I'm not an astronomer. For space questions, consult an astronomer or space agency.",
                'physics': "I'm not a physicist. For physics questions, consult a physics expert.",
                'chemistry': "I'm not a chemist. For chemistry questions, consult a chemistry expert.",
                'biology': "I can help with plant biology, but for general biology, consult a biologist.",
                'psychology': "I'm not a psychologist. For mental health questions, consult a psychologist or counselor.",
                'philosophy': "I'm not a philosopher. For philosophy questions, consult a philosophy expert.",
                'religion': "I'm not a theologian. For religious questions, consult a religious leader or scholar.",
                'language': "I'm not a linguist. For language questions, consult a linguist or language teacher.",
                'translation': "I'm not a translator. For translation help, consult a language expert or translation service.",
                'coding': "I'm not a programming assistant. For coding help, consult a developer or programming forum.",
                'python': "I'm not a programming assistant. For coding help, consult a developer or programming forum.",
                'java': "I'm not a programming assistant. For coding help, consult a developer or programming forum.",
                'javascript': "I'm not a programming assistant. For coding help, consult a developer or programming forum.",
                # ... (add hundreds more as needed, or load from a large list)
            }
            found_topic = None
            for topic in topic_responses:
                if topic in message_lower:
                    found_topic = topic
                    break
            if found_topic:
                response = topic_responses[found_topic]
            else:
                response = "I'm not able to help with that topic. Please ask about plants, gardening, or botany."
            typing_delay = random.uniform(1, 2)
        time.sleep(typing_delay)
        # Add bot response to history
        chat_sessions[session_id]['history'].append({'role': 'bot', 'message': response})
        # Save bot message to DB
        if user_id and SUPABASE_AVAILABLE and session_id != 'default':
            save_message_to_db(session_id, user_id, 'bot', response)
        if len(chat_sessions[session_id]['history']) > 20:
            chat_sessions[session_id]['history'] = chat_sessions[session_id]['history'][-20:]
        return jsonify({
            'response': response,
            'type': 'success',
            'typing': True,
            'typing_delay': typing_delay
        })
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'An error occurred while processing your message. Please try again.'}), 500

def is_botanical_question(message):
    """Check if the message is related to plants or botany (expanded, smarter, typo-tolerant)"""
    botanical_keywords = [
        # Core botanical terms
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
        'orchid', 'rose', 'fern', 'bamboo', 'palm', 'moss', 'algae', 'fungi', 'mushroom',
        # Common fruits and vegetables
        'strawberry', 'apple', 'banana', 'grape', 'orange', 'lemon', 'lime', 'blueberry', 'raspberry',
        'blackberry', 'melon', 'watermelon', 'cantaloupe', 'peach', 'pear', 'plum', 'cherry', 'apricot',
        'kiwi', 'pineapple', 'mango', 'papaya', 'avocado', 'tomato', 'potato', 'carrot', 'onion', 'lettuce',
        'spinach', 'broccoli', 'cabbage', 'cauliflower', 'pepper', 'chili', 'bean', 'pea', 'corn', 'squash',
        'pumpkin', 'zucchini', 'radish', 'turnip', 'beet', 'celery', 'cucumber', 'eggplant', 'garlic', 'ginger',
        'herbs', 'basil', 'mint', 'oregano', 'thyme', 'sage', 'parsley', 'cilantro', 'dill', 'rosemary',
        # Other common plant names
        'sunflower', 'daisy', 'tulip', 'lily', 'iris', 'daffodil', 'marigold', 'pansy', 'begonia', 'azalea',
        'hydrangea', 'peony', 'camellia', 'gardenia', 'jasmine', 'lavender', 'magnolia', 'hibiscus', 'bougainvillea',
        'carnation', 'chrysanthemum', 'fuchsia', 'geranium', 'petunia', 'snapdragon', 'zinnia', 'wisteria',
        'holly', 'ivy', 'maple', 'oak', 'pine', 'cedar', 'birch', 'willow', 'elm', 'ash', 'spruce', 'fir',
    ]
    message_lower = message.lower()
    # Exact match
    if any(keyword in message_lower for keyword in botanical_keywords):
        return True
    # Fuzzy match for each word in message
    words = message_lower.split()
    for word in words:
        close = difflib.get_close_matches(word, botanical_keywords, n=1, cutoff=0.8)
        if close:
            return True
    return False

def get_corrected_botanical_word(message):
    """Return the closest botanical keyword for any word in the message, or None if not found."""
    botanical_keywords = [
        # Core botanical terms
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
        'orchid', 'rose', 'fern', 'bamboo', 'palm', 'moss', 'algae', 'fungi', 'mushroom',
        # Common fruits and vegetables
        'strawberry', 'apple', 'banana', 'grape', 'orange', 'lemon', 'lime', 'blueberry', 'raspberry',
        'blackberry', 'melon', 'watermelon', 'cantaloupe', 'peach', 'pear', 'plum', 'cherry', 'apricot',
        'kiwi', 'pineapple', 'mango', 'papaya', 'avocado', 'tomato', 'potato', 'carrot', 'onion', 'lettuce',
        'spinach', 'broccoli', 'cabbage', 'cauliflower', 'pepper', 'chili', 'bean', 'pea', 'corn', 'squash',
        'pumpkin', 'zucchini', 'radish', 'turnip', 'beet', 'celery', 'cucumber', 'eggplant', 'garlic', 'ginger',
        'herbs', 'basil', 'mint', 'oregano', 'thyme', 'sage', 'parsley', 'cilantro', 'dill', 'rosemary',
        # Other common plant names
        'sunflower', 'daisy', 'tulip', 'lily', 'iris', 'daffodil', 'marigold', 'pansy', 'begonia', 'azalea',
        'hydrangea', 'peony', 'camellia', 'gardenia', 'jasmine', 'lavender', 'magnolia', 'hibiscus', 'bougainvillea',
        'carnation', 'chrysanthemum', 'fuchsia', 'geranium', 'petunia', 'snapdragon', 'zinnia', 'wisteria',
        'holly', 'ivy', 'maple', 'oak', 'pine', 'cedar', 'birch', 'willow', 'elm', 'ash', 'spruce', 'fir',
    ]
    message_lower = message.lower()
    words = message_lower.split()
    for word in words:
        close = difflib.get_close_matches(word, botanical_keywords, n=1, cutoff=0.8)
        if close:
            return close[0]
    return None

def generate_botanical_response_with_memory(message, session):
    """Generate smart botanical responses with conversation memory"""
    # Restrict to botany/plant/gardening questions only (ultra strict, minimal)
    if not is_botanical_question(message):
        return "Please ask me about plants, gardening, or botany."
    try:
        # Build context from recent conversation (last 100 exchanges for deep memory)
        context = ""
        if session['history']:
            recent_messages = session['history'][-100:]  # Last 100 exchanges (user+bot)
            context = "Recent conversation:\n"
            for msg in recent_messages:
                context += f"{msg['role'].title()}: {msg['message']}\n"
            context += "\n"

        # Friendly greeting for greetings
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        message_lower = message.lower().strip()
        if any(greet in message_lower for greet in greetings) and len(message_lower.split()) <= 4:
            time.sleep(1)  # Add a 1-second delay for greetings
            return "Hello! I'm Lumon, your botanical expert. How can I help you today?"

        # Determine if user wants a long answer
        long_keywords = ['explain', 'more', 'details', 'elaborate', 'expand', 'long', 'full', 'in depth']
        wants_long = any(word in message_lower for word in long_keywords)
        # Detect if plant context is present
        plant_context = ''
        ambiguous_words = ['these', 'this', 'it', 'they', 'them', 'where are these', 'where is this', 'where is it', 'where are they']
        if any(word in message_lower for word in ambiguous_words) and session.get('last_plant'):
            plant = session['last_plant']
            plant_context = f"\nPrevious plant identified: {plant.get('plant_name', '')} (Family: {plant.get('family', '')}, Region: {plant.get('region', '')})"
            wants_long = True  # If plant context is present, allow long answer
        max_len = 1000 if wants_long else 200
        search_range = 200 if wants_long else 100
        trunc_len = max_len - 3  # for safety

        # Adaptive prompt
        if wants_long:
            prompt = f"""You are Lumon, a botanical expert. Provide a complete, helpful answer to the user's question. Use the context if relevant.

{context}Current question: {message}{plant_context}

Guidelines:
- Give a full answer if needed.
- Use simple, clear language.
- End your answer with a period.

Response:"""
        else:
            prompt = f"""You are Lumon, a botanical expert. Answer the user's question in 10 to 40 words, unless more is needed. Use the context if relevant.

{context}Current question: {message}{plant_context}

Guidelines:
- Be clear and helpful.
- End your answer with a period.

Response:"""

        # Try Gemini Pro first
        if GOOGLE_API_KEY:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                if response and response.text:
                    result = response.text.strip()
                    # Truncate if too long, but always end at the last period (full sentence)
                    if len(result) > max_len:
                        truncated = result[:trunc_len]
                        last_period = truncated.rfind('.')
                        if last_period != -1:
                            result = truncated[:last_period+1]
                        else:
                            # Try to find the next period after trunc_len (within next search_range chars)
                            next_period = result.find('.', trunc_len, trunc_len + search_range)
                            if next_period != -1:
                                result = result[:next_period+1]
                            else:
                                last_space = truncated.rfind(' ')
                                if last_space != -1:
                                    result = truncated[:last_space]
                                else:
                                    result = truncated  # fallback if no space
                    # Always end with a period
                    if not result.endswith('.'):
                        last_period = result.rfind('.')
                        if last_period != -1:
                            result = result[:last_period+1]
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
        # Detect if user wants long answer or plant context is present
        long_keywords = ['explain', 'more', 'details', 'elaborate', 'expand', 'long', 'full', 'in depth']
        wants_long = any(word in message.lower() for word in long_keywords)
        plant_context = ''
        ambiguous_words = ['these', 'this', 'it', 'they', 'them', 'where are these', 'where is this', 'where is it', 'where are they']
        if any(word in message.lower() for word in ambiguous_words) and session.get('last_plant'):
            plant = session['last_plant']
            plant_context = f"\nPrevious plant identified: {plant.get('plant_name', '')} (Family: {plant.get('family', '')}, Region: {plant.get('region', '')})"
            wants_long = True
        # Adaptive prompt
        if wants_long:
            prompt = f"""You are Lumon, a botanical expert. Provide a complete, helpful answer to the user's question. Use the context if relevant.\n\n{context}Current question: {message}{plant_context}\n\nGuidelines:\n- Give a full answer if needed.\n- Use simple, clear language.\n- End your answer with a period.\n\nResponse:"""
        else:
            prompt = f"""You are Lumon, a botanical expert. Answer the user's question in a clear, helpful way. Use the context if relevant.\n\n{context}Current question: {message}{plant_context}\n\nGuidelines:\n- Be clear and helpful.\n- End your answer with a period.\n\nResponse:"""
        response = together_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.6
        )
        if response.choices and response.choices[0].message:
            result = response.choices[0].message.content.strip()
            # Always end at the last period
            if not result.endswith('.'):
                last_period = result.rfind('.')
                if last_period != -1:
                    result = result[:last_period+1]
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
            # Return specific error for username or email already exists
            error_msg = result.get("error", "Registration failed.")
            return jsonify({"success": False, "error": error_msg}), 400

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
            session.clear()
            session['user_id'] = result["user_id"]
            session['authenticated'] = True
            session.permanent = True  # Make session cookie persistent
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
    if not SUPABASE_AVAILABLE:
        return jsonify({"success": False, "error": "Database not available"}), 503
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        if not access_token:
            return jsonify({"success": False, "error": "Missing access token"}), 400
        from supabase import create_client
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_anon = os.environ.get('SUPABASE_ANON_KEY')
        supabase = create_client(supabase_url, supabase_anon)
        user_response = supabase.auth.get_user(access_token)
        if hasattr(user_response, 'user') and user_response.user:
            session.clear()
            session['user_id'] = user_response.user.id
            session['authenticated'] = True
            session.permanent = True
            return jsonify({"success": True, "message": "OAuth login successful"}), 200
        else:
            return jsonify({"success": False, "error": "Invalid or expired token"}), 401
    except Exception as e:
        logging.error(f"OAuth session error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "Not authenticated"}), 401
        if not SUPABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Database not available"}), 503
        result = db_service.get_user_profile(user_id)
        # PATCH: Ensure profile_pic_url is included
        if result.get('success') and 'profile' in result:
            if 'profile_pic_url' not in result['profile']:
                result['profile']['profile_pic_url'] = None
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

@app.route('/')
def landing():
    # Always show landing page, regardless of authentication status
    return render_template('landing.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/page0')
def page0():
    return render_template('page0.html')

@app.route('/page1')
def page1():
    return render_template('page1.html')

@app.route('/page2')
def page2():
    return render_template('page2.html')
@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/user/update_username', methods=['POST'])
def update_username():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'Missing username'}), 400
    result = db_service.update_username(session['user_id'], username)
    if result.get('success'):
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Failed to update username')}), 400

@app.route('/api/user/update_password', methods=['POST'])
def update_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not old_password or not new_password:
        return jsonify({'success': False, 'error': 'Missing password fields'}), 400
    result = db_service.update_password(session['user_id'], old_password, new_password)
    if result.get('success'):
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Failed to update password')}), 400

@app.route('/api/user/update_country', methods=['POST'])
def update_country():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    data = request.get_json()
    country = data.get('country')
    if not country:
        return jsonify({'success': False, 'error': 'Missing country'}), 400
    result = db_service.update_country(session['user_id'], country)
    if result.get('success'):
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Failed to update country')}), 400

@app.route('/api/user/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    if 'profile_pic' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    file = request.files['profile_pic']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
    uploads_dir = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    filename = f"{session['user_id']}_profile_{file.filename}"
    file_path = os.path.join(uploads_dir, filename)
    file.save(file_path)
    file_url = f"/uploads/{filename}"
    result = db_service.update_profile_pic(session['user_id'], file_url)
    # PATCH: Ensure profile_pic_url is updated
    if result.get('success'):
        return jsonify({'success': True, 'file_url': file_url}), 200
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Failed to update profile picture')}), 400

# --- NEW: Chat message persistence ---
@app.route('/api/user/history', methods=['GET'])
def get_user_history():
    """Fetch chat history for the logged-in user from Supabase."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    if not SUPABASE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Database not available'}), 503
    try:
        user_id = session['user_id']
        # Fetch chat sessions for user
        sessions_result = db_service.get_user_chat_sessions(user_id)
        if not sessions_result['success']:
            return jsonify({'success': False, 'error': 'Could not fetch chat sessions'}), 400
        chat_sessions_list = sessions_result['sessions']
        # For each session, fetch messages
        all_history = []
        for sess in chat_sessions_list:
            session_id = sess['id']
            messages_result = db_service.get_chat_messages(session_id, user_id)
            if messages_result['success']:
                all_history.append({
                    'session_id': session_id,
                    'created_at': sess['created_at'],
                    'messages': messages_result['messages']
                })
        return jsonify({'success': True, 'history': all_history}), 200
    except Exception as e:
        logging.error(f"Error fetching user history: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# --- NEW: Save chat message to Supabase ---
def save_message_to_db(session_id, user_id, role, message):
    if not SUPABASE_AVAILABLE:
        return False
    try:
        db_service.save_chat_message(session_id, user_id, role, message)
        return True
    except Exception as e:
        logging.error(f"Error saving chat message: {e}")
        return False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
