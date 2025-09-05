"""
Data Migration Script - Move existing JSON data to PostgreSQL database
This ensures no data loss during the transition to persistent storage
"""

import json
import os
import logging
import asyncio
from typing import Dict, Any
from .connection import db_manager, TicketDatabase, PanelDatabase, SettingsDatabase

logger = logging.getLogger(__name__)

class DataMigrator:
    """Migrate existing JSON data to database"""
    
    def __init__(self):
        self.tickets_file = "config/tickets_data.json"
        self.panels_file = "data/panels_data.json" 
        self.guild_settings_file = "config/guild_settings.json"
        
    async def migrate_all_data(self):
        """Migrate all existing data to database"""
        logger.info("Starting data migration to database...")
        
        # Initialize database
        if not await db_manager.initialize():
            logger.error("Failed to initialize database for migration")
            return False
            
        try:
            # Migrate tickets
            tickets_migrated = await self.migrate_tickets()
            logger.info(f"Migrated {tickets_migrated} tickets")
            
            # Migrate panels  
            panels_migrated = await self.migrate_panels()
            logger.info(f"Migrated {panels_migrated} panels")
            
            # Migrate guild settings
            settings_migrated = await self.migrate_guild_settings()
            logger.info(f"Migrated {settings_migrated} guild settings")
            
            logger.info("Data migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error during data migration: {e}")
            return False
            
    async def migrate_tickets(self) -> int:
        """Migrate ticket data from JSON to database"""
        if not os.path.exists(self.tickets_file):
            logger.info("No existing tickets file found, skipping ticket migration")
            return 0
            
        try:
            with open(self.tickets_file, 'r') as f:
                tickets_data = json.load(f)
                
            migrated_count = 0
            
            for ticket_id, ticket_data in tickets_data.items():
                try:
                    # Convert string ID to int
                    ticket_id_int = int(ticket_id)
                    
                    success = TicketDatabase.create_ticket(
                        ticket_id=ticket_id_int,
                        guild_id=ticket_data.get('guild_id', 0),
                        channel_id=ticket_data.get('channel_id', 0),
                        creator_id=ticket_data.get('creator_id', 0),
                        reason=ticket_data.get('reason', 'No reason provided'),
                        panel_id=ticket_data.get('panel_id')
                    )
                    
                    if success:
                        # Update additional fields
                        updates = {}
                        if ticket_data.get('status'):
                            updates['status'] = ticket_data['status']
                        if ticket_data.get('claimed_by'):
                            updates['claimed_by'] = ticket_data['claimed_by']
                        if ticket_data.get('members'):
                            updates['members'] = ticket_data['members']
                        if ticket_data.get('tags'):
                            updates['tags'] = ticket_data['tags']
                        if ticket_data.get('closed_by'):
                            updates['closed_by'] = ticket_data['closed_by']
                        if ticket_data.get('transcript_url'):
                            updates['transcript_url'] = ticket_data['transcript_url']
                            
                        if updates:
                            TicketDatabase.update_ticket(ticket_id_int, **updates)
                            
                        migrated_count += 1
                        
                except Exception as e:
                    logger.error(f"Error migrating ticket {ticket_id}: {e}")
                    continue
                    
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error reading tickets file: {e}")
            return 0
            
    async def migrate_panels(self) -> int:
        """Migrate panel data from JSON to database"""
        if not os.path.exists(self.panels_file):
            logger.info("No existing panels file found, skipping panel migration")
            return 0
            
        try:
            with open(self.panels_file, 'r') as f:
                panels_data = json.load(f)
                
            migrated_count = 0
            
            for panel_id, panel_data in panels_data.items():
                try:
                    success = PanelDatabase.create_panel(
                        panel_id=panel_id,
                        guild_id=panel_data.get('guild_id', 0),
                        channel_id=panel_data.get('channel_id', 0),
                        message_id=panel_data.get('message_id', 0),
                        title=panel_data.get('title', 'Untitled Panel'),
                        created_by=panel_data.get('created_by', 0),
                        description=panel_data.get('description')
                    )
                    
                    if success:
                        migrated_count += 1
                        
                except Exception as e:
                    logger.error(f"Error migrating panel {panel_id}: {e}")
                    continue
                    
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error reading panels file: {e}")
            return 0
            
    async def migrate_guild_settings(self) -> int:
        """Migrate guild settings from JSON to database"""
        if not os.path.exists(self.guild_settings_file):
            logger.info("No existing guild settings file found, skipping settings migration")
            return 0
            
        try:
            with open(self.guild_settings_file, 'r') as f:
                guild_settings_data = json.load(f)
                
            migrated_count = 0
            
            for guild_id_str, settings in guild_settings_data.items():
                try:
                    guild_id = int(guild_id_str)
                    
                    success = SettingsDatabase.save_guild_settings(guild_id, settings)
                    
                    if success:
                        migrated_count += 1
                        
                except Exception as e:
                    logger.error(f"Error migrating settings for guild {guild_id_str}: {e}")
                    continue
                    
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error reading guild settings file: {e}")
            return 0
            
    async def backup_json_files(self):
        """Create backup of existing JSON files"""
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups/pre_migration_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        
        files_to_backup = [
            self.tickets_file,
            self.panels_file,
            self.guild_settings_file
        ]
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                shutil.copy2(file_path, backup_path)
                logger.info(f"Backed up {file_path} to {backup_path}")
                
        logger.info(f"JSON files backed up to {backup_dir}")

async def run_migration():
    """Run the data migration process"""
    migrator = DataMigrator()
    
    # Create backup first
    await migrator.backup_json_files()
    
    # Run migration
    success = await migrator.migrate_all_data()
    
    if success:
        logger.info("Data migration completed successfully!")
        logger.info("Your ticket data is now stored in the database and will persist across bot updates")
    else:
        logger.error("Data migration failed!")
        
    return success

if __name__ == "__main__":
    # Can be run standalone
    asyncio.run(run_migration())