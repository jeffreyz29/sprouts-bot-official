# Sticky Messages

Persistent channel messages that automatically repost to keep important information visible.

## 📌 Overview

The Sprouts sticky message system allows you to create messages that automatically repost in channels after regular user activity, ensuring important information stays visible without manual reposting.

### Key Features

- **📍 Automatic Reposting** - Messages repost after each user message
- **⚡ Speed Control** - Fast or slow sticky message modes
- **🔄 Easy Management** - Start, stop, remove sticky messages
- **📋 Server-wide Listing** - View all sticky messages across channels
- **🎨 Rich Content** - Support for text, mentions, and formatting

## 🚀 Getting Started

### Create Basic Sticky Message

```
s.stick <message>
```

Creates a fast sticky message that reposts after every user message.

**Examples:**
```
s.stick 📋 **Server Rules**: Please read #rules before participating!
s.stick 🎉 Welcome to our community! Don't forget to introduce yourself in #introductions!
s.stick 🎮 Looking for teammates? Check out #looking-for-group!
s.stick 📢 Server maintenance scheduled for tonight at 11 PM EST
```

### Create Slow Sticky Message

```
s.stickslow <message>
```

Creates a slow sticky message that reposts less frequently.

**Examples:**
```
s.stickslow 💡 **Tip**: Use s.help to see all available commands
s.stickslow 🔗 Join our website: https://example.com
s.stickslow 📊 Server stats: Use s.serverinfo for detailed information
```

## 🎛️ Managing Sticky Messages

### Stop Sticky Message

```
s.stickstop
```

Temporarily stops the sticky message in the current channel without removing it. The message remains but won't repost.

### Start Sticky Message

```
s.stickstart
```

Resumes a stopped sticky message in the current channel.

### Remove Sticky Message

```
s.stickremove
```

Permanently removes the sticky message from the current channel.

### Change Sticky Speed

```
s.stickspeed <fast|slow>
```

Changes the speed of the sticky message in the current channel.

**Examples:**
```
s.stickspeed fast    # Make sticky repost after every message
s.stickspeed slow    # Make sticky repost less frequently
```

### List All Sticky Messages

```
s.getstickies
```

Shows all sticky messages configured across the entire server with their status and channels.

## 📝 Sticky Message Content

### Text Formatting

Sticky messages support Discord markdown formatting:

```markdown
**Bold text**           - Strong emphasis
*Italic text*          - Light emphasis
__Underline text__      - Underlined
~~Strikethrough~~       - Crossed out
`Code text`             - Inline code
> Quote text            - Blockquote
```

### Using Mentions

Include mentions in sticky messages:

**Examples:**
```
s.stick Welcome to the server! Be sure to check out <#rules> and <#introductions>!
s.stick Questions? Contact our <@&ModeratorRole> team for help!
s.stick 📢 <@everyone> Server event tonight at 8 PM!
```

### Multi-line Messages

Create multi-line sticky messages using line breaks:

**Examples:**
```
s.stick **📋 Server Information**

🎮 **Gaming**: #gaming-general, #looking-for-group
💬 **Chat**: #general-chat, #off-topic  
🎵 **Music**: #music-commands, #music-chat
🎫 **Support**: Use s.new for help tickets
```

## ⚡ Sticky Message Speeds

### Fast Mode (Default)

- **Repost Frequency**: After every user message
- **Best For**: Critical announcements, active channels, temporary notices
- **Use Cases**: Rules reminders, event announcements, urgent information

### Slow Mode

- **Repost Frequency**: Less frequent, based on activity threshold
- **Best For**: Permanent information, less active channels, tips
- **Use Cases**: Server tips, website links, general information

## 🎯 Best Practices

### Effective Sticky Messages

**Good Sticky Content:**
- **Clear and Concise** - Easy to read quickly
- **Relevant Information** - Channel-specific content
- **Actionable Items** - Tell users what to do
- **Updated Regularly** - Keep information current

**Examples:**
```
s.stick 📋 **#rules**: Read server rules | 🎫 **Help**: s.new for support | 🎮 **Gaming**: #looking-for-group
s.stick 🎉 **Welcome!** Introduce yourself, read #rules, and have fun!
s.stick 📢 **Event**: Movie night Friday 8 PM EST in #voice-general
```

### Channel-Specific Usage

**#general or #welcome:**
```
s.stick 👋 Welcome to our server! Please read #rules and introduce yourself in #introductions!
```

**#rules:**
```
s.stick 📋 These rules apply to all server areas. Questions? Contact <@&Staff>
```

