"""
Feature Flag System for SPROUTS Bot
Allows controlled release of new commands and features
"""

import json
import os
import logging
from typing import Dict, List, Optional, Set
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class FeatureFlagManager:
    """Manages feature flags for controlled command releases"""
    
    def __init__(self):
        self.config_file = "config/feature_flags.json"
        self.flags = self._load_flags()
        
        # Define all available features and their commands - ORGANIZED BY ORIGINAL HELP CATEGORIES
        self.feature_definitions = {
            # UTILITIES CATEGORY (from help page "utilities")
            "utilities": {
                "description": "Basic utility commands and server information tools",
                "commands": ["about", "invite", "shards", "vote", "avatar", "channelinfo", "inviteinfo", "ping", "roleinfo", "serverinfo", "userinfo", "setprefix", "prefix", "variables"],
                "always_enabled": True
            },
            
            # CORE SYSTEM (always enabled)
            "core_help": {
                "description": "Core help system",
                "commands": ["help"],
                "always_enabled": True
            },
            
            # TICKETS CATEGORY (from help page "tickets")
            "tickets": {
                "description": "Complete support ticket management system",
                "commands": ["new", "close", "blacklist", "viewstaff", "managetags", "tickettag", "notes", "on-call", "setup", "addadmin", "removeadmin", "addsupport", "removesupport", "createpanel", "listpanels", "delpanel", "ticketsetup", "claim", "unclaim", "add", "remove", "rename", "move", "tag", "transfer", "forceclose", "listtickets", "ticketlimit", "ticketuseembed", "ticketmessage", "tickettopic", "ghostping"]
            },
            
            # EMBEDS CATEGORY (from help page "embeds")
            "embeds": {
                "description": "Create and edit custom embeds",
                "commands": ["embed", "createembed", "embedcreate", "embedquick"],
                "always_enabled": True
            },
            
            # AUTORESPONDERS CATEGORY (from help page "autoresponders")
            "autoresponders": {
                "description": "Automated message responses",
                "commands": ["autoresponder", "autoresponderlist", "autoresponderdelete"]
            },
            
            # STICKY CATEGORY (from help page "sticky")
            "sticky": {
                "description": "Persistent channel messages",
                "commands": ["stick", "stickslow", "stickstop", "stickstart", "stickremove", "getstickies", "stickspeed"]
            },
            
            # REMINDERS CATEGORY (from help page "reminders")
            "reminders": {
                "description": "Personal reminder system",
                "commands": ["remind", "reminders", "delreminder"]
            },
            
            
            
        }
        
        # Initialize default flags if file doesn't exist
        self._initialize_defaults()
    
    def _load_flags(self) -> Dict[str, bool]:
        """Load feature flags from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading feature flags: {e}")
            return {}
    
    def _save_flags(self):
        """Save feature flags to config file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.flags, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving feature flags: {e}")
    
    def _initialize_defaults(self):
        """Initialize default feature flag states"""
        changed = False
        for feature_name, feature_info in self.feature_definitions.items():
            if feature_name not in self.flags:
                # Core features and dev tools are enabled by default
                default_state = feature_info.get("always_enabled", False) or feature_info.get("dev_only", False)
                self.flags[feature_name] = default_state
                changed = True
        
        if changed:
            self._save_flags()
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return self.flags.get(feature_name, False)
    
    def is_command_enabled(self, command_name: str) -> bool:
        """Check if a specific command is enabled"""
        for feature_name, feature_info in self.feature_definitions.items():
            if command_name in feature_info.get("commands", []):
                # Always enabled features override flags
                if feature_info.get("always_enabled", False):
                    return True
                return self.is_feature_enabled(feature_name)
        return False
    
    def is_dev_command(self, command_name: str, bot) -> bool:
        """Check if a command belongs to the DevOnly cog"""
        if hasattr(bot, 'get_cog') and bot.get_cog('DevOnly'):
            dev_cog = bot.get_cog('DevOnly')
            dev_command_names = {cmd.name for cmd in dev_cog.get_commands()}
            return command_name in dev_command_names
        return False
    
    def enable_feature(self, feature_name: str) -> bool:
        """Enable a feature"""
        if feature_name in self.feature_definitions:
            self.flags[feature_name] = True
            self._save_flags()
            return True
        return False
    
    def disable_feature(self, feature_name: str) -> bool:
        """Disable a feature (if not always enabled)"""
        if feature_name in self.feature_definitions:
            feature_info = self.feature_definitions[feature_name]
            if feature_info.get("always_enabled", False):
                return False  # Cannot disable always enabled features
            self.flags[feature_name] = False
            self._save_flags()
            return True
        return False
    
    def get_feature_status(self) -> Dict[str, Dict]:
        """Get status of all features"""
        status = {}
        for feature_name, feature_info in self.feature_definitions.items():
            status[feature_name] = {
                "enabled": self.is_feature_enabled(feature_name),
                "description": feature_info.get("description", ""),
                "commands": feature_info.get("commands", []),
                "always_enabled": feature_info.get("always_enabled", False),
                "dev_only": feature_info.get("dev_only", False)
            }
        return status
    
    def get_enabled_commands(self, bot=None) -> Set[str]:
        """Get set of all currently enabled commands (excluding DevOnly commands)"""
        enabled_commands = set()
        for feature_name, feature_info in self.feature_definitions.items():
            if self.is_feature_enabled(feature_name):
                enabled_commands.update(feature_info.get("commands", []))
        
        # EXCLUDE DevOnly commands from the enabled commands list
        if bot and hasattr(bot, 'get_cog') and bot.get_cog('DevOnly'):
            dev_cog = bot.get_cog('DevOnly')
            dev_command_names = {cmd.name for cmd in dev_cog.get_commands()}
            enabled_commands = enabled_commands - dev_command_names
            
        return enabled_commands
    
    def get_disabled_commands(self) -> Set[str]:
        """Get set of all currently disabled commands"""
        all_commands = set()
        enabled_commands = self.get_enabled_commands()
        
        for feature_info in self.feature_definitions.values():
            all_commands.update(feature_info.get("commands", []))
        
        return all_commands - enabled_commands

# Global feature flag manager instance
feature_manager = FeatureFlagManager()

def feature_flag_check():
    """Decorator to check if command is enabled via feature flags"""
    def decorator(func):
        async def wrapper(self, ctx, *args, **kwargs):
            command_name = ctx.command.name if ctx.command else func.__name__
            
            # COMPLETELY EXCLUDE DevOnly commands from feature flag system
            if feature_manager.is_dev_command(command_name, ctx.bot):
                # DevOnly commands handle their own permissions via cog_check
                return await func(self, ctx, *args, **kwargs)
            
            # Always allow developer access to non-dev commands
            if hasattr(ctx.bot, 'owner_ids') and ctx.author.id in ctx.bot.owner_ids:
                return await func(self, ctx, *args, **kwargs)
            
            # Check if command is enabled for regular users
            if not feature_manager.is_command_enabled(command_name):
                # Silently ignore disabled commands
                return
            
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator