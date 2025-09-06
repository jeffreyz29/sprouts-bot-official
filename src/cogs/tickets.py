"""
SPROUTS Ticket System
Professional ticket management system with modern UI components
Built using discord-tickets architecture with SPROUTS branding
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import os
import asyncio
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import uuid
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR, EMBED_COLOR_HIERARCHY
from emojis import SPROUTS_ERROR, SPROUTS_CHECK, SPROUTS_WARNING, SPROUTS_INFORMATION

logger = logging.getLogger(__name__)

class SproutsTicketSystem(commands.Cog):
    """
    SPROUTS Professional Ticket System
    Modern ticket management with clean UI and professional features
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.name = "SPROUTS Tickets"
        self.tickets_data = {}
        self.panels_data = {}
        self.guild_settings = {}
        
        # Initialize data files
        self.tickets_file = "src/data/github_tickets.json"
        self.panels_file = "src/data/github_panels.json"
        self.settings_file = "src/data/github_settings.json"
        
        # Create data directory
        os.makedirs("src/data", exist_ok=True)
        
        # Load existing data
        self.load_data()
        
        logger.info("SPROUTS ticket system initialized")
    
    def load_data(self):
        """Load ticket data from JSON files (GitHub discord-tickets style)"""
        try:
            # Load tickets
            if os.path.exists(self.tickets_file):
                with open(self.tickets_file, 'r') as f:
                    self.tickets_data = json.load(f)
            
            # Load panels
            if os.path.exists(self.panels_file):
                with open(self.panels_file, 'r') as f:
                    self.panels_data = json.load(f)
            
            # Load guild settings
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.guild_settings = json.load(f)
                    
            logger.info("SPROUTS tickets data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading SPROUTS tickets data: {e}")
    
    def save_data(self):
        """Save ticket data to JSON files"""
        try:
            # Save tickets
            with open(self.tickets_file, 'w') as f:
                json.dump(self.tickets_data, f, indent=2)
            
            # Save panels
            with open(self.panels_file, 'w') as f:
                json.dump(self.panels_data, f, indent=2)
            
            # Save settings
            with open(self.settings_file, 'w') as f:
                json.dump(self.guild_settings, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving SPROUTS tickets data: {e}")

class SproutsTicketView(discord.ui.View):
    """SPROUTS ticket view with modern buttons"""
    
    def __init__(self, ticket_system):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
    
    @discord.ui.button(
        label="Claim",
        style=discord.ButtonStyle.success,
        emoji=SPROUTS_CHECK,
        custom_id="github_claim_ticket"
    )
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Claim ticket with proper ephemeral responses"""
        # Check if user is staff
        if not await self.ticket_system.is_staff(interaction.user, interaction.guild):
            embed = discord.Embed(
                description=f"**{SPROUTS_ERROR} Access Denied**\n\nOnly staff members can claim tickets.",
                color=EMBED_COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if ticket exists
        ticket_data = self.ticket_system.get_ticket_data(interaction.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                description=f"**{SPROUTS_ERROR} Invalid Channel**\n\nThis is not a valid ticket channel.",
                color=EMBED_COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if already claimed
        if ticket_data.get('claimed_by'):
            claimer = interaction.guild.get_member(ticket_data['claimed_by'])
            claimer_name = claimer.display_name if claimer else "Unknown User"
            embed = discord.Embed(
                description=f"**{SPROUTS_WARNING} Already Claimed**\n\nThis ticket is already claimed by **{claimer_name}**.",
                color=EMBED_COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Claim the ticket
        success = await self.ticket_system.claim_ticket(interaction.channel, interaction.user)
        
        if success:
            embed = discord.Embed(
                description=f"**{SPROUTS_CHECK} Ticket Claimed**\n\nYou are now handling this ticket.",
                color=EMBED_COLOR_NORMAL
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                description=f"**{SPROUTS_ERROR} Claim Failed**\n\nUnable to claim this ticket.",
                color=EMBED_COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.danger,
        emoji=SPROUTS_ERROR,
        custom_id="github_close_ticket"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close ticket (GitHub discord-tickets style)"""
        # Check permissions first
        ticket_data = self.ticket_system.get_ticket_data(interaction.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                description=f"**{SPROUTS_ERROR} Error**\n\nThis is not a valid ticket channel.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_author(name="SPROUTS Support", icon_url=self.ticket_system.bot.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Show confirmation modal
        modal = CloseTicketModal(self.ticket_system)
        await interaction.response.send_modal(modal)

class CloseTicketModal(discord.ui.Modal, title="Close Ticket Confirmation"):
    """Modal for close ticket confirmation with reason"""
    
    def __init__(self, ticket_system):
        super().__init__()
        self.ticket_system = ticket_system
    
    reason = discord.ui.TextInput(
        label="Reason for closing (optional)",
        placeholder="Enter a reason for closing this ticket...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        reason = self.reason.value if self.reason.value else "No reason provided"
        
        # Close the ticket
        await self.ticket_system.close_ticket(interaction.channel, interaction.user, reason)
        
        # Send confirmation
        embed = discord.Embed(
            description=f"**{SPROUTS_CHECK} Ticket Closing**\n\nThis ticket is being closed and archived.",
            color=EMBED_COLOR_HIERARCHY
        )
        embed.set_author(name="Ticket Management", icon_url=interaction.user.display_avatar.url)
        await interaction.followup.send(embed=embed)

class SproutsCreateTicketView(discord.ui.View):
    """GitHub discord-tickets style ticket creation panel"""
    
    def __init__(self, panel_id: str, ticket_system):
        super().__init__(timeout=None)
        self.panel_id = panel_id
        self.ticket_system = ticket_system
    
    @discord.ui.button(
        label="Create Support Ticket",
        style=discord.ButtonStyle.primary,
        emoji=SPROUTS_CHECK,
        custom_id="github_create_ticket"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Create new ticket (GitHub discord-tickets style)"""
        await interaction.response.defer(ephemeral=True)
        
        # Check if user already has an open ticket
        existing_ticket = self.ticket_system.get_user_ticket(interaction.user.id, interaction.guild.id)
        if existing_ticket:
            embed = discord.Embed(
                description=f"**{SPROUTS_WARNING} Existing Ticket Found**\n\nYou already have an open ticket: <#{existing_ticket['channel_id']}>",
                color=EMBED_COLOR_ERROR
            )
            embed.set_author(name="SPROUTS Support", icon_url=self.ticket_system.bot.user.display_avatar.url)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Create the ticket
        ticket_channel = await self.ticket_system.create_ticket(
            guild=interaction.guild,
            creator=interaction.user,
            panel_id=self.panel_id,
            reason="Created via panel"
        )
        
        if ticket_channel:
            embed = discord.Embed(
                description=f"**{SPROUTS_CHECK} Ticket Created Successfully**\n\nYour support ticket is ready: {ticket_channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_author(name="SPROUTS Support", icon_url=self.ticket_system.bot.user.display_avatar.url)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                description=f"**{SPROUTS_ERROR} Unable to Create Ticket**\n\nSomething went wrong. Please try again or contact an administrator.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_author(name="SPROUTS Support", icon_url=self.ticket_system.bot.user.display_avatar.url)
            await interaction.followup.send(embed=embed, ephemeral=True)

# Extend the main class with additional methods
class SproutsTicketSystemExtended(SproutsTicketSystem):
    """Extended GitHub ticket system with core functionality"""
    
    def get_guild_settings(self, guild_id: int) -> Dict:
        """Get guild settings from configuration"""
        guild_id_str = str(guild_id)
        return self.guild_settings.get(guild_id_str, {})

    async def is_staff(self, member: discord.Member, guild: discord.Guild) -> bool:
        """Check if member is staff (GitHub discord-tickets style)"""
        # Check for administrator permission
        if member.guild_permissions.administrator:
            return True
        
        # Check for manage channels permission
        if member.guild_permissions.manage_channels:
            return True
        
        # Check guild-specific staff roles
        guild_id = str(guild.id)
        if guild_id in self.guild_settings:
            staff_roles = self.guild_settings[guild_id].get('staff_roles', [])
            member_role_ids = [role.id for role in member.roles]
            if any(role_id in member_role_ids for role_id in staff_roles):
                return True
        
        return False
    
    def get_ticket_data(self, channel_id: int) -> Optional[Dict]:
        """Get ticket data by channel ID"""
        for ticket_id, ticket_data in self.tickets_data.items():
            if ticket_data.get('channel_id') == channel_id:
                ticket_data['id'] = ticket_id  # Ensure ID is included
                return ticket_data
        return None
    
    def get_user_ticket(self, user_id: int, guild_id: int) -> Optional[Dict]:
        """Get user's existing ticket in guild"""
        for ticket_id, ticket_data in self.tickets_data.items():
            if (ticket_data.get('creator_id') == user_id and 
                ticket_data.get('guild_id') == guild_id and
                ticket_data.get('status') == 'open'):
                ticket_data['id'] = ticket_id  # Ensure ID is included
                return ticket_data
        return None
    
    def get_next_ticket_number(self, guild_id: int) -> int:
        """Get the next ticket number for the guild"""
        guild_tickets = [t for t in self.tickets_data.values() if t.get('guild_id') == guild_id]
        if not guild_tickets:
            return 1
        return len(guild_tickets) + 1

    async def create_ticket(
        self, 
        guild: discord.Guild, 
        creator: discord.Member, 
        panel_id: str = None,
        reason: str = "No reason provided"
    ) -> Optional[discord.TextChannel]:
        """Create a new ticket (GitHub discord-tickets style)"""
        try:
            # Generate ticket ID
            ticket_id = str(uuid.uuid4())[:8]
            
            # Get or create ticket category
            category = await self.get_ticket_category(guild)
            
            # Create clean channel name - try username first, fallback to number
            clean_username = ''.join(c for c in creator.name.lower() if c.isalnum())
            if clean_username and len(clean_username) <= 15:
                channel_name = f"ticket-{clean_username}"
            else:
                ticket_number = self.get_next_ticket_number(guild.id)
                channel_name = f"ticket-{ticket_number:04d}"
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                creator: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True
                )
            }
            
            # Add staff permissions
            await self.add_staff_permissions(overwrites, guild)
            
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Support ticket for {creator.display_name} | ID: {ticket_id}"
            )
            
            # Save ticket data
            self.tickets_data[ticket_id] = {
                'id': ticket_id,
                'channel_id': ticket_channel.id,
                'guild_id': guild.id,
                'creator_id': creator.id,
                'panel_id': panel_id,
                'reason': reason,
                'status': 'open',
                'claimed_by': None,
                'created_at': datetime.utcnow().isoformat(),
                'messages': []
            }
            self.save_data()
            
            # Send welcome message (GitHub discord-tickets style)
            await self.send_welcome_message(ticket_channel, creator, ticket_id, reason)
            
            logger.info(f"Created GitHub-style ticket {ticket_id} for {creator}")
            return ticket_channel
            
        except Exception as e:
            logger.error(f"Error creating GitHub-style ticket: {e}")
            return None
    
    async def get_ticket_category(self, guild: discord.Guild) -> Optional[discord.CategoryChannel]:
        """Get or create ticket category"""
        # Look for existing ticket category
        for category in guild.categories:
            if 'ticket' in category.name.lower():
                return category
        
        # Create new category
        try:
            category = await guild.create_category(
                name=f"{SPROUTS_INFORMATION} Support Tickets",
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(read_messages=False)
                }
            )
            return category
        except Exception as e:
            logger.error(f"Error creating ticket category: {e}")
            return None
    
    async def add_staff_permissions(self, overwrites: Dict, guild: discord.Guild):
        """Add staff role permissions to ticket"""
        guild_id = str(guild.id)
        if guild_id in self.guild_settings:
            staff_roles = self.guild_settings[guild_id].get('staff_roles', [])
            for role_id in staff_roles:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_messages=True,
                        embed_links=True,
                        attach_files=True,
                        read_message_history=True
                    )
    
    async def send_welcome_message(
        self, 
        channel: discord.TextChannel, 
        creator: discord.Member, 
        ticket_id: str,
        reason: str
    ):
        """Send GitHub discord-tickets style welcome message"""
        embed = discord.Embed(
            description=f"**Welcome to your support ticket, {creator.mention}**\n\nPlease describe your issue in detail. A staff member will assist you shortly.",
            color=EMBED_COLOR_NORMAL,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Ticket Details",
            value=f"**Creator:** {creator.mention}\n**Reason:** {reason}\n**Status:** Open",
            inline=True
        )
        
        embed.add_field(
            name="Quick Actions",
            value="• Describe your issue\n• Wait for staff response\n• Use buttons to manage",
            inline=True
        )
        
        embed.set_author(name=f"Support Ticket #{ticket_id}", icon_url=creator.display_avatar.url)
        embed.set_footer(
            text="SPROUTS Support Team",
            icon_url=self.bot.user.display_avatar.url
        )
        
        # Add SPROUTS ticket view buttons
        view = SproutsTicketView(self)
        
        await channel.send(embed=embed, view=view)
        
        # Add jump to top button using proper view class
        from .tickets_views import JumpToTopView
        jump_view = JumpToTopView()
        await channel.send("**Ticket Management**", view=jump_view)
    
    async def claim_ticket(self, channel: discord.TextChannel, staff: discord.Member):
        """Claim a ticket (GitHub discord-tickets style)"""
        ticket_data = self.get_ticket_data(channel.id)
        if not ticket_data:
            return False
        
        # Update ticket data
        ticket_id = ticket_data['id']
        self.tickets_data[ticket_id]['claimed_by'] = staff.id
        self.tickets_data[ticket_id]['claimed_at'] = datetime.utcnow().isoformat()
        self.save_data()
        
        # Update channel topic
        await channel.edit(topic=f"Support ticket claimed by {staff.display_name} | ID: {ticket_id}")
        
        logger.info(f"Ticket {ticket_id} claimed by {staff}")
        return True
    
    async def close_ticket(
        self, 
        channel: discord.TextChannel, 
        closer: discord.Member, 
        reason: str = "No reason provided"
    ):
        """Close a ticket (GitHub discord-tickets style)"""
        ticket_data = self.get_ticket_data(channel.id)
        if not ticket_data:
            return False
        
        ticket_id = ticket_data['id']
        
        try:
            # Send countdown warning message first
            warning_embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Ticket Closing",
                description=f"This ticket will be closed in **30 seconds**...\n\n**Closed by:** {closer.mention}\n**Reason:** {reason}",
                color=EMBED_COLOR_HIERARCHY
            )
            warning_embed.set_footer(text="Generating transcript and notifying ticket creator...")
            warning_message = await channel.send(embed=warning_embed)
            
            # Wait for countdown
            await asyncio.sleep(30)
            
            # Delete the warning message
            try:
                await warning_message.delete()
            except:
                pass  # Ignore if message was already deleted
            
            # Generate transcript using GitHub discord-tickets system
            from utils.transcript_generator import transcript_generator
            
            creator = channel.guild.get_member(ticket_data['creator_id'])
            staff_id = ticket_data.get('claimed_by')
            staff = channel.guild.get_member(staff_id) if staff_id else None
            
            transcript_url, transcript_path = await transcript_generator.generate_transcript(
                channel=channel,
                ticket_id=str(ticket_id),
                creator=creator,
                staff=staff,
                reason=ticket_data.get('reason', 'No reason provided'),
                close_reason=reason
            )
            
            # Send transcript to creator
            if creator and transcript_url:
                try:
                    # Get creator and claimer info for DM
                    creator_name = creator.display_name if creator else "Unknown User"
                    
                    claimed_by = "Not claimed"
                    if ticket_data.get('claimed_by'):
                        claimer = channel.guild.get_member(ticket_data['claimed_by'])
                        claimed_by = claimer.display_name if claimer else "Unknown User"
                    
                    # Get timestamps
                    created_timestamp = int(datetime.fromisoformat(ticket_data['created_at']).timestamp())
                    current_timestamp = int(datetime.utcnow().timestamp())
                    
                    dm_embed = discord.Embed(
                        description="Ticket closed",
                        color=EMBED_COLOR_NORMAL
                    )
                    
                    dm_embed.add_field(name="TICKET ID", value=ticket_data['id'], inline=True)
                    dm_embed.add_field(name="OPEN BY", value=creator_name, inline=True)
                    dm_embed.add_field(name="CLOSED BY", value=closer.display_name, inline=True)
                    dm_embed.add_field(name="OPEN TIME", value=f"<t:{created_timestamp}:R>", inline=True)
                    dm_embed.add_field(name="CLAIMED BY", value=claimed_by, inline=True)
                    dm_embed.add_field(name="REASON", value=reason, inline=True)
                    dm_embed.add_field(name="TIMESTAMP", value=f"<t:{current_timestamp}:F>", inline=False)
                    
                    # Set author as server with user's icon
                    dm_embed.set_author(name=channel.guild.name, icon_url=closer.display_avatar.url)
                    dm_embed.set_footer(text="Thank you for using SPROUTS Support!")
                    
                    # Add transcript button to DM
                    dm_view = discord.ui.View()
                    dm_transcript_button = discord.ui.Button(
                        label="View Transcript",
                        style=discord.ButtonStyle.link,
                        url=transcript_url
                    )
                    dm_view.add_item(dm_transcript_button)
                    await creator.send(embed=dm_embed, view=dm_view)
                    logger.info(f"Sent transcript DM for ticket {ticket_id}")
                    
                except Exception as e:
                    logger.error(f"Error sending transcript DM: {e}")
            
            # Send transcript to logging channel if configured
            guild_id = str(channel.guild.id)
            if guild_id in self.guild_settings:
                transcript_channel_id = self.guild_settings[guild_id].get('transcript_channel')
                if transcript_channel_id:
                    transcript_channel = channel.guild.get_channel(transcript_channel_id)
                    if transcript_channel and transcript_url:
                        try:
                            # Get creator and claimer info for logging
                            creator_name = creator.display_name if creator else "Unknown User"
                            
                            claimed_by = "Not claimed"
                            if ticket_data.get('claimed_by'):
                                claimer = channel.guild.get_member(ticket_data['claimed_by'])
                                claimed_by = claimer.display_name if claimer else "Unknown User"
                            
                            # Get timestamps
                            created_timestamp = int(datetime.fromisoformat(ticket_data['created_at']).timestamp())
                            current_timestamp = int(datetime.utcnow().timestamp())
                            
                            log_embed = discord.Embed(
                                description="Ticket closed",
                                color=EMBED_COLOR_HIERARCHY
                            )
                            
                            log_embed.add_field(name="TICKET ID", value=ticket_data['id'], inline=True)
                            log_embed.add_field(name="OPEN BY", value=creator_name, inline=True)
                            log_embed.add_field(name="CLOSED BY", value=closer.display_name, inline=True)
                            log_embed.add_field(name="OPEN TIME", value=f"<t:{created_timestamp}:R>", inline=True)
                            log_embed.add_field(name="CLAIMED BY", value=claimed_by, inline=True)
                            log_embed.add_field(name="REASON", value=reason, inline=True)
                            log_embed.add_field(name="TIMESTAMP", value=f"<t:{current_timestamp}:F>", inline=False)
                            
                            # Set author as server with user's icon
                            log_embed.set_author(name=channel.guild.name, icon_url=closer.display_avatar.url)
                            log_embed.set_footer(text="SPROUTS Ticket System")
                            
                            # Add transcript button to logging
                            log_view = discord.ui.View()
                            log_transcript_button = discord.ui.Button(
                                label="View Transcript",
                                style=discord.ButtonStyle.link,
                                url=transcript_url
                            )
                            log_view.add_item(log_transcript_button)
                            await transcript_channel.send(embed=log_embed, view=log_view)
                            logger.info(f"Sent transcript to logging channel for ticket {ticket_id}")
                            
                        except Exception as e:
                            logger.error(f"Error sending transcript to logging channel: {e}")
            
            # Update ticket data
            self.tickets_data[ticket_id]['status'] = 'closed'
            self.tickets_data[ticket_id]['closed_by'] = closer.id
            self.tickets_data[ticket_id]['closed_at'] = datetime.utcnow().isoformat()
            self.tickets_data[ticket_id]['close_reason'] = reason
            self.tickets_data[ticket_id]['transcript_url'] = transcript_url
            self.save_data()
            
            # Send closing message
            close_embed = discord.Embed(
                description="Ticket closed",
                color=EMBED_COLOR_HIERARCHY
            )
            
            # Get creator and claimer info
            creator = channel.guild.get_member(ticket_data['creator_id'])
            creator_name = creator.display_name if creator else "Unknown User"
            
            claimed_by = "Not claimed"
            if ticket_data.get('claimed_by'):
                claimer = channel.guild.get_member(ticket_data['claimed_by'])
                claimed_by = claimer.display_name if claimer else "Unknown User"
            
            # Get timestamps
            created_timestamp = int(datetime.fromisoformat(ticket_data['created_at']).timestamp())
            current_timestamp = int(datetime.utcnow().timestamp())
            
            close_embed.add_field(name="TICKET ID", value=ticket_data['id'], inline=True)
            close_embed.add_field(name="OPEN BY", value=creator_name, inline=True)
            close_embed.add_field(name="CLOSED BY", value=closer.display_name, inline=True)
            close_embed.add_field(name="OPEN TIME", value=f"<t:{created_timestamp}:R>", inline=True)
            close_embed.add_field(name="CLAIMED BY", value=claimed_by, inline=True)
            close_embed.add_field(name="REASON", value=reason, inline=True)
            close_embed.add_field(name="TIMESTAMP", value=f"<t:{current_timestamp}:F>", inline=False)
            
            # Set author as server with user's icon
            close_embed.set_author(name=channel.guild.name, icon_url=closer.display_avatar.url)
            close_embed.set_footer(text="Channel will be deleted shortly...")
            
            # Add transcript button
            if transcript_url:
                view = discord.ui.View()
                transcript_button = discord.ui.Button(
                    label="View Transcript",
                    style=discord.ButtonStyle.link,
                    url=transcript_url
                )
                view.add_item(transcript_button)
                await channel.send(embed=close_embed, view=view)
            else:
                await channel.send(embed=close_embed)
            
            # Delete channel after a short delay (countdown already happened)
            await asyncio.sleep(5)
            await channel.delete(reason=f"Ticket closed by {closer}")
            
            logger.info(f"Closed GitHub-style ticket {ticket_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing GitHub-style ticket: {e}")
            return False

    # GitHub discord-tickets style commands
    
    
    @commands.command(name="close")
    async def close_ticket_command(self, ctx, *, reason: str = "No reason provided"):
        """Closes the current ticket"""
        # Check if this is a ticket channel
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Check permissions
        is_creator = ticket_data['creator_id'] == ctx.author.id
        is_staff = await self.is_staff(ctx.author, ctx.guild)
        
        if not (is_creator or is_staff):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only the ticket creator or staff can close this ticket.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Close the ticket
        await self.close_ticket(ctx.channel, ctx.author, reason)
    
    @commands.command(name="claim")
    async def claim_ticket_command(self, ctx):
        """Assigns a single staff member to the current ticket"""
        # Check if this is a ticket channel
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Check if user is staff
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                description=f"**{SPROUTS_ERROR} Access Denied**\n\nOnly staff members can claim tickets.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_author(name="SPROUTS Support", icon_url=self.ticket_system.bot.user.display_avatar.url)
            await ctx.send(embed=embed)
            return
        
        # Check if already claimed
        if ticket_data.get('claimed_by'):
            claimer = ctx.guild.get_member(ticket_data['claimed_by'])
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Already Claimed",
                description=f"This ticket is already claimed by {claimer.mention if claimer else 'Unknown User'}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Claim the ticket
        await self.claim_ticket(ctx.channel, ctx.author)
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Ticket Claimed",
            description=f"This ticket has been claimed by {ctx.author.mention}",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed)
    
    
    # ========== TICKETSBOT-COMPATIBLE COMMANDS ==========
    
    # TICKET COMMANDS (14 commands)
    
    @commands.command(name="new", aliases=["open"])
    async def new_ticket(self, ctx, *, subject: str = "Support Request"):
        """Opens a new ticket"""
        # Check for existing ticket
        existing_ticket = self.get_user_ticket(ctx.author.id, ctx.guild.id)
        if existing_ticket:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Existing Ticket",
                description=f"You already have an open ticket: <#{existing_ticket['channel_id']}>",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Create ticket
        ticket_channel = await self.create_ticket(
            guild=ctx.guild,
            creator=ctx.author,
            reason=subject
        )
        
        if ticket_channel:
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Ticket Created",
                description=f"Your support ticket has been created: {ticket_channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.send(embed=embed, delete_after=10)
    
    @commands.command(name="add")
    async def add_user(self, ctx, user: discord.Member):
        """Add a user to an existing ticket"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check permissions
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can add users to tickets.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Add user to channel
        await ctx.channel.set_permissions(
            user,
            read_messages=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True
        )
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} User Added",
            description=f"{user.mention} has been added to this ticket.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="remove")
    async def remove_user(self, ctx, user: discord.Member):
        """Removes a user from the current ticket"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check permissions
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can remove users from tickets.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Remove user from channel
        await ctx.channel.set_permissions(user, overwrite=None)
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} User Removed",
            description=f"{user.mention} has been removed from this ticket.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="rename")
    async def rename_ticket(self, ctx, *, new_ticket_name: str):
        """Renames the current ticket"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check permissions
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can rename tickets.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Rename channel
        old_name = ctx.channel.name
        new_name = f"ticket-{new_ticket_name.lower().replace(' ', '-')}"
        await ctx.channel.edit(name=new_name)
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Ticket Renamed",
            description=f"Ticket renamed from `{old_name}` to `{new_name}`",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="topic")
    async def set_topic(self, ctx, *, topic: str):
        """Set the ticket topic"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Update topic
        await ctx.channel.edit(topic=topic)
        
        # Update database
        ticket_id = ticket_data['id']
        self.tickets_data[ticket_id]['reason'] = topic
        self.save_data()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Topic Updated",
            description=f"Ticket topic updated to: **{topic}**",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed)
    
    
    @commands.command(name="move")
    async def move_ticket(self, ctx, category_id: int):
        """Move ticket to another category using category ID"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check permissions
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can move tickets.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Find category by ID
        category = discord.utils.get(ctx.guild.categories, id=category_id)
        if not category:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Category Not Found",
                description=f"Could not find category with ID: **{category_id}**\n\nTip: Right-click a category and copy ID, or use developer mode to get category IDs.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=15)
            return
        
        # Move channel
        old_category = ctx.channel.category
        await ctx.channel.edit(category=category)
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Ticket Moved",
            description=f"Ticket moved from **{old_category.name if old_category else 'No Category'}** to **{category.name}**\n\nCategory ID: `{category_id}`",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="transfer")
    async def transfer_ticket(self, ctx, user: discord.Member):
        """Transfer ticket to another user"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check permissions
        is_creator = ticket_data['creator_id'] == ctx.author.id
        is_staff = await self.is_staff(ctx.author, ctx.guild)
        
        if not (is_creator or is_staff):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only the ticket creator or staff can transfer tickets.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Transfer ticket
        old_creator = ctx.guild.get_member(ticket_data['creator_id'])
        ticket_id = ticket_data['id']
        
        # Update permissions
        if old_creator:
            await ctx.channel.set_permissions(old_creator, overwrite=None)
        
        await ctx.channel.set_permissions(
            user,
            read_messages=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True
        )
        
        # Update database
        self.tickets_data[ticket_id]['creator_id'] = user.id
        self.save_data()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Ticket Transferred",
            description=f"Ticket transferred from {old_creator.mention if old_creator else 'Unknown User'} to {user.mention}",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="unclaim")
    async def unclaim_ticket(self, ctx):
        """Removes the claim on the current ticket"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check if ticket is claimed
        if not ticket_data.get('claimed_by'):
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Not Claimed",
                description="This ticket is not currently claimed.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check permissions
        is_claimer = ticket_data.get('claimed_by') == ctx.author.id
        is_staff = await self.is_staff(ctx.author, ctx.guild)
        
        if not (is_claimer or is_staff):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only the user who claimed this ticket or staff can release it.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Release claim
        ticket_id = ticket_data['id']
        self.tickets_data[ticket_id]['claimed_by'] = None
        if 'claimed_at' in self.tickets_data[ticket_id]:
            del self.tickets_data[ticket_id]['claimed_at']
        self.save_data()
        
        # Update channel topic
        await ctx.channel.edit(topic=f"Support ticket | ID: {ticket_id}")
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Ticket Released",
            description="This ticket has been released and is now available for other staff to claim.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="forceclose", aliases=["force-close"])
    async def force_close(self, ctx, *, reason: str = "Force closed by admin"):
        """Force close a ticket (admin only)"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check admin permissions
        if not ctx.author.guild_permissions.administrator:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only administrators can force close tickets.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Force close the ticket
        await self.close_ticket(ctx.channel, ctx.author, f"FORCE CLOSED: {reason}")
    
    
    @commands.command(name="closerequest")
    async def close_request(self, ctx, close_delay: int = 24, *, reason: str = "No reason provided"):
        """Send a close request for ticket opener approval"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check if user is staff
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can request ticket closure.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Get ticket creator
        creator = ctx.guild.get_member(ticket_data['creator_id'])
        if not creator:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Creator Not Found",
                description="Cannot find the ticket creator to send close request.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Create close request view
        view = CloseRequestView(close_delay, reason, self)
        embed = discord.Embed(
            title=f"{SPROUTS_WARNING} Close Request",
            description=f"**Staff Member:** {ctx.author.mention}\n**Reason:** {reason}\n\n{creator.mention}, do you approve closing this ticket?",
            color=EMBED_COLOR_HIERARCHY
        )
        embed.add_field(
            name=f"{SPROUTS_WARNING} Auto-close",
            value=f"This ticket will automatically close in **{close_delay} hours** if no response is received.",
            inline=False
        )
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name="reopen")
    async def reopen_ticket(self, ctx, ticket_id: str):
        """Reopen a previously closed ticket (thread mode)"""
        # Check if user is staff
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can reopen tickets.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Find the ticket in data
        if ticket_id not in self.tickets_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Ticket Not Found",
                description=f"No ticket found with ID: `{ticket_id}`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        ticket_data = self.tickets_data[ticket_id]
        
        # Check if ticket is actually closed
        if ticket_data.get('status') != 'closed':
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Already Open",
                description="This ticket is not currently closed.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Try to find the channel
        channel = ctx.guild.get_channel(ticket_data['channel_id'])
        if not channel:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Channel Not Found",
                description="The ticket channel no longer exists and cannot be reopened.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Reopen the ticket
        ticket_data['status'] = 'open'
        ticket_data['reopened_at'] = datetime.utcnow().isoformat()
        ticket_data['reopened_by'] = ctx.author.id
        self.save_data()
        
        # Send confirmation
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Ticket Reopened",
            description=f"Ticket `{ticket_id}` has been reopened by {ctx.author.mention}\n\n**Channel:** {channel.mention}",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed)
        
        # Notify in the ticket channel
        notify_embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Ticket Reopened",
            description=f"This ticket has been reopened by {ctx.author.mention}",
            color=EMBED_COLOR_NORMAL,
            timestamp=datetime.utcnow()
        )
        await channel.send(embed=notify_embed)
    
    @commands.command(name="switchpanel")
    async def switch_panel(self, ctx, to_panel: str):
        """Switch current ticket to another panel configuration"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check if user is staff
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can switch ticket panels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check if panel exists
        if to_panel not in self.panels_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Panel Not Found",
                description=f"No panel found with ID: `{to_panel}`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Update ticket panel reference
        ticket_id = ticket_data['id']
        old_panel = ticket_data.get('panel_id', 'None')
        self.tickets_data[ticket_id]['panel_id'] = to_panel
        self.tickets_data[ticket_id]['switched_at'] = datetime.utcnow().isoformat()
        self.tickets_data[ticket_id]['switched_by'] = ctx.author.id
        self.save_data()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Panel Switched",
            description=f"**From:** `{old_panel}`\n**To:** `{to_panel}`\n\nTicket configuration updated successfully.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="jumptotop")
    async def jump_to_top(self, ctx):
        """Displays a button to click and will automatically scroll to the top of the ticket"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Get first message in channel
        async for message in ctx.channel.history(limit=1, oldest_first=True):
            first_message_url = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{message.id}"
            
            # Create button view
            view = discord.ui.View(timeout=300)
            button = discord.ui.Button(
                label="Jump to Top",
                style=discord.ButtonStyle.primary,
                emoji="📌",
                url=first_message_url
            )
            view.add_item(button)
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Jump to Top",
                description="Click the button below to scroll to the top of this ticket.",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.send(embed=embed, view=view)
            return
        
        # Fallback if no messages found
        embed = discord.Embed(
            title=f"{SPROUTS_WARNING} No Messages",
            description="No messages found in this ticket to jump to.",
            color=EMBED_COLOR_ERROR
        )
        await ctx.send(embed=embed, delete_after=10)

    @commands.command(name="notes")
    async def create_notes(self, ctx):
        """Creates a private thread for staff to talk in, only works in channel mode"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check if user is staff
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can create notes threads.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        try:
            # Create private thread for staff
            thread = await ctx.channel.create_thread(
                name=f"{SPROUTS_INFORMATION} Staff Notes - {ctx.channel.name}",
                type=discord.ChannelType.private_thread,
                reason="Staff notes thread created"
            )
            
            # Create initial message
            embed = discord.Embed(
                title=f"{SPROUTS_INFORMATION} Staff Notes",
                description="This is a private thread for staff discussion about this ticket.\n\n**Only staff members can see this thread.**",
                color=EMBED_COLOR_HIERARCHY
            )
            embed.add_field(
                name=f"{SPROUTS_INFORMATION} Usage Tips",
                value="• Discuss ticket details privately\n• Share internal notes\n• Coordinate response strategies",
                inline=False
            )
            embed.set_footer(text=f"Created by {ctx.author.display_name}")
            
            await thread.send(embed=embed)
            
            # Confirm creation
            confirm_embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Notes Thread Created",
                description=f"Private staff notes thread created: {thread.mention}",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.send(embed=confirm_embed, delete_after=10)
            
        except Exception as e:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Thread Creation Failed",
                description="Unable to create notes thread. Check bot permissions.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            logger.error(f"Failed to create notes thread: {e}")
    
    @commands.command(name="transcript")
    async def generate_transcript(self, ctx):
        """Generate a transcript of the ticket"""
        ticket_data = self.get_ticket_data(ctx.channel.id)
        if not ticket_data:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        try:
            from utils.transcript_generator import transcript_generator
            
            ticket_id = ticket_data['id']
            creator = ctx.guild.get_member(ticket_data['creator_id'])
            staff_id = ticket_data.get('claimed_by')
            staff = ctx.guild.get_member(staff_id) if staff_id else None
            
            # Generate transcript
            transcript_url, transcript_path = await transcript_generator.generate_transcript(
                channel=ctx.channel,
                ticket_id=str(ticket_id),
                creator=creator,
                staff=staff,
                reason=ticket_data.get('reason', 'No reason provided'),
                close_reason="Manual transcript generation"
            )
            
            if transcript_url:
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Transcript Generated",
                    description=f"[View Transcript]({transcript_url})",
                    color=EMBED_COLOR_NORMAL
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Generation Failed",
                    description="Failed to generate transcript. Please try again.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.send(embed=embed, delete_after=10)
                
        except Exception as e:
            logger.error(f"Error generating transcript: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description="An error occurred while generating the transcript.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
    
    @commands.command(name="tickets", aliases=["list"])
    async def list_tickets(self, ctx):
        """List all tickets in the guild"""
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can view the ticket list.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Get guild tickets
        guild_tickets = []
        for ticket_id, ticket_data in self.tickets_data.items():
            if ticket_data.get('guild_id') == ctx.guild.id and ticket_data.get('status') == 'open':
                guild_tickets.append((ticket_id, ticket_data))
        
        if not guild_tickets:
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} No Open Tickets",
                description="There are currently no open tickets in this server.",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Create ticket list embed
        embed = discord.Embed(
            title=f"{SPROUTS_INFORMATION} Open Tickets ({len(guild_tickets)})",
            color=EMBED_COLOR_NORMAL,
            timestamp=datetime.utcnow()
        )
        
        for ticket_id, ticket_data in guild_tickets[:25]:  # Limit to 25 for embed limits
            creator = ctx.guild.get_member(ticket_data['creator_id'])
            claimer = ctx.guild.get_member(ticket_data.get('claimed_by')) if ticket_data.get('claimed_by') else None
            
            field_value = f"**Creator:** {creator.mention if creator else 'Unknown'}\n"
            field_value += f"**Status:** {'Claimed' if claimer else 'Open'}\n"
            if claimer:
                field_value += f"**Claimed by:** {claimer.mention}\n"
            field_value += f"**Channel:** <#{ticket_data['channel_id']}>"
            
            embed.add_field(
                name=f"Ticket {ticket_id}",
                value=field_value,
                inline=True
            )
        
        if len(guild_tickets) > 25:
            embed.set_footer(text=f"Showing first 25 of {len(guild_tickets)} tickets")
        
        await ctx.send(embed=embed, delete_after=30)
    
    # ========== TICKET CONFIGURATION COMMANDS ==========
    
    @commands.group(name="ticketconfig", aliases=["tconfig"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def ticket_config(self, ctx):
        """Ticket system configuration commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title=f"{SPROUTS_INFORMATION} Ticket Configuration",
                description="Configure your server's ticket system settings.",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="Available Commands",
                value="`s.tconfig transcripts <#channel>` - Set transcript logging channel\n"
                      "`s.tconfig category <#category>` - Set ticket category\n"
                      "`s.tconfig staff <@role>` - Add staff role\n"
                      "`s.tconfig view` - View current settings",
                inline=False
            )
            
            embed.set_footer(text="SPROUTS Ticket System")
            await ctx.send(embed=embed)
    
    @ticket_config.command(name="transcripts")
    @commands.has_permissions(administrator=True)
    async def set_transcript_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel where transcripts are logged"""
        if not channel:
            embed = discord.Embed(
                description=f"**{SPROUTS_ERROR} Missing Channel**\n\nPlease mention a channel to set as transcript log.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Update guild settings
        guild_id = str(ctx.guild.id)
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {}
        
        self.guild_settings[guild_id]['transcript_channel'] = channel.id
        self.save_data()
        
        embed = discord.Embed(
            description=f"**{SPROUTS_CHECK} Transcript Channel Set**\n\nTranscripts will now be logged to {channel.mention}",
            color=EMBED_COLOR_NORMAL
        )
        embed.set_author(name="Ticket Configuration", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
    
    @ticket_config.command(name="staff")
    @commands.has_permissions(administrator=True)
    async def add_staff_role(self, ctx, role: discord.Role = None):
        """Add a staff role for ticket management"""
        if not role:
            embed = discord.Embed(
                description=f"**{SPROUTS_ERROR} Missing Role**\n\nPlease mention a role to add as staff.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Update guild settings
        guild_id = str(ctx.guild.id)
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {}
        if 'staff_roles' not in self.guild_settings[guild_id]:
            self.guild_settings[guild_id]['staff_roles'] = []
        
        if role.id in self.guild_settings[guild_id]['staff_roles']:
            embed = discord.Embed(
                description=f"**{SPROUTS_WARNING} Already Added**\n\n{role.mention} is already a staff role.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        self.guild_settings[guild_id]['staff_roles'].append(role.id)
        self.save_data()
        
        embed = discord.Embed(
            description=f"**{SPROUTS_CHECK} Staff Role Added**\n\n{role.mention} can now manage tickets.",
            color=EMBED_COLOR_NORMAL
        )
        embed.set_author(name="Ticket Configuration", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
    
    @ticket_config.command(name="view")
    @commands.has_permissions(administrator=True)
    async def view_config(self, ctx):
        """View current ticket configuration"""
        guild_id = str(ctx.guild.id)
        settings = self.guild_settings.get(guild_id, {})
        
        embed = discord.Embed(
            title=f"{SPROUTS_INFORMATION} Current Ticket Configuration",
            color=EMBED_COLOR_NORMAL,
            timestamp=datetime.utcnow()
        )
        
        # Transcript channel
        transcript_channel_id = settings.get('transcript_channel')
        if transcript_channel_id:
            transcript_channel = ctx.guild.get_channel(transcript_channel_id)
            transcript_text = transcript_channel.mention if transcript_channel else "Channel not found"
        else:
            transcript_text = "Not set"
        
        embed.add_field(
            name="Transcript Channel",
            value=transcript_text,
            inline=True
        )
        
        # Staff roles
        staff_roles = settings.get('staff_roles', [])
        if staff_roles:
            role_mentions = []
            for role_id in staff_roles:
                role = ctx.guild.get_role(role_id)
                if role:
                    role_mentions.append(role.mention)
            staff_text = "\n".join(role_mentions) if role_mentions else "Roles not found"
        else:
            staff_text = "None set"
        
        embed.add_field(
            name="Staff Roles",
            value=staff_text,
            inline=True
        )
        
        embed.set_footer(text="SPROUTS Ticket System")
        await ctx.send(embed=embed)

    # Panel Management Commands
    @commands.command(name="createpanel")
    @commands.has_permissions(manage_channels=True)
    async def create_panel(self, ctx, *, title: str = "Support Tickets"):
        """Create a ticket panel with button"""
        try:
            if not await self.is_staff(ctx.author, ctx.guild):
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Access Denied",
                    description="Only staff members can create ticket panels.",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url
                )
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Generate shorter random panel ID (8 characters: letters and numbers, mixed case)
            panel_id = ''.join(
                random.choices(string.ascii_letters + string.digits, k=8))

            # Create panel embed
            embed = discord.Embed(
                title=title,
                description="Click the button below to create a support ticket.\nOur staff will assist you as soon as possible!",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_footer(text=f"Panel ID: {panel_id}")
            embed.timestamp = discord.utils.utcnow()

            # Create panel view
            view = SproutsCreateTicketView(panel_id, self)
            panel_message = await ctx.send(embed=embed, view=view)

            # Store panel data
            guild_settings = self.get_guild_settings(ctx.guild.id)
            category_id = guild_settings.get('ticket_category_id')

            self.panels_data[panel_id] = {
                'guild_id': ctx.guild.id,
                'channel_id': ctx.channel.id,
                'message_id': panel_message.id,
                'title': title,
                'created_by': ctx.author.id,
                'created_at': datetime.utcnow().isoformat(),
                'category_id': category_id,
                'default_reason': 'Support Request'
            }
            self.save_data()

            # Confirmation message
            confirm_embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Panel Created",
                description=f"Ticket panel created successfully!\n\n**ID:** `{panel_id}`\n**Title:** {title}",
                color=EMBED_COLOR_NORMAL
            )
            confirm_embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            confirm_embed.timestamp = discord.utils.utcnow()
            # Send ephemeral confirmation that deletes after 10 seconds
            await ctx.reply(embed=confirm_embed, mention_author=False, delete_after=10)

        except Exception as e:
            logger.error(f"Error creating panel: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description=f"An error occurred while creating the panel: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="listpanels")
    @commands.has_permissions(manage_channels=True)
    async def list_panels(self, ctx):
        """List all ticket panels in the server"""
        try:
            if not await self.is_staff(ctx.author, ctx.guild):
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Access Denied",
                    description="Only staff members can list ticket panels.",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url
                )
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Filter panels for this guild and check if messages still exist
            guild_panels = {
                pid: pdata
                for pid, pdata in self.panels_data.items()
                if pdata.get('guild_id') == ctx.guild.id
            }

            # Check which panels still have their messages and are active
            active_panels = {}
            panels_to_remove = []

            for panel_id, panel_data in guild_panels.items():
                try:
                    channel = ctx.guild.get_channel(panel_data.get('channel_id'))
                    if channel:
                        # Try to fetch the message to see if it still exists
                        message = await channel.fetch_message(panel_data.get('message_id'))
                        if message:
                            active_panels[panel_id] = panel_data
                        else:
                            panels_to_remove.append(panel_id)
                    else:
                        panels_to_remove.append(panel_id)
                except (discord.NotFound, discord.Forbidden, Exception):
                    # Message doesn't exist or can't access it
                    panels_to_remove.append(panel_id)

            # Clean up panels with deleted messages from database
            if panels_to_remove:
                for panel_id in panels_to_remove:
                    if panel_id in self.panels_data:
                        del self.panels_data[panel_id]
                self.save_data()

            if not active_panels:
                embed = discord.Embed(
                    title=f"{SPROUTS_INFORMATION} No Active Panels",
                    description="No active ticket panels found in this server.\n\nUse `s.createpanel` to create a new panel.",
                    color=EMBED_COLOR_NORMAL
                )
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url
                )
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Create embed with active panels
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Active Ticket Panels",
                description=f"Found **{len(active_panels)}** active panel{'s' if len(active_panels) != 1 else ''} in this server:",
                color=EMBED_COLOR_NORMAL
            )

            # Add each panel as a field
            for panel_id, panel_data in active_panels.items():
                channel = ctx.guild.get_channel(panel_data.get('channel_id'))
                creator = ctx.guild.get_member(panel_data.get('created_by'))
                created_date = datetime.fromisoformat(
                    panel_data.get('created_at')).strftime('%Y-%m-%d')

                channel_text = channel.mention if channel else "*Channel Deleted*"
                creator_text = creator.display_name if creator else "*Unknown User*"

                embed.add_field(
                    name=f"**{panel_data.get('title', 'Untitled Panel')}**",
                    value=f"**ID:** `{panel_id}`\n"
                    f"**Channel:** {channel_text}\n"
                    f"**Created by:** {creator_text}\n"
                    f"**Created:** {created_date}",
                    inline=True
                )

            # Clean up formatting if needed
            if len(active_panels) % 3 != 0:
                # Add invisible field to align layout
                embed.add_field(name="\u200b", value="\u200b", inline=True)

            embed.set_footer(
                text=f"Use 's.delpanel <panel_id>' to delete a panel • Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()

            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error listing panels: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description=f"An error occurred while listing panels: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="delpanel")
    @commands.has_permissions(manage_channels=True)
    async def delete_panel(self, ctx, panel_id: str):
        """Delete a ticket panel"""
        try:
            if not await self.is_staff(ctx.author, ctx.guild):
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Access Denied",
                    description="Only staff members can delete ticket panels.",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url
                )
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Check if panel exists
            if panel_id not in self.panels_data:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Panel Not Found",
                    description=f"No panel found with ID: `{panel_id}`\n\nUse `s.listpanels` to see all available panels.",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url
                )
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            panel_data = self.panels_data[panel_id]

            # Check if panel belongs to this guild
            if panel_data.get('guild_id') != ctx.guild.id:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Access Denied",
                    description="You can only delete panels from this server.",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url
                )
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Try to delete the original message and track status
            message_status = None
            try:
                channel = ctx.guild.get_channel(panel_data.get('channel_id'))
                if not channel:
                    message_status = f"{SPROUTS_ERROR} Channel not found"
                else:
                    try:
                        message = await channel.fetch_message(panel_data.get('message_id'))
                        await message.delete()
                        message_status = f"{SPROUTS_CHECK} Panel message deleted"
                    except discord.NotFound:
                        message_status = f"{SPROUTS_WARNING} Panel message already deleted"
                    except discord.Forbidden:
                        message_status = f"{SPROUTS_ERROR} No permission to delete message"
                    except Exception as e:
                        message_status = f"{SPROUTS_ERROR} Error deleting message: {str(e)}"
            except Exception as e:
                message_status = f"{SPROUTS_ERROR} Error accessing channel: {str(e)}"

            # Remove from data
            del self.panels_data[panel_id]
            self.save_data()

            # Success confirmation
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Panel Deleted",
                description=f"Panel `{panel_id}` has been successfully deleted.\n\n**Title:** {panel_data.get('title', 'Unknown')}\n**Status:** {message_status}",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error deleting panel: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description=f"An error occurred while deleting the panel: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    """Setup the GitHub Discord-Tickets system"""
    cog = SproutsTicketSystemExtended(bot)
    await bot.add_cog(cog)
    
    # Add persistent views
    bot.add_view(SproutsTicketView(cog))
    bot.add_view(SproutsCreateTicketView("persistent", cog))
    
    logger.info("GitHub Discord-Tickets system loaded successfully")