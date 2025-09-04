# Installation & Setup

This guide will walk you through setting up Sprouts Discord bot from scratch.

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.11 or higher** installed on your system
- **Git** for cloning the repository
- **Discord Developer Account** to create a bot application
- **MongoDB Database** (local or cloud instance)
- **Text Editor** or IDE for configuration

## 🤖 Creating a Discord Bot

### Step 1: Create Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Enter **"Sprouts"** as the application name
4. Click **"Create"**

### Step 2: Configure Bot Settings

1. Navigate to the **"Bot"** section in the left sidebar
2. Click **"Add Bot"**
3. Under **"Privileged Gateway Intents"**, enable:
   - ✅ **Presence Intent**
   - ✅ **Server Members Intent** 
   - ✅ **Message Content Intent**

### Step 3: Get Bot Token

1. In the **"Bot"** section, click **"Reset Token"**
2. **Copy the token** - you'll need this later
3. ⚠️ **Keep this token secret** - never share it publicly

## 🔧 Environment Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/your-username/sprouts-bot.git
cd sprouts-bot
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Environment Variables

Create a `.env` file in the root directory:

```env
# Required Settings
DISCORD_BOT_TOKEN=your_bot_token_here
BOT_OWNER_ID=your_discord_user_id
MONGO_URI=your_mongodb_connection_string

# Optional Settings
DEFAULT_PREFIX=s.
LOG_COMMANDS_CHANNEL=
LOG_DMS_CHANNEL=
LOG_GUILD_EVENTS=

# Embed Colors (Hex values)
EMBED_COLOR_NORMAL=0x2ecc71
EMBED_COLOR_ERROR=0xe74c3c
EMBED_COLOR_HIERARCHY=0xFFE682
```

### Step 4: MongoDB Setup

#### Option A: MongoDB Atlas (Cloud)
1. Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a new cluster
3. Get connection string
4. Add to `MONGO_URI` in `.env`

#### Option B: Local MongoDB
```bash
# Install MongoDB locally
# Ubuntu/Debian
sudo apt install mongodb

# macOS with Homebrew
brew install mongodb/brew/mongodb-community

# Start MongoDB service
sudo systemctl start mongodb

# Connection string for local instance
MONGO_URI=mongodb://localhost:27017/sprouts
```

## 🚀 First Run

### Step 1: Test Configuration

```bash
python -c "from config import *; print('Configuration loaded successfully!')"
```

### Step 2: Start the Bot

```bash
python main.py
```

You should see output similar to:
```
INFO: Starting Sprouts Bot (Production Mode)...
INFO: Bot is starting up...
INFO: sprouts#4364 has connected to Discord!
INFO: Bot is in X guilds
```

### Step 3: Verify Web Dashboard

Visit `http://localhost:5000` to access the web dashboard and verify everything is working.

## 📝 Bot Permissions

When inviting the bot to your server, ensure it has these permissions:

### Essential Permissions
- ✅ **Read Messages**
- ✅ **Send Messages** 
- ✅ **Embed Links**
- ✅ **Attach Files**
- ✅ **Read Message History**
- ✅ **Add Reactions**
- ✅ **Use External Emojis**

### Administrative Permissions
- ✅ **Manage Messages** (for sticky messages)
- ✅ **Manage Channels** (for ticket system)
- ✅ **Manage Roles** (for ticket permissions)
- ✅ **View Audit Log** (for logging features)

### Invite URL Generator

Use this URL template, replacing `YOUR_CLIENT_ID` with your bot's client ID:

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8589934592&scope=bot%20applications.commands
```

## 🔍 Verification

### Test Basic Commands

In your Discord server:

```
s.help          # Display help menu
s.ping          # Check bot responsiveness  
s.info          # Show bot information
```

### Test Core Features

```
s.ticket setup  # Initialize ticket system
s.embed create  # Launch embed builder
s.sticky add    # Create sticky message
```

## ❌ Common Issues

### Bot Not Responding
- ✅ Check bot token is correct
- ✅ Verify bot has message permissions
- ✅ Ensure intents are enabled

### Database Connection Failed
- ✅ Verify MongoDB is running
- ✅ Check connection string format
- ✅ Ensure database allows connections

### Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Port Already in Use
```bash
# Kill process using port 5000
sudo lsof -ti:5000 | xargs kill -9
```

## ✅ Next Steps

Once installation is complete:

1. **[Configure Basic Settings](configuration.md)** - Set up prefixes, colors, and channels
2. **[Take First Steps](first-steps.md)** - Learn essential commands and setup
3. **[Explore Features](../features/)** - Dive into tickets, embeds, and automation

---

**Need help?** Check our [Troubleshooting Guide](../support/troubleshooting.md) or join the support server.