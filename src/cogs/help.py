"""
Simple Help Command (Text Commands Only)
Displays commands in a simple list format like the original image
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from src.emojis import SPROUTS_ERROR

# Add success color if not in config
EMBED_COLOR_SUCCESS = 0x77DD77
from src.cogs.guild_settings import guild_settings

logger = logging.getLogger(__name__)

class DetailedCommandHelpView(discord.ui.View):
    """Interactive view for extremely detailed command help"""
    
    def __init__(self, command, prefix, user):
        super().__init__(timeout=300)
        self.command = command
        self.prefix = prefix
        self.user = user
        self.current_page = "main"
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the user who ran the command to use buttons"""
        return interaction.user.id == self.user.id
    
    def get_detailed_command_info(self):
        """Get extremely detailed information about the command"""
        detailed_info = {
            # Basic Commands
            "ping": {
                "category": "Utility",
                "description": "Check bot latency and response time with detailed system statistics",
                "usage": f"`{self.prefix}ping`",
                "detailed_usage": [
                    f"`{self.prefix}ping` - Shows bot latency, API response time, and system stats"
                ],
                "examples": [
                    f"`{self.prefix}ping` - Shows bot response time and system performance",
                    "Example output: Bot latency: 45ms, API ping: 120ms, Memory: 234MB"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works",
                    "If bot is offline, command won't respond at all",
                    f"**Note:** Just type `{self.prefix}ping` with no additional text"
                ]
            },
            
            "userinfo": {
                "category": "Utility", 
                "description": "Display comprehensive user information including roles, join dates, and account details",
                "usage": f"`{self.prefix}userinfo [@user]`",
                "detailed_usage": [
                    f"`{self.prefix}userinfo` - Shows YOUR information",
                    f"`{self.prefix}userinfo @username` - Shows MENTIONED user's info",
                    f"`{self.prefix}userinfo username` - Shows info by username",
                    f"`{self.prefix}userinfo 123456789` - Shows info by user ID"
                ],
                "examples": [
                    f"`{self.prefix}userinfo` - Shows your own detailed information",
                    f"`{self.prefix}userinfo @John` - Shows John's user information",
                    f"`{self.prefix}userinfo John` - Search for user named John",
                    f"`{self.prefix}userinfo 123456789` - Get user info by ID"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**User not found:** `User 'xyz' not found in this server.`",
                    "**Invalid ID:** `Invalid user ID format.`",
                    "**User left server:** `User no longer in this server.`",
                    f"**Solution:** Use `{self.prefix}userinfo @username` or make sure user is in server"
                ]
            },
            
            "avatar": {
                "category": "Utility",
                "description": "Display a user's avatar in full resolution with download links",
                "usage": f"`{self.prefix}avatar [@user]`", 
                "detailed_usage": [
                    f"`{self.prefix}avatar` - Shows YOUR avatar",
                    f"`{self.prefix}avatar @username` - Shows mentioned user's avatar",
                    f"`{self.prefix}avatar username` - Shows avatar by username"
                ],
                "examples": [
                    f"`{self.prefix}avatar` - Shows your own profile picture",
                    f"`{self.prefix}avatar @John` - Shows John's profile picture",
                    f"`{self.prefix}avatar John` - Search for John's avatar by name",
                    f"`{self.prefix}avatar 123456789` - Get avatar by user ID"
                ],
                "permissions": "None required", 
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**User not found:** Shows error embed with suggestion to check spelling",
                    "**Default avatar:** Shows Discord's default avatar if user has none",
                    f"**Solution:** Use `{self.prefix}avatar @username` to mention the user directly"
                ]
            },
            
            "setprefix": {
                "category": "Server Management",
                "description": "Change the bot's command prefix for this server (Administrator only)",
                "usage": f"{self.prefix}setprefix <new_prefix>",
                "detailed_usage": [
                    f"`{self.prefix}setprefix !` - Changes prefix to !",
                    f"`{self.prefix}setprefix bot.` - Changes prefix to bot.",
                    f"`{self.prefix}setprefix >>` - Changes prefix to >>",
                    f"`{self.prefix}setprefix reset` - Reset to default prefix (s.)"
                ],
                "examples": [
                    f"`{self.prefix}setprefix !` - Change commands to !help, !ping, etc.",
                    f"`{self.prefix}setprefix ?` - Change commands to ?help, ?ping, etc.", 
                    f"`{self.prefix}setprefix sp.` - Change commands to sp.help, sp.ping, etc.",
                    f"`{self.prefix}setprefix reset` - Go back to default prefix commands"
                ],
                "permissions": "Administrator",
                "cooldown": "10 seconds per server",
                "error_scenarios": [
                    "**Missing permissions:** `You need Administrator permissions to change the server prefix.`",
                    f"**No prefix provided:** `Please provide a new prefix. Example: {self.prefix}setprefix !`",
                    "**Prefix too long:** `Prefix must be 5 characters or less.`",
                    f"**Solution:** Make sure you type: `{self.prefix}setprefix <your_new_prefix>`"
                ]
            },
            
            # Ticket System Commands
            "new": {
                "category": "Ticket System",
                "description": "Create a new support ticket with optional reason",
                "usage": f"{self.prefix}new [reason]",
                "detailed_usage": [
                    f"`{self.prefix}new` - Creates ticket with no reason",
                    f"`{self.prefix}new I need help with billing` - Creates ticket with reason",
                    f"`{self.prefix}new Bug report: Bot not responding` - Detailed reason"
                ],
                "examples": [
                    f"`{self.prefix}new` - Creates a simple support ticket",
                    f"`{self.prefix}new I can't access my account` - Ticket with specific issue",
                    f"`{self.prefix}new Bug: Commands not working` - Bug report ticket",
                    f"`{self.prefix}new Need help with Discord roles` - Help request ticket"
                ],
                "permissions": "None required",
                "cooldown": "30 seconds per user", 
                "error_scenarios": [
                    "**Tickets disabled:** `Ticket system is not enabled in this server.`",
                    "**Too many tickets:** `You already have the maximum number of open tickets.`",
                    "**Channel creation failed:** `Failed to create ticket channel. Contact an administrator.`",
                    f"**Solution:** Ask an admin to run `{self.prefix}ticketsetup` to enable tickets"
                ]
            },
            
            "add": {
                "category": "Ticket System",
                "description": "Add a member to the current ticket (Staff only)",
                "usage": f"{self.prefix}add <member>",
                "detailed_usage": [
                    f"`{self.prefix}add @username` - Add user by mention",
                    f"`{self.prefix}add username` - Add user by username",
                    f"`{self.prefix}add 123456789` - Add user by ID"
                ],
                "examples": [
                    f"`{self.prefix}add @John` - Add John to ticket",
                    f"`{self.prefix}add Support Team` - Add by username",
                    f"`{self.prefix}add 351738977602887681` - Add by user ID"
                ],
                "permissions": "**Manage Channels** required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Missing permissions:** `You need Manage Channels permission to add users.`",
                    "**User not found:** `Could not find user 'username' in this server.`",
                    "**User already in ticket:** `User is already added to this ticket.`"
                ]
            },
            
            # Auto Responder Commands - Simple System
            "autoresponder": {
                "category": "Auto Responders",
                "description": "Simple auto-response system with trigger and reply functionality",
                "usage": f"{self.prefix}autoresponder <add|editreply|remove|list|toggle> [arguments]",
                "detailed_usage": [
                    f"`{self.prefix}autoresponder add trigger:<trigger> reply:<response>` - Add new auto responder",
                    f"`{self.prefix}autoresponder editreply trigger:<trigger> reply:<new response>` - Edit responder reply",
                    f"`{self.prefix}autoresponder remove <trigger>` - Remove auto responder",
                    f"`{self.prefix}autoresponder list` - List all auto responders", 
                    f"`{self.prefix}autoresponder toggle <trigger>` - Enable/disable responder"
                ],
                "examples": [
                    f"`{self.prefix}autoresponder add trigger:hello reply:Hello there! Welcome!` - Basic responder",
                    f"`{self.prefix}autoresponder add trigger:rules reply:Please check #rules channel` - Rules reminder",
                    f"`{self.prefix}autoresponder editreply trigger:hello reply:Hi there! Welcome to our server!` - Edit existing responder",
                    f"`{self.prefix}autoresponder remove hello` - Remove responder",
                    f"`{self.prefix}autoresponder list` - See all server auto responders"
                ],
                "permissions": "**Administrator** required for all autoresponder commands",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Missing permissions:** `You need Administrator permission.`",
                    "**Invalid format:** `Use format: s.autoresponder add trigger:<trigger> reply:<response>`",
                    "**Trigger not found:** `Auto responder 'trigger' does not exist.`",
                    "**Trigger exists:** `Auto responder for that trigger already exists.`"
                ]
            },
            
            # Reminder Commands
            "remind": {
                "category": "Reminders",
                "description": "Set a personal reminder that will notify you after specified time",
                "usage": f"{self.prefix}remind <time> <message>",
                "detailed_usage": [
                    f"`{self.prefix}remind 1h Take a break` - 1 hour reminder",
                    f"`{self.prefix}remind 30m Check the oven` - 30 minute reminder", 
                    f"`{self.prefix}remind 1d2h3m Meeting tomorrow` - Complex time",
                    f"`{self.prefix}remind 45s Quick reminder` - 45 second reminder"
                ],
                "examples": [
                    f"`{self.prefix}remind 2h Meeting with team` - 2 hour reminder",
                    f"`{self.prefix}remind 1d Birthday party` - 1 day reminder",
                    f"`{self.prefix}remind 30m Take medication` - 30 minute reminder",
                    f"`{self.prefix}remind 1w Weekend plans` - 1 week reminder"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Invalid time format:** Shows valid formats: 1d, 2h, 30m, 45s",
                    "**Missing message:** `Please provide a reminder message.`",
                    "**Time too long:** `Maximum reminder time is 1 year.`",
                    "**Time too short:** `Minimum reminder time is 1 second.`"
                ]
            },
            
            # Server Stats Commands
            "serverstats": {
                "category": "Server Monitoring",
                "description": "Monitor and display real-time server statistics",
                "usage": f"{self.prefix}serverstats <start|stop|show|list>",
                "detailed_usage": [
                    f"`{self.prefix}serverstats start` - Start monitoring this server",
                    f"`{self.prefix}serverstats stop` - Stop monitoring this server",
                    f"`{self.prefix}serverstats show` - Display current stats",
                    f"`{self.prefix}serverstats list` - List all monitored servers"
                ],
                "examples": [
                    f"`{self.prefix}serverstats start` - Begin monitoring",
                    f"`{self.prefix}serverstats show` - View statistics",
                    f"`{self.prefix}serverstats stop` - Stop monitoring"
                ],
                "permissions": "**Manage Guild** required for start/stop",
                "cooldown": "15 seconds per server",
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Guild permission.`",
                    "**Already monitoring:** `Server statistics already enabled.`",
                    "**Not monitoring:** `Server statistics not enabled for this server.`",
                    "**Invalid subcommand:** `Valid options: start, stop, show, list`"
                ]
            },
            
            
            # Utility Commands
            "serverinfo": {
                "category": "Utility",
                "description": "Display comprehensive server information including stats, features, and settings",
                "usage": f"{self.prefix}serverinfo",
                "detailed_usage": [
                    f"`{self.prefix}serverinfo` - Shows complete server information"
                ],
                "examples": [
                    f"`{self.prefix}serverinfo` - Get server details, member count, channels, roles",
                    "Shows: Creation date, verification level, boost status, features"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works in servers",
                    "**DM usage:** Cannot be used in direct messages"
                ]
            },
            
            "channelinfo": {
                "category": "Utility",
                "description": "Display detailed information about any server channel",
                "usage": f"{self.prefix}channelinfo [#channel]",
                "detailed_usage": [
                    f"`{self.prefix}channelinfo` - Shows info about current channel",
                    f"`{self.prefix}channelinfo #general` - Shows info about mentioned channel",
                    f"`{self.prefix}channelinfo 123456789` - Shows info by channel ID"
                ],
                "examples": [
                    f"`{self.prefix}channelinfo` - Current channel details",
                    f"`{self.prefix}channelinfo #announcements` - Specific channel info",
                    f"`{self.prefix}channelinfo 987654321` - Channel info by ID"
                ],
                "permissions": "None required",
                "cooldown": "8 seconds per user",
                "error_scenarios": [
                    "**Channel not found:** `Channel not found in this server.`",
                    "**Invalid ID:** `Invalid channel ID format.`",
                    "**No access:** `You don't have access to view that channel.`"
                ]
            },
            
            "roleinfo": {
                "category": "Utility",
                "description": "Display detailed information about any server role",
                "usage": f"{self.prefix}roleinfo <@role|role_name>",
                "detailed_usage": [
                    f"`{self.prefix}roleinfo @Admin` - Shows info about mentioned role",
                    f"`{self.prefix}roleinfo Admin` - Shows info by role name",
                    f"`{self.prefix}roleinfo 123456789` - Shows info by role ID"
                ],
                "examples": [
                    f"`{self.prefix}roleinfo @Moderator` - Moderator role details",
                    f"`{self.prefix}roleinfo Member` - Member role by name",
                    f"`{self.prefix}roleinfo 456789123` - Role info by ID"
                ],
                "permissions": "None required",
                "cooldown": "8 seconds per user",
                "error_scenarios": [
                    "**Role not found:** `Role 'name' not found in this server.`",
                    "**Invalid ID:** `Invalid role ID format.`",
                    "**Solution:** Use `{self.prefix}roleinfo @rolename` to mention the role"
                ]
            },
            
            "inviteinfo": {
                "category": "Utility",
                "description": "Display information about a Discord invite link",
                "usage": f"{self.prefix}inviteinfo <invite_code>",
                "detailed_usage": [
                    f"`{self.prefix}inviteinfo abc123` - Info about invite code",
                    f"`{self.prefix}inviteinfo discord.gg/abc123` - Info from full invite URL"
                ],
                "examples": [
                    f"`{self.prefix}inviteinfo abc123` - Shows server, channel, member count",
                    f"`{self.prefix}inviteinfo https://discord.gg/abc123` - From full URL"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Invalid invite:** `The invite code is invalid or expired.`",
                    "**No access:** `Cannot access invite information.`",
                    "**Solution:** Make sure the invite code is correct and not expired"
                ]
            },
            
            "variables": {
                "category": "Utility",
                "description": "Display all available variables for embed builder and auto-responses",
                "usage": f"{self.prefix}variables",
                "detailed_usage": [
                    f"`{self.prefix}variables` - Shows all 80+ available variables"
                ],
                "examples": [
                    f"`{self.prefix}variables` - View variables like $(user.name), $(server.name)",
                    "Use variables in embeds and auto-responses for dynamic content"
                ],
                "permissions": "None required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works"
                ]
            },
            
            # Bot Info Commands
            "about": {
                "category": "Bot Info",
                "description": "Display detailed bot statistics, uptime, and system information",
                "usage": f"{self.prefix}about",
                "detailed_usage": [
                    f"`{self.prefix}about` - Shows bot stats, uptime, system info"
                ],
                "examples": [
                    f"`{self.prefix}about` - View bot uptime, server count, memory usage",
                    "Shows: Framework version, Python version, system specs"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works"
                ]
            },
            
            "invite": {
                "category": "Bot Info",
                "description": "Get bot invite link and support server information",
                "usage": f"{self.prefix}invite",
                "detailed_usage": [
                    f"`{self.prefix}invite` - Shows bot invite link and support server"
                ],
                "examples": [
                    f"`{self.prefix}invite` - Add bot to your server with proper permissions",
                    "Includes: Bot invite link, support server, key features"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works"
                ]
            },
            
            "shards": {
                "category": "Bot Info",
                "description": "Display shard information and server distribution",
                "usage": f"{self.prefix}shards",
                "detailed_usage": [
                    f"`{self.prefix}shards` - Shows shard info and server list with pagination"
                ],
                "examples": [
                    f"`{self.prefix}shards` - View current shard, total shards, server distribution",
                    "Use arrow buttons to navigate through server pages"
                ],
                "permissions": "None required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works"
                ]
            },
            
            "vote": {
                "category": "Bot Info",
                "description": "Get voting links to support the bot on bot lists",
                "usage": f"{self.prefix}vote",
                "detailed_usage": [
                    f"`{self.prefix}vote` - Shows voting links and current bot stats"
                ],
                "examples": [
                    f"`{self.prefix}vote` - Vote on Top.gg and other bot lists",
                    "Help support bot development by voting every 12 hours"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works"
                ]
            },
            
            # Additional Ticket Commands
            "close": {
                "category": "Ticket System",
                "description": "Close the current ticket with optional reason",
                "usage": f"{self.prefix}close [reason]",
                "detailed_usage": [
                    f"`{self.prefix}close` - Close ticket with no reason",
                    f"`{self.prefix}close Issue resolved` - Close with reason",
                    f"`{self.prefix}close Duplicate ticket` - Close with explanation"
                ],
                "examples": [
                    f"`{self.prefix}close` - Simple ticket closure",
                    f"`{self.prefix}close Issue has been resolved` - Close with resolution note",
                    f"`{self.prefix}close User no longer needs help` - Close with status update"
                ],
                "permissions": "**Manage Channels** or ticket creator",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Missing permissions:** `You need Manage Channels permission to close tickets.`",
                    "**Already closed:** `This ticket is already closed.`"
                ]
            },
            
            "forceclose": {
                "category": "Ticket System", 
                "description": "Force close any ticket without confirmation (Staff only)",
                "usage": f"{self.prefix}forceclose [ticket_id]",
                "detailed_usage": [
                    f"`{self.prefix}forceclose` - Force close current ticket",
                    f"`{self.prefix}forceclose ticket-001` - Force close specific ticket by ID"
                ],
                "examples": [
                    f"`{self.prefix}forceclose` - Immediately close current ticket",
                    f"`{self.prefix}forceclose ticket-001` - Force close ticket-001",
                    f"`{self.prefix}forceclose 12345` - Force close ticket by number"
                ],
                "permissions": "**Manage Channels** required",
                "cooldown": "5 seconds per user", 
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Channels permission.`",
                    "**Ticket not found:** `Ticket with ID 'xyz' not found.`",
                    "**Already closed:** `Ticket is already closed.`"
                ]
            },
            
            "claim": {
                "category": "Ticket System",
                "description": "Claim ownership of the current ticket",
                "usage": f"{self.prefix}claim",
                "detailed_usage": [
                    f"`{self.prefix}claim` - Claim ownership of current ticket"
                ],
                "examples": [
                    f"`{self.prefix}claim` - Take ownership of the ticket",
                    "Shows your name as the assigned staff member"
                ],
                "permissions": "**Manage Channels** required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Missing permissions:** `You need Manage Channels permission.`",
                    "**Already claimed:** `This ticket is already claimed by another staff member.`"
                ]
            },
            
            "unclaim": {
                "category": "Ticket System",
                "description": "Release ownership of a claimed ticket",
                "usage": f"{self.prefix}unclaim",
                "detailed_usage": [
                    f"`{self.prefix}unclaim` - Release ownership of current ticket"
                ],
                "examples": [
                    f"`{self.prefix}unclaim` - Remove yourself as assigned staff",
                    "Makes ticket available for other staff to claim"
                ],
                "permissions": "**Manage Channels** required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not claimed:** `This ticket is not currently claimed.`",
                    "**Not owner:** `You can only release tickets you have claimed.`"
                ]
            },
            
            "remove": {
                "category": "Ticket System",
                "description": "Remove a member from the current ticket",
                "usage": f"{self.prefix}remove <member>",
                "detailed_usage": [
                    f"`{self.prefix}remove @username` - Remove user by mention",
                    f"`{self.prefix}remove username` - Remove user by username",
                    f"`{self.prefix}remove 123456789` - Remove user by ID"
                ],
                "examples": [
                    f"`{self.prefix}remove @John` - Remove John from ticket",
                    f"`{self.prefix}remove BadUser` - Remove by username",
                    f"`{self.prefix}remove 351738977602887681` - Remove by user ID"
                ],
                "permissions": "**Manage Channels** required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Missing permissions:** `You need Manage Channels permission.`",
                    "**User not found:** `Could not find user in this ticket.`",
                    "**Cannot remove creator:** `Cannot remove the ticket creator.`"
                ]
            },
            
            "listtickets": {
                "category": "Ticket System",
                "description": "List all open tickets in the server",
                "usage": f"{self.prefix}listtickets",
                "detailed_usage": [
                    f"`{self.prefix}listtickets` - Shows all open tickets with details"
                ],
                "examples": [
                    f"`{self.prefix}listtickets` - View ticket list with creators, status, priority",
                    "Shows: Ticket ID, creator, claimed status, priority level"
                ],
                "permissions": "**Manage Channels** required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Channels permission.`",
                    "**No tickets:** `No active tickets at the moment.`"
                ]
            },
            
            "topic": {
                "category": "Ticket System",
                "description": "Set or change the ticket topic/subject",
                "usage": f"{self.prefix}topic <new_topic>",
                "detailed_usage": [
                    f"`{self.prefix}topic Billing Issue` - Set ticket topic",
                    f"`{self.prefix}topic Bug Report: Login Problem` - Detailed topic"
                ],
                "examples": [
                    f"`{self.prefix}topic Account Recovery` - Set topic to account recovery",
                    f"`{self.prefix}topic Server Issues` - Set topic to server problems",
                    f"`{self.prefix}topic Feature Request` - Set topic for new feature"
                ],
                "permissions": "**Manage Channels** or ticket creator",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Missing permissions:** `You need Manage Channels permission or be the ticket creator.`",
                    "**No topic provided:** `Please provide a topic for the ticket.`"
                ]
            },
            
            
            "rename": {
                "category": "Ticket System",
                "description": "Rename the ticket channel",
                "usage": f"{self.prefix}rename <new_name>",
                "detailed_usage": [
                    f"`{self.prefix}rename billing-issue` - Rename to billing-issue",
                    f"`{self.prefix}rename urgent-bug-report` - Rename with description"
                ],
                "examples": [
                    f"`{self.prefix}rename account-help` - Rename to account-help",
                    f"`{self.prefix}rename server-problem` - Rename to server-problem",
                    f"`{self.prefix}rename feature-request` - Rename to feature-request"
                ],
                "permissions": "**Manage Channels** required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Missing permissions:** `You need Manage Channels permission.`",
                    "**Invalid name:** `Channel name contains invalid characters.`",
                    "**Name too long:** `Channel name must be 100 characters or less.`"
                ]
            },
            
            "move": {
                "category": "Ticket System",
                "description": "Move ticket to a different category",
                "usage": f"{self.prefix}move <#category>",
                "detailed_usage": [
                    f"`{self.prefix}move #Support` - Move to Support category",
                    f"`{self.prefix}move #Urgent` - Move to Urgent category"
                ],
                "examples": [
                    f"`{self.prefix}move #General-Support` - Move to general support",
                    f"`{self.prefix}move #Billing-Issues` - Move to billing category",
                    f"`{self.prefix}move #Bug-Reports` - Move to bug reports"
                ],
                "permissions": "**Manage Channels** required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Missing permissions:** `You need Manage Channels permission.`",
                    "**Category not found:** `The specified category does not exist.`",
                    "**Category full:** `The target category has reached its channel limit.`"
                ]
            },
            
            
            # Embed Builder Commands
            "embed": {
                "category": "Embed Builder",
                "description": "Advanced embed creation and management system",
                "usage": f"{self.prefix}embed <create|edit|list|view|delete|export|import>",
                "detailed_usage": [
                    f"`{self.prefix}embed create` - Create new embed with visual editor",
                    f"`{self.prefix}embed edit EmbedName` - Edit existing embed",
                    f"`{self.prefix}embed list` - List all saved embeds",
                    f"`{self.prefix}embed view EmbedName` - Preview saved embed",
                    f"`{self.prefix}embed delete EmbedName` - Delete saved embed",
                    f"`{self.prefix}embed export EmbedName` - Export as YAML template",
                    f"`{self.prefix}embed import` - Import from YAML template"
                ],
                "examples": [
                    f"`{self.prefix}embed create` - Start interactive embed creator",
                    f"`{self.prefix}embed edit WelcomeMessage` - Edit welcome embed",
                    f"`{self.prefix}embed list` - See all server embeds",
                    f"`{self.prefix}embed export Rules` - Export rules embed as template"
                ],
                "permissions": "**Manage Messages** required for create/edit/delete",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Messages permission.`",
                    "**Embed not found:** `Embed 'name' does not exist.`",
                    "**Invalid YAML:** `The YAML template format is invalid.`",
                    "**Too many embeds:** `Maximum of 25 embeds per server.`"
                ]
            },
            
            # Sticky Messages Commands
            "stick": {
                "category": "Sticky Messages",
                "description": "Create a sticky message in the current channel",
                "usage": f"{self.prefix}stick <message>",
                "detailed_usage": [
                    f"`{self.prefix}stick Welcome to our server!` - Create sticky text",
                    f"`{self.prefix}stick EmbedName` - Create sticky from saved embed"
                ],
                "examples": [
                    f"`{self.prefix}stick Please read the rules!` - Text sticky message",
                    f"`{self.prefix}stick WelcomeEmbed` - Sticky from saved embed",
                    f"`{self.prefix}stick Check out our website: example.com` - Info sticky"
                ],
                "permissions": "**Manage Messages** required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Messages permission.`",
                    "**Already exists:** `A sticky message already exists in this channel.`",
                    "**Message too long:** `Sticky message must be 2000 characters or less.`"
                ]
            },
            
            "stickstop": {
                "category": "Sticky Messages",
                "description": "Stop the sticky message in current channel",
                "usage": f"{self.prefix}stickstop",
                "detailed_usage": [
                    f"`{self.prefix}stickstop` - Stop sticky in current channel"
                ],
                "examples": [
                    f"`{self.prefix}stickstop` - Remove sticky message from this channel",
                    "The sticky message will stop appearing after new messages"
                ],
                "permissions": "**Manage Messages** required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Messages permission.`",
                    "**No sticky:** `No sticky message found in this channel.`"
                ]
            },
            
            # Prefix Commands
            "prefix": {
                "category": "Server Management",
                "description": "Show the current server prefix",
                "usage": f"{self.prefix}prefix",
                "detailed_usage": [
                    f"`{self.prefix}prefix` - Display current server prefix"
                ],
                "examples": [
                    f"`{self.prefix}prefix` - Shows current prefix (e.g., 's.' or '!')",
                    "Also shows if bot mention is enabled as prefix"
                ],
                "permissions": "Manage server or Admin permissions",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works"
                ]
            },

            "setprefix": {
                "category": "Server Management",
                "description": "Sets a new prefix for the server",
                "usage": f"{self.prefix}setprefix",
                "detailed_usage": [
                    f"`{self.prefix}setprefix` - Sets a new new prefix for the server"
                ],
                "examples": [
                    f"`{self.prefix}setprefix s.`",
                    "Also shows if bot mention is enabled as prefix"
                ],
                "permissions": "Manage server or Admin permissions",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works"
                ]
            },
            
            # Sticky Messages - Additional Commands
            "stickslow": {
                "category": "Sticky Messages",
                "description": "Create a slow sticky message (less frequent updates)",
                "usage": f"{self.prefix}stickslow <message>",
                "detailed_usage": [
                    f"`{self.prefix}stickslow Welcome message` - Create slow sticky text",
                    f"`{self.prefix}stickslow EmbedName` - Create slow sticky from embed"
                ],
                "examples": [
                    f"`{self.prefix}stickslow Please follow the rules` - Slow text sticky",
                    f"`{self.prefix}stickslow RulesEmbed` - Slow sticky from saved embed",
                    f"`{self.prefix}stickslow Join our Discord for updates` - Info sticky"
                ],
                "permissions": "**Manage Messages** required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Messages permission.`",
                    "**Already exists:** `A sticky message already exists in this channel.`",
                    "**Message too long:** `Sticky message must be 2000 characters or less.`"
                ]
            },
            
            "stickstart": {
                "category": "Sticky Messages", 
                "description": "Restart a stopped sticky message in current channel",
                "usage": f"{self.prefix}stickstart",
                "detailed_usage": [
                    f"`{self.prefix}stickstart` - Restart sticky in current channel"
                ],
                "examples": [
                    f"`{self.prefix}stickstart` - Resume sticky message in this channel",
                    "The sticky message will start appearing again after new messages"
                ],
                "permissions": "**Manage Messages** required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Messages permission.`",
                    "**No sticky:** `No sticky message found in this channel.`",
                    "**Already running:** `Sticky message is already active in this channel.`"
                ]
            },
            
            "stickremove": {
                "category": "Sticky Messages",
                "description": "Permanently remove sticky message from current channel",
                "usage": f"{self.prefix}stickremove",
                "detailed_usage": [
                    f"`{self.prefix}stickremove` - Remove sticky from current channel"
                ],
                "examples": [
                    f"`{self.prefix}stickremove` - Delete sticky message completely",
                    "This permanently removes the sticky message configuration"
                ],
                "permissions": "**Manage Messages** required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Messages permission.`",
                    "**No sticky:** `No sticky message found in this channel.`"
                ]
            },
            
            "getstickies": {
                "category": "Sticky Messages",
                "description": "List all sticky messages in the server",
                "usage": f"{self.prefix}getstickies",
                "detailed_usage": [
                    f"`{self.prefix}getstickies` - Show all server sticky messages"
                ],
                "examples": [
                    f"`{self.prefix}getstickies` - View all stickies with channel info, status",
                    "Shows: Channel, message content, status (active/stopped), speed"
                ],
                "permissions": "**Manage Messages** required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Messages permission.`",
                    "**No stickies:** `No sticky messages found in this server.`"
                ]
            },
            
            "stickspeed": {
                "category": "Sticky Messages",
                "description": "View or change sticky message update speed",
                "usage": f"{self.prefix}stickspeed [speed]",
                "detailed_usage": [
                    f"`{self.prefix}stickspeed` - View current speed",
                    f"`{self.prefix}stickspeed fast` - Set to fast updates",
                    f"`{self.prefix}stickspeed slow` - Set to slow updates"
                ],
                "examples": [
                    f"`{self.prefix}stickspeed` - Check current update speed",
                    f"`{self.prefix}stickspeed fast` - Update after every message",
                    f"`{self.prefix}stickspeed slow` - Update every 5 messages"
                ],
                "permissions": "**Manage Messages** required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Missing permissions:** `You need Manage Messages permission.`",
                    "**No sticky:** `No sticky message found in this channel.`",
                    "**Invalid speed:** `Speed must be: fast or slow`"
                ]
            },
            
            # Reminder Commands - Additional
            "reminders": {
                "category": "Reminders",
                "description": "List all your active reminders",
                "usage": f"{self.prefix}reminders",
                "detailed_usage": [
                    f"`{self.prefix}reminders` - Show all your active reminders"
                ],
                "examples": [
                    f"`{self.prefix}reminders` - View your reminder list with times and messages",
                    "Shows: Reminder ID, time remaining, message content"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No reminders:** `You have no active reminders.`"
                ]
            },
            
            "delreminder": {
                "category": "Reminders",
                "description": "Delete a specific reminder by ID",
                "usage": f"{self.prefix}delreminder <reminder_id>",
                "detailed_usage": [
                    f"`{self.prefix}delreminder 1` - Delete reminder ID 1",
                    f"`{self.prefix}delreminder 5` - Delete reminder ID 5"
                ],
                "examples": [
                    f"`{self.prefix}delreminder 1` - Remove your first reminder",
                    f"`{self.prefix}delreminder 3` - Remove your third reminder",
                    f"Use `{self.prefix}reminders` to see all IDs first"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Invalid ID:** `Reminder ID must be a number.`",
                    "**Not found:** `You don't have a reminder with ID X.`",
                    "**No reminders:** `You have no reminders to delete.`"
                ]
            },
        }
        
        # Get command info or return generic info
        cmd_name = self.command.name.lower()
        return detailed_info.get(cmd_name, {
            "category": "Unknown",
            "description": self.command.help or "No description available",
            "usage": f"{self.prefix}{self.command.name}",
            "detailed_usage": [f"`{self.prefix}{self.command.name}` - Basic usage"],
            "examples": [f"`{self.prefix}{self.command.name}` - Example usage"],
            "permissions": "Check command documentation",
            "cooldown": "Varies per command",
            "error_scenarios": ["Use the command correctly to avoid errors"]
        })
    
    def create_main_embed(self):
        """Create the main detailed help embed"""
        info = self.get_detailed_command_info()
        
        embed = discord.Embed(
            title=f"{self.command.name.title()} Command",
            description=info['description'],
            color=EMBED_COLOR_NORMAL
        )
        
        # Clean usage section
        embed.add_field(
            name="Quick Usage",
            value=f"`{info['usage']}`",
            inline=False
        )
        
        # Top examples with clean formatting
        examples = info['examples'][:2]  # Show only 2 examples to avoid clutter
        examples_text = "\n".join([f"• {example}" for example in examples])
        embed.add_field(
            name="Examples",
            value=examples_text,
            inline=False
        )
        
        # Requirements in a cleaner format
        embed.add_field(
            name="Requirements",
            value=f"Permissions: {info['permissions']}",
            inline=True
        )
        
        embed.add_field(
            name="Cooldown",
            value=info['cooldown'],
            inline=True
        )
        
        embed.add_field(
            name="Category",
            value=info['category'],
            inline=True
        )
        
        embed.add_field(
            name="More Information",
            value="Use the buttons below to see detailed usage, all examples, or troubleshooting help.",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {self.user.display_name} • Page 1/4", icon_url=self.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    def create_detailed_usage_embed(self):
        """Create detailed usage embed showing how to use the command"""
        info = self.get_detailed_command_info()
        
        embed = discord.Embed(
            title=f"Detailed Usage: {self.command.name}",
            description=f"How to use the `{self.command.name}` command",
            color=EMBED_COLOR_NORMAL
        )
        
        # Show the detailed usage patterns from the command data
        detailed_usage = info.get('detailed_usage', [f"`{self.prefix}{self.command.name}` - Basic usage"])
        usage_text = "\n".join(detailed_usage)
        
        embed.add_field(
            name="Usage Patterns", 
            value=usage_text,
            inline=False
        )
        
        # Show examples from the command data
        examples = info.get('examples', [f"`{self.prefix}{self.command.name}` - Example"])
        examples_text = "\n".join(examples)
        
        embed.add_field(
            name="Examples",
            value=examples_text,
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {self.user.display_name} • Detailed Usage", icon_url=self.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    def create_examples_embed(self):
        """Create comprehensive examples embed"""
        info = self.get_detailed_command_info()
        
        embed = discord.Embed(
            title=f"{self.command.name.title()} - All Examples",
            description="Copy any example below and customize it for your needs:",
            color=EMBED_COLOR_SUCCESS
        )
        
        # Format examples with clean bullet points and numbering
        examples_with_numbers = []
        for i, example in enumerate(info['examples'], 1):
            examples_with_numbers.append(f"**{i}.** {example}")
        
        examples_text = "\n\n".join(examples_with_numbers)
        embed.add_field(
            name="Ready-to-Use Examples",
            value=examples_text,
            inline=False
        )
        
        embed.add_field(
            name="Pro Tips", 
            value="```\n• Copy examples exactly as shown\n• Replace @user with actual mentions\n• Check spelling of names/roles\n• Wait for cooldowns between commands\n```",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {self.user.display_name} • Page 3/4", icon_url=self.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    def create_errors_embed(self):
        """Create common errors and solutions embed"""
        info = self.get_detailed_command_info()
        
        embed = discord.Embed(
            title=f"{self.command.name.title()} - Troubleshooting",
            description="Having issues? Check these common problems and solutions:",
            color=EMBED_COLOR_ERROR
        )
        
        # Format errors with clean numbering and separation
        error_items = []
        for i, error in enumerate(info['error_scenarios'], 1):
            # Clean up error formatting
            clean_error = error.replace("**", "").replace("`", "")
            error_items.append(f"**{i}.** {clean_error}")
        
        errors_text = "\n\n".join(error_items)
        embed.add_field(
            name="Common Issues & Solutions",
            value=errors_text,
            inline=False
        )
        
        embed.add_field(
            name="General Troubleshooting Steps",
            value="```\n1. Check your spelling and format\n2. Verify you have required permissions\n3. Ensure user/channel/role exists\n4. Wait for command cooldown\n5. Copy examples exactly as shown\n6. Try using mentions (@user) instead of names\n```",
            inline=False
        )
        
        embed.add_field(
            name="Still Need Help?",
            value="If none of these solutions work, ask a server administrator or check the command examples again.",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {self.user.display_name} • Page 4/4", icon_url=self.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    def create_format_guide_embed(self):
        """Create format guide embed explaining command syntax symbols"""
        embed = discord.Embed(
            title="Format Guide",
            color=EMBED_COLOR_NORMAL
        )
        
        embed.add_field(
            name="Format Guide",
            value="```\n<required>  - Must provide this\n[optional]  - Can provide this\n|           - Choose one option\n...         - Can repeat multiple times\n```",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {self.user.display_name} • Format Guide", icon_url=self.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    @discord.ui.button(label="Format Guide", style=discord.ButtonStyle.primary, row=0)
    async def format_guide_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show format guide page"""
        embed = self.create_format_guide_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        self.current_page = "format"
    
    @discord.ui.button(label="Detailed Usage", style=discord.ButtonStyle.primary, row=0)
    async def detailed_usage_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show detailed usage page"""
        embed = self.create_detailed_usage_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        self.current_page = "usage"
    
    @discord.ui.button(label="Common Errors", style=discord.ButtonStyle.danger, row=0)
    async def errors_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show errors and solutions page"""
        embed = self.create_errors_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        self.current_page = "errors"
    
    @discord.ui.button(label="Exit", style=discord.ButtonStyle.secondary, row=1)
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the help message"""
        embed = discord.Embed(
            title="Help Closed",
            description=f"Help for `{self.command.name}` has been closed.\n"
                       f"Use `{self.prefix}help {self.command.name}` to reopen.",
            color=EMBED_COLOR_SUCCESS
        )
        embed.set_footer(text=f"Closed by {self.user.display_name}", icon_url=self.user.display_avatar.url)
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    async def on_timeout(self):
        """Handle view timeout"""
        # Disable all buttons when timeout
        for item in self.children:
            item.disabled = True

class HelpCommand(commands.Cog):
    """Simple help command with list layout"""
    
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = None
    
    def cog_unload(self):
        self.bot.help_command = self._original_help_command
    
    @commands.command(name="help", help="Show commands list")
    async def help_command(self, ctx, *, command_name: Optional[str] = None):
        """Simple help command with list format"""
        try:
            # Get prefix for this guild
            if ctx.guild:
                prefix = guild_settings.get_prefix(ctx.guild.id)
            else:
                prefix = 's.'
            
            # If specific command requested
            if command_name:
                await self.show_command_help(ctx, command_name, prefix)
                return
            
            # Show main help list
            embed = discord.Embed(
                title="Sprouts Commands List",
                description=f"Optional arguments are marked by `[arg]` and mandatory arguments are marked by `<arg>`.\n\n"
                           f"Use `{prefix}help <command>` for detailed info.\n"
                           f"This server prefix: `{prefix}`, <@{self.bot.user.id}>",
                color=EMBED_COLOR_NORMAL
            )
            
            # Uncategorized commands
            uncategorized_commands = [
                "`about` - Show bot statistics, uptime, and system information",
                "`invite` - Get bot invite link and support server links", 
                "`shards` - Display bot shard information and latency",
                "`vote` - Get voting links to support the bot"
            ]
            
            embed.add_field(
                name="Uncategorized",
                value="\n".join(uncategorized_commands),
                inline=False
            )
            
            # Utilities commands
            utilities_commands = [
                "`avatar` - Get user's avatar (defaults to yourself)",
                "`channelinfo` - Get detailed channel information",
                "`inviteinfo` - Get information about Discord invite", 
                "`ping` - Check bot response time and API latency",
                "`roleinfo` - Get detailed role information and permissions",
                "`serverinfo` - Get detailed server information and statistics",
                "`userinfo` - Get detailed user information (defaults to yourself)",
                "`setprefix` - Set custom command prefix for this server",
                "`prefix` - Show current server prefix",
                "`variables` - Show all available variables for embeds and messages"
            ]
            
            embed.add_field(
                name="Utilities", 
                value="\n".join(utilities_commands),
                inline=False
            )
            
            
            # Ticket commands
            ticket_commands = [
                "`new` - Create support ticket",
                "`add` - Add member to ticket",
                "`claim` - Claim ticket ownership", 
                "`close` - Close ticket",
                "`forceclose` - Force close ticket",
                "`move` - Move to a new ticket category",
                "`unclaim` - Release ticket ownership",
                "`remove` - Remove member from ticket",
                "`listtickets` - List active guild tickets",
                "`topic` - Sets the topic of the ticket",
                "`rename` - Rename a ticket channel",
                "`createpanel` - Create a new ticket panel",
                "`listpanels` - List the active ticket panels",
                "`delpanel` - Delete an active ticket panel",
                "`ticketsetup` - Setup system",
                "`ticketlimit` - Sets the ticket limit, by default is 10",
                "`ticketuseembed` - Uses an custom embed for the ticket message"
            ]
            
            embed.add_field(
                name="Ticket",
                value="\n".join(ticket_commands),
                inline=False
            )
            
            # Embed Builder commands
            embed_commands = [
                "`embedcreate` - Create a new embed with visual editor",
                "`embedcreateempty` - Create an empty embed to edit later",
                "`embedlist` - List all saved embeds",
                "`embedview` - View a saved embed",
                "`embededit` - Edit an embed with visual interface",
                "`embeddelete` - Delete a saved embed",
                "`embedexport` - Export embed as YAML template",
                "`embedimport` - Import embed from YAML template",
                "`embedoldedit` - Legacy text-based embed editor"
            ]
            
            embed.add_field(
                name="Embed Builder",
                value="\n".join(embed_commands),
                inline=False
            )
            
            # Auto Responders commands - SIMPLE SYSTEM
            auto_responder_commands = [
                "`autoresponder add` - Add simple auto responder",
                "`autoresponder editreply` - Edit responder reply", 
                "`autoresponder remove` - Remove auto responder",
                "`autoresponder list` - List all auto responders",
                "`autoresponder toggle` - Enable/disable responder",
                "Format: `trigger:<text> reply:<response>`",
                "Simple trigger and reply system without complex functions"
            ]
            
            embed.add_field(
                name="Auto Responders",
                value="\n".join(auto_responder_commands),
                inline=False
            )
            
            # Sticky Messages commands
            sticky_commands = [
                "`stick` - Create sticky message",
                "`stickslow` - Create slow sticky message",
                "`stickstop` - Stop sticky in channel", 
                "`stickstart` - Restart sticky in channel",
                "`stickremove` - Remove sticky completely",
                "`getstickies` - List all server stickies",
                "`stickspeed` - View/change sticky speed"
            ]
            
            embed.add_field(
                name="Sticky Messages",
                value="\n".join(sticky_commands),
                inline=False
            )
            
            # Reminders commands
            reminder_commands = [
                "`remind` - Set a personal reminder",
                "`reminders` - List your active reminders", 
                "`delreminder` - Delete a specific reminder"
            ]
            
            embed.add_field(
                name="Reminders",
                value="\n".join(reminder_commands),
                inline=False
            )
            
            
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Help command used by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await ctx.reply("An error occurred while displaying help.", mention_author=False)
    
    async def show_command_help(self, ctx, command_name: str, prefix: str):
        """Show extremely detailed help for a specific command with interactive buttons"""
        try:
            # Handle subcommands properly (e.g., "autoresponder add")
            if ' ' in command_name:
                parts = command_name.split(' ', 1)
                main_command = self.bot.get_command(parts[0].lower())
                if main_command and hasattr(main_command, 'commands'):
                    # This is a group command, look for the subcommand
                    subcommand = main_command.get_command(parts[1].lower())
                    if subcommand:
                        command = subcommand
                    else:
                        command = None
                else:
                    command = None
            else:
                command = self.bot.get_command(command_name.lower())
            
            if not command:
                embed = discord.Embed(
                    title="Command Not Found",
                    description=f"No command named `{command_name}` was found.\n"
                               f"Use `{self.prefix}help` to see all available commands.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Use the modern interactive help system with buttons
            help_view = DetailedCommandHelpView(command, prefix, ctx.author)
            embed = help_view.create_main_embed()
            await ctx.reply(embed=embed, view=help_view, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error showing command help for '{command_name}': {e}")
            # If it's likely a command not found, show proper error
            current_prefix = guild_settings.get_prefix(ctx.guild.id) if ctx.guild else "s."
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Command Not Found",
                description=f"No command named `{command_name}` was found.\n"
                           f"Use `{current_prefix}help` to see all available commands.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

async def setup_help(bot):
    """Setup help command for the bot"""
    await bot.add_cog(HelpCommand(bot))
    logger.info("Help command setup completed")

# For backwards compatibility
async def setup(bot):
    await setup_help(bot)
