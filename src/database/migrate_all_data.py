"""
Comprehensive Data Migration Script
Migrates ALL bot data from JSON files to PostgreSQL database
Ensures complete data persistence across all bot systems
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from .all_data_access import (
    SavedEmbedsDatabase, AutoresponderDatabase, ReminderDatabase,
    StickyMessageDatabase, GuildConfigDatabase, SystemConfigDatabase
)
from .migrate_data import DataMigrator as TicketDataMigrator

logger = logging.getLogger(__name__)


class ComprehensiveDataMigrator:
    """Migrates all bot data from JSON files to database"""
    
    def __init__(self):
        self.data_files = {
            # Existing data files
            "saved_embeds": "src/data/saved_embeds.json",
            "autoresponders": "src/data/autoresponders.json",
            "reminders": "src/data/reminders.json",
            "sticky_messages": "src/data/sticky_messages.json",
            
            # Configuration files
            "guild_settings": "config/guild_settings.json",
            "cmd_logging_settings": "config/cmd_logging_settings.json",
            "dm_logging_settings": "config/dm_logging_settings.json",
            "dm_settings": "config/dm_settings.json",
            "global_logging": "config/global_logging.json",
            "server_join_settings": "config/server_join_settings.json",
            "server_stats": "config/server_stats.json",
            "tags_data": "config/tags_data.json",
            "global_cooldown": "config/global_cooldown.json",
            "maintenance": "src/data/maintenance.json",
        }
    
    def load_json_file(self, file_path: str) -> Dict:
        """Safely load JSON file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded {file_path}")
                return data if isinstance(data, dict) else {}
            return {}
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return {}
    
    async def migrate_saved_embeds(self):
        """Migrate saved embeds to database"""
        logger.info("Migrating saved embeds...")
        
        embeds_data = self.load_json_file(self.data_files["saved_embeds"])
        migrated_count = 0
        
        for guild_id_str, guild_embeds in embeds_data.items():
            # Skip if the guild_id is not a valid integer (could be metadata)
            if not guild_id_str.isdigit():
                continue
                
            guild_id = int(guild_id_str)
            
            if isinstance(guild_embeds, dict):
                # In the saved embeds format, each entry is directly an embed_name -> embed_data
                for embed_name, embed_data in guild_embeds.items():
                    if isinstance(embed_data, dict):
                        # Extract user from embed data or use a default
                        user_id = 0  # Default user ID for migrated embeds
                        
                        success = SavedEmbedsDatabase.save_embed(
                            guild_id, user_id, embed_name, embed_data
                        )
                        if success:
                            migrated_count += 1
        
        logger.info(f"Migrated {migrated_count} saved embeds")
        return migrated_count
    
    async def migrate_autoresponders(self):
        """Migrate autoresponders to database"""
        logger.info("Migrating autoresponders...")
        
        autoresponders_data = self.load_json_file(self.data_files["autoresponders"])
        migrated_count = 0
        
        for guild_id_str, guild_responders in autoresponders_data.items():
            guild_id = int(guild_id_str)
            
            if isinstance(guild_responders, list):
                for responder in guild_responders:
                    if isinstance(responder, dict):
                        autoresponder_id = AutoresponderDatabase.create_autoresponder(
                            guild_id=guild_id,
                            trigger=responder.get('trigger', ''),
                            response=responder.get('response', ''),
                            created_by=responder.get('created_by', 0),
                            match_type=responder.get('match_type', 'contains')
                        )
                        if autoresponder_id:
                            migrated_count += 1
        
        logger.info(f"Migrated {migrated_count} autoresponders")
        return migrated_count
    
    async def migrate_reminders(self):
        """Migrate reminders to database"""
        logger.info("Migrating reminders...")
        
        reminders_data = self.load_json_file(self.data_files["reminders"])
        migrated_count = 0
        
        for reminder_id, reminder in reminders_data.items():
            if isinstance(reminder, dict):
                # Parse the datetime
                remind_at = None
                if 'remind_at' in reminder:
                    try:
                        remind_at = datetime.fromisoformat(reminder['remind_at'].replace('Z', '+00:00'))
                    except:
                        # Try alternative parsing
                        try:
                            remind_at = datetime.strptime(reminder['remind_at'], '%Y-%m-%d %H:%M:%S')
                        except:
                            logger.warning(f"Could not parse reminder time: {reminder['remind_at']}")
                            continue
                
                if remind_at:
                    new_reminder_id = ReminderDatabase.create_reminder(
                        user_id=reminder.get('user_id', 0),
                        channel_id=reminder.get('channel_id', 0),
                        message=reminder.get('message', ''),
                        remind_at=remind_at,
                        guild_id=reminder.get('guild_id') if reminder.get('guild_id') else None,
                        is_dm=reminder.get('is_dm', False)
                    )
                    if new_reminder_id:
                        migrated_count += 1
        
        logger.info(f"Migrated {migrated_count} reminders")
        return migrated_count
    
    async def migrate_sticky_messages(self):
        """Migrate sticky messages to database"""
        logger.info("Migrating sticky messages...")
        
        sticky_data = self.load_json_file(self.data_files["sticky_messages"])
        migrated_count = 0
        
        for guild_id_str, guild_stickies in sticky_data.items():
            guild_id = int(guild_id_str)
            
            if isinstance(guild_stickies, dict):
                for channel_id_str, sticky_info in guild_stickies.items():
                    channel_id = int(channel_id_str)
                    
                    if isinstance(sticky_info, dict):
                        embed_data = sticky_info.get('embed')
                        sticky_id = StickyMessageDatabase.create_sticky_message(
                            guild_id=guild_id,
                            channel_id=channel_id,
                            content=sticky_info.get('content', ''),
                            created_by=sticky_info.get('created_by', 0),
                            embed_data=embed_data if embed_data else None
                        )
                        
                        if sticky_id and 'last_message_id' in sticky_info:
                            # Update last message ID
                            StickyMessageDatabase.update_last_message(
                                guild_id, channel_id, sticky_info['last_message_id']
                            )
                        
                        if sticky_id:
                            migrated_count += 1
        
        logger.info(f"Migrated {migrated_count} sticky messages")
        return migrated_count
    
    async def migrate_guild_configurations(self):
        """Migrate all guild-specific configurations to database"""
        logger.info("Migrating guild configurations...")
        
        # Consolidate all configuration data by guild
        guild_configs = {}
        
        # Process each configuration file type
        config_mappings = {
            "cmd_logging_settings": "cmd_logging_enabled",
            "dm_logging_settings": "dm_logging_enabled",
            "server_stats": "auto_stats_enabled",
            "global_logging": "log_guild_events",
            "server_join_settings": "server_join_logging",
            "maintenance": "maintenance_mode"
        }
        
        for file_key, setting_key in config_mappings.items():
            file_data = self.load_json_file(self.data_files[file_key])
            
            for guild_id_str, value in file_data.items():
                if guild_id_str.isdigit():
                    guild_id = int(guild_id_str)
                    
                    if guild_id not in guild_configs:
                        guild_configs[guild_id] = {}
                    
                    # Process different data structures
                    if file_key == "cmd_logging_settings":
                        if isinstance(value, dict) and value.get('channel_id'):
                            guild_configs[guild_id]["log_commands_channel"] = value['channel_id']
                            guild_configs[guild_id]["cmd_logging_enabled"] = True
                    elif file_key == "dm_logging_settings":
                        if isinstance(value, dict) and value.get('channel_id'):
                            guild_configs[guild_id]["log_dms_channel"] = value['channel_id']
                            guild_configs[guild_id]["dm_logging_enabled"] = True
                    elif file_key == "server_stats":
                        if isinstance(value, dict):
                            if value.get('channel_id'):
                                guild_configs[guild_id]["server_stats_channel"] = value['channel_id']
                            if value.get('message_id'):
                                guild_configs[guild_id]["server_stats_message_id"] = value['message_id']
                            guild_configs[guild_id]["auto_stats_enabled"] = value.get('enabled', False)
                    else:
                        # Simple boolean or value mapping
                        if isinstance(value, dict):
                            guild_configs[guild_id][setting_key] = value.get('enabled', False)
                        else:
                            guild_configs[guild_id][setting_key] = bool(value)
        
        # Apply consolidated configurations to database
        migrated_count = 0
        for guild_id, config in guild_configs.items():
            success = GuildConfigDatabase.update_guild_config(guild_id, **config)
            if success:
                migrated_count += 1
        
        logger.info(f"Migrated configurations for {migrated_count} guilds")
        return migrated_count
    
    async def migrate_system_configurations(self):
        """Migrate system-wide configurations"""
        logger.info("Migrating system configurations...")
        
        migrated_count = 0
        
        # Migrate global cooldown settings
        cooldown_data = self.load_json_file(self.data_files["global_cooldown"])
        if cooldown_data:
            success = SystemConfigDatabase.set_config(
                "global_cooldown", 
                cooldown_data,
                "Global cooldown settings for bot commands"
            )
            if success:
                migrated_count += 1
        
        # Migrate maintenance settings
        maintenance_data = self.load_json_file(self.data_files["maintenance"])
        if maintenance_data:
            success = SystemConfigDatabase.set_config(
                "maintenance_mode",
                maintenance_data,
                "Bot maintenance mode configuration"
            )
            if success:
                migrated_count += 1
        
        # Add migration timestamp
        SystemConfigDatabase.set_config(
            "data_migration_completed",
            {
                "completed_at": datetime.now().isoformat(),
                "migrated_systems": [
                    "saved_embeds", "autoresponders", "reminders", 
                    "sticky_messages", "guild_configurations", "system_configurations",
                    "tickets"  # From existing migration
                ]
            },
            "Data migration completion status"
        )
        
        logger.info(f"Migrated {migrated_count} system configurations")
        return migrated_count
    
    async def migrate_all_data(self):
        """Migrate all bot data from JSON to database"""
        logger.info("Starting comprehensive data migration...")
        
        total_migrated = 0
        migration_results = {}
        
        try:
            # Migrate existing ticket system data first (if not already done)
            ticket_migrator = TicketDataMigrator()
            ticket_results = await ticket_migrator.migrate_all_data()
            migration_results["tickets"] = ticket_results  # Boolean result
            
            # Migrate all other data systems
            migration_results["saved_embeds"] = await self.migrate_saved_embeds()
            migration_results["autoresponders"] = await self.migrate_autoresponders()
            migration_results["reminders"] = await self.migrate_reminders()
            migration_results["sticky_messages"] = await self.migrate_sticky_messages()
            migration_results["guild_configurations"] = await self.migrate_guild_configurations()
            migration_results["system_configurations"] = await self.migrate_system_configurations()
            
            # Calculate total - handle different return types
            for system, result in migration_results.items():
                if isinstance(result, int):
                    total_migrated += result
                elif isinstance(result, dict):
                    # Handle nested dictionary results (like from ticket migration)
                    total_migrated += sum(v for v in result.values() if isinstance(v, int))
                elif isinstance(result, bool):
                    # Handle boolean results
                    if result:
                        total_migrated += 1
            
            logger.info(f"Comprehensive migration completed! Migrated {total_migrated} total items")
            logger.info(f"Migration breakdown: {migration_results}")
            
            return migration_results
            
        except Exception as e:
            logger.error(f"Error during comprehensive migration: {e}")
            return None
    
    async def backup_json_files(self):
        """Create backup of all JSON files before migration"""
        logger.info("Creating backup of JSON files before migration...")
        
        backup_dir = "backup_pre_migration"
        os.makedirs(backup_dir, exist_ok=True)
        
        backed_up_files = 0
        
        for file_type, file_path in self.data_files.items():
            if os.path.exists(file_path):
                try:
                    import shutil
                    backup_path = os.path.join(backup_dir, file_path.replace('/', '_'))
                    shutil.copy2(file_path, backup_path)
                    backed_up_files += 1
                    logger.info(f"Backed up: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to backup {file_path}: {e}")
        
        logger.info(f"Backed up {backed_up_files} files to {backup_dir}")
        return backed_up_files