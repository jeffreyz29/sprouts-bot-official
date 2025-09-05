"""
Web Statistics Module for SPROUTS Bot
Provides bot statistics and monitoring data
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BotStats:
    """Bot statistics tracking"""
    
    def __init__(self):
        self.stats = {
            "commands_used": 0,
            "guilds": 0,
            "users": 0,
            "uptime": "0 seconds"
        }
    
    def update_stats(self, bot):
        """Update bot statistics"""
        try:
            self.stats["guilds"] = len(bot.guilds)
            self.stats["users"] = sum(guild.member_count for guild in bot.guilds)
        except Exception as e:
            logger.error(f"Error updating bot stats: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current bot statistics"""
        return self.stats.copy()
    
    def increment_command_usage(self):
        """Increment command usage counter"""
        self.stats["commands_used"] += 1
    
    def update_guild_count(self, guild_count):
        """Update guild count"""
        self.stats["guilds"] = guild_count
    
    def update_member_count(self, member_count):
        """Update member count"""
        self.stats["users"] = member_count

# Global instance
bot_stats = BotStats()