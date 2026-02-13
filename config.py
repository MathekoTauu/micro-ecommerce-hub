import os
from dotenv import load_dotenv

load_dotenv()

class Config:
   # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')  # IMPORTANT: Change in production!
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # Lightning Network settings - REST API
    LND_HOST = os.getenv('LND_HOST', '127.0.0.1')
    LND_REST_PORT = int(os.getenv('LND_REST_PORT', 8081))  # alice=8081, bob=8082, carol=8083
    
    # Paths - adjust network number and node name as needed
    POLAR_BASE = os.getenv('POLAR_BASE', r'C:\Users\tauma\.polar\networks\5\volumes\lnd\alice')
    LND_MACAROON_PATH = os.path.join(POLAR_BASE, 'data', 'chain', 'bitcoin', 'regtest', 'admin.macaroon')
    
    # Application settings
    PRODUCTS_FILE = os.path.join('data', 'products.json')
    VENDORS_FILE = os.path.join('data', 'vendors.json')
    DATABASE_URI = 'sqlite:///data/database.db'
    
    # Payment settings
    PAYMENT_TIMEOUT = 3600  # 1 hour
    ESCROW_RELEASE_DELAY = 86400  # 24 hours