**#support:**
```
s.stick 🎫 Need help? Use s.new to create a support ticket and staff will assist you!
```

**#gaming:**
```
s.stick 🎮 Looking for teammates? Post your game and platform here!
```

## 🔧 Advanced Usage

### Temporary Sticky Messages

For short-term announcements:

1. **Create sticky** for the event/announcement
2. **Use fast mode** for maximum visibility
3. **Remove after event** with `s.stickremove`

**Example:**
```
s.stick 🎉 **SERVER ANNIVERSARY EVENT** - Triple XP active for 24 hours! 🎉
# After event ends:
s.stickremove
```

### Scheduled Maintenance

For server updates and maintenance:

```
s.stick ⚠️ **Scheduled Maintenance** - Bot will be offline tonight 11 PM - 1 AM EST for updates
# Change speed for less spam:
s.stickspeed slow
# Remove after maintenance:
s.stickremove
```

### Channel Guidelines

Create channel-specific guidelines:

```
# In #media-sharing:
s.stick 📸 **Media Guidelines**: Original content only | Credit creators | No NSFW | Use appropriate channels

# In #voice-text:
s.stick 🎵 **Voice Chat**: Be respectful | No background noise | Use push-to-talk for quality
```

## 📊 Management Dashboard

### Monitor Sticky Messages

Regular maintenance tasks:

1. **Review All Stickies**: `s.getstickies` monthly
2. **Update Content**: Keep information current
3. **Check Relevance**: Remove outdated messages
4. **Speed Optimization**: Adjust speeds based on channel activity

### Channel Activity Considerations

**High Activity Channels:**
- Use **slow speed** to prevent spam
- Keep messages **very concise**
- **Rotate content** to prevent staleness

**Low Activity Channels:**
- **Fast speed** works well
- **Longer messages** acceptable
- **Permanent information** preferred

## 🔐 Permissions

### Required Bot Permissions

For sticky message functionality:
- ✅ **Send Messages** - Post sticky messages
- ✅ **Read Messages** - Monitor channel activity
- ✅ **Manage Messages** - Delete old sticky messages
- ✅ **Read Message History** - Track repost timing

### User Permissions

**Creating Sticky Messages:**
- **Manage Messages** permission required in the channel
- Channel-specific permission checking

**Managing Existing Stickies:**
- **Manage Messages** permission for stop/start/remove
- **Administrator** permission for server-wide listing

## ❓ Troubleshooting

### Common Issues

**Sticky Message Not Reposting:**
- ✅ Check if sticky is active: `s.getstickies`
- ✅ Verify bot has **Send Messages** permission
- ✅ Ensure bot has **Manage Messages** permission
- ✅ Confirm channel activity (stickies need user messages to trigger)

**Messages Posting Too Frequently:**
- ✅ Change to slow mode: `s.stickspeed slow`
- ✅ Consider if sticky is necessary in high-activity channel
- ✅ Review message content for brevity

**Can't Remove Sticky Message:**
- ✅ Verify you have **Manage Messages** permission
- ✅ Make sure you're in the correct channel
- ✅ Try `s.stickstop` first, then `s.stickremove`

**Old Sticky Messages Remaining:**
- ✅ Bot may not have permission to delete old messages
- ✅ Manually delete old sticky, it won't repost
- ✅ Check bot role hierarchy and permissions

### Performance Considerations

**Server Load:**
- Monitor number of active sticky messages
- Use slow mode in high-activity channels
- Remove unnecessary stickies regularly

**User Experience:**
- Avoid too many sticky messages
- Keep content relevant and updated
- Consider user feedback about stickies

## 💡 Creative Uses

### Interactive Stickies

**Role Selection Reminder:**
```
s.stick 🎭 **Get Your Roles!** React in #role-selection to get notification roles for games, events, and updates!
```

**Event Coordination:**
```
s.stick 📅 **Weekly Events** - Monday: Game Night | Wednesday: Movie Night | Friday: Community Meetup
```

**Community Building:**
```
s.stick 💬 **Daily Question**: What's your favorite feature of this server? Share in replies!
```

### Information Hubs

**Resource Centers:**
```
s.stick 📚 **Resources** | 📖 Guides: #tutorials | 🔗 Links: #useful-links | 📊 Stats: s.serverinfo
```

**Quick References:**
```
s.stick ⚡ **Quick Commands** | 🎫 Help: s.new | 👤 Profile: s.userinfo | 🏓 Ping: s.ping
```

---

**Next:** Learn about [Reminders](reminders.md) for personal time-based notifications.