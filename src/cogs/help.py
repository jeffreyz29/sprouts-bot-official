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
                    "**Existing ticket:** `You already have an open ticket: #ticket-123`",
                    "**Channel creation failed:** `Failed to create ticket channel. Contact an administrator.`",
                    "**Tickets disabled:** `Ticket system is not enabled in this server.`",
                    f"**Solution:** Ask an admin to run `{self.prefix}panel` to create ticket panels"
                ]
            },
            
            "close": {
                "category": "Ticket System",
                "description": "Close the current ticket and generate a transcript",
                "usage": f"{self.prefix}close [reason]",
                "detailed_usage": [
                    f"`{self.prefix}close` - Close ticket with no reason",
                    f"`{self.prefix}close Issue resolved` - Close with reason",
                    f"`{self.prefix}close User helped successfully` - Detailed close reason"
                ],
                "examples": [
                    f"`{self.prefix}close` - Simple ticket closure",
                    f"`{self.prefix}close Problem solved` - Close with reason",
                    f"`{self.prefix}close User was helped by support team` - Detailed reason"
                ],
                "permissions": "Ticket creator or staff",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**No permissions:** `Only ticket creator or staff can close tickets.`",
                    "**Transcript failed:** `Failed to generate transcript. Ticket still closed.`"
                ]
            },
            
            "claim": {
                "category": "Ticket System",
                "description": "Claim a ticket for yourself (Staff only)",
                "usage": f"{self.prefix}claim",
                "detailed_usage": [
                    f"`{self.prefix}claim` - Claim the current ticket"
                ],
                "examples": [
                    f"`{self.prefix}claim` - Take ownership of the ticket"
                ],
                "permissions": "Staff role required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not staff:** `Only staff can claim tickets.`",
                    "**Already claimed:** `This ticket is already claimed by another staff member.`"
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
                "permissions": "Staff role required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not staff:** `Only staff can add users to tickets.`",
                    "**User not found:** `Could not find user 'username' in this server.`",
                    "**User already in ticket:** `User is already added to this ticket.`"
                ]
            },
            
            "remove": {
                "category": "Ticket System",
                "description": "Remove a member from the current ticket (Staff only)",
                "usage": f"{self.prefix}remove <member>",
                "detailed_usage": [
                    f"`{self.prefix}remove @username` - Remove user by mention",
                    f"`{self.prefix}remove username` - Remove user by username",
                    f"`{self.prefix}remove 123456789` - Remove user by ID"
                ],
                "examples": [
                    f"`{self.prefix}remove @John` - Remove John from ticket",
                    f"`{self.prefix}remove Support Team` - Remove by username",
                    f"`{self.prefix}remove 351738977602887681` - Remove by user ID"
                ],
                "permissions": "Staff role required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not staff:** `Only staff can remove users from tickets.`",
                    "**User not found:** `Could not find user 'username' in this server.`",
                    "**User not in ticket:** `User is not in this ticket.`"
                ]
            },
            
            "rename": {
                "category": "Ticket System",
                "description": "Rename the current ticket channel (Staff only)",
                "usage": f"{self.prefix}rename <new_name>",
                "detailed_usage": [
                    f"`{self.prefix}rename billing issue` - Rename to ticket-billing-issue",
                    f"`{self.prefix}rename bug report` - Rename to ticket-bug-report"
                ],
                "examples": [
                    f"`{self.prefix}rename account help` - Rename to ticket-account-help",
                    f"`{self.prefix}rename discord bot issue` - Rename to ticket-discord-bot-issue"
                ],
                "permissions": "Staff role required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not staff:** `Only staff can rename tickets.`",
                    "**No name:** `Please provide a new name for the ticket.`"
                ]
            },
            
            "topic": {
                "category": "Ticket System",
                "description": "Set the topic/description for the current ticket",
                "usage": f"{self.prefix}topic <new_topic>",
                "detailed_usage": [
                    f"`{self.prefix}topic User needs help with billing` - Set ticket topic",
                    f"`{self.prefix}topic Bug report: Commands not working` - Bug topic"
                ],
                "examples": [
                    f"`{self.prefix}topic Account access issue` - Set topic",
                    f"`{self.prefix}topic Discord permissions help needed` - Detailed topic"
                ],
                "permissions": "Ticket participants",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**No topic:** `Please provide a topic for the ticket.`"
                ]
            },
            
            
            "move": {
                "category": "Ticket System",
                "description": "Move the ticket to a different category using category ID (Staff only)",
                "usage": f"{self.prefix}move <category_id>",
                "detailed_usage": [
                    f"`{self.prefix}move 123456789012345678` - Move ticket to category with specified ID",
                    f"Right-click category → Copy ID to get category ID (requires Developer Mode)"
                ],
                "examples": [
                    f"`{self.prefix}move 987654321098765432` - Move ticket to category ID 987654321098765432",
                    f"`{self.prefix}move 123456789012345678` - Move ticket using specific category ID"
                ],
                "permissions": "Staff role required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not staff:** `Only staff can move tickets.`",
                    "**Category not found:** `Could not find category: 'category_name'`"
                ]
            },
            
            "transfer": {
                "category": "Ticket System",
                "description": "Transfer ticket ownership to another user",
                "usage": f"{self.prefix}transfer <user>",
                "detailed_usage": [
                    f"`{self.prefix}transfer @newowner` - Transfer to mentioned user",
                    f"`{self.prefix}transfer username` - Transfer by username"
                ],
                "examples": [
                    f"`{self.prefix}transfer @John` - Transfer ticket to John",
                    f"`{self.prefix}transfer Support Lead` - Transfer to support lead"
                ],
                "permissions": "Ticket creator or staff",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**No permissions:** `Only ticket creator or staff can transfer tickets.`",
                    "**User not found:** `Could not find user in this server.`"
                ]
            },
            
            "release": {
                "category": "Ticket System",
                "description": "Release (unclaim) the current ticket",
                "usage": f"{self.prefix}release",
                "detailed_usage": [
                    f"`{self.prefix}release` - Release ticket claim",
                    f"`{self.prefix}unclaim` - Same as release (alias)"
                ],
                "examples": [
                    f"`{self.prefix}release` - Release the ticket for other staff",
                    f"`{self.prefix}unclaim` - Unclaim the ticket"
                ],
                "permissions": "Claimer or staff",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not claimed:** `This ticket is not currently claimed.`",
                    "**No permissions:** `Only the claimer or staff can release tickets.`"
                ]
            },
            
            "forceclose": {
                "category": "Ticket System",
                "description": "Force close a ticket (Administrator only)",
                "usage": f"{self.prefix}forceclose [reason]",
                "detailed_usage": [
                    f"`{self.prefix}forceclose` - Force close with no reason",
                    f"`{self.prefix}forceclose Spam ticket` - Force close with reason",
                    f"`{self.prefix}force-close User violation` - Using alias"
                ],
                "examples": [
                    f"`{self.prefix}forceclose` - Emergency ticket closure",
                    f"`{self.prefix}forceclose Duplicate ticket` - Close duplicate",
                    f"`{self.prefix}force-close Policy violation` - Policy violation closure"
                ],
                "permissions": "Administrator only",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not admin:** `Only administrators can force close tickets.`"
                ]
            },
            
            "createpanel": {
                "category": "Ticket System",
                "description": "Create a ticket panel with interactive button (Staff only)",
                "usage": f"`{self.prefix}createpanel [title]`",
                "detailed_usage": [
                    f"`{self.prefix}createpanel` - Create panel with default title 'Support Tickets'",
                    f"`{self.prefix}createpanel Bug Reports` - Create panel with custom title",
                    f"`{self.prefix}createpanel General Support` - Panel for general support tickets"
                ],
                "examples": [
                    f"`{self.prefix}createpanel` - Default support ticket panel",
                    f"`{self.prefix}createpanel Technical Support` - Technical support panel",
                    f"`{self.prefix}createpanel Billing Questions` - Billing support panel"
                ],
                "permissions": "Staff role required + Manage Channels permission",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not staff:** `Only staff members can create ticket panels.`",
                    "**No permissions:** `Missing Manage Channels permission.`",
                    "**Error creating:** `An error occurred while creating the panel.`"
                ]
            },
            
            "listpanels": {
                "category": "Ticket System", 
                "description": "List all active ticket panels in the server (Staff only)",
                "usage": f"`{self.prefix}listpanels`",
                "detailed_usage": [
                    f"`{self.prefix}listpanels` - Show all active panels with details",
                    f"Shows panel ID, title, channel, creator, and creation date",
                    f"Automatically cleans up panels with deleted messages"
                ],
                "examples": [
                    f"`{self.prefix}listpanels` - View all server panels",
                    f"Panel cleanup happens automatically during listing"
                ],
                "permissions": "Staff role required + Manage Channels permission",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not staff:** `Only staff members can list ticket panels.`",
                    "**No panels:** `No active ticket panels found in this server.`",
                    "**No permissions:** `Missing Manage Channels permission.`"
                ]
            },
            
            "delpanel": {
                "category": "Ticket System",
                "description": "Delete a ticket panel by ID (Staff only)",
                "usage": f"`{self.prefix}delpanel <panel_id>`",
                "detailed_usage": [
                    f"`{self.prefix}delpanel ABC12345` - Delete panel with ID ABC12345",
                    f"Use `{self.prefix}listpanels` to find panel IDs",
                    f"Deletes both the panel message and database entry"
                ],
                "examples": [
                    f"`{self.prefix}delpanel XYZ98765` - Delete specific panel",
                    f"`{self.prefix}delpanel DEF456AB` - Remove outdated panel"
                ],
                "permissions": "Staff role required + Manage Channels permission",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not staff:** `Only staff members can delete ticket panels.`",
                    "**Panel not found:** `No panel found with ID: 'panel_id'`",
                    "**Wrong server:** `You can only delete panels from this server.`",
                    "**No permissions:** `Missing Manage Channels permission.`"
                ]
            },

            "transcript": {
                "category": "Ticket System",
                "description": "Generate a transcript of the current ticket",
                "usage": f"{self.prefix}transcript",
                "detailed_usage": [
                    f"`{self.prefix}transcript` - Generate and view transcript"
                ],
                "examples": [
                    f"`{self.prefix}transcript` - Create transcript with viewing URL"
                ],
                "permissions": "Ticket participants",
                "cooldown": "30 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Generation failed:** `Failed to generate transcript. Please try again.`"
                ]
            },
            
            "tickets": {
                "category": "Ticket System",
                "description": "List all open tickets in the server (Staff only)",
                "usage": f"{self.prefix}tickets",
                "detailed_usage": [
                    f"`{self.prefix}tickets` - List all open tickets",
                    f"`{self.prefix}list` - Same as tickets (alias)"
                ],
                "examples": [
                    f"`{self.prefix}tickets` - View all open tickets with details",
                    f"`{self.prefix}list` - List tickets with creators and status"
                ],
                "permissions": "Staff role required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**Not staff:** `Only staff can view the ticket list.`",
                    "**No tickets:** `There are currently no open tickets in this server.`"
                ]
            },
            
            
            "notes": {
                "category": "Ticket System",
                "description": "Create a private staff notes thread for the ticket",
                "usage": f"{self.prefix}notes",
                "detailed_usage": [
                    f"`{self.prefix}notes` - Create private staff thread"
                ],
                "examples": [
                    f"`{self.prefix}notes` - Create notes thread for internal discussion"
                ],
                "permissions": "Staff role required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not staff:** `Only staff can create notes threads.`",
                    "**Thread exists:** `A notes thread already exists for this ticket.`"
                ]
            },

            # NEW TICKETSBOT COMMANDS - Complete documentation for all 33 commands
            
            "open": {
                "category": "Ticket System", 
                "description": "Alternative command to create a new support ticket (alias for 'new')",
                "usage": f"`{self.prefix}open [subject]`",
                "detailed_usage": [
                    f"`{self.prefix}open` - Creates ticket with no subject",
                    f"`{self.prefix}open I need help with billing` - Creates ticket with subject",
                    f"`{self.prefix}open Bug report: Bot not responding` - Detailed subject"
                ],
                "examples": [
                    f"`{self.prefix}open` - Creates a simple support ticket",
                    f"`{self.prefix}open Can't access my account` - Ticket with specific issue", 
                    f"`{self.prefix}open Payment processing error` - Payment issue ticket",
                    f"`{self.prefix}open Discord bot permissions help` - Permission help ticket"
                ],
                "permissions": "None required",
                "cooldown": "30 seconds per user",
                "error_scenarios": [
                    "**Existing ticket:** `You already have an open ticket: #ticket-123`",
                    "**Channel creation failed:** `Failed to create ticket channel. Contact an administrator.`",
                    "**Tickets disabled:** `Ticket system is not enabled in this server.`",
                    f"**Solution:** Ask an admin to run `{self.prefix}panel` to create ticket panels",
                    "**Rate limited:** `Please wait 30 seconds before creating another ticket.`"
                ]
            },
            
            "unclaim": {
                "category": "Ticket System",
                "description": "Remove your claim from the current ticket, making it available for other staff",
                "usage": f"`{self.prefix}unclaim`",
                "detailed_usage": [
                    f"`{self.prefix}unclaim` - Remove your claim from ticket"
                ],
                "examples": [
                    f"`{self.prefix}unclaim` - Release ticket for other staff to handle",
                    "After unclaiming, other staff can claim this ticket"
                ],
                "permissions": "Staff role required (must be the claimer)",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not claimed:** `This ticket is not currently claimed.`",
                    "**Not your claim:** `You can only unclaim tickets you have claimed.`",
                    "**Not staff:** `Only staff members can unclaim tickets.`"
                ]
            },
            
            "closerequest": {
                "category": "Ticket System",
                "description": "Send a close request to the ticket opener for approval",
                "usage": f"`{self.prefix}closerequest [reason]`",
                "detailed_usage": [
                    f"`{self.prefix}closerequest` - Send close request with no reason",
                    f"`{self.prefix}closerequest Issue resolved` - Send close request with reason",
                    f"`{self.prefix}closerequest User helped successfully` - Detailed close reason"
                ],
                "examples": [
                    f"`{self.prefix}closerequest` - Send basic close request to user",
                    f"`{self.prefix}closerequest Problem solved` - Request closure with reason",
                    f"`{self.prefix}closerequest All questions answered` - Detailed closure request"
                ],
                "permissions": "Staff role required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not staff:** `Only staff can send close requests.`",
                    "**User offline:** `Ticket opener is not available. Use regular close instead.`",
                    "**Already requested:** `A close request is already pending for this ticket.`"
                ]
            },
            
            "jumptotop": {
                "category": "Ticket System",
                "description": "Display a button that users can click to jump to the top of the ticket",
                "usage": f"`{self.prefix}jumptotop`",
                "detailed_usage": [
                    f"`{self.prefix}jumptotop` - Shows jump to top button for easy navigation"
                ],
                "examples": [
                    f"`{self.prefix}jumptotop` - Helpful for long tickets with lots of messages",
                    "Users can click the button to quickly scroll to the ticket beginning"
                ],
                "permissions": "Ticket participants",
                "cooldown": "30 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Button limit:** `Too many buttons in this channel. Try again later.`"
                ]
            },
            
            "reopen": {
                "category": "Ticket System",
                "description": "Reopen a previously closed ticket by ID",
                "usage": f"`{self.prefix}reopen <ticket_id>`",
                "detailed_usage": [
                    f"`{self.prefix}reopen 123` - Reopen ticket with ID 123",
                    f"`{self.prefix}reopen ticket-456` - Reopen using full ticket name"
                ],
                "examples": [
                    f"`{self.prefix}reopen 123` - Reopen closed ticket #123",
                    f"`{self.prefix}reopen 456` - Restore previously closed ticket",
                    "Reopened tickets restore all previous messages and permissions"
                ],
                "permissions": "Staff role required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**Ticket not found:** `Could not find a closed ticket with ID: 123`",
                    "**Not staff:** `Only staff can reopen closed tickets.`",
                    "**Already open:** `Ticket 123 is already open.`",
                    "**Channel exists:** `Cannot reopen - a channel with this name already exists.`"
                ]
            },
            
            "switchpanel": {
                "category": "Ticket System",
                "description": "Switch the current ticket to a different panel configuration",
                "usage": f"`{self.prefix}switchpanel <panel_name>`",
                "detailed_usage": [
                    f"`{self.prefix}switchpanel Support` - Switch to Support panel config",
                    f"`{self.prefix}switchpanel Bug Reports` - Switch to Bug Reports panel"
                ],
                "examples": [
                    f"`{self.prefix}switchpanel General Support` - Move to general support panel",
                    f"`{self.prefix}switchpanel VIP Support` - Move to VIP support panel",
                    f"`{self.prefix}switchpanel Technical` - Move to technical support panel"
                ],
                "permissions": "Staff role required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `This command can only be used in ticket channels.`",
                    "**Not staff:** `Only staff can switch ticket panels.`",
                    "**Panel not found:** `Could not find panel: 'panel_name'`",
                    "**Same panel:** `Ticket is already using this panel configuration.`"
                ]
            },
            
            # SETTING COMMANDS (15 commands)
            
            "addadmin": {
                "category": "Ticket Settings",
                "description": "Grant admin privileges to a user or role for the ticket system",
                "usage": f"`{self.prefix}addadmin <user/role>`",
                "detailed_usage": [
                    f"`{self.prefix}addadmin @Admin` - Add admin role to ticket system",
                    f"`{self.prefix}addadmin @JohnDoe` - Add user as ticket admin",
                    f"`{self.prefix}addadmin 123456789` - Add user by ID as admin"
                ],
                "examples": [
                    f"`{self.prefix}addadmin @Moderator` - Give Moderator role admin access",
                    f"`{self.prefix}addadmin @Manager` - Give Manager role admin privileges",
                    f"`{self.prefix}addadmin @Alice` - Give user Alice admin access"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can manage ticket admins.`",
                    "**Missing target:** `Please specify a user or role to add as admin.`",
                    "**User/role not found:** `Could not find that user or role in this server.`",
                    "**Already admin:** `This user/role already has admin privileges.`"
                ]
            },
            
            "removeadmin": {
                "category": "Ticket Settings",
                "description": "Revoke admin privileges from a user or role for the ticket system",
                "usage": f"`{self.prefix}removeadmin <user/role>`",
                "detailed_usage": [
                    f"`{self.prefix}removeadmin @Admin` - Remove admin role from ticket system",
                    f"`{self.prefix}removeadmin @JohnDoe` - Remove user's admin privileges",
                    f"`{self.prefix}removeadmin 123456789` - Remove admin by user ID"
                ],
                "examples": [
                    f"`{self.prefix}removeadmin @OldModerator` - Remove admin access from old mod",
                    f"`{self.prefix}removeadmin @FormerManager` - Revoke manager's admin access",
                    f"`{self.prefix}removeadmin @Bob` - Remove Bob's admin privileges"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can manage ticket admins.`",
                    "**Missing target:** `Please specify a user or role to remove as admin.`",
                    "**User/role not found:** `Could not find that user or role in this server.`",
                    "**Not admin:** `This user/role doesn't have admin privileges.`"
                ]
            },
            
            "addsupport": {
                "category": "Ticket Settings",
                "description": "Add support staff privileges to a user or role for the ticket system",
                "usage": f"`{self.prefix}addsupport <user/role>`",
                "detailed_usage": [
                    f"`{self.prefix}addsupport @Support` - Add support role to ticket system",
                    f"`{self.prefix}addsupport @JaneDoe` - Add user as support staff",
                    f"`{self.prefix}addsupport 987654321` - Add support staff by user ID"
                ],
                "examples": [
                    f"`{self.prefix}addsupport @Helper` - Give Helper role support access",
                    f"`{self.prefix}addsupport @Agent` - Give Agent role support privileges",
                    f"`{self.prefix}addsupport @Charlie` - Give Charlie support access"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can manage support staff.`",
                    "**Missing target:** `Please specify a user or role to add as support.`",
                    "**User/role not found:** `Could not find that user or role in this server.`",
                    "**Already support:** `This user/role already has support privileges.`"
                ]
            },
            
            "removesupport": {
                "category": "Ticket Settings",
                "description": "Remove support staff privileges from a user or role for the ticket system",
                "usage": f"`{self.prefix}removesupport <user/role>`",
                "detailed_usage": [
                    f"`{self.prefix}removesupport @Support` - Remove support role from ticket system",
                    f"`{self.prefix}removesupport @JaneDoe` - Remove user's support privileges",
                    f"`{self.prefix}removesupport 987654321` - Remove support by user ID"
                ],
                "examples": [
                    f"`{self.prefix}removesupport @OldHelper` - Remove support access from old helper",
                    f"`{self.prefix}removesupport @FormerAgent` - Revoke agent's support access",
                    f"`{self.prefix}removesupport @David` - Remove David's support privileges"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can manage support staff.`",
                    "**Missing target:** `Please specify a user or role to remove as support.`",
                    "**User/role not found:** `Could not find that user or role in this server.`",
                    "**Not support:** `This user/role doesn't have support privileges.`"
                ]
            },
            
            "blacklist": {
                "category": "Ticket Settings",
                "description": "Toggle blacklist status for a user or role in the ticket system",
                "usage": f"`{self.prefix}blacklist <user/role>`",
                "detailed_usage": [
                    f"`{self.prefix}blacklist @BadUser` - Toggle blacklist for user",
                    f"`{self.prefix}blacklist @SpamRole` - Toggle blacklist for role",
                    f"`{self.prefix}blacklist 111222333` - Toggle blacklist by user ID"
                ],
                "examples": [
                    f"`{self.prefix}blacklist @Spammer` - Prevent Spammer from creating tickets",
                    f"`{self.prefix}blacklist @Troll` - Block Troll from ticket system",
                    f"`{self.prefix}blacklist @GoodUser` - Unblacklist previously blocked user"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can manage the blacklist.`",
                    "**Missing target:** `Please specify a user or role to blacklist/unblacklist.`",
                    "**User/role not found:** `Could not find that user or role in this server.`",
                    "**Cannot blacklist staff:** `Cannot blacklist users with admin or support privileges.`"
                ]
            },
            
            "viewstaff": {
                "category": "Ticket Settings",
                "description": "Display all current ticket admins and support staff",
                "usage": f"`{self.prefix}viewstaff`",
                "detailed_usage": [
                    f"`{self.prefix}viewstaff` - Shows complete staff list with roles and users"
                ],
                "examples": [
                    f"`{self.prefix}viewstaff` - View all ticket admins and support staff",
                    "Shows organized list of all roles and users with ticket permissions"
                ],
                "permissions": "Staff role required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Not staff:** `Only staff can view the staff list.`",
                    "**No staff configured:** `No staff roles or users have been configured yet.`"
                ]
            },
            
            "panel": {
                "category": "Ticket Settings",
                "description": "Display setup guide for creating ticket panels with buttons",
                "usage": f"`{self.prefix}panel`",
                "detailed_usage": [
                    f"`{self.prefix}panel` - Shows complete panel creation guide"
                ],
                "examples": [
                    f"`{self.prefix}panel` - Learn how to create ticket panel with buttons",
                    "Provides step-by-step instructions for setting up ticket panels"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can access panel setup.`",
                    "**Embed builder missing:** `Embed builder system is required for panels.`"
                ]
            },
            
            "setup": {
                "category": "Ticket Settings",
                "description": "Show available ticket system setup options",
                "usage": f"`{self.prefix}setup`",
                "detailed_usage": [
                    f"`{self.prefix}setup` - Show all setup options",
                    f"`{self.prefix}setup limit <number>` - Set user ticket limit",
                    f"`{self.prefix}setup transcripts <channel>` - Set transcript channel",
                    f"`{self.prefix}setup use-threads` - Toggle thread vs channel mode"
                ],
                "examples": [
                    f"`{self.prefix}setup` - View all available setup commands",
                    f"`{self.prefix}setup limit 3` - Limit users to 3 tickets each",
                    f"`{self.prefix}setup transcripts #logs` - Send transcripts to #logs",
                    f"`{self.prefix}setup use-threads` - Switch between threads and channels"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can access setup options.`",
                    "**Invalid limit:** `Ticket limit must be between 1 and 10.`",
                    "**Channel not found:** `Could not find the specified transcript channel.`"
                ]
            },
            
            "autoclose": {
                "category": "Ticket Settings", 
                "description": "Configure automatic ticket closing settings",
                "usage": f"`{self.prefix}autoclose`",
                "detailed_usage": [
                    f"`{self.prefix}autoclose` - Show autoclose options menu",
                    f"`{self.prefix}autoclose configure` - Edit autoclose settings",
                    f"`{self.prefix}autoclose exclude` - Exclude current ticket from autoclose"
                ],
                "examples": [
                    f"`{self.prefix}autoclose` - View current autoclose configuration",
                    f"`{self.prefix}autoclose configure` - Set inactive timeout periods",
                    f"`{self.prefix}autoclose exclude` - Prevent this ticket from auto-closing"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can configure autoclose.`",
                    "**Not in ticket:** `Exclude command can only be used in ticket channels.`",
                    "**Invalid timeout:** `Autoclose timeout must be between 1 hour and 30 days.`"
                ]
            },
            
            # TAG COMMANDS (4 commands)
            
            "managetags": {
                "category": "Ticket Tags",
                "description": "Manage ticket tags for quick responses",
                "usage": f"`{self.prefix}managetags`",
                "detailed_usage": [
                    f"`{self.prefix}managetags` - Show tag management options",
                    f"`{self.prefix}managetags add <id> <content>` - Create new tag",
                    f"`{self.prefix}managetags delete <id>` - Delete existing tag",
                    f"`{self.prefix}managetags list` - List all available tags"
                ],
                "examples": [
                    f"`{self.prefix}managetags` - Open tag management menu",
                    f"`{self.prefix}managetags add welcome Welcome to our support!` - Create welcome tag",
                    f"`{self.prefix}managetags delete old-tag` - Remove unwanted tag",
                    f"`{self.prefix}managetags list` - See all configured tags"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can manage tags.`",
                    "**Tag exists:** `A tag with that ID already exists.`",
                    "**Tag not found:** `Could not find tag with ID: 'tag-id'`",
                    "**Content too long:** `Tag content must be 2000 characters or less.`"
                ]
            },
            
            "tag": {
                "category": "Ticket Tags",
                "description": "Send a predefined tag message in the current ticket",
                "usage": f"`{self.prefix}tag <tag_id>`",
                "detailed_usage": [
                    f"`{self.prefix}tag welcome` - Send welcome tag message",
                    f"`{self.prefix}tag rules` - Send server rules tag",
                    f"`{self.prefix}tag closing` - Send ticket closing tag"
                ],
                "examples": [
                    f"`{self.prefix}tag welcome` - Send welcome message to ticket opener",
                    f"`{self.prefix}tag faq` - Send frequently asked questions",
                    f"`{self.prefix}tag escalate` - Send escalation information"
                ],
                "permissions": "Staff role required",
                "cooldown": "3 seconds per user",
                "error_scenarios": [
                    "**Not in ticket:** `Tags can only be used in ticket channels.`",
                    "**Not staff:** `Only staff can use tags.`",
                    "**Tag not found:** `Could not find tag: 'tag-id'`",
                    f"**No tags:** `No tags configured. Use {self.prefix}managetags to create tags.`"
                ]
            },
            
            # STAFF MANAGEMENT COMMAND
            
            "staff": {
                "category": "Ticket Settings",
                "description": "Open modern staff management interface with select menus",
                "usage": f"`{self.prefix}staff`",
                "detailed_usage": [
                    f"`{self.prefix}staff` - Open interactive staff management menu"
                ],
                "examples": [
                    f"`{self.prefix}staff` - Manage admins, support staff, and blacklist",
                    "Use dropdown menus to add/remove staff and manage permissions"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can access staff management.`",
                    "**Menu error:** `Failed to load staff management interface.`"
                ]
            },
            
            # CORE BOT COMMANDS
            
            "about": {
                "category": "Bot Information",
                "description": "Display comprehensive bot statistics, uptime, and system information",
                "usage": f"`{self.prefix}about`",
                "detailed_usage": [
                    f"`{self.prefix}about` - Shows bot uptime, server count, memory usage, and system specs"
                ],
                "examples": [
                    f"`{self.prefix}about` - View complete bot statistics and performance metrics",
                    "Shows uptime, server/user counts, memory usage, Python version, and OS info"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works",
                    "Shows bot performance metrics and system resource usage"
                ]
            },
            
            "invite": {
                "category": "Bot Information",
                "description": "Get bot invite link with proper permissions and support server information",
                "usage": f"`{self.prefix}invite`",
                "detailed_usage": [
                    f"`{self.prefix}invite` - Provides bot invite link with pre-configured permissions"
                ],
                "examples": [
                    f"`{self.prefix}invite` - Add bot to your server with full functionality",
                    "Includes invite link, support server, and feature highlights"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works",
                    "Provides all necessary links and permission information"
                ]
            },
            
            "shards": {
                "category": "Bot Information",
                "description": "Display bot shard information and server distribution with pagination",
                "usage": f"`{self.prefix}shards`",
                "detailed_usage": [
                    f"`{self.prefix}shards` - Shows shard info and paginated server list with navigation"
                ],
                "examples": [
                    f"`{self.prefix}shards` - View bot's shard info and browse connected servers",
                    "Interactive pagination to explore all servers bot is connected to"
                ],
                "permissions": "None required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works",
                    "Shows current shard, total shards, and server distribution"
                ]
            },
            
            "vote": {
                "category": "Bot Information",
                "description": "Get voting links to support the bot on listing platforms",
                "usage": f"`{self.prefix}vote`",
                "detailed_usage": [
                    f"`{self.prefix}vote` - Provides voting links for Top.gg and other bot lists"
                ],
                "examples": [
                    f"`{self.prefix}vote` - Support bot development by voting every 12 hours",
                    "Shows voting platforms, current stats, and voting benefits"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works",
                    "Displays current bot statistics and voting information"
                ]
            },
            
            # UTILITY COMMANDS
            
            "serverinfo": {
                "category": "Server Utilities",
                "description": "Display comprehensive server information and statistics",
                "usage": f"`{self.prefix}serverinfo`",
                "detailed_usage": [
                    f"`{self.prefix}serverinfo` - Shows detailed server statistics and information"
                ],
                "examples": [
                    f"`{self.prefix}serverinfo` - View server member count, creation date, boost level",
                    "Shows verification level, features, roles, channels, and server owner"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**DM only:** `This command can only be used in servers, not DMs.`",
                    "**Server unavailable:** `Could not fetch server information.`"
                ]
            },
            
            "channelinfo": {
                "category": "Server Utilities",
                "description": "Get detailed information about a Discord channel",
                "usage": f"`{self.prefix}channelinfo [#channel]`",
                "detailed_usage": [
                    f"`{self.prefix}channelinfo` - Shows current channel information",
                    f"`{self.prefix}channelinfo #general` - Shows info for specific channel"
                ],
                "examples": [
                    f"`{self.prefix}channelinfo` - View current channel details",
                    f"`{self.prefix}channelinfo #announcements` - Get announcements channel info"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Channel not found:** `Could not find the specified channel.`",
                    "**No access:** `You don't have permission to view that channel.`"
                ]
            },
            
            "roleinfo": {
                "category": "Server Utilities",
                "description": "Display detailed information about a server role",
                "usage": f"`{self.prefix}roleinfo <@role or role name>`",
                "detailed_usage": [
                    f"`{self.prefix}roleinfo @Moderator` - Shows role info by mention",
                    f"`{self.prefix}roleinfo Moderator` - Shows role info by name"
                ],
                "examples": [
                    f"`{self.prefix}roleinfo @Admin` - View Admin role permissions and details",
                    f"`{self.prefix}roleinfo Member` - Get Member role information"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Role not found:** `Could not find role: 'role-name'`",
                    "**Missing role:** `Please specify a role to get information about.`"
                ]
            },
            
            "inviteinfo": {
                "category": "Server Utilities",
                "description": "Get information about a Discord invite link",
                "usage": f"`{self.prefix}inviteinfo <invite_code>`",
                "detailed_usage": [
                    f"`{self.prefix}inviteinfo discord.gg/abc123` - Analyze full invite link",
                    f"`{self.prefix}inviteinfo abc123` - Analyze just the invite code"
                ],
                "examples": [
                    f"`{self.prefix}inviteinfo discord.gg/example` - Get invite details",
                    f"`{self.prefix}inviteinfo abc123def` - Check invite validity and server info"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Invalid invite:** `The provided invite link is invalid or expired.`",
                    "**Missing invite:** `Please provide an invite link or code to analyze.`"
                ]
            },
            
            "prefix": {
                "category": "Server Management",
                "description": "Display the current command prefix for this server",
                "usage": f"`{self.prefix}prefix`",
                "detailed_usage": [
                    f"`{self.prefix}prefix` - Shows current server prefix and mention option"
                ],
                "examples": [
                    f"`{self.prefix}prefix` - Check what prefix is currently set",
                    "Also shows if bot mention is enabled as a prefix alternative"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works",
                    "Shows current prefix and bot mention availability"
                ]
            },
            
            "variables": {
                "category": "Utilities",
                "description": "Display all available variables for embeds, autoresponders, and messages",
                "usage": f"`{self.prefix}variables`",
                "detailed_usage": [
                    f"`{self.prefix}variables` - Shows complete variable reference with 40+ variables"
                ],
                "examples": [
                    f"`{self.prefix}variables` - View all user, server, channel, date/time variables",
                    "Variables use $(variable.name) syntax for embeds and auto-responses"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No errors possible** - This command always works",
                    "Shows comprehensive variable reference for customization"
                ]
            },
            
            # AUTORESPONDER COMMANDS
            
            "autoresponder": {
                "category": "Auto Responders",
                "description": "Advanced autoresponder system with comprehensive features and multiple match modes",
                "usage": f"`{self.prefix}autoresponder <add/list/show/remove/editreply/editmatchmode/showraw>`",
                "detailed_usage": [
                    f"`{self.prefix}autoresponder add` - Create new autoresponder with interactive modal setup",
                    f"`{self.prefix}autoresponder list` - View all configured autoresponders with status",
                    f"`{self.prefix}autoresponder show <id>` - Show detailed information about specific autoresponder",
                    f"`{self.prefix}autoresponder remove <id>` - Delete an autoresponder by ID",
                    f"`{self.prefix}autoresponder editreply <id>` - Edit response message using modal",
                    f"`{self.prefix}autoresponder editmatchmode <id>` - Change trigger match mode",
                    f"`{self.prefix}autoresponder showraw <id>` - Display raw response text",
                    f"`{self.prefix}reset server autoresponders` - Reset all server autoresponders"
                ],
                "examples": [
                    f"`{self.prefix}autoresponder add` - Create autoresponder with modal for trigger/response",
                    f"`{self.prefix}autoresponder list` - See all autoresponders with IDs and status",
                    f"`{self.prefix}autoresponder show ar1` - View complete details for autoresponder ID 'ar1'",
                    f"`{self.prefix}autoresponder remove ar1` - Delete autoresponder with ID 'ar1'",
                    f"`{self.prefix}autoresponder editreply ar1` - Edit response for autoresponder 'ar1'",
                    f"`{self.prefix}autoresponder editmatchmode ar1` - Change match mode (exact/contains/startswith/endswith/regex)"
                ],
                "permissions": "Administrator permission required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `You need Administrator permission to manage autoresponders.`",
                    "**Invalid ID:** `Autoresponder ID 'ar1' not found!`",
                    "**No autoresponders:** `This server has no autoresponders configured.`",
                    "**Match modes:** Available modes: exact, contains, startswith, endswith, regex"
                ]
            },
            
            # REMINDER COMMANDS
            
            "remind": {
                "category": "Reminders",
                "description": "Set a personal reminder with flexible time parsing",
                "usage": f"`{self.prefix}remind <time> <message>`",
                "detailed_usage": [
                    f"`{self.prefix}remind 1h Take a break` - Reminder in 1 hour",
                    f"`{self.prefix}remind 30m Check the oven` - Reminder in 30 minutes",
                    f"`{self.prefix}remind 2d Call mom` - Reminder in 2 days",
                    f"`{self.prefix}remind 1w Meeting prep` - Reminder in 1 week"
                ],
                "examples": [
                    f"`{self.prefix}remind 15m Meeting starts` - 15 minute reminder",
                    f"`{self.prefix}remind 2h Lunch break` - 2 hour reminder",
                    f"`{self.prefix}remind 1d Submit assignment` - Daily reminder",
                    f"`{self.prefix}remind 3w Vacation planning` - Weekly reminder"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Invalid time:** `Please use format like: 1h, 30m, 2d, 1w`",
                    "**Missing message:** `Please provide a reminder message.`",
                    "**Time too long:** `Reminders can't be set for more than 30 days.`",
                    "**Time too short:** `Reminders must be at least 1 minute in the future.`"
                ]
            },
            
            "reminders": {
                "category": "Reminders",
                "description": "List all your active reminders with details",
                "usage": f"`{self.prefix}reminders`",
                "detailed_usage": [
                    f"`{self.prefix}reminders` - Shows all your active reminders with IDs and times"
                ],
                "examples": [
                    f"`{self.prefix}reminders` - View all pending reminders",
                    "Shows reminder ID, message, and time remaining for each reminder"
                ],
                "permissions": "None required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No reminders:** `You don't have any active reminders.`",
                    f"**Create reminder:** `Use {self.prefix}remind <time> <message> to create one.`"
                ]
            },
            
            "delreminder": {
                "category": "Reminders",
                "description": "Delete a specific reminder by ID",
                "usage": f"`{self.prefix}delreminder <reminder_id>`",
                "detailed_usage": [
                    f"`{self.prefix}delreminder 1` - Delete reminder with ID 1",
                    f"`{self.prefix}delreminder 5` - Delete reminder with ID 5"
                ],
                "examples": [
                    f"`{self.prefix}delreminder 2` - Remove reminder ID 2",
                    f"Use `{self.prefix}reminders` first to see your reminder IDs"
                ],
                "permissions": "None required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Invalid ID:** `Could not find reminder with ID: 123`",
                    "**Not your reminder:** `You can only delete your own reminders.`",
                    "**Missing ID:** `Please provide a reminder ID to delete.`"
                ]
            },
            
            # STICKY MESSAGE COMMANDS
            
            "stick": {
                "category": "Sticky Messages",
                "description": "Create a sticky message that auto-reposts when new messages are sent",
                "usage": f"`{self.prefix}stick <message or embed_name>`",
                "detailed_usage": [
                    f"`{self.prefix}stick Welcome to our server!` - Create text sticky message",
                    f"`{self.prefix}stick RulesEmbed` - Create sticky from saved embed"
                ],
                "examples": [
                    f"`{self.prefix}stick Please follow the rules` - Text sticky message",
                    f"`{self.prefix}stick WelcomeEmbed` - Use saved embed as sticky",
                    f"`{self.prefix}stick Join our Discord for updates` - Info sticky"
                ],
                "permissions": "Manage Messages permission required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `You need Manage Messages permission.`",
                    "**Already exists:** `A sticky message already exists in this channel.`",
                    "**Message too long:** `Sticky message must be 2000 characters or less.`",
                    "**Embed not found:** `Could not find saved embed: 'embed-name'`"
                ]
            },
            
            "stickslow": {
                "category": "Sticky Messages",
                "description": "Create a slow sticky message with less frequent updates",
                "usage": f"`{self.prefix}stickslow <message or embed_name>`",
                "detailed_usage": [
                    f"`{self.prefix}stickslow Welcome message` - Create slow sticky text",
                    f"`{self.prefix}stickslow EmbedName` - Create slow sticky from embed"
                ],
                "examples": [
                    f"`{self.prefix}stickslow Please follow the rules` - Slow text sticky",
                    f"`{self.prefix}stickslow RulesEmbed` - Slow sticky from saved embed",
                    f"`{self.prefix}stickslow Join our Discord` - Low-frequency info sticky"
                ],
                "permissions": "Manage Messages permission required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `You need Manage Messages permission.`",
                    "**Already exists:** `A sticky message already exists in this channel.`",
                    "**Message too long:** `Sticky message must be 2000 characters or less.`"
                ]
            },
            
            "stickstop": {
                "category": "Sticky Messages",
                "description": "Stop the sticky message in the current channel",
                "usage": f"`{self.prefix}stickstop`",
                "detailed_usage": [
                    f"`{self.prefix}stickstop` - Pause sticky message without deleting it"
                ],
                "examples": [
                    f"`{self.prefix}stickstop` - Temporarily pause sticky message",
                    f"Use {self.prefix}stickstart to resume it later"
                ],
                "permissions": "Manage Messages permission required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `You need Manage Messages permission.`",
                    "**No sticky:** `No sticky message exists in this channel.`",
                    "**Already stopped:** `Sticky message is already stopped.`"
                ]
            },
            
            "stickstart": {
                "category": "Sticky Messages",
                "description": "Resume a stopped sticky message in the current channel",
                "usage": f"`{self.prefix}stickstart`",
                "detailed_usage": [
                    f"`{self.prefix}stickstart` - Resume sticky message in current channel"
                ],
                "examples": [
                    f"`{self.prefix}stickstart` - Resume paused sticky message",
                    "Restarts the sticky message auto-posting behavior"
                ],
                "permissions": "Manage Messages permission required",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `You need Manage Messages permission.`",
                    "**No sticky:** `No sticky message exists in this channel.`",
                    "**Already running:** `Sticky message is already active.`"
                ]
            },
            
            "stickremove": {
                "category": "Sticky Messages",
                "description": "Permanently remove the sticky message from current channel",
                "usage": f"`{self.prefix}stickremove`",
                "detailed_usage": [
                    f"`{self.prefix}stickremove` - Completely delete sticky message"
                ],
                "examples": [
                    f"`{self.prefix}stickremove` - Delete sticky message permanently",
                    "This action cannot be undone - sticky will be completely removed"
                ],
                "permissions": "Manage Messages permission required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `You need Manage Messages permission.`",
                    "**No sticky:** `No sticky message exists in this channel.`"
                ]
            },
            
            "getstickies": {
                "category": "Sticky Messages",
                "description": "List all sticky messages in the server",
                "usage": f"`{self.prefix}getstickies`",
                "detailed_usage": [
                    f"`{self.prefix}getstickies` - Shows all sticky messages with channels and status"
                ],
                "examples": [
                    f"`{self.prefix}getstickies` - View all server sticky messages",
                    "Shows channel, message content, and active/stopped status"
                ],
                "permissions": "Manage Messages permission required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `You need Manage Messages permission.`",
                    "**No stickies:** `No sticky messages are configured in this server.`"
                ]
            },
            
            "stickspeed": {
                "category": "Sticky Messages",
                "description": "View or change sticky message update speed",
                "usage": f"`{self.prefix}stickspeed [new_speed]`",
                "detailed_usage": [
                    f"`{self.prefix}stickspeed` - View current update speed",
                    f"`{self.prefix}stickspeed 5` - Set update speed to 5 messages"
                ],
                "examples": [
                    f"`{self.prefix}stickspeed` - Check current sticky update frequency",
                    f"`{self.prefix}stickspeed 3` - Sticky reposts every 3 new messages"
                ],
                "permissions": "Manage Messages permission required",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `You need Manage Messages permission.`",
                    "**Invalid speed:** `Speed must be between 1 and 20 messages.`",
                    "**No sticky:** `No sticky message exists in this channel.`"
                ]
            },
            
            # LOGGING COMMANDS
            
            "cmdlogs": {
                "category": "Logging (Developer)",
                "description": "Configure global command logging across all servers",
                "usage": f"`{self.prefix}cmdlogs <set/status/stats/test>`",
                "detailed_usage": [
                    f"`{self.prefix}cmdlogs set #channel` - Set command logging channel",
                    f"`{self.prefix}cmdlogs status` - Check logging status",
                    f"`{self.prefix}cmdlogs stats` - View logging statistics",
                    f"`{self.prefix}cmdlogs test` - Send test log message"
                ],
                "examples": [
                    f"`{self.prefix}cmdlogs set #bot-logs` - Log all commands to #bot-logs",
                    f"`{self.prefix}cmdlogs status` - Check current logging configuration"
                ],
                "permissions": "Bot owner only",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Channel not found:** `Could not find the specified channel.`",
                    "**No permissions:** `Bot doesn't have permission to send messages in that channel.`"
                ]
            },
            
            "dmlogs": {
                "category": "Logging (Developer)",
                "description": "Configure global DM logging system",
                "usage": f"`{self.prefix}dmlogs <set/status/test>`",
                "detailed_usage": [
                    f"`{self.prefix}dmlogs set #channel` - Set DM logging channel",
                    f"`{self.prefix}dmlogs status` - Check DM logging status",
                    f"`{self.prefix}dmlogs test` - Send test DM log"
                ],
                "examples": [
                    f"`{self.prefix}dmlogs set #dm-logs` - Log all DMs to #dm-logs",
                    f"`{self.prefix}dmlogs status` - Check current DM logging setup"
                ],
                "permissions": "Bot owner only",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Channel not found:** `Could not find the specified channel.`",
                    "**No permissions:** `Bot needs Send Messages permission in that channel.`"
                ]
            },
            
            "guildlogs": {
                "category": "Logging (Developer)",
                "description": "Configure global guild event logging",
                "usage": f"`{self.prefix}guildlogs <set/status>`",
                "detailed_usage": [
                    f"`{self.prefix}guildlogs set #channel` - Set guild event logging channel",
                    f"`{self.prefix}guildlogs status` - Check guild logging status"
                ],
                "examples": [
                    f"`{self.prefix}guildlogs set #guild-events` - Log guild joins/leaves",
                    f"`{self.prefix}guildlogs status` - View current guild logging config"
                ],
                "permissions": "Bot owner only",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Channel not found:** `Could not find the specified channel.`"
                ]
            },
            
            # DEVELOPER COMMANDS
            
            "reload": {
                "category": "Developer",
                "description": "Reload a specific bot cog/module (Developer only)",
                "usage": f"`{self.prefix}reload <cog_name>`",
                "detailed_usage": [
                    f"`{self.prefix}reload tickets` - Reload tickets cog",
                    f"`{self.prefix}reload utilities` - Reload utilities cog"
                ],
                "examples": [
                    f"`{self.prefix}reload help` - Reload help system",
                    f"`{self.prefix}reload autoresponders` - Reload autoresponder system"
                ],
                "permissions": "Bot owner only",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Cog not found:** `Could not find cog: 'cog-name'`",
                    "**Reload failed:** `Failed to reload cog due to syntax error.`"
                ]
            },
            
            "reloadall": {
                "category": "Developer",
                "description": "Reload all bot cogs/modules at once (Developer only)",
                "usage": f"`{self.prefix}reloadall`",
                "detailed_usage": [
                    f"`{self.prefix}reloadall` - Reload every cog in the bot"
                ],
                "examples": [
                    f"`{self.prefix}reloadall` - Complete bot refresh without restart"
                ],
                "permissions": "Bot owner only",
                "cooldown": "30 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Partial failure:** `Some cogs failed to reload due to errors.`"
                ]
            },
            
            "eval": {
                "category": "Developer",
                "description": "Evaluate Python code in bot context (Developer only)",
                "usage": f"`{self.prefix}eval <python_code>`",
                "detailed_usage": [
                    f"`{self.prefix}eval len(self.bot.guilds)` - Get guild count",
                    f"`{self.prefix}eval ctx.guild.name` - Get current guild name"
                ],
                "examples": [
                    f"`{self.prefix}eval 2 + 2` - Simple math evaluation",
                    f"`{self.prefix}eval len(self.bot.users)` - Count bot users"
                ],
                "permissions": "Bot owner only",
                "cooldown": "5 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Syntax error:** `Invalid Python syntax in code.`",
                    "**Runtime error:** `Code execution failed with error.`"
                ]
            },
            
            "setstatus": {
                "category": "Developer",
                "description": "Change bot's Discord status (Developer only)",
                "usage": f"`{self.prefix}setstatus <online/idle/dnd/invisible>`",
                "detailed_usage": [
                    f"`{self.prefix}setstatus online` - Set status to online",
                    f"`{self.prefix}setstatus dnd` - Set status to do not disturb"
                ],
                "examples": [
                    f"`{self.prefix}setstatus idle` - Show as away/idle",
                    f"`{self.prefix}setstatus invisible` - Appear offline"
                ],
                "permissions": "Bot owner only",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Invalid status:** `Status must be: online, idle, dnd, or invisible.`"
                ]
            },
            
            "setactivity": {
                "category": "Developer",
                "description": "Change bot's activity/rich presence (Developer only)",
                "usage": f"`{self.prefix}setactivity <playing/watching/listening> <text>`",
                "detailed_usage": [
                    f"`{self.prefix}setactivity playing Discord` - Playing Discord",
                    f"`{self.prefix}setactivity watching servers` - Watching servers",
                    f"`{self.prefix}setactivity listening music` - Listening to music"
                ],
                "examples": [
                    f"`{self.prefix}setactivity playing with tickets` - Playing with tickets",
                    f"`{self.prefix}setactivity watching {{servers}} servers` - Dynamic server count"
                ],
                "permissions": "Bot owner only",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Invalid type:** `Activity type must be: playing, watching, or listening.`"
                ]
            },
            
            # MONITORING COMMANDS
            
            "monitoring": {
                "category": "Monitoring (Developer)",
                "description": "Advanced bot monitoring dashboard with system metrics",
                "usage": f"`{self.prefix}monitoring <ratelimits/shards/cluster/alerts/export>`",
                "detailed_usage": [
                    f"`{self.prefix}monitoring ratelimits` - View Discord API rate limits",
                    f"`{self.prefix}monitoring shards` - Check shard health and latency",
                    f"`{self.prefix}monitoring cluster` - Cluster performance metrics",
                    f"`{self.prefix}monitoring alerts` - System alerts and warnings",
                    f"`{self.prefix}monitoring export` - Export metrics data"
                ],
                "examples": [
                    f"`{self.prefix}monitoring ratelimits` - Check API usage and limits",
                    f"`{self.prefix}monitoring shards` - View shard status and ping times"
                ],
                "permissions": "Bot owner only",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Monitoring unavailable:** `Monitoring system is currently offline.`"
                ]
            },
            
            "cluster": {
                "category": "Cluster Management (Developer)",
                "description": "Manage bot cluster operations and optimization",
                "usage": f"`{self.prefix}cluster <info/shards/optimize/export>`",
                "detailed_usage": [
                    f"`{self.prefix}cluster info` - Display cluster information",
                    f"`{self.prefix}cluster shards` - Show shard distribution",
                    f"`{self.prefix}cluster optimize` - Optimize cluster performance",
                    f"`{self.prefix}cluster export` - Export cluster data"
                ],
                "examples": [
                    f"`{self.prefix}cluster info` - View current cluster status",
                    f"`{self.prefix}cluster optimize` - Balance load across shards"
                ],
                "permissions": "Bot owner only",
                "cooldown": "20 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Cluster error:** `Cluster management system encountered an error.`"
                ]
            },
            
            # DATA MANAGEMENT COMMANDS
            
            "backup": {
                "category": "Data Management (Developer)",
                "description": "Create manual backup of bot data (Developer only)",
                "usage": f"`{self.prefix}backup [backup_name]`",
                "detailed_usage": [
                    f"`{self.prefix}backup` - Create backup with timestamp",
                    f"`{self.prefix}backup pre-update` - Create named backup"
                ],
                "examples": [
                    f"`{self.prefix}backup` - Create automatic backup",
                    f"`{self.prefix}backup before-changes` - Named backup for safety"
                ],
                "permissions": "Bot owner only",
                "cooldown": "60 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Backup failed:** `Failed to create backup due to file system error.`"
                ]
            },
            
            "restore": {
                "category": "Data Management (Developer)",
                "description": "Restore bot data from backup (Developer only)",
                "usage": f"`{self.prefix}restore <backup_name>`",
                "detailed_usage": [
                    f"`{self.prefix}restore latest` - Restore from latest backup",
                    f"`{self.prefix}restore backup-name` - Restore specific backup"
                ],
                "examples": [
                    f"`{self.prefix}restore startup_backup` - Restore startup backup",
                    f"`{self.prefix}restore pre-update` - Restore named backup"
                ],
                "permissions": "Bot owner only",
                "cooldown": "120 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**Backup not found:** `Could not find backup: 'backup-name'`",
                    "**Restore failed:** `Failed to restore backup due to corruption.`"
                ]
            },
            
            "listbackups": {
                "category": "Data Management (Developer)",
                "description": "List all available backups with details (Developer only)",
                "usage": f"`{self.prefix}listbackups`",
                "detailed_usage": [
                    f"`{self.prefix}listbackups` - Shows all backups with creation dates and sizes"
                ],
                "examples": [
                    f"`{self.prefix}listbackups` - View all available backups for restoration"
                ],
                "permissions": "Bot owner only",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**Owner only:** `This command is restricted to bot owners.`",
                    "**No backups:** `No backups are currently available.`"
                ]
            },

            "addsupport": {
                "category": "Ticket System",
                "description": "Add support roles or users to the ticket system",
                "usage": f"{self.prefix}addsupport <role_or_user>",
                "detailed_usage": [
                    f"`{self.prefix}addsupport @Support` - Add support role",
                    f"`{self.prefix}addsupport @username` - Add support user"
                ],
                "examples": [
                    f"`{self.prefix}addsupport @Helper` - Add helper role as support",
                    f"`{self.prefix}addsupport @JaneDoe` - Add user as support"
                ],
                "permissions": "Administrator permission",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can add support roles.`",
                    "**Invalid target:** `Please specify a valid role or user.`",
                    "**Already support:** `This role/user is already support.`"
                ]
            },

            "blacklist": {
                "category": "Ticket System",
                "description": "Manage the ticket system blacklist",
                "usage": f"{self.prefix}blacklist <add|remove|list> [user]",
                "detailed_usage": [
                    f"`{self.prefix}blacklist add @user` - Blacklist a user",
                    f"`{self.prefix}blacklist remove @user` - Remove from blacklist",
                    f"`{self.prefix}blacklist list` - View blacklisted users"
                ],
                "examples": [
                    f"`{self.prefix}blacklist add @Spammer` - Prevent user from creating tickets",
                    f"`{self.prefix}blacklist remove @ReformedUser` - Allow tickets again",
                    f"`{self.prefix}blacklist list` - See all blacklisted users"
                ],
                "permissions": "Administrator permission",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can manage blacklist.`",
                    "**Invalid action:** `Valid actions: add, remove, list`",
                    "**User not found:** `Could not find the specified user.`"
                ]
            },

            "viewstaff": {
                "category": "Ticket System",
                "description": "View all staff members and roles in the ticket system",
                "usage": f"{self.prefix}viewstaff",
                "detailed_usage": [
                    f"`{self.prefix}viewstaff` - List all admins and support staff"
                ],
                "examples": [
                    f"`{self.prefix}viewstaff` - See admin roles, support roles, and individual staff"
                ],
                "permissions": "Staff role required",
                "cooldown": "15 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only staff can view the staff list.`",
                    "**No staff set:** `No staff roles have been configured yet.`"
                ]
            },

            "tconfig": {
                "category": "Ticket System",
                "description": "Configure ticket system settings via commands",
                "usage": f"{self.prefix}tconfig <transcripts|staff|view> [value]",
                "detailed_usage": [
                    f"`{self.prefix}tconfig transcripts #channel` - Set transcript channel",
                    f"`{self.prefix}tconfig staff @role` - Add staff role",
                    f"`{self.prefix}tconfig view` - View current settings"
                ],
                "examples": [
                    f"`{self.prefix}tconfig transcripts #ticket-logs` - Set logging channel",
                    f"`{self.prefix}tconfig staff @Support` - Add support role",
                    f"`{self.prefix}tconfig view` - See current configuration"
                ],
                "permissions": "Administrator permission",
                "cooldown": "10 seconds per user",
                "error_scenarios": [
                    "**No permissions:** `Only administrators can configure tickets.`",
                    "**Invalid option:** `Valid options: transcripts, staff, view`",
                    "**Invalid channel:** `Please specify a valid text channel.`"
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
            
            # Embed Builder Commands
            
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
                "title": f"{self.bot.user.display_name} Commands List",
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
                "title": f"{SPROUTS_CHECK} TicketsBot-Compatible System (33 Commands)",
                "description": f"Complete TicketsBot.net equivalent with all enterprise features\nPrefix: `{prefix}`",
                "fields": [
                    {
                        "name": "🎫 Ticket Commands (14)",
                        "value": "`new/open <subject>` - Opens new ticket | `close [reason]` - Closes ticket\n"
                                "`add <user>` - Add user | `remove <user>` - Remove user\n"
                                "`claim` - Assign staff | `unclaim` - Remove claim\n"
                                "`rename <name>` - Rename ticket | `transfer <user>` - Transfer ownership\n"
                                "`closerequest [reason]` - Request close | `reopen <id>` - Reopen ticket\n"
                                "`jumptotop` - Jump button | `notes` - Staff thread | `switchpanel` - Change panel",
                        "inline": False
                    },
                    {
                        "name": "⚙️ Setting Commands (15)",
                        "value": "`addadmin/removeadmin <user>` - Admin management\n"
                                "`addsupport/removesupport <user>` - Support management\n"
                                "`blacklist <user>` - Toggle blacklist | `viewstaff` - List staff\n"
                                "`panel` - Panel setup | `setup limit/transcripts/use-threads`\n"
                                "`autoclose configure/exclude` - Auto-close settings",
                        "inline": False
                    },
                    {
                        "name": "🏷️ Tag Commands (4)",
                        "value": "`managetags add/delete/list` - Manage tags\n"
                                "`tag <tag_id>` - Send tag message snippet",
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
        """Create dynamic help pages with all bot commands"""
        pages = []
        
        # Get all bot commands
        bot_commands = {cmd.name for cmd in self.bot.commands if not cmd.hidden}
        
        # Build command categories in the exact order specified by user
        from collections import OrderedDict
        command_categories = OrderedDict([
            ("Uncategorized Commands", {
                "commands": ["about", "invite", "shards", "vote"],
                "description": "Essential bot information and system commands"
            }),
            ("Utility Commands", {
                "commands": ["avatar", "channelinfo", "inviteinfo", "ping", "roleinfo", "serverinfo", "userinfo", "setprefix", "prefix", "variables"],
                "description": "User and server information tools"
            }),
            ("User Ticket Commands", {
                "commands": ["new", "close"],
                "description": "Basic ticket commands for users"
            }),
            ("Staff Ticket Management", {
                "commands": ["claim", "unclaim", "add", "remove", "rename", "topic", "move", "transfer", "forceclose", "tickets", "notes", "transcript"],
                "description": "Advanced ticket management for staff"
            }),
            ("Ticket Administration", {
                "commands": ["settings", "addadmin", "addsupport", "blacklist", "viewstaff", "tconfig"],
                "description": "Administrative ticket configuration commands"
            }),
            ("Auto responders", {
                "commands": ["autoresponder"],
                "description": "Advanced automated message responses with match modes"
            }),
            ("Sticky messages", {
                "commands": ["stick", "stickslow", "stickstop", "stickstart", "stickremove", "getstickies", "stickspeed"],
                "description": "Persistent channel messages"
            }),
            ("Reminders", {
                "commands": ["remind", "reminders", "delreminder"],
                "description": "Personal reminder system"
            })
        ])
        
        # Build pages dynamically
        current_page = None
        current_fields = 0
        page_number = 1
        total_categories = len([cat for cat in command_categories.keys() if command_categories[cat]["commands"]])
        
        # Process all categories in order
        for category_name, category_data in command_categories.items():
            # Get commands for this category that actually exist in the bot
            category_commands = []
            for cmd in category_data["commands"]:
                if cmd in bot_commands:
                    # Get description from bot command or use fallback
                    cmd_obj = self.bot.get_command(cmd)
                    desc = cmd_obj.help if cmd_obj and cmd_obj.help else "No description available"
                    
                    # Handle special cases
                    if cmd in ["new", "open"]:
                        if "new / open" not in [c.split(" - ")[0].strip("`") for c in category_commands]:
                            category_commands.append("`new` / `open` - Create new support ticket")
                    elif cmd != "open":  # Skip open since it's combined with new
                        category_commands.append(f"`{cmd}` - {desc}")
            
            # Skip empty categories
            if not category_commands:
                continue
            
            # Create new page if needed (6 pages instead of 3)
            if current_page is None or current_fields >= 1:
                if current_page is not None:
                    pages.append(current_page)
                
                current_page = discord.Embed(
                    title=f"{self.bot.user.display_name} Commands",
                    description=f"Use `{prefix}help <command>` for detailed info.\nThis server prefix: `{prefix}`, <@1411758556667056310>",
                    color=EMBED_COLOR_NORMAL
                )
                
                # Set bot thumbnail
                if self.bot.user and self.bot.user.display_avatar:
                    current_page.set_thumbnail(url=self.bot.user.display_avatar.url)
                
                current_fields = 0
                page_number += 1
            
            # Add category to current page with character limit check
            field_value = "\n".join(category_commands)
            
            # Split field if it exceeds Discord's 1024 character limit
            if len(field_value) > 1024:
                # Split commands into chunks that fit within 1024 characters
                chunks = []
                current_chunk = []
                current_length = 0
                
                for cmd in category_commands:
                    cmd_with_newline = cmd + "\n" if current_chunk else cmd
                    if current_length + len(cmd_with_newline) > 1020:  # Leave buffer for safety
                        chunks.append("\n".join(current_chunk))
                        current_chunk = [cmd]
                        current_length = len(cmd)
                    else:
                        current_chunk.append(cmd)
                        current_length += len(cmd_with_newline)
                
                # Add remaining commands
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                
                # Add first chunk
                current_page.add_field(
                    name=category_name,
                    value=chunks[0],
                    inline=False
                )
                current_fields += 1
                
                # Add remaining chunks as continuation fields
                for i, chunk in enumerate(chunks[1:], 1):
                    # Create new page if needed (6 pages instead of 3)
                    if current_fields >= 1:
                        pages.append(current_page)
                        current_page = discord.Embed(
                            title=f"{self.bot.user.display_name} Commands",
                            description=f"Use `{prefix}help <command>` for detailed info.\nThis server prefix: `{prefix}`, <@1411758556667056310>",
                            color=EMBED_COLOR_NORMAL
                        )
                        if self.bot.user and self.bot.user.display_avatar:
                            current_page.set_thumbnail(url=self.bot.user.display_avatar.url)
                        current_fields = 0
                    
                    current_page.add_field(
                        name=f"{category_name} (continued {i+1})",
                        value=chunk,
                        inline=False
                    )
                    current_fields += 1
            else:
                # Field fits within limit
                current_page.add_field(
                    name=category_name,
                    value=field_value,
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
    
    
    async def show_command_help(self, ctx, command_name: str, prefix: str):
        """Show extremely detailed help for a specific command with interactive buttons"""
        try:
            # Check if command is enabled via feature flags first
            # REMOVED: Feature flag check for individual command help - s.help <command> should always work
            # Users should be able to see help for any command, even if the feature is disabled
            if False:  # Always allow individual command help
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


async def setup_help(bot):
    """Setup help command for the bot"""
    await bot.add_cog(HelpCommand(bot))
    logger.info("Help command setup completed")

# For backwards compatibility
async def setup(bot):
    await setup_help(bot)
