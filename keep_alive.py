"""
Keep-Alive Web Server for SPROUTS Bot
Provides a simple health check endpoint on port 8080
"""

import threading
import logging
from flask import Flask, jsonify

logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "sprouts-bot-keepalive",
        "message": "SPROUTS Bot is running"
    })

@app.route('/health')
def health():
    """Alternative health check endpoint"""
    return jsonify({"status": "healthy"})

def start_keep_alive():
    """Start the keep-alive server in a daemon thread"""
    try:
        def run_keep_alive():
            app.run(host='0.0.0.0', port=8080, debug=False)
        
        thread = threading.Thread(target=run_keep_alive, daemon=True)
        thread.start()
        logger.info("Keep-alive server started on port 8080")
    except Exception as e:
        logger.error(f"Error starting keep-alive server: {e}")