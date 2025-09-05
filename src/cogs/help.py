"""
Simple Help Command (Text Commands Only)
Displays commands in a simple list format like the original image
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from src.emojis import SPROUTS_ERROR, SPROUTS_CHECK, SPROUTS_WARNING, SPROUTS_INFORMATION
from src.feature_flags import feature_manager

# Add success color if not in config
EMBED_COLOR_SUCCESS = 0x77DD77
from src.cogs.guild_settings import guild_settings

logger = logging.getLogger(__name__)

class HelpPaginationView(discord.ui.View):
    """Pagination view for help command with Previous, Next, Close buttons"""
    
    def __init__(self, pages, user_id, prefix):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = 0
        self.user_id = user_id
        self.prefix = prefix
        
        # Update button states
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page"""
        self.previous_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page == len(self.pages) - 1)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the user who ran the command to use buttons"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot control someone else's help menu!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = self.pages[self.current_page]
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            embed = self.pages[self.current_page]
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the help menu"""
        embed = discord.Embed(
            description="Help menu closed.",
            color=EMBED_COLOR_NORMAL
        )
        await interaction.response.edit_message(embed=embed, view=None)

class DetailedCommandHelpView(discord.ui.View):
    """Modern interactive view for command help with sleek design"""
    
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
            
            # Embed Builder - SPROUTS System
            "embed": {
                "category": "Embed Builder",
                "description": "SPROUTS advanced Discord-native embed builder with interactive forms and live preview",
                "usage": f"{self.prefix}embed",
                "detailed_usage": [
                    f"`{self.prefix}embed` - Open the main embed builder interface",
                    f"`{self.prefix}createembed` - Alternative command name",
                    f"`{self.prefix}embedcreate` - Alternative command name"
                ],
                "examples": [
                    f"`{self.prefix}embed` - Start the interactive embed builder",
                    "Choose from: Interactive Builder, Quick Builder, Templates, or JSON Import",
                    "Create professional embeds with live preview before sending"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "features": [
                    "🎨 **Interactive Builder** - Step-by-step creation with modal forms",
                    "⚡ **Quick Builder** - Fast single-modal creation",
                    "📋 **Professional Templates** - 6 pre-made designs (announcement, welcome, rules, event, support, info)",
                    "📤 **JSON Import/Export** - Import from external builders & export for reuse",
                    "🎨 **Live Preview** - See your embed before sending",
                    "🎨 **Advanced Color System** - Named colors (red, blue, discord) + hex support"
                ],
                "error_scenarios": [
                    "**No errors possible** - The builder handles all validation",
                    "**JSON Import:** Invalid JSON format will be clearly reported",
                    "**Modal Timeout:** Modals timeout after 5 minutes of inactivity"
                ]
            },
            
            "createembed": {
                "category": "Embed Builder",
                "description": "Alternative command name for SPROUTS embed builder",
                "usage": f"{self.prefix}createembed",
                "detailed_usage": [
                    f"`{self.prefix}createembed` - Same as {self.prefix}embed command"
                ],
                "examples": [
                    f"`{self.prefix}createembed` - Opens the interactive embed builder interface"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - Redirects to main embed builder"
                ]
            },
            
            "embedcreate": {
                "category": "Embed Builder", 
                "description": "Alternative command name for SPROUTS embed builder",
                "usage": f"{self.prefix}embedcreate",
                "detailed_usage": [
                    f"`{self.prefix}embedcreate` - Same as {self.prefix}embed command"
                ],
                "examples": [
                    f"`{self.prefix}embedcreate` - Opens the interactive embed builder interface"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user", 
                "error_scenarios": [
                    "**No errors possible** - Redirects to main embed builder"
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

class HelpView(discord.ui.View):
    """Simple help navigation with Previous, Next, and Close buttons"""
    
    def __init__(self, bot, user, prefix):
        super().__init__(timeout=300)
        self.bot = bot
        self.user = user
        self.prefix = prefix
        self.current_page = "main"
        self.page_order = ["main", "utilities", "tickets", "embeds", "autoresponders", "sticky", "reminders", "serverstats"]
        self.current_index = 0
        
        # Define all help pages with the same content structure
        self.pages = {
            "main": {
                "title": "Sprouts Commands List",
                "description": f"Optional arguments are marked by `[arg]` and mandatory arguments are marked by `<arg>`.\n\nUse `{prefix}help <command>` for detailed info.\nThis server prefix: `{prefix}`, <@{self.bot.user.id}>",
                "fields": [
                    {
                        "name": f"{SPROUTS_INFORMATION} Command Categories",
                        "value": "Use the buttons below to browse different command categories:\n\n"
                                f"{SPROUTS_INFORMATION} **Utilities** - Basic bot commands and server info\n"
                                f"{SPROUTS_INFORMATION} **Tickets** - Support ticket system management\n"
                                f"{SPROUTS_INFORMATION} **Embed Builder** - Create and edit custom embeds\n" 
                                f"{SPROUTS_INFORMATION} **Auto Responders** - Automated message responses\n"
                                f"{SPROUTS_INFORMATION} **Sticky Messages** - Persistent channel messages\n"
                                f"{SPROUTS_INFORMATION} **Reminders** - Personal reminder system\n"
                                f"{SPROUTS_INFORMATION} **Server Stats** - Server monitoring tools",
                        "inline": False
                    }
                ]
            },
            "utilities": {
                "title": f"{SPROUTS_INFORMATION} Utilities Commands",
                "description": f"Basic utility commands and server information tools\nPrefix: `{prefix}`",
                "fields": [
                    {
                        "name": "Basic Info Commands",
                        "value": "`about` - Show bot statistics, uptime, and system information\n"
                                "`invite` - Get bot invite link and support server links\n"
                                "`shards` - Display bot shard information and latency\n"
                                "`vote` - Get voting links to support the bot",
                        "inline": False
                    },
                    {
                        "name": "User & Server Info",
                        "value": "`avatar` - Get user's avatar (defaults to yourself)\n"
                                "`channelinfo` - Get detailed channel information\n"
                                "`inviteinfo` - Get information about Discord invite\n"
                                "`ping` - Check bot response time and API latency\n"
                                "`roleinfo` - Get detailed role information and permissions\n"
                                "`serverinfo` - Get detailed server information and statistics\n"
                                "`userinfo` - Get detailed user information (defaults to yourself)",
                        "inline": False
                    },
                    {
                        "name": "Configuration",
                        "value": "`setprefix` - Set custom command prefix for this server\n"
                                "`prefix` - Show current server prefix\n"
                                "`variables` - Show all available variables for embeds and messages",
                        "inline": False
                    }
                ]
            },
            "tickets": {
                "title": f"{SPROUTS_INFORMATION} Ticket System Commands",
                "description": f"Complete support ticket management system\nPrefix: `{prefix}`",
                "fields": [
                    {
                        "name": "User Ticket Commands",
                        "value": "`new` / `open` - Create new support ticket\n"
                                "`close` - Close current ticket with reason",
                        "inline": False
                    },
                    {
                        "name": "Staff Tools & Moderation",
                        "value": "`blacklist` - Manage user blacklist system\n"
                                "`viewstaff` - View all staff members\n"
                                "`managetags add/delete/list` - Manage response tags\n"
                                "`tickettag` - Send tag response\n"
                                "`notes` - Create staff-only thread\n"
                                "`on-call` - Toggle staff auto-assignment",
                        "inline": False
                    },
                    {
                        "name": "Configuration Commands",
                        "value": "`setup auto` - Initial ticket system configuration\n"
                                "`setup limit` - Set user ticket limit per server\n"
                                "`setup transcripts` - Configure full conversation transcripts\n"
                                "`setup use-threads` - Toggle threads vs channels\n"
                                "`autoclose configure` - Configure automatic closure\n"
                                "`autoclose exclude` - Exclude ticket from autoclose\n"
                                "`addadmin` / `removeadmin` - Manage admin roles\n"
                                "`addsupport` / `removesupport` - Manage staff roles",
                        "inline": False
                    },
                    {
                        "name": "Ticket Panels & Setup",
                        "value": "`createpanel` - Create new ticket panel\n"
                                "`listpanels` - List all ticket panels\n"
                                "`delpanel` - Delete ticket panel\n"
                                "`ticketsetup` - Interactive setup wizard\n"
                                "`ticketlimit` - Set user ticket limit\n"
                                "`ghostping` - Toggle ghost ping",
                        "inline": False
                    },
                    {
                        "name": "Staff Ticket Management",
                        "value": "`claim` - Claim ownership of ticket\n"
                                "`unclaim` - Release ticket ownership\n"
                                "`add` - Add user to current ticket\n"
                                "`remove` - Remove user from ticket\n"
                                "`rename` - Rename ticket channel\n"
                                "`tickettopic` - Set ticket description\n"
                                "`move` - Move ticket to category\n"
                                "`forceclose` - Force close any ticket\n"
                                "`listtickets` - View all active tickets",
                        "inline": False
                    }
                ]
            },
            "embeds": {
                "title": f"{SPROUTS_INFORMATION} SPROUTS Style Embed System",
                "description": f"Professional partnership-grade embed builder with advanced customization\nPrefix: `{prefix}`",
                "fields": [
                    {
                        "name": "Advanced Embed Creation",
                        "value": "`embedcreate [name]` - Create professional embed with visual editor\n"
                                "`embededit [name] [element] [value]` - Edit specific embed elements\n"
                                "`embedcreateempty [name]` - Create blank embed template\n"
                                "`embedtest [name]` - Preview embed before saving",
                        "inline": False
                    },
                    {
                        "name": "Embed Management & Variables", 
                        "value": "`embedlist` - List all saved embeds with previews\n"
                                "`embedview [name]` - View saved embed with full details\n"
                                "`embeddelete [name]` - Remove saved embed\n"
                                "`embedvariables` - Show all available variables",
                        "inline": False
                    },
                    {
                        "name": "Import, Export & Templates",
                        "value": "`embedexport [name]` - Export as shareable YAML template\n"
                                "`embedimport` - Import from YAML/JSON template\n"
                                "`embedcopy [name] [newname]` - Copy existing embed\n"
                                "`embedtemplate [type]` - Load partnership templates",
                        "inline": False
                    },
                    {
                        "name": "Quick Actions & Integration",
                        "value": "`embedsend [name] [#channel]` - Send embed to channel\n"
                                "`embedattach [name]` - Attach to autoresponder/panel\n"
                                "`embedcolor [name] [hex]` - Quick color changes\n"
                                "`embedpreview [name]` - Live preview with variables",
                        "inline": False
                    }
                ]
            },
            "autoresponders": {
                "title": f"{SPROUTS_INFORMATION} Auto Responders Commands",
                "description": f"Simple trigger and reply system\nPrefix: `{prefix}`",
                "fields": [
                    {
                        "name": "Auto Responder Management",
                        "value": "`autoresponder add` - Add simple auto responder\n"
                                "`autoresponder editreply` - Edit responder reply\n"
                                "`autoresponder remove` - Remove auto responder\n"
                                "`autoresponder list` - List all auto responders\n"
                                "`autoresponder toggle` - Enable/disable responder",
                        "inline": False
                    },
                    {
                        "name": "Format & Usage",
                        "value": "**Format:** `trigger:<text> reply:<response>`\n"
                                "Simple trigger and reply system without complex functions\n\n"
                                "**Example:**\n"
                                f"`{prefix}autoresponder add trigger:hello reply:Hello there!`",
                        "inline": False
                    }
                ]
            },
            "sticky": {
                "title": f"{SPROUTS_INFORMATION} Sticky Messages Commands", 
                "description": f"Persistent channel messages that auto-repost\nPrefix: `{prefix}`",
                "fields": [
                    {
                        "name": "Sticky Message Controls",
                        "value": "`stick` - Create sticky message\n"
                                "`stickslow` - Create slow sticky message\n"
                                "`stickstop` - Stop sticky in channel\n"
                                "`stickstart` - Restart sticky in channel\n"
                                "`stickremove` - Remove sticky completely",
                        "inline": False
                    },
                    {
                        "name": "Management",
                        "value": "`getstickies` - List all server stickies\n"
                                "`stickspeed` - View/change sticky speed",
                        "inline": False
                    }
                ]
            },
            "reminders": {
                "title": f"{SPROUTS_INFORMATION} Reminders Commands",
                "description": f"Personal reminder system with flexible time formats\nPrefix: `{prefix}`",
                "fields": [
                    {
                        "name": "Reminder Management",
                        "value": "`remind` - Set a personal reminder\n"
                                "`reminders` - List your active reminders\n"
                                "`delreminder` - Delete a specific reminder",
                        "inline": False
                    },
                    {
                        "name": "Time Format Examples",
                        "value": f"`{prefix}remind 1h Take a break` - 1 hour reminder\n"
                                f"`{prefix}remind 30m Check dinner` - 30 minute reminder\n"
                                f"`{prefix}remind 1d2h Meeting` - 1 day 2 hours reminder\n"
                                "Supports: s (seconds), m (minutes), h (hours), d (days), w (weeks)",
                        "inline": False
                    }
                ]
            },
            "serverstats": {
                "title": f"{SPROUTS_INFORMATION} Server Stats Commands",
                "description": f"Real-time server monitoring and statistics\nPrefix: `{prefix}`",
                "fields": [
                    {
                        "name": "Server Statistics",
                        "value": "`serverstats` - View/manage server statistics monitoring\n"
                                "Provides real-time member count tracking and server analytics\n"
                                "Requires **Manage Guild** permission to enable/disable",
                        "inline": False
                    }
                ]
            }
        }
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the user who ran the command to use buttons"""
        return interaction.user.id == self.user.id
    
    async def create_embed(self, page_key):
        """Create embed for specific page"""
        page = self.pages[page_key]
        
        embed = discord.Embed(
            title=page["title"],
            description=page["description"],
            color=EMBED_COLOR_NORMAL
        )
        
        for field in page["fields"]:
            embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field.get("inline", False)
            )
        
        embed.set_footer(
            text=f"Use {self.prefix}help <command> for detailed command info",
            icon_url=self.user.display_avatar.url
        )
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        await interaction.response.defer()
        
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.page_order) - 1  # Wrap to last page
            
        self.current_page = self.page_order[self.current_index]
        embed = await self.create_embed(self.current_page)
        await interaction.edit_original_response(embed=embed, view=self)
    
    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        await interaction.response.defer()
        
        if self.current_index < len(self.page_order) - 1:
            self.current_index += 1
        else:
            self.current_index = 0  # Wrap to first page
            
        self.current_page = self.page_order[self.current_index]
        embed = await self.create_embed(self.current_page)
        await interaction.edit_original_response(embed=embed, view=self)
    
    @discord.ui.button(label=f'{SPROUTS_ERROR} Close', style=discord.ButtonStyle.danger)
    async def close_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the help menu"""
        await interaction.response.defer()
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
            
        embed = discord.Embed(
            title="Help Menu Closed",
            description="Thanks for using the help system!",
            color=EMBED_COLOR_SUCCESS
        )
        await interaction.edit_original_response(embed=embed, view=self)
    
    async def on_timeout(self):
        """Disable view when timeout occurs"""
        for item in self.children:
            item.disabled = True


class HelpCommand(commands.Cog):
    """Interactive help command with button navigation"""
    
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = None
    
    def cog_unload(self):
        self.bot.help_command = self._original_help_command
    
    @commands.command(name="help", help="Show commands list")
    async def help_command(self, ctx, *, command_name: Optional[str] = None):
        """Show help for bot commands with button pagination"""
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
            
            # Create paginated help
            pages = self.create_help_pages(prefix, ctx.author)
            view = HelpPaginationView(pages, ctx.author.id, prefix)
            await ctx.reply(embed=pages[0], view=view, mention_author=False)
            logger.info(f"Help command used by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await ctx.reply("An error occurred while displaying help.", mention_author=False)
    
    def create_help_pages(self, prefix, author):
        """Create dynamic help pages based on enabled features"""
        pages = []
        
        # Get enabled commands (automatically excludes dev-only commands)
        enabled_commands = list(feature_manager.get_enabled_commands(self.bot))
        
        # Define command categories and their commands
        command_categories = {
            "Core Commands": {
                "commands": ["help", "ping", "avatar", "userinfo", "serverinfo"],
                "descriptions": {
                    "help": "Show commands list and get detailed help",
                    "ping": "Check bot response time and API latency",
                    "avatar": "Display user's avatar in full resolution",
                    "userinfo": "Get detailed user information",
                    "serverinfo": "Get comprehensive server statistics"
                }
            },
            "Utility Commands": {
                "commands": ["channelinfo", "roleinfo", "variables", "setprefix"],
                "descriptions": {
                    "channelinfo": "Get detailed channel information",
                    "roleinfo": "Get detailed role information",
                    "variables": "Show available embed variables",
                    "setprefix": "Set custom command prefix"
                }
            },
            "User Ticket Commands": {
                "commands": ["new", "open", "close", "tickettopic"],
                "descriptions": {
                    "new": "Create new support ticket",
                    "open": "Create new support ticket (alias for new)",
                    "close": "Close current ticket with reason",
                    "tickettopic": "Set ticket description"
                }
            },
            "Staff Ticket Management": {
                "commands": ["claim", "unclaim", "add", "remove", "rename", "transcript", "forceclose"],
                "descriptions": {
                    "claim": "Claim ownership of ticket",
                    "unclaim": "Release ticket ownership", 
                    "add": "Add user to current ticket",
                    "remove": "Remove user from ticket",
                    "rename": "Rename ticket channel",
                    "transcript": "Generate ticket transcript",
                    "forceclose": "Force close any ticket"
                }
            },
            "Ticket System Setup": {
                "commands": ["ticketsetup", "ticketpanel", "addadmin", "removeadmin", "addsupport", "removesupport"],
                "descriptions": {
                    "ticketsetup": "Interactive ticket system setup",
                    "ticketpanel": "Create new ticket panel",
                    "addadmin": "Add admin role to ticket system",
                    "removeadmin": "Remove admin role from ticket system",
                    "addsupport": "Add support role to ticket system", 
                    "removesupport": "Remove support role from ticket system"
                }
            },
            "Ticket Moderation": {
                "commands": ["blacklist", "unblacklist", "blacklistcheck"],
                "descriptions": {
                    "blacklist": "Add user to ticket blacklist",
                    "unblacklist": "Remove user from ticket blacklist",
                    "blacklistcheck": "Check if user is blacklisted"
                }
            },
            "Embed Builder": {
                "commands": ["embed", "createembed", "embedcreate"],
                "descriptions": {
                    "embed": "SPROUTS advanced Discord-native embed builder",
                    "createembed": "Create professional embeds with interactive forms",
                    "embedcreate": "Advanced embed creation with live preview"
                }
            },
            "Auto Systems": {
                "commands": ["autoresponder", "autoresponderlist", "autoresponderdelete"],
                "descriptions": {
                    "autoresponder": "Create auto responder with modern UI",
                    "autoresponderlist": "List all server auto responders",
                    "autoresponderdelete": "Delete an auto responder"
                }
            },
            "Sticky Messages": {
                "commands": ["stick", "stickslow", "stickstop", "stickstart", "stickremove", "getstickies", "stickspeed"],
                "descriptions": {
                    "stick": "Create sticky message",
                    "stickslow": "Create slow sticky message", 
                    "stickstop": "Stop sticky in channel",
                    "stickstart": "Restart sticky in channel",
                    "stickremove": "Remove sticky completely",
                    "getstickies": "List all server stickies",
                    "stickspeed": "View/change sticky speed"
                }
            },
            "Reminders": {
                "commands": ["remind", "reminders", "delreminder"],
                "descriptions": {
                    "remind": "Set a personal reminder",
                    "reminders": "List your active reminders",
                    "delreminder": "Delete a specific reminder"
                }
            },
            "Server Statistics": {
                "commands": ["serverstats", "statssetup"],
                "descriptions": {
                    "serverstats": "View real-time server statistics",
                    "statssetup": "Configure server stats display"
                }
            },
            "Event Logging": {
                "commands": ["eventlogging", "loggingsetup"],
                "descriptions": {
                    "eventlogging": "Configure guild event logging",
                    "loggingsetup": "Setup logging channels"
                }
            },
            "Command Logging": {
                "commands": ["cmdlogging"],
                "descriptions": {
                    "cmdlogging": "Configure command usage logging"
                }
            },
            "DM Logging": {
                "commands": ["dmlogging"],
                "descriptions": {
                    "dmlogging": "Configure DM logging system"
                }
            }
        }
        
        # Build pages dynamically
        current_page = None
        current_fields = 0
        page_number = 1
        
        for category_name, category_data in command_categories.items():
            # Filter commands that are enabled
            available_commands = []
            for cmd in category_data["commands"]:
                if cmd in enabled_commands:
                    desc = category_data["descriptions"].get(cmd, "No description available")
                    if cmd in ["new", "open"]:
                        available_commands.append("`new` / `open` - Create new support ticket")
                    elif cmd != "open":  # Skip open since it's combined with new
                        available_commands.append(f"`{cmd}` - {desc}")
            
            # Skip empty categories
            if not available_commands:
                continue
            
            # Create new page if needed
            if current_page is None or current_fields >= 3:
                if current_page is not None:
                    pages.append(current_page)
                
                current_page = discord.Embed(
                    title="Sprouts Commands",
                    description=f"Use `{prefix}help <command>` for detailed info.\nThis server prefix: `{prefix}`, <@1411758556667056310>",
                    color=EMBED_COLOR_NORMAL
                )
                
                # Set bot thumbnail
                if self.bot.user and self.bot.user.display_avatar:
                    current_page.set_thumbnail(url=self.bot.user.display_avatar.url)
                
                current_fields = 0
                page_number += 1
            
            # Add category to current page
            current_page.add_field(
                name=category_name,
                value="\n".join(available_commands),
                inline=False
            )
            current_fields += 1
        
        # Add the last page if it has content
        if current_page is not None and current_fields > 0:
            pages.append(current_page)
        
        # Add page numbers to footers
        total_pages = len(pages)
        for i, page in enumerate(pages):
            page.set_footer(
                text=f"Page {i+1}/{total_pages} • Requested by {author.display_name}",
                icon_url=author.display_avatar.url
            )
        
        # If no enabled commands, show a minimal page
        if not pages:
            minimal_page = discord.Embed(
                title="Sprouts Commands",
                description=f"No commands are currently available.\nContact the bot developer for assistance.",
                color=EMBED_COLOR_ERROR
            )
            minimal_page.set_footer(text=f"Requested by {author.display_name}", icon_url=author.display_avatar.url)
            pages.append(minimal_page)
        
        return pages
    
    async def show_command_help(self, ctx, command_name, prefix):
        page2 = discord.Embed(
            title="Sprouts Commands",
            description=f"Use `{prefix}help <command>` for detailed info.\nThis server prefix: `{prefix}`, <@1411758556667056310>",
            color=EMBED_COLOR_NORMAL
        )
        
        # Set bot thumbnail
        if self.bot.user and self.bot.user.display_avatar:
            page2.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # User Ticket Commands
        page2.add_field(
            name="User Ticket Commands",
            value=(
                "`new` / `open` - Create new support ticket\n"
                "`close` - Close current ticket with reason"
            ),
            inline=False
        )
        
        # Staff Ticket Management
        page2.add_field(
            name="Staff Ticket Management",
            value=(
                "`claim` - Claim ownership of ticket\n"
                "`unclaim` - Release ticket ownership\n"
                "`add` - Add user to current ticket\n"
                "`remove` - Remove user from ticket\n"
                "`rename` - Rename ticket channel\n"
                "`tickettopic` - Set ticket description\n"
                "`move` - Move ticket to category\n"
                "`forceclose` - Force close any ticket\n"
                "`listtickets` - View all active tickets"
            ),
            inline=False
        )
        
        # Ticket Panels & Setup
        page2.add_field(
            name="Ticket Panels & Setup",
            value=(
                "`createpanel` - Create new ticket panel\n"
                "`listpanels` - List all ticket panels\n"
                "`delpanel` - Delete ticket panel\n"
                "`ticketsetup` - Interactive setup wizard\n"
                "`ticketlimit` - Set user ticket limit\n"
                "`ghostping` - Toggle ghost ping"
            ),
            inline=False
        )
        
        page2.set_footer(text=f"Page 2/5 • Requested by {author.display_name}", icon_url=author.display_avatar.url)
        pages.append(page2)
        
        # Page 3: Configuration Commands & Advanced Features
        page3 = discord.Embed(
            title="Sprouts Commands",
            description=f"Use `{prefix}help <command>` for detailed info.\nThis server prefix: `{prefix}`, <@1411758556667056310>",
            color=EMBED_COLOR_NORMAL
        )
        
        # Set bot thumbnail
        if self.bot.user and self.bot.user.display_avatar:
            page3.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Configuration Commands
        page3.add_field(
            name="Configuration Commands",
            value=(
                "`setup auto` - Initial ticket system configuration\n"
                "`setup limit` - Set user ticket limit per server\n"
                "`setup transcripts` - Configure full conversation transcripts\n"
                "`setup use-threads` - Toggle threads vs channels\n"
                "`autoclose configure` - Configure automatic closure\n"
                "`autoclose exclude` - Exclude ticket from autoclose\n"
                "`addadmin` / `removeadmin` - Manage admin roles\n"
                "`addsupport` / `removesupport` - Manage staff roles"
            ),
            inline=False
        )
        
        # Advanced Features
        page3.add_field(
            name="Advanced Features",
            value=(
                "`blacklist` - Manage user blacklist system\n"
                "`viewstaff` - View all staff members\n"
                "`managetags add/delete/list` - Manage response tags\n"
                "`tickettag` - Send tag response\n"
                "`notes` - Create staff-only thread\n"
                "`on-call` - Toggle staff auto-assignment"
            ),
            inline=False
        )
        
        page3.set_footer(text=f"Page 3/5 • Requested by {author.display_name}", icon_url=author.display_avatar.url)
        pages.append(page3)
        
        # Page 4: Modern Embed Builder & Auto Responder System
        page4 = discord.Embed(
            title="Sprouts Commands",
            description=f"Use `{prefix}help <command>` for detailed info.\nThis server prefix: `{prefix}`, <@1411758556667056310>",
            color=EMBED_COLOR_NORMAL
        )
        
        # Set bot thumbnail
        if self.bot.user and self.bot.user.display_avatar:
            page4.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Embed Builder & Management
        page4.add_field(
            name="Embed Builder & Management",
            value=(
                "`embed` - Access comprehensive embed creation tools\n"
                "`embedquick` - Quick embed creation with modal\n"
                "`embedlist` - List all your saved embeds"
            ),
            inline=False
        )
        
        # Auto Responder System
        page4.add_field(
            name="Auto Responder System",
            value=(
                "`autoresponder` - Create auto responder with embed support\n"
                "`autoresponderlist` - List all server auto responders\n"
                "`autoresponderdelete` - Delete an auto responder"
            ),
            inline=False
        )
        
        page4.set_footer(text=f"Page 4/5 • Requested by {author.display_name}", icon_url=author.display_avatar.url)
        pages.append(page4)
        
        # Page 5: Sticky Messages & Reminders
        page5 = discord.Embed(
            title="Sprouts Commands",
            description=f"Use `{prefix}help <command>` for detailed info.\nThis server prefix: `{prefix}`, <@1411758556667056310>",
            color=EMBED_COLOR_NORMAL
        )
        
        # Set bot thumbnail
        if self.bot.user and self.bot.user.display_avatar:
            page5.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Sticky Messages
        page5.add_field(
            name="Sticky Messages",
            value=(
                "`stick` - Create sticky message\n"
                "`stickslow` - Create slow sticky message\n"
                "`stickstop` - Stop sticky in channel\n"
                "`stickstart` - Restart sticky in channel\n"
                "`stickremove` - Remove sticky completely\n"
                "`getstickies` - List all server stickies\n"
                "`stickspeed` - View/change sticky speed"
            ),
            inline=False
        )
        
        # Reminders
        page5.add_field(
            name="Reminders",
            value=(
                "`remind` - Set a personal reminder\n"
                "`reminders` - List your active reminders\n"
                "`delreminder` - Delete a specific reminder"
            ),
            inline=False
        )
        
        page5.set_footer(text=f"Page 5/5 • Requested by {author.display_name}", icon_url=author.display_avatar.url)
        pages.append(page5)
        
        return pages
    
    async def show_command_help(self, ctx, command_name: str, prefix: str):
        """Show extremely detailed help for a specific command with interactive buttons"""
        try:
            # Check if command is enabled via feature flags first
            if not feature_manager.is_command_enabled(command_name.lower()):
                # Silently ignore disabled commands - don't show "not found" to prevent discovery
                embed = discord.Embed(
                    title="Command Not Found", 
                    description=f"No command named `{command_name}` was found.\n"
                               f"Use `{prefix}help` to see all available commands.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
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
                               f"Use `{prefix}help` to see all available commands.",
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

class DetailedCommandHelpView(discord.ui.View):
    """Interactive view for detailed command help with buttons"""
    
    def __init__(self, command, prefix: str, author: discord.Member):
        super().__init__(timeout=300)
        self.command = command
        self.prefix = prefix
        self.author = author
        self.current_page = "main"
    
    def create_main_embed(self):
        """Create the main command help embed"""
        embed = discord.Embed(
            title=f"Command: {self.prefix}{self.command.name}",
            description=self.command.help or "Creates a new support ticket",
            color=0xCCFFD1
        )
        
        # Add usage information
        if hasattr(self.command, 'signature') and self.command.signature:
            usage = f"{self.prefix}{self.command.name} {self.command.signature}"
        else:
            usage = f"{self.prefix}{self.command.name} [reason=No reason provided]"
        
        embed.add_field(
            name="Usage",
            value=f"```\n{usage}\n```",
            inline=False
        )
        
        # Add category
        if hasattr(self.command, 'cog') and self.command.cog:
            category = self.command.cog.qualified_name
        else:
            category = "TicketSystem"
            
        embed.add_field(
            name="📁 Category",
            value=category,
            inline=False
        )
        
        # Add footer
        embed.set_footer(
            text=f"Requested by {self.author.display_name} • Use {self.prefix}help for all commands • Today at {datetime.now().strftime('%I:%M %p')}",
            icon_url=self.author.display_avatar.url
        )
        
        return embed
    
    def create_detailed_usage_embed(self):
        """Create detailed usage embed"""
        embed = discord.Embed(
            title=f"Detailed Usage - {self.prefix}{self.command.name}",
            description="Comprehensive usage examples and parameters",
            color=0xCCFFD1
        )
        
        # Command-specific examples
        if self.command.name == "new":
            embed.add_field(
                name="Basic Usage",
                value=f"```\n{self.prefix}new I need help with my account\n{self.prefix}new Bug report - login issues\n{self.prefix}new\n```",
                inline=False
            )
            embed.add_field(
                name="Parameters",
                value="**[reason]** - Optional reason for creating the ticket\n• If no reason provided, defaults to 'No reason provided'\n• Can include detailed descriptions and emojis\n• Maximum 2000 characters",
                inline=False
            )
        elif self.command.name == "close":
            embed.add_field(
                name="Basic Usage",
                value=f"```\n{self.prefix}close Issue resolved\n{self.prefix}close User helped successfully\n{self.prefix}close\n```",
                inline=False
            )
            embed.add_field(
                name="Parameters",
                value="**[reason]** - Optional reason for closing\n• Defaults to 'No reason provided'\n• Appears in transcript and logs\n• Helps staff track resolution types",
                inline=False
            )
        else:
            embed.add_field(
                name="Usage Examples",
                value=f"```\n{self.prefix}{self.command.name}\n```",
                inline=False
            )
        
        embed.set_footer(text=f"Detailed usage for {self.command.name}")
        return embed
    
    def create_common_errors_embed(self):
        """Create common errors embed"""
        embed = discord.Embed(
            title=f"Common Errors - {self.prefix}{self.command.name}",
            description="Common issues and how to resolve them",
            color=0xFFE682
        )
        
        if self.command.name == "new":
            embed.add_field(
                name="Blacklisted User",
                value="**Error:** `You are currently blacklisted from creating tickets.`\n**Solution:** Contact a server administrator for assistance.",
                inline=False
            )
            embed.add_field(
                name="Ticket Limit Reached",
                value="**Error:** `You have reached the maximum number of open tickets.`\n**Solution:** Close an existing ticket before creating a new one.",
                inline=False
            )
            embed.add_field(
                name="No Ticket Category",
                value="**Error:** `No ticket category configured.`\n**Solution:** Ask administrators to set up the ticket system first.",
                inline=False
            )
        elif self.command.name == "close":
            embed.add_field(
                name="Not a Ticket Channel",
                value="**Error:** `This command can only be used in ticket channels.`\n**Solution:** Use this command only in active ticket channels.",
                inline=False
            )
            embed.add_field(
                name="No Permission",
                value="**Error:** `Only staff members or the ticket creator can close tickets.`\n**Solution:** Ask a staff member to close the ticket for you.",
                inline=False
            )
        else:
            embed.add_field(
                name="Permission Denied",
                value="**Error:** Missing required permissions\n**Solution:** Contact an administrator",
                inline=False
            )
        
        embed.set_footer(text=f"Common errors for {self.command.name}")
        return embed
    
    @discord.ui.button(label="Detailed Usage", style=discord.ButtonStyle.primary)
    async def detailed_usage(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Only the command user can use these buttons.", ephemeral=True)
            return
        
        embed = self.create_detailed_usage_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Common Errors", style=discord.ButtonStyle.secondary)
    async def common_errors(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Only the command user can use these buttons.", ephemeral=True)
            return
        
        embed = self.create_common_errors_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Only the command user can use these buttons.", ephemeral=True)
            return
        
        await interaction.response.edit_message(view=None)
        self.stop()

async def setup_help(bot):
    """Setup help command for the bot"""
    await bot.add_cog(HelpCommand(bot))
    logger.info("Help command setup completed")

# For backwards compatibility
async def setup(bot):
    await setup_help(bot)
