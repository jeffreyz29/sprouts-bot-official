# Configuration

Learn how to customize Sprouts bot settings for your Discord server.

## 🎛️ Basic Configuration

### Command Prefix

Change the bot's command prefix (default is `s.`):

```
s.setprefix !
s.setprefix sprouts
s.setprefix >>
```

### Bot Status & Activity

Customize bot presence:

```
# Set custom status
s.setstatus online
s.setstatus idle  
s.setstatus dnd
s.setstatus invisible

# Set custom activity
s.setactivity playing Managing your server
s.setactivity listening to your feedback
s.setactivity watching over your community
```

### Embed Colors

Customize embed colors for different message types:

```env
# In your .env file
EMBED_COLOR_NORMAL=0x2ecc71    # Green for success
EMBED_COLOR_ERROR=0xe74c3c     # Red for errors  
EMBED_COLOR_HIERARCHY=0xFFE682 # Yellow for warnings
```

## 🏷️ Server-Specific Settings

### Guild Configuration

Each server has its own configuration stored in `config/` directory:

```json
{
  "guild_id": "123456789012345678",
  "prefix": "s.",
  "ticket_settings": {
    "category_id": null,
    "log_channel_id": null,
    "staff_role_ids": []
  },
  "logging": {
    "commands_channel": null,
    "dms_channel": null,
    "events_enabled": false
  }
}
```

### Logging Setup

Configure different types of logging:

#### Command Logging
Track all bot command usage:
```
s.setcmdlog #bot-commands
s.removecmdlog  # Disable command logging
```

#### DM Logging  
Monitor direct messages sent to the bot:
```
s.setdmlog #dm-logs
s.removedmlog  # Disable DM logging
```

#### Event Logging
Log server events (joins, leaves, etc.):
```
s.toggleeventlog  # Enable/disable event logging
```

### Server Stats Monitor

Set up automatic server statistics tracking:

```
s.serverstats setup #stats-channel
```

This creates auto-updating embeds showing:
- 👥 **Member Count**
- 🤖 **Bot Count** 
- 📊 **Total Users**
- 📈 **Growth Statistics**

## 🎫 Ticket System Configuration

### Basic Setup

Initialize the ticket system:

```
s.ticket setup
```

This opens an interactive setup panel where you can configure:

- **🏷️ Category** - Where ticket channels are created
- **👥 Staff Roles** - Who can manage tickets
- **📝 Log Channel** - Where ticket activities are recorded
- **🎨 Embed Settings** - Customize ticket panel appearance

### Advanced Ticket Settings

Configure ticket-specific options:

```json
{
  "ticket_settings": {
    "category_id": "123456789012345678",
    "log_channel_id": "123456789012345678", 
    "staff_role_ids": ["123456789012345678"],
    "max_tickets_per_user": 3,
    "auto_close_inactive": true,
    "inactive_timeout": 86400,
    "transcript_enabled": true
  }
}
```

## 📝 Embed Builder Settings

### Saved Embeds

Configure persistent embed storage:

```
# Create and save embeds
s.embed create
s.embedlist        # View saved embeds
s.embeddel name    # Delete saved embed
```

### Default Templates

Set up default embed templates for common use cases:

- **Welcome Messages**
- **Server Rules** 
- **Announcement Templates**
- **Ticket Responses**

## 🤖 Auto Responder Configuration

### Creating Auto Responders

Set up automated responses to keywords:

```
s.autoresponder add "hello" "Hello there! Welcome to the server!"
s.autoresponder add "support" "Need help? Create a ticket with s.ticket create"
```

### Advanced Trigger Options

```json
{
  "trigger": "support",
  "response": "Need help? Click the button below!",
  "match_type": "contains",      // exact, contains, starts_with, ends_with
  "case_sensitive": false,
  "cooldown": 30,               // Seconds between triggers
  "channels": ["123456789"],     // Specific channels only
  "roles_required": [],         // Required roles to trigger
  "delete_trigger": false       // Delete original message
}
```

## 📌 Sticky Message Settings

