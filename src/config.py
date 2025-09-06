"""
Configuration settings for the Discord bot
"""

import os
import logging

# Optional imports with graceful fallbacks - no more dependency errors!
try:
    import pymongo
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

try:
    import ssl
    import certifi
    CERTIFI_AVAILABLE = True
except ImportError:
    CERTIFI_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)

BOT_CONFIG = {
    'prefix': os.getenv('DEFAULT_PREFIX', 's.'),  # Default prefix for text commands
    'description': 'A Sprouts is a semi-public Discord bot that makes server life easier. From customizable commands to automated moderation and smooth ticket handling for APM portals, Sprouts keeps your community running effortlessly.',
    'version': '1.0.0',
    'author': 'Discord Bot Developer',
    'color': 0xCCFFD1,  # Default embed color
}

# Environment variables with fallbacks
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))
MONGO_URI = os.getenv('MONGO_URI', '')

# Import custom emojis
from emojis import SPROUTS_CHECK, SPROUTS_ERROR, SPROUTS_WARNING, SPROUTS_INFORMATION, get_emoji

# Optional logging channels (can be set via environment if needed)
LOG_COMMANDS_CHANNEL = int(os.getenv('LOG_COMMANDS_CHANNEL', '0') or '0')
LOG_DMS_CHANNEL = int(os.getenv('LOG_DMS_CHANNEL', '0') or '0')


# Bot settings
MAX_MESSAGE_LENGTH = 2000

# Bot regular embed color - used for general embeds
EMBED_COLOR_NORMAL = 0xCCFFD1      # Regular bot embed color (#CCFFD1)

# SPROUTS Emoji Colors - Using official hex codes
EMBED_COLOR_SUCCESS = 0x2ecc71     # SPROUTS_CHECK - success/configuration - Green
EMBED_COLOR_ERROR = 0xe74c3c       # SPROUTS_ERROR - failures/bot errors - Red  
EMBED_COLOR_WARNING = 0xffea69     # SPROUTS_WARNING - caution/user input issues - Yellow
EMBED_COLOR_INFO = 0x69beff        # SPROUTS_INFORMATION - information/help/guides - Blue
EMBED_COLOR_INFORMATION = 0x69beff # Alias for SPROUTS_INFORMATION

# Legacy color compatibility (deprecated - use specific emoji colors above)
EMBED_COLOR_HIERARCHY = 0xFFE682

# Command cooldowns (in seconds)
COMMAND_COOLDOWNS = {
    'ping': 5,
    'hello': 3,
    'info': 10
}

# MongoDB Connection Handler
class MongoDBHandler:
    def __init__(self):
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB with fast fallback to JSON"""
        if not MONGO_URI or not PYMONGO_AVAILABLE:
            if not PYMONGO_AVAILABLE:
                logger.info("MongoDB package not available - using JSON storage")
            else:
                logger.warning("MONGO_URI not set - using JSON storage")
            return
        
        logger.info("Attempting quick MongoDB connection...")
        
        # Single fast connection attempt with short timeout
        try:
            # Quick connection with minimal timeout to avoid startup delays
            connection_args = {
                'serverSelectionTimeoutMS': 3000,  # 3 second timeout
                'connectTimeoutMS': 3000,
            }
            
            # Add TLS settings only if certifi is available
            if CERTIFI_AVAILABLE:
                connection_args.update({
                    'tls': True,
                    'tlsAllowInvalidCertificates': True,
                    'tlsAllowInvalidHostnames': True
                })
            
            self.client = MongoClient(MONGO_URI, **connection_args)
            # Quick ping test
            self.client.admin.command('ping')
            self.db = self.client.sprouts_bot
            logger.info("MongoDB connected successfully!")
            return
            
        except Exception as e:
            logger.info(f"MongoDB connection failed ({str(e)[:50]}...) - using JSON fallback mode")
            if self.client:
                try:
                    self.client.close()
                except:
                    pass
            self.client = None
            self.db = None
    
    def is_connected(self):
        """Check if MongoDB is connected"""
        return self.client is not None and self.db is not None
    
    def get_collection(self, name):
        """Get a MongoDB collection"""
        if not self.is_connected():
            return None
        return self.db[name] if self.db else None
    
    def save_json_data(self, collection_name, data):
        """Save JSON data to MongoDB collection"""
        if not self.is_connected():
            return False
        try:
            collection = self.get_collection(collection_name)
            if not collection:
                return False
            # Clear existing data and insert new
            collection.delete_many({})
            if isinstance(data, dict) and data:
                collection.insert_one(data)
            elif isinstance(data, list) and data:
                collection.insert_many(data)
            return True
        except Exception as e:
            logger.error(f"Error saving to {collection_name}: {e}")
            return False
    
    def load_json_data(self, collection_name, default=None):
        """Load JSON data from MongoDB collection"""
        if not self.is_connected():
            return default if default is not None else {}
            
        try:
            collection = self.get_collection(collection_name)
            data = list(collection.find({}, {'_id': 0}))  # Exclude MongoDB _id
            
            if not data:
                return default if default is not None else {}
            elif len(data) == 1:
                return data[0]
            else:
                return data
                
        except Exception as e:
            logger.error(f"Error loading from {collection_name}: {e}")
            return default if default is not None else {}

# Initialize MongoDB handler
mongodb = MongoDBHandler()
