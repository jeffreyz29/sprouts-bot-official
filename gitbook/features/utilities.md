# Utilities

Essential server management and information tools for Discord administrators and users.

## 🛠️ Overview

The Sprouts utilities system provides a comprehensive set of tools for server information, user management, and bot configuration, making server administration easier and more efficient.

### Key Features

- **📊 Server Information** - Comprehensive server statistics and details
- **👤 User Management** - User profiles, avatars, and information
- **🔧 Bot Configuration** - Prefix settings and bot management
- **🌐 Network Tools** - Ping tests and connection monitoring
- **🔍 Discord Tools** - Invite analysis and server discovery

## 📊 Server Information Commands

### Server Details

```
s.serverinfo
```

Displays comprehensive server information including:
- **Basic Details** - Name, ID, owner, creation date
- **Member Statistics** - Total members, verification level
- **Server Features** - Boost level, boost count, verification
- **Channel Counts** - Text, voice, and category channels
- **Role Information** - Total roles and permissions

### Channel Information

```
s.channelinfo [#channel]
```

Shows detailed channel information:
- **Channel Details** - Name, ID, type, creation date
- **Settings** - Category, position, NSFW status, slowmode
- **Topic** - Channel topic and description (if set)
- **Permissions** - Access controls and restrictions

**Examples:**
```
s.channelinfo                # Current channel info
s.channelinfo #general       # Specific channel info
s.channelinfo 123456789      # Channel info by ID
```

### Role Information

```
s.roleinfo <@role|role_name>
```

Displays detailed role information:
- **Role Details** - Name, ID, color, creation date
- **Settings** - Position, mentionable, hoisted status
- **Members** - Number of users with this role
- **Permissions** - Key permissions granted by role

**Examples:**
```
s.roleinfo @Moderator        # Role info by mention
s.roleinfo Admin             # Role info by name
s.roleinfo 987654321         # Role info by ID
```

## 👤 User Information Commands

### User Profiles

```
s.userinfo [@user]
```

Shows comprehensive user information:
- **User Details** - Username, display name, ID, bot status
- **Server Info** - Join date, nickname, top role
- **Account Info** - Creation date, status, activity
- **Presence** - Online status and current activity

**Examples:**
```
s.userinfo                   # Your own information
s.userinfo @username         # Specific user info
s.userinfo 123456789         # User info by ID
```

### Avatar Display

```
s.avatar [@user]
```

Displays user avatars in high resolution:
- **High-Quality Image** - Full resolution avatar display
- **Download Links** - PNG, JPG, and WebP format links
- **Server vs Global** - Shows both if different
- **Animated Support** - GIF support for Nitro users

**Examples:**
```
s.avatar                     # Your own avatar
s.avatar @username           # Specific user's avatar
s.avatar 123456789           # Avatar by user ID
```

## 🔧 Bot Configuration

### Prefix Management

```
s.prefix
```

Shows the current bot prefix for the server with usage instructions.

```
s.setprefix <new_prefix>
```

Changes the bot's command prefix for the current server (Administrator only):

**Examples:**
```
s.setprefix !                # Change prefix to !
s.setprefix bot.             # Change prefix to bot.
s.setprefix >>               # Change prefix to >>
s.setprefix reset            # Reset to default (s.)
```

**Requirements:**
- **Administrator** permission required
- Prefix must be 5 characters or less
- Cannot use certain reserved characters

## 🌐 Network & Performance Tools

### Bot Response Time

```
s.ping
```

Checks bot performance and connectivity:
- **Heartbeat Latency** - Discord API connection quality
- **Response Time** - Message processing speed
- **Uptime** - How long bot has been running
- **System Stats** - Memory usage and performance

## 🔍 Discord Utility Tools

### Invite Analysis

```
s.inviteinfo <invite_code>
```

Analyzes Discord invite links:
- **Server Details** - Name, ID, member counts
- **Invite Info** - Code, channel, creator, creation date
- **Statistics** - Approximate member and online counts
- **Expiry Information** - When invite expires (if applicable)

**Examples:**
```
s.inviteinfo discord.gg/abc123    # Full invite URL
s.inviteinfo abc123               # Just the invite code
```

## 📋 Variable Reference

### Available Variables

```
s.variables
```

Displays all available variables for use in embeds, auto-responders, and other bot features:

**User Variables:**
- `$(user.name)` - Username
- `$(user.mention)` - User mention
- `$(user.id)` - User ID
- `$(user.nick)` - Server nickname
- `$(user.avatar)` - Avatar URL
- `$(user.joined)` - Server join date
- `$(user.created)` - Account creation date

**Server Variables:**
- `$(server.name)` - Server name
- `$(server.members)` - Member count
- `$(server.id)` - Server ID
- `$(server.owner)` - Server owner mention
- `$(server.created)` - Server creation date
- `$(server.boost)` - Boost level

