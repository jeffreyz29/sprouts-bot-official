# Ticket System

A comprehensive support ticket system with panels, claiming, priorities, transcripts, and advanced management features.

## 🎫 Overview

The Sprouts ticket system provides a professional support experience for Discord servers, enabling users to get help privately while giving staff powerful management tools.

### Key Features

- **🎛️ Interactive Setup Panel** - Easy configuration interface
- **🎨 Customizable Ticket Panels** - Beautiful embed-based ticket creation
- **👥 Staff Management** - Role-based access and claiming system  
- **📝 Comprehensive Logging** - Full activity tracking and transcripts
- **🔄 Auto-Management** - Cleanup and maintenance features
- **📊 Priority System** - Organize tickets by importance

## 🚀 Initial Setup

### Step 1: Launch Setup

```
s.ticketsetup
```

This opens an interactive setup panel with the following options:

#### 🏷️ Set Category
Choose where ticket channels will be created:
- Lists all available categories in your server
- Shows current selection
- Automatically manages channel permissions

#### 👥 Configure Staff Roles  
Set which roles can manage tickets:
- Add multiple staff roles
- Each role gets ticket management permissions
- Staff can claim, close, and transfer tickets

#### 📝 Set Log Channel
Configure ticket activity logging:
- All ticket events are logged here
- Includes creation, claiming, closing, and transfers
- Provides audit trail for staff review

#### 🧹 Cleanup Data
Remove orphaned ticket data:
- Finds tickets for deleted channels
- Cleans up database entries
- Helps maintain system health

### Step 2: Create Ticket Panel

After setup, create a ticket panel for users:

```
s.createpanel [title]
```

This generates a beautiful embed with a "Create Ticket" button that users can click to open new tickets.

## 🎨 Ticket Panel Customization

### Default Panel Features

The ticket panel includes:
- **📋 Title**: "🎫 Support Tickets"
- **📝 Description**: Clear instructions for users
- **🎨 Color**: Matches your bot's theme
- **🔘 Button**: "Create Ticket" with emoji

### Custom Embed Integration

Use saved embeds for ticket panels:

```
s.embed create          # Create custom embed
s.embed save ticket     # Save as "ticket"
s.ticketuseembed ticket # Use for ticket panel
```

This allows complete customization of:
- Colors and styling
- Text and descriptions  
- Additional fields
- Footer information

## 🔧 Ticket Management

### Creating Tickets

Users can create tickets by:
1. **Clicking the panel button** (recommended)
2. **Using the command**: `s.new [reason]`

Example:
```
s.new I need help with my account
```

### Claiming Tickets

Staff members can claim tickets for assignment:

```
s.claim                 # Claim current ticket
s.claim @staff         # Transfer to specific staff member
```

When claimed:
- ✅ Ticket shows as "claimed by [Staff]"
- 👤 Only the claiming staff gets notifications
- 📝 Claim is logged in the log channel

### Closing Tickets

Close tickets with optional reason:

```
s.close                # Close with confirmation  
s.close spam          # Close with reason
s.forceclose          # Close without confirmation (staff only)
```

Closing process:
1. **⚠️ Confirmation** - User must confirm closure
2. **📄 Transcript** - Automatic transcript generation
3. **📝 Logging** - Close event logged with reason
4. **🗑️ Cleanup** - Channel deleted after transcript

## 📄 Transcript System

### Automatic Transcripts

Every closed ticket generates a transcript:

- **📂 Storage**: `src/data/transcripts/`
- **📅 Filename**: `ticket-{id}-{timestamp}.html`
- **📋 Content**: All messages, embeds, and attachments
- **🎨 Formatting**: Beautiful HTML with Discord styling

### Manual Transcripts

Generate transcripts without closing:

```
s.transcript           # Generate for current ticket
```

Useful for:
- **📊 Progress reports**
- **🔄 Handoffs between staff**  
- **📁 Archiving long-running tickets**

### Transcript Features

Transcripts include:
- **💬 All Messages** - Complete conversation history
- **📎 Attachments** - Links to uploaded files
- **👥 User Info** - Participant details and roles
- **⏰ Timestamps** - Exact message timing
- **🎨 Rich Formatting** - Embeds, reactions, and styling

## 🎯 Advanced Features

### Priority System

Organize tickets by importance:

```
s.priority high        # Set high priority
s.priority medium      # Set medium priority  
s.priority low         # Set low priority
```

Priority indicators:
- 🔴 **High**: Urgent issues requiring immediate attention
- 🟡 **Medium**: Standard support requests
- 🟢 **Low**: General questions and feedback

### Transfer System

Move tickets between staff members:

```
s.transfer @newstaff   # Transfer to specific staff
```

