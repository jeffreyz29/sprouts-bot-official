"""
Comprehensive Database Schema for All Bot Data
Creates tables for persistent storage of all bot systems
"""

import psycopg2
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def initialize_comprehensive_schema(database_url: str) -> bool:
    """Initialize complete database schema for all bot data"""
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Create comprehensive schema for all bot data
        cursor.execute("""
            -- Saved Embeds table (for embed builder system)
            CREATE TABLE IF NOT EXISTS saved_embeds (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                embed_name VARCHAR(100) NOT NULL,
                embed_data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, embed_name)
            );
            
            -- Autoresponders table (for autoresponder system)
            CREATE TABLE IF NOT EXISTS autoresponders (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                trigger_text VARCHAR(500) NOT NULL,
                response_text TEXT NOT NULL,
                created_by BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT true,
                match_type VARCHAR(20) DEFAULT 'contains'
            );
            
            -- Reminders table (for reminder system)
            CREATE TABLE IF NOT EXISTS reminders (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                guild_id BIGINT,
                channel_id BIGINT NOT NULL,
                message TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_completed BOOLEAN DEFAULT false,
                is_dm BOOLEAN DEFAULT false
            );
            
            -- Sticky Messages table (for sticky message system)
            CREATE TABLE IF NOT EXISTS sticky_messages (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                message_content TEXT NOT NULL,
                embed_data JSONB,
                created_by BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_message_id BIGINT,
                is_active BOOLEAN DEFAULT true,
                UNIQUE(guild_id, channel_id)
            );
            
            -- Guild Configuration table (comprehensive settings)
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id BIGINT PRIMARY KEY,
                prefix VARCHAR(10) DEFAULT 's.',
                log_commands_channel BIGINT,
                log_dms_channel BIGINT,
                log_guild_events BOOLEAN DEFAULT false,
                server_stats_channel BIGINT,
                server_stats_message_id BIGINT,
                auto_stats_enabled BOOLEAN DEFAULT false,
                dm_logging_enabled BOOLEAN DEFAULT false,
                cmd_logging_enabled BOOLEAN DEFAULT false,
                maintenance_mode BOOLEAN DEFAULT false,
                server_join_logging BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- System Configuration table (global settings)
            CREATE TABLE IF NOT EXISTS system_config (
                key VARCHAR(100) PRIMARY KEY,
                value JSONB NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tags table (for tag system)
            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                tag_name VARCHAR(100) NOT NULL,
                tag_content TEXT NOT NULL,
                created_by BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                use_count INTEGER DEFAULT 0,
                UNIQUE(guild_id, tag_name)
            );
        """)
        
        # Create indexes for performance
        cursor.execute("""
            -- Indexes for saved embeds
            CREATE INDEX IF NOT EXISTS idx_saved_embeds_guild_user ON saved_embeds(guild_id, user_id);
            CREATE INDEX IF NOT EXISTS idx_saved_embeds_name ON saved_embeds(guild_id, embed_name);
            
            -- Indexes for autoresponders
            CREATE INDEX IF NOT EXISTS idx_autoresponders_guild ON autoresponders(guild_id);
            CREATE INDEX IF NOT EXISTS idx_autoresponders_active ON autoresponders(guild_id, is_active);
            
            -- Indexes for reminders
            CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id);
            CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at);
            CREATE INDEX IF NOT EXISTS idx_reminders_completed ON reminders(is_completed);
            CREATE INDEX IF NOT EXISTS idx_reminders_guild ON reminders(guild_id);
            
            -- Indexes for sticky messages
            CREATE INDEX IF NOT EXISTS idx_sticky_messages_guild ON sticky_messages(guild_id);
            CREATE INDEX IF NOT EXISTS idx_sticky_messages_channel ON sticky_messages(channel_id);
            CREATE INDEX IF NOT EXISTS idx_sticky_messages_active ON sticky_messages(guild_id, is_active);
            
            -- Indexes for tags
            CREATE INDEX IF NOT EXISTS idx_tags_guild ON tags(guild_id);
            CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(guild_id, tag_name);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Comprehensive database schema initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize comprehensive schema: {e}")
        return False

def check_schema_exists(database_url: str) -> dict:
    """Check which tables exist in the database"""
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        required_tables = [
            'tickets', 'ticket_panels', 'guild_settings',  # Existing tables
            'saved_embeds', 'autoresponders', 'reminders',  # New tables
            'sticky_messages', 'guild_config', 'system_config', 'tags'
        ]
        
        return {
            'existing': existing_tables,
            'required': required_tables,
            'missing': [t for t in required_tables if t not in existing_tables]
        }
        
    except Exception as e:
        logger.error(f"Failed to check schema: {e}")
        return {'existing': [], 'required': [], 'missing': []}