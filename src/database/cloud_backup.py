"""
Enhanced Cloud Data Security and Backup System for SPROUTS Bot
Provides comprehensive data protection for cloud deployment
"""

import json
import os
import shutil
import logging
import datetime
import hashlib
import gzip
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

class CloudDataSecurity:
    """Enhanced data security and backup system for cloud deployment"""
    
    def __init__(self):
        self.backup_dir = "backups"
        self.config_dir = "config"
        self.data_dir = "src/data"
        self.max_backups = 20  # Keep 20 most recent backups
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Critical data files that must never be lost
        self.critical_files = [
            "config/guild_settings.json",
            "config/tickets_data.json", 
            "config/feature_flags.json",
            "src/data/saved_embeds.json",
            "src/data/ticket_settings.json",
            "src/data/panels_data.json",
            "src/data/autoresponders.json",
            "src/data/sticky_messages.json",
            "src/data/reminders.json"
        ]
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file for integrity checking"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def create_secure_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a comprehensive secure backup with integrity verification"""
        try:
            if not backup_name:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"secure_backup_{timestamp}"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            backup_manifest = {
                "backup_name": backup_name,
                "created_at": datetime.datetime.now().isoformat(),
                "files": {},
                "integrity_hashes": {},
                "version": "2.0",
                "description": "Enhanced secure backup with integrity verification"
            }
            
            # Backup all critical files
            files_backed_up = 0
            for file_path in self.critical_files:
                if os.path.exists(file_path):
                    try:
                        # Create directory structure in backup
                        backup_file_path = os.path.join(backup_path, file_path)
                        os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(file_path, backup_file_path)
                        
                        # Calculate and store hash
                        file_hash = self.calculate_file_hash(file_path)
                        backup_manifest["files"][file_path] = {
                            "size": os.path.getsize(file_path),
                            "modified": datetime.datetime.fromtimestamp(
                                os.path.getmtime(file_path)
                            ).isoformat(),
                            "hash": file_hash
                        }
                        backup_manifest["integrity_hashes"][file_path] = file_hash
                        files_backed_up += 1
                        
                    except Exception as e:
                        logger.error(f"Error backing up {file_path}: {e}")
            
            # Backup entire transcripts directory
            transcripts_source = "src/data/transcripts"
            if os.path.exists(transcripts_source):
                transcripts_backup = os.path.join(backup_path, transcripts_source)
                try:
                    shutil.copytree(transcripts_source, transcripts_backup)
                    # Count transcript files
                    transcript_count = len([f for f in os.listdir(transcripts_source) 
                                          if f.endswith('.html')])
                    backup_manifest["transcripts"] = {
                        "count": transcript_count,
                        "path": transcripts_source
                    }
                except Exception as e:
                    logger.error(f"Error backing up transcripts: {e}")
            
            # Save backup manifest
            manifest_path = os.path.join(backup_path, "backup_manifest.json")
            with open(manifest_path, 'w') as f:
                json.dump(backup_manifest, f, indent=2)
            
            # Compress backup for space efficiency
            self.compress_backup(backup_path)
            
            logger.info(f"Secure backup created: {backup_name} ({files_backed_up} files)")
            return {
                "success": True,
                "backup_name": backup_name,
                "files_backed_up": files_backed_up,
                "path": backup_path
            }
            
        except Exception as e:
            logger.error(f"Error creating secure backup: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def compress_backup(self, backup_path: str):
        """Compress backup directory to save space"""
        try:
            # Create compressed archive
            archive_path = f"{backup_path}.tar.gz"
            shutil.make_archive(backup_path, 'gztar', backup_path)
            
            # Remove uncompressed directory
            shutil.rmtree(backup_path)
            
            logger.info(f"Backup compressed: {archive_path}")
            
        except Exception as e:
            logger.error(f"Error compressing backup: {e}")
    
    def verify_backup_integrity(self, backup_name: str) -> Dict[str, Any]:
        """Verify backup integrity using stored hashes"""
        try:
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.tar.gz")
            if not os.path.exists(backup_path):
                return {"success": False, "error": "Backup not found"}
            
            # Extract backup temporarily for verification
            temp_extract = f"{backup_path}_temp"
            shutil.unpack_archive(backup_path, temp_extract)
            
            # Load manifest
            manifest_path = os.path.join(temp_extract, backup_name, "backup_manifest.json")
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            verification_results = {
                "backup_name": backup_name,
                "verified_files": 0,
                "failed_files": [],
                "integrity_check": True
            }
            
            # Verify each file's integrity
            for file_path, file_info in manifest["files"].items():
                backup_file_path = os.path.join(temp_extract, backup_name, file_path)
                if os.path.exists(backup_file_path):
                    current_hash = self.calculate_file_hash(backup_file_path)
                    if current_hash == file_info["hash"]:
                        verification_results["verified_files"] += 1
                    else:
                        verification_results["failed_files"].append(file_path)
                        verification_results["integrity_check"] = False
                else:
                    verification_results["failed_files"].append(file_path)
                    verification_results["integrity_check"] = False
            
            # Cleanup temporary extraction
            shutil.rmtree(temp_extract)
            
            logger.info(f"Backup verification completed: {backup_name}")
            return {"success": True, "results": verification_results}
            
        except Exception as e:
            logger.error(f"Error verifying backup integrity: {e}")
            return {"success": False, "error": str(e)}
    
    def restore_from_backup(self, backup_name: str) -> Dict[str, Any]:
        """Restore data from a secure backup"""
        try:
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.tar.gz")
            if not os.path.exists(backup_path):
                return {"success": False, "error": "Backup not found"}
            
            # Create current backup before restoration
            pre_restore_backup = self.create_secure_backup(f"pre_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Extract backup
            temp_extract = f"{backup_path}_restore"
            shutil.unpack_archive(backup_path, temp_extract)
            
            restore_results = {
                "backup_name": backup_name,
                "restored_files": 0,
                "failed_files": [],
                "pre_restore_backup": pre_restore_backup.get("backup_name", "failed")
            }
            
            # Load manifest
            manifest_path = os.path.join(temp_extract, backup_name, "backup_manifest.json")
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Restore each file
            for file_path in manifest["files"].keys():
                backup_file_path = os.path.join(temp_extract, backup_name, file_path)
                if os.path.exists(backup_file_path):
                    try:
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        # Restore file
                        shutil.copy2(backup_file_path, file_path)
                        restore_results["restored_files"] += 1
                        
                    except Exception as e:
                        logger.error(f"Error restoring {file_path}: {e}")
                        restore_results["failed_files"].append(file_path)
                else:
                    restore_results["failed_files"].append(file_path)
            
            # Restore transcripts if they exist
            transcripts_backup = os.path.join(temp_extract, backup_name, "src/data/transcripts")
            if os.path.exists(transcripts_backup):
                try:
                    if os.path.exists("src/data/transcripts"):
                        shutil.rmtree("src/data/transcripts")
                    shutil.copytree(transcripts_backup, "src/data/transcripts")
                except Exception as e:
                    logger.error(f"Error restoring transcripts: {e}")
            
            # Cleanup temporary extraction
            shutil.rmtree(temp_extract)
            
            logger.info(f"Data restored from backup: {backup_name}")
            return {"success": True, "results": restore_results}
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_old_backups(self):
        """Remove old backups to save space, keeping the most recent ones"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.tar.gz') and file.startswith('secure_backup_'):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups if we have more than max_backups
            if len(backup_files) > self.max_backups:
                for file_path, _ in backup_files[self.max_backups:]:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed old backup: {os.path.basename(file_path)}")
                    except Exception as e:
                        logger.error(f"Error removing old backup {file_path}: {e}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get comprehensive backup system status"""
        try:
            status = {
                "total_backups": 0,
                "total_size_mb": 0,
                "latest_backup": None,
                "critical_files_status": {},
                "storage_health": "healthy"
            }
            
            # Count backups and calculate size
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.tar.gz'):
                    file_path = os.path.join(self.backup_dir, file)
                    size = os.path.getsize(file_path)
                    backup_files.append({
                        "name": file,
                        "size_mb": round(size / (1024 * 1024), 2),
                        "created": datetime.datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).isoformat()
                    })
                    status["total_size_mb"] += round(size / (1024 * 1024), 2)
            
            status["total_backups"] = len(backup_files)
            
            # Find latest backup
            if backup_files:
                latest = max(backup_files, key=lambda x: x["created"])
                status["latest_backup"] = latest
            
            # Check critical files status
            for file_path in self.critical_files:
                status["critical_files_status"][file_path] = {
                    "exists": os.path.exists(file_path),
                    "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    "last_modified": datetime.datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).isoformat() if os.path.exists(file_path) else None
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting backup status: {e}")
            return {"error": str(e)}
    
    async def auto_backup_schedule(self, interval_hours: int = 6):
        """Automated backup scheduling for continuous data protection"""
        while True:
            try:
                # Create automatic backup
                result = self.create_secure_backup(
                    f"auto_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                if result["success"]:
                    logger.info(f"Automatic backup completed: {result['backup_name']}")
                    
                    # Cleanup old backups
                    self.cleanup_old_backups()
                else:
                    logger.error(f"Automatic backup failed: {result.get('error', 'Unknown error')}")
                
                # Wait for next backup cycle
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Error in auto backup schedule: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying

# Global instance
cloud_security = CloudDataSecurity()