Transfer features:
- **🔄 Permission update** - New staff gets access
- **📝 Notification** - Both staff members notified
- **📊 Tracking** - Transfer logged for accountability

### Bulk Operations

Manage multiple tickets efficiently:

```
s.listtickets          # List all open tickets
s.listpanels           # List all ticket panels
s.delpanel <panel_id>  # Delete ticket panel
s.ticketlimit [number] # Set max tickets per user
```

### Auto-Close System

Configure automatic ticket closure:

```json
{
  "auto_close": {
    "enabled": true,
    "inactive_hours": 72,
    "warning_hours": 48,
    "exclude_claimed": true
  }
}
```

## 🛠️ Staff Commands Reference

### Basic Commands
| Command | Description | Usage |
|---------|-------------|-------|
| `s.new [reason]` | Create new ticket | `s.new I need help` |
| `s.claim` | Claim ticket | `s.claim` |
| `s.close [reason]` | Close ticket | `s.close Issue resolved` |
| `s.forceclose` | Force close ticket | `s.forceclose` |
| `s.add <member>` | Add member to ticket | `s.add @user` |
| `s.remove <member>` | Remove from ticket | `s.remove @user` |
| `s.transfer <@staff>` | Transfer ticket | `s.transfer @staff` |

### Management Commands
| Command | Description | Usage |
|---------|-------------|-------|
| `s.ticketsetup` | Configure system | `s.ticketsetup` |
| `s.createpanel [title]` | Create panel | `s.createpanel Support` |
| `s.listtickets` | List all tickets | `s.listtickets` |
| `s.listpanels` | List all panels | `s.listpanels` |
| `s.delpanel <id>` | Delete panel | `s.delpanel abc123` |
| `s.ticketlimit [num]` | Set user limit | `s.ticketlimit 5` |

### Priority Commands
| Command | Description | Usage |
|---------|-------------|-------|
| `s.priority high` | High priority | `s.priority high` |
| `s.priority medium` | Medium priority | `s.priority medium` |
| `s.priority low` | Low priority | `s.priority low` |

## 📊 Ticket Statistics

### Individual Stats

View detailed ticket information:

```
s.ticket stats
```

Shows:
- **📈 Total Tickets** - All-time ticket count
- **⏳ Open Tickets** - Currently active tickets
- **✅ Closed Today** - Daily closure rate
- **👥 Staff Performance** - Tickets per staff member

### Server Overview

Dashboard view of ticket health:
- **📊 Response Times** - Average staff response
- **🔄 Resolution Rate** - Tickets closed vs created
- **📈 Growth Trends** - Ticket volume over time
- **🎯 Satisfaction** - User feedback scores

## 🔐 Permissions & Security

### Required Bot Permissions

For full functionality:
- ✅ **Manage Channels** - Create/delete ticket channels
- ✅ **Manage Roles** - Set ticket permissions
- ✅ **Read Messages** - Access ticket content
- ✅ **Send Messages** - Respond in tickets
- ✅ **Embed Links** - Send formatted messages
- ✅ **Attach Files** - Share transcripts
- ✅ **Manage Messages** - Clean up tickets

### Staff Role Configuration

Staff roles automatically receive:
- **👀 View Channel** - Access to all tickets
- **💬 Send Messages** - Respond to users
- **📎 Attach Files** - Share resources
- **📝 Manage Messages** - Moderate content
- **👥 Mention @everyone** - Escalate issues

### User Privacy

Privacy protection features:
- **🔒 Private Channels** - Only ticket creator and staff access
- **👥 Permission Inheritance** - Follows category settings
- **📝 Transcript Security** - Local storage only
- **🗑️ Auto-Cleanup** - Channels deleted after closing

## ❓ Troubleshooting

### Common Issues

**Tickets not creating:**
- ✅ Check bot has **Manage Channels** permission
- ✅ Verify category has available channel slots (< 50)
- ✅ Ensure bot role is above staff roles

**Staff can't access tickets:**
- ✅ Verify staff roles are configured in setup
- ✅ Check role hierarchy (bot role above staff)
- ✅ Confirm staff roles have basic permissions

**Transcripts not generating:**
- ✅ Check `src/data/transcripts/` directory exists
- ✅ Verify bot has file write permissions
- ✅ Ensure transcript system is enabled

### Getting Support

Need help with the ticket system?
- **📚 Documentation** - Check this guide first
- **🎫 Create Ticket** - Use the system to report issues
- **💬 Support Server** - Join our Discord for help
- **🐛 Bug Reports** - Report issues on GitHub

---

**Next:** Learn about the [Embed Builder](embed-builder.md) to create beautiful ticket panels and responses.