# First Steps

Get started with Sprouts bot and learn the essential commands for server management.

## 🌱 Welcome to Sprouts!

Now that you've installed and configured Sprouts, let's walk through the essential features and commands to get your server running smoothly.

## 📚 Basic Commands

### Help System

Get comprehensive help information:

```
s.help              # Main help menu
s.help tickets      # Ticket system help
s.help embeds       # Embed builder help  
s.help utilities    # Utility commands help
```

### Bot Information

Check bot status and information:

```
s.info              # Bot information and stats
s.ping              # Check bot response time
s.uptime            # How long bot has been running
```

## 🎫 Setting Up Your First Ticket System

### Step 1: Initialize Ticket System

```
s.ticket setup
```

This opens an interactive setup panel where you'll configure:

1. **📂 Category** - Select where ticket channels will be created
2. **👥 Staff Roles** - Choose roles that can manage tickets  
3. **📝 Log Channel** - Pick channel for ticket activity logs
4. **🎨 Customize** - Set colors and messages

### Step 2: Create Ticket Panel

```
s.ticket panel
```

This creates a beautiful ticket panel with a button users can click to create tickets.

### Step 3: Test the System

1. Click the "Create Ticket" button
2. Verify a new ticket channel is created
3. Test ticket commands: `s.claim`, `s.close`, `s.transcript`

## 📝 Creating Your First Embed

### Step 1: Launch Embed Builder

```
s.embed create
```

This opens the interactive embed builder with:
- **Live Preview** - See changes in real-time
- **Dropdown Menus** - Easy field selection
- **Color Picker** - Visual color selection
- **Template Library** - Pre-made designs

### Step 2: Design Your Embed

1. **Set Title** - Choose your embed title
2. **Add Description** - Write your main content  
3. **Pick Color** - Select brand colors
4. **Add Fields** - Include structured information
5. **Set Footer** - Add footer text and icon

### Step 3: Save & Use

```
s.embed save welcome     # Save as "welcome"
s.embed use welcome      # Post the saved embed
s.embedlist             # View all saved embeds
```

## 🤖 Setting Up Auto Responders

### Create Basic Auto Responders

```
s.autoresponder add "hello" "Hello! Welcome to our server! 👋"
s.autoresponder add "support" "Need help? Use `s.ticket create` to get assistance!"
```

### Advanced Auto Responders

```
s.autoresponder add "rules" "📋 Server Rules" --embed --channel #general
s.autoresponder add "faq" "❓ Check out our FAQ channel: <#123456>" --cooldown 60
```

### Manage Auto Responders

```
s.autoresponder list      # View all responders
s.autoresponder remove hello  # Remove a responder
s.autoresponder edit hello    # Modify existing responder
```

## 📌 Creating Sticky Messages

### Basic Sticky Messages

Keep important information visible:

```
s.sticky add "📋 **Server Rules**: Please read our rules in <#rules> before participating!"
```

### Embed Sticky Messages

```
s.sticky add --embed "Welcome Message"  # Uses saved embed
```

### Manage Stickies

```
s.sticky list            # View all sticky messages
s.sticky remove          # Remove sticky from current channel
s.sticky toggle          # Enable/disable sticky
```

## ⏰ Setting Up Reminders

### Personal Reminders

```
s.remind me in 30 minutes Take a break
s.remind me tomorrow at 3pm Team meeting
s.remind me next week Update server rules
```

### Server Reminders  

```
s.remind #announcements in 1 hour Server maintenance starting
s.remind @everyone in 2 days Event registration closes
```

### Manage Reminders

```
s.reminders             # View your reminders
s.reminder cancel 1     # Cancel reminder by ID
s.reminder edit 1       # Edit existing reminder
```

## 📊 Setting Up Server Stats

### Initialize Server Stats

```
s.serverstats setup #stats-channel
```

This creates auto-updating embeds showing:
- 👥 **Total Members**
- 🤖 **Bot Count**
- 📈 **Growth Rate** 
- 📊 **Channel Statistics**

### Customize Stats Display

```
s.serverstats refresh    # Manual refresh
s.serverstats config     # Modify display settings
s.serverstats remove     # Remove stats monitor
```

## 🔍 Enabling Logging

### Command Logging

Track who uses bot commands:

```
s.setcmdlog #bot-logs
```

### DM Logging

Monitor direct messages to the bot:

```
s.setdmlog #dm-logs  
```

### Event Logging

Log server events (joins, leaves, etc.):

```
s.toggleeventlog
```

## 🛠️ Useful Utilities

### Server Information

```
s.serverinfo            # Complete server details
s.userinfo @username    # User information and stats
s.avatar @username      # Display user's avatar
```

### Channel Management

```
s.purge 10              # Delete last 10 messages
s.slowmode 30           # Set 30 second slowmode
s.lock                  # Lock current channel
s.unlock                # Unlock current channel
```

### Role Management

```
s.role @user RoleName   # Add role to user
s.role remove @user Role # Remove role from user  
s.roles @user           # Show user's roles
```

## 🎨 Customization Tips

### Custom Prefix

Change the command prefix to match your server:

```
s.setprefix !
s.setprefix bot!
s.setprefix sprouts
```

### Bot Presence

Customize what the bot is "doing":

```
s.setstatus online      # Set online status
s.setactivity watching over the server
s.setactivity listening to your feedback
```

### Color Themes

Customize embed colors to match your server branding by editing the environment variables.

## 🎯 Quick Setup Checklist

- [ ] **Test basic commands** (`s.help`, `s.ping`)
- [ ] **Set up ticket system** (`s.ticket setup`)
- [ ] **Create first embed** (`s.embed create`)
- [ ] **Add auto responders** for common questions
- [ ] **Set sticky message** with server info
- [ ] **Configure logging** channels
- [ ] **Set up server stats** monitor
- [ ] **Customize bot prefix** and presence
- [ ] **Test all major features** with your team
- [ ] **Train staff** on ticket management

## ❓ Common First Steps Questions

### "The bot isn't responding to commands"
- ✅ Check bot has **Message permissions**
- ✅ Verify correct **prefix** (default is `s.`)  
- ✅ Make sure bot is **online** and **in your server**

### "Ticket setup isn't working"
- ✅ Bot needs **Manage Channels** permission
- ✅ Bot needs **Manage Roles** permission
- ✅ Category must have available channel slots

### "Embeds look broken"
- ✅ Bot needs **Embed Links** permission
- ✅ Check embed color codes are valid hex
- ✅ Verify all required fields are filled

### "Sticky messages not reposting"
- ✅ Bot needs **Manage Messages** permission
- ✅ Check message threshold is reached
- ✅ Verify sticky is enabled in that channel

## 🚀 Next Steps

Once you're comfortable with the basics:

1. **[Explore Advanced Features](../features/)** - Deep dive into each system
2. **[Set Up Logging](../administration/logging.md)** - Monitor bot activity  
3. **[Configure Web Dashboard](../administration/web-dashboard.md)** - Access web interface
4. **[Plan Production Deployment](../deployment/)** - Prepare for live usage

---

**Need help?** Join our support server or check the [troubleshooting guide](../support/troubleshooting.md)!