"""
Discord Bot Main Entry Point - Production Ready
Optimized for single-instance deployment
"""

import asyncio
import logging
import os
import signal
import sys
import discord
from dotenv import load_dotenv
from bot import DiscordBot

# Load environment variables
load_dotenv()

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global bot instance for cleanup
bot = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down...")
    if bot and not bot.is_closed():
        asyncio.create_task(bot.close())
    sys.exit(0)

async def main():
    """Main function - Production ready bot startup"""
    global bot
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Validate environment
        token = os.getenv('DISCORD_BOT_TOKEN', '').strip()
        if not token:
            logger.error("DISCORD_BOT_TOKEN environment variable not set!")
            return
        
        # Initialize bot
        bot = DiscordBot()
        logger.info("Starting Discord bot in production mode...")
        
        # Start bot with automatic reconnection
        await bot.start(token)
        
    except discord.LoginFailure:
        logger.error("Invalid Discord bot token!")
    except discord.HTTPException as e:
        logger.error(f"Discord API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        if bot and not bot.is_closed():
            logger.info("Closing bot connection...")
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