**Channel Variables:**
- `$(channel)` - Current channel mention
- `$(channel.name)` - Channel name
- `$(channel.id)` - Channel ID
- `$(channel.topic)` - Channel topic

**Date/Time Variables:**
- `$(date)` - Current date
- `$(time)` - Current time
- `$(timestamp)` - Unix timestamp

## 📈 Bot Information Commands

### Bot Statistics

```
s.about
```

Shows detailed bot information:
- **Bot Statistics** - Uptime, server count, user count
- **System Information** - Memory usage, CPU, Python version
- **Framework Details** - Discord.py version, dependencies
- **Performance Metrics** - Commands processed, response times

### Bot Invite

```
s.invite
```

Provides bot invitation information:
- **Invite Link** - Add bot to your server
- **Required Permissions** - Necessary bot permissions
- **Support Information** - Help server and contact details
- **Feature Highlights** - Key bot capabilities

### Shard Information

```
s.shards
```

Displays bot shard information (for large bots):
- **Current Shard** - Which shard serves this server
- **Shard Statistics** - Latency and server distribution
- **Total Shards** - How many shards are running
- **Server List** - Servers on current shard (with pagination)

### Voting Information

```
s.vote
```

Shows bot voting and support information:
- **Voting Links** - Support the bot on listing sites
- **Current Stats** - Vote count and rankings
- **Benefits** - Rewards for voting (if applicable)
- **Frequency** - How often you can vote

## 🎯 Practical Usage Examples

### Server Onboarding

**New Server Setup:**
```
s.serverinfo                 # Review server details
s.setprefix !               # Set preferred prefix
s.channelinfo #general      # Check channel settings
s.roleinfo @everyone        # Review default permissions
```

### User Management

**Investigating Users:**
```
s.userinfo @suspicious_user  # Check user details
s.avatar @user               # Verify profile picture
s.roleinfo @Member           # Check role permissions
```

### Server Analysis

**Server Health Check:**
```
s.ping                       # Check bot performance
s.serverinfo                 # Review server statistics
s.shards                     # Check shard performance
s.about                      # Review bot system status
```

### Invite Investigation

**Analyzing Invites:**
```
s.inviteinfo discord.gg/xyz123   # Check where invite leads
s.inviteinfo abc123              # Analyze invite details
```

## 🔧 Advanced Administration

### Prefix Strategy

**Multi-Server Management:**
```
# Gaming Server
s.setprefix !

# Professional Server  
s.setprefix bot.

# Community Server
s.setprefix >>
```

### Information Gathering

**User Research:**
```
s.userinfo @user             # Basic user information
s.avatar @user               # Profile picture verification
s.roleinfo @user_top_role    # Permission analysis
```

**Channel Analysis:**
```
s.channelinfo #channel       # Channel configuration
s.serverinfo                 # Server-wide context
s.variables                  # Available customization options
```

## 🛡️ Permissions Required

### User Commands (No Permissions)
- `s.ping`, `s.about`, `s.invite`, `s.vote`, `s.shards`
- `s.avatar`, `s.userinfo`, `s.serverinfo`
- `s.channelinfo`, `s.roleinfo`, `s.inviteinfo`
- `s.variables`, `s.prefix`

### Administrative Commands
- `s.setprefix` - **Administrator** permission required

### Bot Requirements
- **Send Messages** - For all command responses
- **Embed Links** - For formatted information displays
- **Read Message History** - For command processing
- **Use External Emojis** - For custom bot emojis

## ❓ Troubleshooting

### Common Issues

**Commands Not Responding:**
- ✅ Check bot has **Send Messages** permission
- ✅ Verify correct command prefix: `s.prefix`
- ✅ Ensure bot is online and responsive: `s.ping`

**Information Not Displaying:**
- ✅ Bot needs **Embed Links** permission
- ✅ Check if channel allows bot messages
- ✅ Verify bot can access mentioned users/channels/roles

**Prefix Changes Not Working:**
- ✅ Requires **Administrator** permission
- ✅ Prefix must be 5 characters or less
- ✅ Some characters may be reserved

**User/Role/Channel Not Found:**
- ✅ Check spelling and formatting
- ✅ Use mentions for accuracy: `@user`, `@role`, `#channel`
- ✅ Verify bot can see the target user/role/channel

### Performance Issues

**Slow Response Times:**
- ✅ Check `s.ping` for bot latency
- ✅ Review `s.shards` for shard performance
- ✅ Use `s.about` to check system resources

**Information Outdated:**
- ✅ Information is real-time when command runs
- ✅ Re-run command for updated data
- ✅ Check if user/channel/role was recently changed

---

**Next:** Learn about [Logging System](../administration/logging.md) for monitoring bot activity.