"""
Database Connection and Management for Persistent Ticket Data
SPROUTS enterprise database persistence approach
"""

import os
import asyncio
import logging
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import psycopg2.pool
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for persistent ticket data storage"""
    
    def __init__(self):
        self._pool = None
        self.database_url = os.getenv('DATABASE_URL')
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            # Create connection pool for better performance
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=self.database_url,
                cursor_factory=RealDictCursor
            )
            logger.info("Database connection pool initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
            
    def get_connection(self):
        """Get database connection from pool"""
        if not self._pool:
            raise Exception("Database pool not initialized")
        return self._pool.getconn()
        
    def return_connection(self, conn):
        """Return connection to pool"""
        if self._pool:
            self._pool.putconn(conn)
            
    async def close_pool(self):
        """Close database connection pool"""
        if self._pool:
            self._pool.closeall()
            self._pool = None
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()

class TicketDatabase:
    """Database operations for tickets"""
    
    @staticmethod
    def create_ticket(ticket_id: int, guild_id: int, channel_id: int, creator_id: int, 
                     reason: str = "No reason provided", panel_id: str = None):
        """Create a new ticket in database"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO tickets (id, guild_id, channel_id, creator_id, reason, panel_id, members)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                guild_id = EXCLUDED.guild_id,
                channel_id = EXCLUDED.channel_id,
                creator_id = EXCLUDED.creator_id,
                reason = EXCLUDED.reason,
                panel_id = EXCLUDED.panel_id
            """
            
            cursor.execute(query, (ticket_id, guild_id, channel_id, creator_id, reason, panel_id, [creator_id]))
            conn.commit()
            logger.info(f"Created ticket {ticket_id} in database")
            return True
            
        except Exception as e:
            logger.error(f"Error creating ticket in database: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)
                
    @staticmethod
    def get_ticket(ticket_id: int) -> Optional[Dict]:
        """Get ticket data from database"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting ticket from database: {e}")
            return None
        finally:
            if conn:
                db_manager.return_connection(conn)
                
    @staticmethod
    def get_tickets_by_guild(guild_id: int, status: str = None) -> List[Dict]:
        """Get all tickets for a guild"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            if status:
                cursor.execute("SELECT * FROM tickets WHERE guild_id = %s AND status = %s", (guild_id, status))
            else:
                cursor.execute("SELECT * FROM tickets WHERE guild_id = %s", (guild_id,))
                
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting guild tickets from database: {e}")
            return []
        finally:
            if conn:
                db_manager.return_connection(conn)
                
    @staticmethod
    def get_ticket_by_channel(channel_id: int) -> Optional[Dict]:
        """Get ticket by channel ID"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tickets WHERE channel_id = %s", (channel_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting ticket by channel from database: {e}")
            return None
        finally:
            if conn:
                db_manager.return_connection(conn)
                
    @staticmethod
    def update_ticket(ticket_id: int, **updates):
        """Update ticket data"""
        if not updates:
            return True
            
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Build dynamic UPDATE query
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                values.append(value)
                
            values.append(ticket_id)  # For WHERE clause
            
            query = f"UPDATE tickets SET {', '.join(set_clauses)} WHERE id = %s"
            cursor.execute(query, values)
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating ticket in database: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)
                
    @staticmethod
    def close_ticket(ticket_id: int, closed_by: int, reason: str = "No reason provided"):
        """Close a ticket"""
        return TicketDatabase.update_ticket(
            ticket_id,
            status='closed',
            closed_by=closed_by,
            closed_at=datetime.utcnow(),
            reason=reason
        )
        
    @staticmethod
    def delete_ticket(ticket_id: int):
        """Delete ticket from database"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error deleting ticket from database: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)
                
    @staticmethod
    def count_user_tickets(guild_id: int, user_id: int, status: str = 'open') -> int:
        """Count tickets for a user in a guild"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM tickets WHERE guild_id = %s AND creator_id = %s AND status = %s",
                (guild_id, user_id, status)
            )
            
            result = cursor.fetchone()
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Error counting user tickets: {e}")
            return 0
        finally:
            if conn:
                db_manager.return_connection(conn)

class PanelDatabase:
    """Database operations for ticket panels"""
    
    @staticmethod
    def create_panel(panel_id: str, guild_id: int, channel_id: int, message_id: int,
                    title: str, created_by: int, description: str = None):
        """Create a new panel in database"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO ticket_panels (id, guild_id, channel_id, message_id, title, description, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                guild_id = EXCLUDED.guild_id,
                channel_id = EXCLUDED.channel_id,
                message_id = EXCLUDED.message_id,
                title = EXCLUDED.title,
                description = EXCLUDED.description
            """
            
            cursor.execute(query, (panel_id, guild_id, channel_id, message_id, title, description, created_by))
            conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating panel in database: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)
                
    @staticmethod
    def get_panel(panel_id: str) -> Optional[Dict]:
        """Get panel data from database"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM ticket_panels WHERE id = %s", (panel_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting panel from database: {e}")
            return None
        finally:
            if conn:
                db_manager.return_connection(conn)
                
    @staticmethod
    def get_panels_by_guild(guild_id: int) -> List[Dict]:
        """Get all panels for a guild"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM ticket_panels WHERE guild_id = %s ORDER BY created_at DESC", (guild_id,))
            results = cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting guild panels from database: {e}")
            return []
        finally:
            if conn:
                db_manager.return_connection(conn)
                
    @staticmethod
    def delete_panel(panel_id: str):
        """Delete panel from database"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM ticket_panels WHERE id = %s", (panel_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error deleting panel from database: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)

class SettingsDatabase:
    """Database operations for guild settings"""
    
    @staticmethod
    def get_guild_settings(guild_id: int) -> Dict:
        """Get guild settings from database"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM guild_settings WHERE guild_id = %s", (guild_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            else:
                # Create default settings
                default_settings = {
                    'guild_id': guild_id,
                    'max_tickets_per_user': 10,
                    'naming_scheme': 'username',
                    'use_threads': False,
                    'prefix': 's.'
                }
                SettingsDatabase.save_guild_settings(guild_id, default_settings)
                return default_settings
                
        except Exception as e:
            logger.error(f"Error getting guild settings from database: {e}")
            return {'guild_id': guild_id, 'max_tickets_per_user': 10}
        finally:
            if conn:
                db_manager.return_connection(conn)
                
    @staticmethod
    def save_guild_settings(guild_id: int, settings: Dict):
        """Save guild settings to database"""
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO guild_settings 
            (guild_id, log_channel_id, staff_roles, ticket_category_id, max_tickets_per_user, 
             naming_scheme, use_threads, auto_close_hours, prefix, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (guild_id) DO UPDATE SET
                log_channel_id = EXCLUDED.log_channel_id,
                staff_roles = EXCLUDED.staff_roles,
                ticket_category_id = EXCLUDED.ticket_category_id,
                max_tickets_per_user = EXCLUDED.max_tickets_per_user,
                naming_scheme = EXCLUDED.naming_scheme,
                use_threads = EXCLUDED.use_threads,
                auto_close_hours = EXCLUDED.auto_close_hours,
                prefix = EXCLUDED.prefix,
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(query, (
                guild_id,
                settings.get('log_channel_id'),
                settings.get('staff_roles', []),
                settings.get('ticket_category_id'),
                settings.get('max_tickets_per_user', 10),
                settings.get('naming_scheme', 'username'),
                settings.get('use_threads', False),
                settings.get('auto_close_hours'),
                settings.get('prefix', 's.'),
                datetime.utcnow()
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving guild settings to database: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                db_manager.return_connection(conn)