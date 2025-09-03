"""
Keep Alive Module
Helps maintain bot uptime by providing a simple HTTP endpoint
"""

from flask import Flask
import threading
import logging

logger = logging.getLogger(__name__)

# Create a simple Flask app for keep-alive pings
app = Flask(__name__)

@app.route('/')
def keep_alive():
    """Simple endpoint to respond to uptime checks"""
    return "Bot is alive and running! 🌱"

@app.route('/status')
def status():
    """Status endpoint with basic health information"""
    return {
        "status": "online",
        "message": "Sprouts Bot is running",
        "uptime_check": "OK"
    }

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return "pong"

def run_keep_alive_server():
    """Run the keep-alive server on port 8080"""
    try:
        logger.info("Starting keep-alive server on port 8080...")
        app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Error running keep-alive server: {e}")

def start_keep_alive():
    """Start the keep-alive server in a separate thread"""
    try:
        server_thread = threading.Thread(target=run_keep_alive_server, daemon=True)
        server_thread.start()
        logger.info("Keep-alive server started successfully")
    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {e}")

if __name__ == "__main__":
    # Run keep-alive server directly
    run_keep_alive_server()