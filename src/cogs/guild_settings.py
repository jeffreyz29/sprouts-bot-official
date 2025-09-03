"""
Guild Settings Management
Handles per-guild settings like custom prefixes
"""

import json
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class GuildSettings:
    """Manages guild-specific settings"""
    
    def __init__(self):
        self.settings_file = "config/guild_settings.json"
        self.settings = self.load_settings()
        self.default_prefix = "s."
    
    def load_settings(self) -> Dict:
        """Load guild settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading guild settings: {e}")
        return {}
    
    def save_settings(self):
        """Save guild settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving guild settings: {e}")
    
    def get_prefix(self, guild_id: Optional[int]) -> str:
        """Get prefix for a guild"""
        if guild_id is None:
            return self.default_prefix
        
        guild_str = str(guild_id)
        return self.settings.get(guild_str, {}).get('prefix', self.default_prefix)
    
    def set_prefix(self, guild_id: int, prefix: str):
        """Set prefix for a guild"""
        guild_str = str(guild_id)
        if guild_str not in self.settings:
            self.settings[guild_str] = {}
        
        self.settings[guild_str]['prefix'] = prefix
        self.save_settings()
    
    def get_all_guild_settings(self, guild_id: int) -> Dict:
        """Get all settings for a guild"""
        guild_str = str(guild_id)
        return self.settings.get(guild_str, {})
    
    def update_guild_setting(self, guild_id: int, key: str, value):
        """Update a specific setting for a guild"""
        guild_str = str(guild_id)
        if guild_str not in self.settings:
            self.settings[guild_str] = {}
        
        self.settings[guild_str][key] = value
        self.save_settings()

# Global instance
guild_settings = GuildSettings()