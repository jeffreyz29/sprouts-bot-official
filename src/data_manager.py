"""
Centralized Data Manager for Sprouts Bot
Handles backup, restoration, and persistence of all bot configurations
"""

import json
import os
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Any
import asyncio

logger = logging.getLogger(__name__)

class DataManager:
    """Centralized manager for all bot data persistence and backup"""
    
    def __init__(self):
        self.backup_dir = "backups"
        self.config_files = {
            # Configuration files
            "guild_settings": "config/guild_settings.json",
            "tickets_data": "config/tickets_data.json", 
            "cmd_logging_settings": "config/cmd_logging_settings.json",
            "dm_logging_settings": "config/dm_logging_settings.json",
            "dm_settings": "config/dm_settings.json",
            "global_logging": "config/global_logging.json",
            "server_join_settings": "config/server_join_settings.json",
            "server_stats": "config/server_stats.json",
            "tags_data": "config/tags_data.json",
            
            # Data files
            "saved_embeds": "src/data/saved_embeds.json",
            "sticky_messages": "src/data/sticky_messages.json", 
            "ticket_settings": "src/data/ticket_settings.json",
            "autoresponders": "src/data/autoresponders.json",
            "reminders": "src/data/reminders.json",
            "reminder_counter": "src/data/reminder_counter.json",
            "panels_data": "src/data/panels_data.json",
            
            # Development settings
            "global_cooldown": "config/global_cooldown.json",
            "maintenance": "src/data/maintenance.json"
        }
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def create_backup(self, backup_name: str = None) -> str:
        """Create a complete backup of all bot data"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"sprouts_backup_{timestamp}"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            backed_up_files = []
            
            # Backup all configuration files
            for file_type, file_path in self.config_files.items():
                if os.path.exists(file_path):
                    # Create subdirectories in backup if needed
                    backup_file_path = os.path.join(backup_path, file_path)
                    os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                    
                    # Copy file to backup
                    shutil.copy2(file_path, backup_file_path)
                    backed_up_files.append(file_path)
                    logger.info(f"Backed up: {file_path}")
            
            # Backup transcripts directory
            transcripts_dir = "src/data/transcripts"
            if os.path.exists(transcripts_dir):
                backup_transcripts = os.path.join(backup_path, transcripts_dir)
                shutil.copytree(transcripts_dir, backup_transcripts, dirs_exist_ok=True)
                logger.info(f"Backed up transcripts directory")
            
            # Create backup metadata
            metadata = {
                "backup_name": backup_name,
                "timestamp": datetime.now().isoformat(),
                "files_backed_up": backed_up_files,
                "total_files": len(backed_up_files)
            }
            
            with open(os.path.join(backup_path, "backup_metadata.json"), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Created backup '{backup_name}' with {len(backed_up_files)} files")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restore bot data from a backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                logger.error(f"Backup '{backup_name}' not found")
                return False
            
            # Read backup metadata
            metadata_file = os.path.join(backup_path, "backup_metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"Restoring backup from {metadata.get('timestamp', 'unknown time')}")
            
            restored_files = []
            
            # Restore all files
            for file_type, file_path in self.config_files.items():
                backup_file_path = os.path.join(backup_path, file_path)
                
                if os.path.exists(backup_file_path):
                    # Ensure target directory exists
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Restore file
                    shutil.copy2(backup_file_path, file_path)
                    restored_files.append(file_path)
                    logger.info(f"Restored: {file_path}")
            
            # Restore transcripts directory
            backup_transcripts = os.path.join(backup_path, "src/data/transcripts")
            if os.path.exists(backup_transcripts):
                target_transcripts = "src/data/transcripts"
                if os.path.exists(target_transcripts):
                    shutil.rmtree(target_transcripts)
                shutil.copytree(backup_transcripts, target_transcripts)
                logger.info("Restored transcripts directory")
            
            logger.info(f"Restored {len(restored_files)} files from backup '{backup_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup '{backup_name}': {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        try:
            if not os.path.exists(self.backup_dir):
                return backups
            
            for item in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(backup_path):
                    metadata_file = os.path.join(backup_path, "backup_metadata.json")
                    
                    backup_info = {"name": item, "path": backup_path}
                    
                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            backup_info.update(metadata)
                        except:
                            pass
                    
                    # Get backup size and file count
                    try:
                        total_size = sum(
                            os.path.getsize(os.path.join(dirpath, filename))
                            for dirpath, dirnames, filenames in os.walk(backup_path)
                            for filename in filenames
                        )
                        backup_info["size_mb"] = round(total_size / (1024 * 1024), 2)
                    except:
                        backup_info["size_mb"] = 0
                    
                    backups.append(backup_info)
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def verify_data_integrity(self) -> Dict[str, bool]:
        """Verify that all critical data files exist and are valid"""
        integrity_report = {}
        
        for file_type, file_path in self.config_files.items():
            try:
                if os.path.exists(file_path):
                    # Try to parse JSON to verify integrity
                    with open(file_path, 'r') as f:
                        json.load(f)
                    integrity_report[file_type] = True
                else:
                    integrity_report[file_type] = False
                    logger.warning(f"Missing data file: {file_path}")
            except json.JSONDecodeError:
                integrity_report[file_type] = False
                logger.error(f"Corrupted JSON file: {file_path}")
            except Exception as e:
                integrity_report[file_type] = False
                logger.error(f"Error checking {file_path}: {e}")
        
        return integrity_report
    
    def create_empty_defaults(self):
        """Create empty default files for missing configurations"""
        defaults = {
            "guild_settings": {},
            "tickets_data": {},
            "cmd_logging_settings": {},
            "dm_logging_settings": {},
            "dm_settings": {},
            "global_logging": {},
            "server_join_settings": {},
            "server_stats": {},
            "tags_data": {},
            "saved_embeds": {},
            "sticky_messages": {},
            "ticket_settings": {},
            "autoresponders": {},
            "reminders": {},
            "reminder_counter": {"total_reminders": 0},
            "panels_data": {},
            "global_cooldown": {"cooldown_seconds": 0},
            "maintenance": {"enabled": False}
        }
        
        for file_type, default_data in defaults.items():
            if file_type in self.config_files:
                file_path = self.config_files[file_type]
                
                if not os.path.exists(file_path):
                    try:
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, 'w') as f:
                            json.dump(default_data, f, indent=2)
                        logger.info(f"Created default file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to create default file {file_path}: {e}")
    
    async def auto_backup_on_startup(self):
        """Create an automatic backup when the bot starts"""
        try:
            # Check if this is a fresh deployment from GitHub
            is_fresh_deployment = self.detect_fresh_deployment()
            
            # Only create startup backup if we have existing data
            has_data = any(os.path.exists(path) for path in self.config_files.values())
            
            if has_data:
                backup_path = self.create_backup("startup_backup")
                if backup_path:
                    logger.info("Created startup backup for data safety")
                    
                    # Clean up old startup backups (keep only 5 most recent)
                    await self.cleanup_old_backups(backup_prefix="startup_backup", keep_count=5)
            
            # If fresh deployment and we have a GitHub backup, restore it
            if is_fresh_deployment:
                await self.try_restore_from_github()
                    
        except Exception as e:
            logger.error(f"Failed to create startup backup: {e}")
    
    def detect_fresh_deployment(self) -> bool:
        """Detect if this is a fresh deployment from GitHub"""
        try:
            # Check for GitHub deployment indicators
            indicators = [
                # Check if .git directory exists (GitHub deployment)
                os.path.exists('.git'),
                # Check if most config files are missing (fresh deployment)
                len([path for path in self.config_files.values() if os.path.exists(path)]) < 3,
                # Check if backups directory is empty or missing
                not os.path.exists(self.backup_dir) or len(os.listdir(self.backup_dir)) == 0
            ]
            
            is_fresh = sum(indicators) >= 2
            if is_fresh:
                logger.info("Detected fresh GitHub deployment")
            
            return is_fresh
            
        except Exception as e:
            logger.error(f"Error detecting deployment status: {e}")
            return False
    
    async def try_restore_from_github(self):
        """Try to restore data from a GitHub-committed backup"""
        try:
            # Look for a special GitHub backup file
            github_backup_file = "github_restore_backup.json"
            
            if os.path.exists(github_backup_file):
                logger.info("📥 Found GitHub restore backup file")
                
                with open(github_backup_file, 'r') as f:
                    restore_data = json.load(f)
                
                backup_name = restore_data.get('backup_name')
                owner_id = restore_data.get('owner_id')
                created_by = restore_data.get('created_by')
                
                if backup_name and os.path.exists(os.path.join(self.backup_dir, backup_name)):
                    logger.info(f"Auto-restoring from GitHub backup: {backup_name}")
                    success = self.restore_backup(backup_name)
                    
                    if success:
                        logger.info("Successfully restored data from GitHub backup")
                        # Remove the restore trigger file
                        os.remove(github_backup_file)
                    else:
                        logger.error("Failed to restore GitHub backup")
                else:
                    logger.warning(f"GitHub backup '{backup_name}' not found")
            else:
                logger.info("ℹ️ No GitHub restore backup file found - fresh start")
                
        except Exception as e:
            logger.error(f"Error restoring from GitHub: {e}")
    
    def create_github_restore_file(self, backup_name: str, owner_id: int) -> bool:
        """Create a GitHub restore file for deployment restoration"""
        try:
            restore_data = {
                "backup_name": backup_name,
                "owner_id": owner_id,
                "created_by": "Sprouts Bot Owner",
                "created_at": datetime.now().isoformat(),
                "description": "This file triggers automatic data restoration on GitHub deployment"
            }
            
            with open("github_restore_backup.json", 'w') as f:
                json.dump(restore_data, f, indent=2)
            
            logger.info(f"Created GitHub restore file for backup: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating GitHub restore file: {e}")
            return False
    
    async def cleanup_old_backups(self, backup_prefix: str = None, keep_count: int = 10):
        """Clean up old backups to save space"""
        try:
            backups = self.list_backups()
            
            if backup_prefix:
                backups = [b for b in backups if b["name"].startswith(backup_prefix)]
            
            if len(backups) > keep_count:
                # Remove oldest backups
                to_remove = backups[keep_count:]
                for backup in to_remove:
                    backup_path = backup["path"]
                    if os.path.exists(backup_path):
                        shutil.rmtree(backup_path)
                        logger.info(f"Cleaned up old backup: {backup['name']}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")

# Global instance
data_manager = DataManager()