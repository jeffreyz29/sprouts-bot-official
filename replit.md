# Overview

Sprouts is a comprehensive, production-ready Discord bot designed for server management and community engagement. The bot provides a complete suite of features including a ticket system, embed builder, auto-responders, utility commands, event logging, and real-time monitoring capabilities. Built with Python and discord.py, it includes both Discord functionality and web-based monitoring interfaces.

**PRODUCTION STATUS: FINALIZED AND DEPLOYMENT READY**
- Bot completely restructured and optimized for single-instance deployment
- All environment variables properly configured in app.json and .do/app.yaml
- Zero LSP diagnostics - clean, error-free codebase
- Single web process configuration eliminates duplicate message issues
- All features operational: ticket system, embed builder, auto-responders, logging, web dashboard
- Proper production logging and graceful shutdown handling implemented
- Clean file structure with unnecessary directories and files removed
- ALL default Unicode emojis removed - only 3 custom animated emojis used
- About command updated with dynamic title and Top.gg vote link
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
- **Data Organization**: Structured data storage in config/ and src/data/ directories

## Security and Access Control
- **Owner-only Commands**: Developer commands restricted by Discord user ID
- **Guild-specific Settings**: Per-server configuration isolation
- **Staff Role Management**: Role-based permissions for ticket system and moderation

## Error Handling and Logging
- **Comprehensive Logging**: Multi-level logging to both file and console
- **Error Recovery**: Graceful error handling with fallback mechanisms
- **Event Tracking**: Command usage and DM logging capabilities

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
- `src/cogs/help.py` - Help command system (duplicate modern_help.py removed)
- `src/cogs/invite_checker.py` - Advanced Discord invite validation system

**Structure Purpose:**
- `main.py` handles production startup, logging, signal handling
- `bot.py` contains the DiscordBot class and core functionality
- `bot_with_web.py` orchestrates both Discord bot and web dashboard
- `invite_checker.py` provides comprehensive invite scanning and validation

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