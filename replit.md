# Overview

Sprouts is a comprehensive, production-ready Discord bot designed for server management and community engagement. The bot provides a complete suite of features including a ticket system, embed builder, auto-responders, utility commands, event logging, and real-time monitoring capabilities. Built with Python and discord.py, it includes both Discord functionality and web-based monitoring interfaces.

**PRODUCTION STATUS: FINALIZED AND DEPLOYMENT READY**
- Bot completely restructured and optimized for single-instance deployment
- All environment variables properly configured in app.json and .do/app.yaml
- Clean, organized codebase with proper file structure
- Single web process configuration eliminates duplicate message issues
- All features operational: ticket system, embed builder, auto-responders, logging, web dashboard
- Proper production logging and graceful shutdown handling implemented
- Clean file structure with unnecessary files removed and data properly organized
- ALL default Unicode emojis replaced with 3 custom animated SPROUTS emojis
- Invite checker system removed for simplified bot functionality
- Help command cleaned of duplicates and properly organized
- Data files organized: config/ for settings, src/data/ for application data and transcripts
- Ready for GitHub commit and Digital Ocean App Platform deployment

# User Preferences

Preferred communication style: Simple, everyday language.
Bot deployment preference: Digital Ocean App Platform with single-instance configuration

# System Architecture

## Core Framework
- **Discord Bot Framework**: Built on discord.py 2.3.2 with command and cog-based architecture
- **Command System**: Hybrid text command system with custom prefixes and mention support
- **Event System**: Comprehensive event listeners for guild management and logging

## Application Structure
- **Modular Cog Design**: Features organized into separate cogs (ticket, embed_builder, utilities, etc.)
- **Configuration Management**: JSON-based configuration files for guild-specific settings
- **Data Persistence**: File-based storage using JSON for tickets, embeds, and user data
- **Variable Processing**: Dynamic variable replacement system for customizable content

## Web Interface
- **Flask Dashboard**: Real-time bot monitoring and statistics at localhost:5000
- **Keep-Alive Service**: Health check endpoint running on port 8080
- **Multi-threaded Architecture**: Concurrent Discord bot and web server operation

## Database and Storage
- **File-based Storage**: JSON files for configuration and persistent data
- **MongoDB Support**: Required MongoDB integration via pymongo for data persistence
- **Organized Data Structure**: 
  - `config/` - Configuration files (guild settings, server stats, etc.)
  - `src/data/` - Application data (saved embeds, sticky messages, ticket settings)
  - `src/data/transcripts/` - Ticket transcripts and logs

## Security and Access Control
- **Owner-only Commands**: Developer commands restricted by Discord user ID
- **Guild-specific Settings**: Per-server configuration isolation
- **Staff Role Management**: Role-based permissions for ticket system and moderation

## Error Handling and Logging
- **Comprehensive Logging**: Multi-level logging to both file and console
- **Error Recovery**: Graceful error handling with fallback mechanisms
- **Event Tracking**: Command usage and DM logging capabilities

# Feature Set

## Core Systems
- **Ticket System**: Complete support ticket management with panels, claiming, priorities, transcripts
- **Embed Builder**: Visual embed creation with dropdown menus, live preview, and variable processing
- **Auto Responders**: Trigger-based automated message responses with variable support
- **Sticky Messages**: Channel-specific persistent messages that auto-repost
- **Reminders**: User reminder system with time parsing and notifications
- **Utilities**: Server info, user info, avatar display, ping checks, variable reference

## Administrative Features
- **Developer Commands**: Bot management, data operations, maintenance mode, changelog distribution
- **Server Stats**: Real-time server monitoring with auto-updating embeds
- **Event Logging**: Command logging, DM logging, guild event tracking
- **Rate Limit Monitoring**: Automatic rate limit detection and alerting

## Custom Branding
- **SPROUTS Animated Emojis**: Three custom animated emojis used throughout the bot
  - `SPROUTS_CHECK` - Success/confirmation actions
  - `SPROUTS_ERROR` - Error/failure messages  
  - `SPROUTS_WARNING` - Warning/caution notifications
- **Consistent Visual Identity**: All help commands and messages use custom emoji branding

# External Dependencies

## Core Discord Framework
- **discord.py**: Primary Discord API wrapper for bot functionality
- **PyNaCl**: Voice and audio processing support

## Web Services
- **Flask**: Web dashboard and monitoring interface
- **Jinja2**: Template engine for web interface rendering
- **Werkzeug**: WSGI toolkit for Flask applications

## Data Management
- **pymongo**: MongoDB client library for optional database support
- **PyYAML**: YAML configuration file processing
- **python-dotenv**: Environment variable management

## System Utilities
- **psutil**: System resource monitoring and statistics
- **aiohttp**: Asynchronous HTTP client for Discord API optimization
- **certifi**: SSL certificate verification

## Development and Deployment
- **typing-extensions**: Enhanced type hints for better code quality
- **pathlib**: Modern file path handling (built-in Python module)

The bot is designed to run in containerized environments like Replit and Digital Ocean App Platform, with automatic setup scripts and health monitoring endpoints for reliable deployment and maintenance.

## Clean File Structure

**Core Files:**
- `main.py` - Production entry point with logging and graceful shutdown
- `bot.py` - Discord bot class definition and configuration  
- `bot_with_web.py` - Combined bot + web server (current workflow)
- `config/` - All configuration files (server stats, guild settings, etc.)
- `src/data/` - All application data (embeds, tickets, transcripts)

**Organized Data Structure:**
- Configuration files in `config/` for settings and bot configuration
- Application data in `src/data/` including user embeds and ticket information  
- Transcripts properly stored in `src/data/transcripts/` for organization
- Source code modularized in `src/cogs/` by functionality

## Deployment Configuration

**Digital Ocean App Platform Ready:**
- `.do/app.yaml` - Native Digital Ocean configuration
- `Procfile` - Single web process definition
- `app.json` - Complete app metadata with all environment variables
- `runtime.txt` - Python 3.11.0 specification
- `main.py` - Production entry point with graceful shutdown
- `bot_with_web.py` - Combined bot and web server

**Environment Variables Configured:**
- `DISCORD_BOT_TOKEN` (required)
- `BOT_OWNER_ID` (required) 
- `DEFAULT_PREFIX` (defaults to "s.")
- `MONGO_URI` (required for data storage)
- `LOG_COMMANDS_CHANNEL` (defaults to empty)
- `LOG_DMS_CHANNEL` (defaults to empty)
- `LOG_GUILD_EVENTS` (defaults to empty)
- `EMBED_COLOR_NORMAL` (0x2ecc71)
- `EMBED_COLOR_ERROR` (0xe74c3c)
- `EMBED_COLOR_HIERARCHY` (0xFFE682)

**Health Monitoring:**
- Keep-alive endpoint on port 8080
- Web dashboard on port 5000
- Automatic health checks configured

# Recent Updates

**File Organization (Latest):**
- Moved `server_stats.json` from `src/data/` to `config/` for proper organization
- Relocated `transcripts/` folder into `src/data/transcripts/` for unified data structure
- Removed duplicate empty `data/` folder from root directory
- Updated all file references to use new organized structure

**System Cleanup:**
- Removed entire invite checker system (files, imports, help sections)
- Cleaned duplicate "Utilities" section from help command
- Removed all Python cache files and __pycache__ directories
- Updated data management help descriptions to reflect actual data types managed

**Emoji Implementation:**
- Replaced all Unicode emojis with custom SPROUTS animated emojis throughout the bot
- Fixed emoji display issues in ticket system, embed builder, and error messages
- Ensured consistent branding across all bot interactions and help commands