### Basic Sticky Setup

Create persistent messages that repost automatically:

```
s.sticky add "📋 Server Rules: Please read #rules before participating!"
s.sticky remove   # Remove sticky from current channel
s.sticky list     # View all sticky messages
```

### Sticky Configuration Options

```json
{
  "channel_id": "123456789012345678",
  "message": "Your sticky message here",
  "embed": null,              // Optional embed object
  "repost_threshold": 5,      // Messages before repost
  "max_reposts": 50,          // Maximum reposts per day
  "enabled": true
}
```

## ⏰ Reminder System

### User Reminder Settings

Configure reminder limitations and defaults:

```json
{
  "max_reminders_per_user": 10,
  "max_reminder_duration": 2592000,  // 30 days in seconds
  "timezone_default": "UTC",
  "reminder_channel_fallback": null
}
```

### Time Parsing Configuration

Supported time formats:
- **Natural**: `in 5 minutes`, `tomorrow at 3pm`
- **Relative**: `5m`, `2h`, `1d`, `1w`
- **Absolute**: `2023-12-25 15:30`

## 🔒 Permission Configuration

### Role-Based Permissions

Configure which roles can use specific features:

```json
{
  "permissions": {
    "ticket_staff": ["123456789012345678"],
    "embed_creators": ["123456789012345678"],  
    "autoresponder_managers": ["123456789012345678"],
    "server_admins": ["123456789012345678"]
  }
}
```

### Channel Restrictions

Limit bot functionality to specific channels:

```json
{
  "channel_restrictions": {
    "tickets_only": ["123456789012345678"],
    "commands_disabled": ["123456789012345678"],
    "embed_creation": ["123456789012345678"]
  }
}
```

## 🎨 Customization Options

### Custom Emoji Integration

Replace default emojis with your server's custom emojis:

```python
# In src/emojis.py
SPROUTS_CHECK = "<a:custom_check:123456789012345678>"
SPROUTS_WARNING = "<a:custom_warning:123456789012345678>"  
SPROUTS_ERROR = "<a:custom_error:123456789012345678>"
```

### Message Templates

Customize bot response templates:

```json
{
  "messages": {
    "ticket_created": "🎫 Your ticket has been created: {channel_mention}",
    "ticket_closed": "✅ Ticket closed by {user_mention}",
    "reminder_sent": "⏰ Reminder: {reminder_text}",
    "embed_saved": "💾 Embed '{name}' has been saved!"
  }
}
```

## 📊 Data Management

### Database Configuration

Configure MongoDB storage settings:

```json
{
  "database": {
    "name": "sprouts_bot",
    "collections": {
      "guilds": "guild_settings",
      "tickets": "ticket_data",
      "reminders": "user_reminders",
      "embeds": "saved_embeds"
    }
  }
}
```

### File Storage

Configure local file storage paths:

```json
{
  "storage": {
    "config_path": "./config/",
    "data_path": "./src/data/",
    "transcripts_path": "./src/data/transcripts/",
    "logs_path": "./logs/"
  }
}
```

## ✅ Configuration Validation

### Test Your Configuration

Verify all settings are working correctly:

```
s.config test     # Test all configuration  
s.config reload   # Reload configuration files
s.config backup   # Create configuration backup
```

### Health Checks

Monitor configuration health:

```
s.health          # Overall bot health
s.health database # Database connectivity
s.health permissions # Permission validation
```

## 🔄 Configuration Updates

### Live Updates

Most settings can be updated without restarting the bot:

- ✅ **Prefixes** - Immediate effect
- ✅ **Logging channels** - Immediate effect  
- ✅ **Ticket settings** - Immediate effect
- ❌ **Environment variables** - Requires restart
- ❌ **Database settings** - Requires restart

### Backup & Restore

```bash
# Backup current configuration
python scripts/backup_config.py

# Restore from backup
python scripts/restore_config.py backup_2023_12_25.json
```

---

**Next:** Learn the [First Steps](first-steps.md) to start using your configured bot effectively.