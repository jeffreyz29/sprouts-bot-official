"""
Comprehensive Database Access Layer for All Bot Data
Provides database operations for all bot systems
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from psycopg2.extras import Json
from .connection import db_manager

logger = logging.getLogger(__name__)


class SavedEmbedsDatabase:
    """Database operations for saved embeds"""
    
    @staticmethod
    def save_embed(guild_id: int, user_id: int, embed_name: str, embed_data: dict):
        """Save an embed to database"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO saved_embeds (guild_id, user_id, embed_name, embed_data, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (guild_id, user_id, embed_name) 
            DO UPDATE SET embed_data = %s, updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(query, (guild_id, user_id, embed_name, Json(embed_data), Json(embed_data)))
            conn.commit()
            logger.info(f"Saved embed '{embed_name}' for user {user_id} in guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving embed: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)
    
    @staticmethod
    def get_user_embeds(guild_id: int, user_id: int) -> List[Dict]:
        """Get all embeds for a user in a guild"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT embed_name, embed_data, created_at, updated_at 
                FROM saved_embeds 
                WHERE guild_id = %s AND user_id = %s
                ORDER BY embed_name
            """, (guild_id, user_id))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting user embeds: {e}")
            return []
        finally:
            if conn:
                db_manager.return_connection(conn)
    
    @staticmethod
    def delete_embed(guild_id: int, user_id: int, embed_name: str) -> bool:
        """Delete a specific embed"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM saved_embeds 
                WHERE guild_id = %s AND user_id = %s AND embed_name = %s
            """, (guild_id, user_id, embed_name))
            
            success = cursor.rowcount > 0
            conn.commit()
            
            if success:
                logger.info(f"Deleted embed '{embed_name}' for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting embed: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)


class AutoresponderDatabase:
    """Database operations for autoresponders"""
    
    @staticmethod
    def create_autoresponder(guild_id: int, trigger: str, response: str, created_by: int, match_type: str = 'contains'):
        """Create new autoresponder"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO autoresponders (guild_id, trigger_text, response_text, created_by, match_type)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (guild_id, trigger, response, created_by, match_type))
            
            autoresponder_id = cursor.fetchone()['id']
            conn.commit()
            logger.info(f"Created autoresponder {autoresponder_id} in guild {guild_id}")
            return autoresponder_id
            
        except Exception as e:
            logger.error(f"Error creating autoresponder: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                db_manager.return_connection(conn)
    
    @staticmethod
    def get_guild_autoresponders(guild_id: int, active_only: bool = True) -> List[Dict]:
        """Get all autoresponders for a guild"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, trigger_text, response_text, created_by, match_type, is_active, created_at
                FROM autoresponders 
                WHERE guild_id = %s
            """
            
            params = [guild_id]
            if active_only:
                query += " AND is_active = true"
            
            query += " ORDER BY created_at"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting autoresponders: {e}")
            return []
        finally:
            if conn:
                db_manager.return_connection(conn)
    
    @staticmethod
    def delete_autoresponder(autoresponder_id: int) -> bool:
        """Delete an autoresponder"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM autoresponders WHERE id = %s", (autoresponder_id,))
            success = cursor.rowcount > 0
            conn.commit()
            
            if success:
                logger.info(f"Deleted autoresponder {autoresponder_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting autoresponder: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)


class ReminderDatabase:
    """Database operations for reminders"""
    
    @staticmethod
    def create_reminder(user_id: int, channel_id: int, message: str, remind_at: datetime, guild_id: int = None, is_dm: bool = False):
        """Create new reminder"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO reminders (user_id, guild_id, channel_id, message, remind_at, is_dm)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, guild_id, channel_id, message, remind_at, is_dm))
            
            reminder_id = cursor.fetchone()['id']
            conn.commit()
            logger.info(f"Created reminder {reminder_id} for user {user_id}")
            return reminder_id
            
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                db_manager.return_connection(conn)
    
    @staticmethod
    def get_due_reminders() -> List[Dict]:
        """Get all reminders that are due"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, guild_id, channel_id, message, remind_at, is_dm
                FROM reminders 
                WHERE remind_at <= CURRENT_TIMESTAMP AND is_completed = false
                ORDER BY remind_at
            """)
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting due reminders: {e}")
            return []
        finally:
            if conn:
                db_manager.return_connection(conn)
    
    @staticmethod
    def complete_reminder(reminder_id: int) -> bool:
        """Mark reminder as completed"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE reminders SET is_completed = true 
                WHERE id = %s
            """, (reminder_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
            
        except Exception as e:
            logger.error(f"Error completing reminder: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)


class StickyMessageDatabase:
    """Database operations for sticky messages"""
    
    @staticmethod
    def create_sticky_message(guild_id: int, channel_id: int, content: str, created_by: int, embed_data: dict = None):
        """Create or update sticky message for channel"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sticky_messages (guild_id, channel_id, message_content, embed_data, created_by)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (guild_id, channel_id) 
                DO UPDATE SET 
                    message_content = %s,
                    embed_data = %s,
                    created_by = %s,
                    created_at = CURRENT_TIMESTAMP,
                    is_active = true
                RETURNING id
            """, (guild_id, channel_id, content, Json(embed_data) if embed_data else None, created_by,
                  content, Json(embed_data) if embed_data else None, created_by))
            
            sticky_id = cursor.fetchone()['id']
            conn.commit()
            logger.info(f"Created/updated sticky message {sticky_id} in channel {channel_id}")
            return sticky_id
            
        except Exception as e:
            logger.error(f"Error creating sticky message: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                db_manager.return_connection(conn)
    
    @staticmethod
    def get_sticky_message(guild_id: int, channel_id: int) -> Optional[Dict]:
        """Get sticky message for channel"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, message_content, embed_data, created_by, last_message_id, is_active
                FROM sticky_messages 
                WHERE guild_id = %s AND channel_id = %s AND is_active = true
            """, (guild_id, channel_id))
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting sticky message: {e}")
            return None
        finally:
            if conn:
                db_manager.return_connection(conn)
    
    @staticmethod
    def update_last_message(guild_id: int, channel_id: int, message_id: int) -> bool:
        """Update the last message ID for sticky message"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sticky_messages 
                SET last_message_id = %s
                WHERE guild_id = %s AND channel_id = %s
            """, (message_id, guild_id, channel_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
            
        except Exception as e:
            logger.error(f"Error updating sticky message: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)


class GuildConfigDatabase:
    """Database operations for comprehensive guild configuration"""
    
    @staticmethod
    def get_guild_config(guild_id: int) -> Dict:
        """Get comprehensive guild configuration"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM guild_config WHERE guild_id = %s
            """, (guild_id,))
            
            result = cursor.fetchone()
            return dict(result) if result else {}
            
        except Exception as e:
            logger.error(f"Error getting guild config: {e}")
            return {}
        finally:
            if conn:
                db_manager.return_connection(conn)
    
    @staticmethod
    def update_guild_config(guild_id: int, **config_data) -> bool:
        """Update guild configuration"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            if not config_data:
                return True
            
            # Build upsert query
            columns = ['guild_id'] + list(config_data.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            
            set_clauses = []
            for key in config_data.keys():
                if key != 'guild_id':
                    set_clauses.append(f"{key} = EXCLUDED.{key}")
            
            query = f"""
                INSERT INTO guild_config ({', '.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT (guild_id) 
                DO UPDATE SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            """
            
            values = [guild_id] + list(config_data.values())
            cursor.execute(query, values)
            conn.commit()
            logger.info(f"Updated guild config for {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating guild config: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)


class SystemConfigDatabase:
    """Database operations for system-wide configuration"""
    
    @staticmethod
    def get_config(key: str) -> Any:
        """Get system configuration value"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT value FROM system_config WHERE key = %s", (key,))
            result = cursor.fetchone()
            return result['value'] if result else None
            
        except Exception as e:
            logger.error(f"Error getting system config: {e}")
            return None
        finally:
            if conn:
                db_manager.return_connection(conn)
    
    @staticmethod
    def set_config(key: str, value: Any, description: str = None) -> bool:
        """Set system configuration value"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO system_config (key, value, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (key) 
                DO UPDATE SET value = %s, description = COALESCE(%s, system_config.description), updated_at = CURRENT_TIMESTAMP
            """, (key, Json(value), description, Json(value), description))
            
            conn.commit()
            logger.info(f"Set system config: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting system config: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)