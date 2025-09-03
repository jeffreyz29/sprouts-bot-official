"""
Discord Bot with Integrated Web Viewer
Runs both the Discord bot and Flask web server simultaneously
"""

import asyncio
import threading
import time
import logging
from main import main as run_discord_bot
from web_viewer import run_web_server
from keep_alive import start_keep_alive

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def start_web_server():
    """Start the Flask web server in a separate thread"""
    try:
        logger.info("Starting web server thread...")
        run_web_server()
    except Exception as e:
        logger.error(f"Error in web server: {e}")

def start_discord_bot():
    """Start the Discord bot"""
    try:
        logger.info("Starting Discord bot...")
        asyncio.run(run_discord_bot())
    except Exception as e:
        logger.error(f"Error in Discord bot: {e}")

def main():
    """Main function - Production ready with single instance control"""
    try:
        logger.info("Starting Sprouts Bot (Production Mode) with Web Dashboard...")
        
        # Start keep-alive server first
        start_keep_alive()
        logger.info("Keep-alive server started on port 8080")
        
        # Start web server in a separate thread
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        
        # Give servers time to start
        time.sleep(3)
        logger.info("Web viewer available at http://localhost:5000")
        logger.info("Keep-alive endpoint available at http://localhost:8080")
        
        # Start Discord bot in main thread
        start_discord_bot()
        
    except KeyboardInterrupt:
        logger.info("Shutting down bot, web server, and keep-alive...")
    except Exception as e:
        logger.error(f"Critical error: {e}")

if __name__ == "__main__":
    main()