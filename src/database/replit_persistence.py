"""
Replit-Specific Data Persistence Manager
Uses Replit's persistent storage solutions to prevent data loss during deployments
"""

import os
import json
import logging
import asyncio
import base64
import gzip
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

logger = logging.getLogger(__name__)

class ReplitPersistenceManager:
    """Manages data persistence using Replit's persistent storage solutions"""
    
    def __init__(self):
        # Use PostgreSQL database for complete persistence
        self.db_pool = None
        
        # Critical data that must be preserved
        self.persistent_data_types = {
            "guild_settings": "config/guild_settings.json",
            "ticket_data": "config/tickets_data.json", 
            "feature_flags": "config/feature_flags.json",
            "saved_embeds": "src/data/saved_embeds.json",
            "ticket_settings": "src/data/ticket_settings.json",
            "panel_data": "src/data/panels_data.json",
            "autoresponders": "src/data/autoresponders.json",
            "sticky_messages": "src/data/sticky_messages.json",
            "reminders": "src/data/reminders.json",
            "server_stats": "config/server_stats.json"
        }
    
    async def initialize_persistence_system(self):
        """Initialize the persistence system using file-based backups"""
        try:
            logger.info("Initializing Replit persistence system...")
            
            # Check if this is a fresh deployment
            is_fresh_deployment = await self.detect_fresh_deployment()
            
            if is_fresh_deployment:
                logger.info("Fresh deployment detected - data protection activated")
                # For now, we ensure all directories exist and create defaults if needed
                self.ensure_critical_directories()
                await self.create_emergency_defaults()
            else:
                logger.info("Existing deployment - creating backup checkpoint")
                # Use the existing cloud backup system
                from src.database.cloud_backup import cloud_security
                result = cloud_security.create_secure_backup("replit_checkpoint")
                if result.get("success"):
                    logger.info(f"Replit checkpoint backup created: {result['backup_name']}")
            
            logger.info("Replit persistence system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing persistence system: {e}")
            return False
    
    def ensure_critical_directories(self):
        """Ensure all critical directories exist"""
        try:
            critical_dirs = [
                "config",
                "src/data",
                "src/data/transcripts", 
                "backups",
                ".deployment_state"
            ]
            
            for dir_path in critical_dirs:
                os.makedirs(dir_path, exist_ok=True)
                
                # Create .gitkeep to ensure directory persists
                gitkeep_path = os.path.join(dir_path, ".gitkeep")
                if not os.path.exists(gitkeep_path):
                    with open(gitkeep_path, 'w') as f:
                        f.write(f"# Persistent directory for SPROUTS bot\n")
                        f.write(f"# Created: {datetime.now().isoformat()}\n")
            
            logger.info("Critical directories ensured")
            
        except Exception as e:
            logger.error(f"Error ensuring directories: {e}")
    
    async def create_persistence_tables_placeholder(self):
        """Create database tables for persistent data storage"""
        try:
            async with self.db_pool.acquire() as conn:
                # Create persistent data storage table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS persistent_data (
                        id SERIAL PRIMARY KEY,
                        data_type VARCHAR(100) NOT NULL UNIQUE,
                        file_path VARCHAR(500) NOT NULL,
                        data_content TEXT NOT NULL,
                        data_hash VARCHAR(64),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        version INTEGER DEFAULT 1
                    )
                """)
                
                # Create deployment tracking table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS deployment_history (
                        id SERIAL PRIMARY KEY,
                        deployment_id VARCHAR(100) NOT NULL,
                        deployment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        bot_version VARCHAR(50),
                        data_snapshot_id INTEGER,
                        restoration_successful BOOLEAN DEFAULT FALSE,
                        notes TEXT
                    )
                """)
                
                # Create data snapshots table for versioning
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_snapshots (
                        id SERIAL PRIMARY KEY,
                        snapshot_name VARCHAR(200) NOT NULL,
                        snapshot_data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_count INTEGER DEFAULT 0,
                        total_size INTEGER DEFAULT 0
                    )
                """)
                
                logger.info("Persistence tables created/verified")
                
        except Exception as e:
            logger.error(f"Error creating persistence tables: {e}")
            raise
    
    async def detect_fresh_deployment(self) -> bool:
        """Detect if this is a fresh deployment by checking for missing files"""
        try:
            missing_files = 0
            total_files = len(self.persistent_data_types)
            
            for data_type, file_path in self.persistent_data_types.items():
                if not os.path.exists(file_path):
                    missing_files += 1
            
            # If more than 50% of files are missing, it's likely a fresh deployment
            is_fresh = (missing_files / total_files) > 0.5
            
            if is_fresh:
                logger.info(f"Fresh deployment detected: {missing_files}/{total_files} files missing")
            
            return is_fresh
            
        except Exception as e:
            logger.error(f"Error detecting fresh deployment: {e}")
            return False
    
    async def backup_all_data_to_database(self):
        """Backup all critical data to the database"""
        try:
            backed_up_count = 0
            deployment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            async with self.db_pool.acquire() as conn:
                # Create snapshot data
                snapshot_data = {}
                total_size = 0
                
                for data_type, file_path in self.persistent_data_types.items():
                    if os.path.exists(file_path):
                        try:
                            # Read and compress file data
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            
                            # Compress the data to save space
                            compressed_data = gzip.compress(file_content.encode('utf-8'))
                            encoded_data = base64.b64encode(compressed_data).decode('utf-8')
                            
                            # Calculate hash for integrity
                            import hashlib
                            file_hash = hashlib.sha256(file_content.encode('utf-8')).hexdigest()
                            
                            # Store in database
                            await conn.execute("""
                                INSERT INTO persistent_data 
                                (data_type, file_path, data_content, data_hash, updated_at, version)
                                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, 
                                    COALESCE((SELECT version + 1 FROM persistent_data WHERE data_type = $1), 1))
                                ON CONFLICT (data_type) 
                                DO UPDATE SET 
                                    data_content = EXCLUDED.data_content,
                                    data_hash = EXCLUDED.data_hash,
                                    updated_at = CURRENT_TIMESTAMP,
                                    version = persistent_data.version + 1
                            """, data_type, file_path, encoded_data, file_hash)
                            
                            # Add to snapshot
                            snapshot_data[data_type] = {
                                "file_path": file_path,
                                "hash": file_hash,
                                "size": len(file_content),
                                "backup_time": datetime.now().isoformat()
                            }
                            
                            total_size += len(file_content)
                            backed_up_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error backing up {file_path}: {e}")
                
                # Create snapshot record
                snapshot_id = await conn.fetchval("""
                    INSERT INTO data_snapshots (snapshot_name, snapshot_data, file_count, total_size)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """, f"deployment_backup_{deployment_id}", json.dumps(snapshot_data), backed_up_count, total_size)
                
                # Record deployment
                await conn.execute("""
                    INSERT INTO deployment_history 
                    (deployment_id, bot_version, data_snapshot_id, notes)
                    VALUES ($1, $2, $3, $4)
                """, deployment_id, "2.0", snapshot_id, f"Backed up {backed_up_count} files")
                
                logger.info(f"Successfully backed up {backed_up_count} files to database")
                return {"success": True, "files_backed_up": backed_up_count, "snapshot_id": snapshot_id}
                
        except Exception as e:
            logger.error(f"Error backing up data to database: {e}")
            return {"success": False, "error": str(e)}
    
    async def restore_all_data_from_database(self):
        """Restore all critical data from the database"""
        try:
            restored_count = 0
            
            async with self.db_pool.acquire() as conn:
                # Get all persistent data
                rows = await conn.fetch("""
                    SELECT data_type, file_path, data_content, data_hash 
                    FROM persistent_data 
                    ORDER BY updated_at DESC
                """)
                
                for row in rows:
                    try:
                        data_type = row['data_type']
                        file_path = row['file_path']
                        encoded_data = row['data_content']
                        stored_hash = row['data_hash']
                        
                        # Decode and decompress data
                        compressed_data = base64.b64decode(encoded_data.encode('utf-8'))
                        file_content = gzip.decompress(compressed_data).decode('utf-8')
                        
                        # Verify integrity
                        import hashlib
                        current_hash = hashlib.sha256(file_content.encode('utf-8')).hexdigest()
                        
                        if current_hash != stored_hash:
                            logger.warning(f"Hash mismatch for {file_path} - data may be corrupted")
                        
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        # Restore file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(file_content)
                        
                        restored_count += 1
                        logger.info(f"Restored: {file_path}")
                        
                    except Exception as e:
                        logger.error(f"Error restoring {row['file_path']}: {e}")
                
                # Update deployment history
                deployment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                await conn.execute("""
                    INSERT INTO deployment_history 
                    (deployment_id, restoration_successful, notes)
                    VALUES ($1, $2, $3)
                """, f"restore_{deployment_id}", restored_count > 0, f"Restored {restored_count} files")
                
                logger.info(f"Successfully restored {restored_count} files from database")
                return {"success": True, "files_restored": restored_count}
                
        except Exception as e:
            logger.error(f"Error restoring data from database: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_emergency_defaults(self):
        """Create emergency default files if restoration fails"""
        try:
            logger.info("Creating emergency default files...")
            
            defaults = {
                "config/guild_settings.json": {},
                "config/tickets_data.json": {},
                "config/feature_flags.json": {
                    "core_help": True,
                    "core_utilities": True,
                    "developer_tools": True
                },
                "src/data/saved_embeds.json": {},
                "src/data/ticket_settings.json": {},
                "src/data/panels_data.json": {},
                "src/data/autoresponders.json": {},
                "src/data/sticky_messages.json": {},
                "src/data/reminders.json": {},
                "config/server_stats.json": {}
            }
            
            created_count = 0
            for file_path, default_data in defaults.items():
                if not os.path.exists(file_path):
                    try:
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, 'w') as f:
                            json.dump(default_data, f, indent=2)
                        created_count += 1
                        logger.info(f"Created emergency default: {file_path}")
                    except Exception as e:
                        logger.error(f"Error creating default {file_path}: {e}")
            
            logger.info(f"Created {created_count} emergency default files")
            return created_count
            
        except Exception as e:
            logger.error(f"Error creating emergency defaults: {e}")
            return 0
    
    async def get_persistence_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the persistence system"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get backup count
                backup_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM persistent_data
                """)
                
                # Get latest deployment info
                latest_deployment = await conn.fetchrow("""
                    SELECT * FROM deployment_history 
                    ORDER BY deployment_time DESC 
                    LIMIT 1
                """)
                
                # Get snapshot count
                snapshot_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM data_snapshots
                """)
                
                # Check file system status
                files_present = 0
                files_missing = []
                for data_type, file_path in self.persistent_data_types.items():
                    if os.path.exists(file_path):
                        files_present += 1
                    else:
                        files_missing.append(file_path)
                
                return {
                    "database_backups": backup_count,
                    "snapshots_available": snapshot_count,
                    "files_present": files_present,
                    "files_missing": files_missing,
                    "total_files": len(self.persistent_data_types),
                    "latest_deployment": dict(latest_deployment) if latest_deployment else None,
                    "system_health": "healthy" if len(files_missing) == 0 else "needs_attention"
                }
                
        except Exception as e:
            logger.error(f"Error getting persistence status: {e}")
            return {"error": str(e)}
    
    async def schedule_automatic_backups(self):
        """Schedule automatic backups every hour"""
        try:
            while True:
                await asyncio.sleep(3600)  # 1 hour
                logger.info("Running scheduled backup...")
                result = await self.backup_all_data_to_database()
                if result.get("success"):
                    logger.info(f"Scheduled backup completed: {result['files_backed_up']} files")
                else:
                    logger.error(f"Scheduled backup failed: {result.get('error')}")
        except Exception as e:
            logger.error(f"Error in scheduled backup: {e}")

# Global instance
replit_persistence = ReplitPersistenceManager()