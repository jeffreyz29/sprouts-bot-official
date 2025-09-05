"""
Deployment Persistence Manager for SPROUTS Bot
Ensures data survives updates, pushes, and redeployments
"""

import os
import json
import shutil
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile
import zipfile

logger = logging.getLogger(__name__)

class DeploymentPersistenceManager:
    """Manages data persistence across deployments and updates"""
    
    def __init__(self):
        # Persistent directories that must survive rebuilds
        self.persistent_paths = [
            "config/",
            "src/data/",
            "backups/",
            "src/data/transcripts/",
            ".deployment_state/"
        ]
        
        # Critical files that must never be lost
        self.critical_files = [
            "config/guild_settings.json",
            "config/tickets_data.json", 
            "config/feature_flags.json",
            "src/data/saved_embeds.json",
            "src/data/ticket_settings.json",
            "src/data/panels_data.json",
            "src/data/autoresponders.json",
            "src/data/sticky_messages.json",
            "src/data/reminders.json",
            "config/server_stats.json"
        ]
        
        # Deployment state tracking
        self.state_dir = ".deployment_state"
        self.state_file = os.path.join(self.state_dir, "deployment_state.json")
        
        # Initialize state directory
        os.makedirs(self.state_dir, exist_ok=True)
        
        # Initialize deployment state
        self.deployment_state = self.load_deployment_state()
    
    def load_deployment_state(self) -> Dict[str, Any]:
        """Load deployment state from persistent storage"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            return {
                "last_deployment": None,
                "deployment_count": 0,
                "data_version": "1.0",
                "critical_files_hash": {},
                "backup_schedule": {
                    "pre_deployment": True,
                    "post_deployment": True,
                    "interval_hours": 6
                }
            }
        except Exception as e:
            logger.error(f"Error loading deployment state: {e}")
            return {}
    
    def save_deployment_state(self):
        """Save deployment state to persistent storage"""
        try:
            self.deployment_state["last_updated"] = datetime.now().isoformat()
            with open(self.state_file, 'w') as f:
                json.dump(self.deployment_state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving deployment state: {e}")
    
    def detect_deployment_change(self) -> bool:
        """Detect if this is a new deployment or rebuild"""
        try:
            # Check for indicators of new deployment
            indicators = {
                "git_commit_changed": self.check_git_commit_change(),
                "code_timestamp_changed": self.check_code_timestamp_change(),
                "missing_runtime_files": self.check_missing_runtime_files(),
                "environment_reset": self.check_environment_reset()
            }
            
            deployment_detected = any(indicators.values())
            
            if deployment_detected:
                logger.info(f"Deployment change detected: {indicators}")
                self.deployment_state["deployment_count"] += 1
                self.deployment_state["last_deployment"] = datetime.now().isoformat()
                self.save_deployment_state()
            
            return deployment_detected
            
        except Exception as e:
            logger.error(f"Error detecting deployment change: {e}")
            return False
    
    def check_git_commit_change(self) -> bool:
        """Check if git commit has changed"""
        try:
            if os.path.exists('.git'):
                # Get current commit
                current_commit = os.popen('git rev-parse HEAD 2>/dev/null').read().strip()
                last_commit = self.deployment_state.get("last_git_commit")
                
                if current_commit and current_commit != last_commit:
                    self.deployment_state["last_git_commit"] = current_commit
                    return True
            return False
        except:
            return False
    
    def check_code_timestamp_change(self) -> bool:
        """Check if main code files have newer timestamps"""
        try:
            main_files = ["bot.py", "main.py", "src/cogs/ticket.py"]
            newest_timestamp = 0
            
            for file_path in main_files:
                if os.path.exists(file_path):
                    timestamp = os.path.getmtime(file_path)
                    newest_timestamp = max(newest_timestamp, timestamp)
            
            last_code_timestamp = self.deployment_state.get("last_code_timestamp", 0)
            
            if newest_timestamp > last_code_timestamp:
                self.deployment_state["last_code_timestamp"] = newest_timestamp
                return True
                
            return False
        except:
            return False
    
    def check_missing_runtime_files(self) -> bool:
        """Check if runtime files are missing (indicating fresh deployment)"""
        try:
            runtime_indicators = [
                ".deployment_state/runtime.lock",
                "temp/",
                "__pycache__/"
            ]
            
            missing_count = sum(1 for path in runtime_indicators if not os.path.exists(path))
            return missing_count >= 2
        except:
            return False
    
    def check_environment_reset(self) -> bool:
        """Check if environment has been reset"""
        try:
            # Check if process ID has changed significantly
            current_pid = os.getpid()
            last_pid = self.deployment_state.get("last_process_id", current_pid)
            
            # Check if working directory is fresh
            cwd_created = os.path.getctime(".")
            last_cwd_time = self.deployment_state.get("last_cwd_time", cwd_created)
            
            self.deployment_state["last_process_id"] = current_pid
            self.deployment_state["last_cwd_time"] = cwd_created
            
            return abs(cwd_created - last_cwd_time) > 300  # 5 minutes difference
        except:
            return False
    
    async def pre_deployment_backup(self) -> Dict[str, Any]:
        """Create comprehensive backup before deployment"""
        try:
            logger.info("Creating pre-deployment backup...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"pre_deployment_{timestamp}"
            
            # Create secure backup using cloud security system
            from src.database.cloud_backup import cloud_security
            result = cloud_security.create_secure_backup(backup_name)
            
            if result.get("success"):
                # Store backup info in deployment state
                self.deployment_state["last_pre_deployment_backup"] = {
                    "name": backup_name,
                    "created": datetime.now().isoformat(),
                    "files_count": result.get("files_backed_up", 0)
                }
                self.save_deployment_state()
                
                logger.info(f"Pre-deployment backup created: {backup_name}")
                return result
            else:
                logger.error(f"Pre-deployment backup failed: {result.get('error')}")
                return result
                
        except Exception as e:
            logger.error(f"Error creating pre-deployment backup: {e}")
            return {"success": False, "error": str(e)}
    
    async def post_deployment_verification(self) -> Dict[str, Any]:
        """Verify data integrity after deployment"""
        try:
            logger.info("Verifying data integrity post-deployment...")
            
            verification_results = {
                "critical_files_present": 0,
                "critical_files_missing": [],
                "data_integrity_ok": True,
                "backup_system_ok": True,
                "total_checks": 0
            }
            
            # Check critical files
            for file_path in self.critical_files:
                verification_results["total_checks"] += 1
                if os.path.exists(file_path):
                    verification_results["critical_files_present"] += 1
                    
                    # Verify file is not empty and valid JSON
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        logger.debug(f"Verified: {file_path}")
                    except:
                        verification_results["critical_files_missing"].append(f"{file_path} (corrupted)")
                        verification_results["data_integrity_ok"] = False
                else:
                    verification_results["critical_files_missing"].append(file_path)
                    verification_results["data_integrity_ok"] = False
            
            # Check backup system
            backup_dir_exists = os.path.exists("backups")
            if not backup_dir_exists:
                verification_results["backup_system_ok"] = False
            
            # Log results
            if verification_results["data_integrity_ok"]:
                logger.info("Post-deployment verification passed")
            else:
                logger.warning(f"Post-deployment issues detected: {verification_results['critical_files_missing']}")
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Error in post-deployment verification: {e}")
            return {"data_integrity_ok": False, "error": str(e)}
    
    async def auto_restore_if_needed(self) -> bool:
        """Automatically restore data if deployment caused data loss"""
        try:
            verification = await self.post_deployment_verification()
            
            if not verification["data_integrity_ok"]:
                logger.warning("Data integrity issues detected, attempting auto-restore...")
                
                # Get the most recent backup
                last_backup = self.deployment_state.get("last_pre_deployment_backup")
                if last_backup:
                    backup_name = last_backup["name"]
                    
                    # Attempt restore
                    from src.database.cloud_backup import cloud_security
                    restore_result = cloud_security.restore_from_backup(backup_name)
                    
                    if restore_result.get("success"):
                        logger.info(f"Auto-restore successful from backup: {backup_name}")
                        return True
                    else:
                        logger.error(f"Auto-restore failed: {restore_result.get('error')}")
                        return False
                else:
                    logger.error("No recent backup available for auto-restore")
                    return False
            
            return True  # No restore needed
            
        except Exception as e:
            logger.error(f"Error in auto-restore: {e}")
            return False
    
    def create_persistence_indicators(self):
        """Create files that indicate persistent data locations"""
        try:
            # Create .gitkeep files in critical directories
            for path in self.persistent_paths:
                if os.path.isdir(path) or path.endswith('/'):
                    dir_path = path.rstrip('/')
                    os.makedirs(dir_path, exist_ok=True)
                    
                    gitkeep_path = os.path.join(dir_path, '.gitkeep')
                    if not os.path.exists(gitkeep_path):
                        with open(gitkeep_path, 'w') as f:
                            f.write(f"# Keep this directory for SPROUTS bot data persistence\n")
                            f.write(f"# Created: {datetime.now().isoformat()}\n")
            
            # Create README for deployment persistence
            readme_path = ".deployment_state/README.md"
            with open(readme_path, 'w') as f:
                f.write("# SPROUTS Bot Deployment Persistence\n\n")
                f.write("This directory contains deployment state and persistence information.\n")
                f.write("DO NOT DELETE - Required for data persistence across deployments.\n\n")
                f.write("## Critical Directories:\n")
                for path in self.persistent_paths:
                    f.write(f"- `{path}` - Contains bot data that must persist\n")
                
            logger.info("Created persistence indicators")
            
        except Exception as e:
            logger.error(f"Error creating persistence indicators: {e}")
    
    async def initialize_deployment_protection(self):
        """Initialize the complete deployment protection system"""
        try:
            logger.info("Initializing deployment protection system...")
            
            # Create persistence indicators
            self.create_persistence_indicators()
            
            # Check if this is a new deployment
            is_new_deployment = self.detect_deployment_change()
            
            if is_new_deployment:
                logger.info("New deployment detected - running protection protocols")
                
                # Verify data integrity
                verification = await self.post_deployment_verification()
                
                # Auto-restore if needed
                if not verification["data_integrity_ok"]:
                    restore_success = await self.auto_restore_if_needed()
                    if restore_success:
                        logger.info("Data successfully restored after deployment")
                    else:
                        logger.error("Failed to restore data after deployment")
                        # Create emergency defaults
                        from src.data_manager import data_manager
                        data_manager.create_empty_defaults()
                        logger.info("Created emergency default files")
            
            # Create backup for next deployment
            await self.pre_deployment_backup()
            
            logger.info("Deployment protection system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing deployment protection: {e}")
            return False

# Global instance
persistence_manager = DeploymentPersistenceManager()