"""
Discord Bot Ticket System (Text Commands Only)
A comprehensive ticket system with text commands for staff management
"""

import discord
from discord.ext import commands
import logging
import json
import os
import asyncio
import io
from datetime import datetime, timedelta
from typing import Optional, List
import random
import string
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from src.emojis import SPROUTS_ERROR, SPROUTS_CHECK, SPROUTS_WARNING

logger = logging.getLogger(__name__)

# Ticket data storage
TICKETS_FILE = "config/tickets_data.json"
PANELS_FILE = "data/panels_data.json"


class TicketButtons(discord.ui.View):
    """Persistent view for ticket channel buttons"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket",
                       style=discord.ButtonStyle.danger,
                       custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
        """Close ticket button handler"""
        try:
            # Get the ticket cog
            ticket_cog = interaction.client.get_cog('TicketSystem')
            if not ticket_cog:
                await interaction.response.send_message(
                    "Ticket system not available", ephemeral=True)
                return

            # Check if user is staff or ticket owner
            if not ticket_cog.is_staff(interaction.user):
                # Check if they're the ticket owner
                ticket_id = interaction.channel.id
                ticket_data = ticket_cog.tickets_data.get(str(ticket_id))
                if not ticket_data or ticket_data.get(
                        'creator_id') != interaction.user.id:
                    await interaction.response.send_message(
                        "Only staff or the ticket owner can close this ticket",
                        ephemeral=True)
                    return

            # Show confirmation dialog instead of directly closing
            embed = discord.Embed(
                title="Close Ticket Confirmation",
                description=
                f"Are you sure you want to close this ticket?\n\n**Reason:** No reason provided\n**Channel:** {interaction.channel.mention}\n\n**WARNING: This action cannot be undone!**\n**This confirmation will timeout in 30 seconds**",
                color=EMBED_COLOR_NORMAL)

            # Create context for the confirmation
            ctx = await interaction.client.get_context(interaction.message)
            ctx.author = interaction.user
            ctx.channel = interaction.channel

            view = CloseConfirmation(ticket_cog, ctx, "No reason provided")
            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error in close ticket button: {e}")
            await interaction.response.send_message("Error closing ticket",
                                                    ephemeral=True)

    @discord.ui.button(label="Claim Ticket",
                       style=discord.ButtonStyle.secondary,
                       custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
        """Claim ticket button handler"""
        try:
            # Get the ticket cog
            ticket_cog = interaction.client.get_cog('TicketSystem')
            if not ticket_cog:
                await interaction.response.send_message(
                    "Ticket system not available", ephemeral=True)
                return

            # Check if user is staff
            if not ticket_cog.is_staff(interaction.user):
                await interaction.response.send_message(
                    "Only staff can claim tickets", ephemeral=True)
                return

            # Use the existing claim logic
            ctx = await interaction.client.get_context(interaction.message)
            ctx.author = interaction.user
            ctx.channel = interaction.channel

            await ticket_cog.claim_ticket(ctx)
            await interaction.response.defer()

        except Exception as e:
            logger.error(f"Error in claim ticket button: {e}")
            await interaction.response.send_message("Error claiming ticket",
                                                    ephemeral=True)


class CloseConfirmation(discord.ui.View):
    """Confirmation view for closing tickets"""

    def __init__(self, ticket_cog, ctx, reason):
        super().__init__(timeout=30)
        self.ticket_cog = ticket_cog
        self.ctx = ctx
        self.reason = reason
        self.confirmed = False

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.danger)
    async def confirm_close(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        """Confirm ticket close"""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "Only the person who initiated the close can confirm.",
                ephemeral=True)
            return

        self.confirmed = True

        # Start countdown with initial response
        await interaction.response.edit_message(
            content="**Closing ticket in 5 seconds...**",
            view=None,
            embed=None)

        # Live countdown from 4 to 1 (we already showed 5)
        for seconds_left in range(4, 0, -1):
            await asyncio.sleep(1)
            await interaction.edit_original_response(
                content=
                f"**Closing ticket in {seconds_left} second{'s' if seconds_left != 1 else ''}...**"
            )

        # Final countdown and close
        await asyncio.sleep(1)
        await interaction.edit_original_response(
            content="**Closing ticket now...**")
        await self.ticket_cog._process_ticket_close(self.ctx, self.reason)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_close(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
        """Cancel ticket close"""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "Only the person who initiated the close can cancel.",
                ephemeral=True)
            return

        embed = discord.Embed(
            title="{SPROUTS_CHECK} Ticket Close Cancelled",
            description="The ticket close has been cancelled.",
            color=EMBED_COLOR_NORMAL)
        await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self):
        """Handle timeout"""
        if not self.confirmed:
            embed = discord.Embed(
                title="Close Confirmation Timed Out",
                description=
                "The ticket close confirmation has timed out. Please run the close command again if you want to close this ticket.",
                color=EMBED_COLOR_ERROR)
            try:
                await self.ctx.edit_last_response(embed=embed, view=None)
            except:
                pass


class StaffPanel(discord.ui.View):
    """Staff panel with advanced ticket management"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Staff Panel",
                       style=discord.ButtonStyle.primary,
                       custom_id="staff_panel")
    async def show_staff_panel(self, interaction: discord.Interaction,
                               button: discord.ui.Button):
        """Show staff panel with ticket management options"""
        try:
            # Get the ticket cog
            ticket_cog = interaction.client.get_cog('TicketSystem')
            if not ticket_cog:
                await interaction.response.send_message(
                    "Ticket system not available", ephemeral=True)
                return

            # Check if user is staff
            if not ticket_cog.is_staff(interaction.user):
                await interaction.response.send_message(
                    "Only staff can access the staff panel", ephemeral=True)
                return

            embed = discord.Embed(
                title="Staff Panel",
                description="Advanced ticket management commands:",
                color=EMBED_COLOR_NORMAL)

            embed.add_field(name="Basic Commands",
                            value="`{ctx.prefix}add @user` - Add member to ticket\n"
                            "`{ctx.prefix}remove @user` - Remove member from ticket\n"
                            "`{ctx.prefix}topic <topic>` - Set ticket topic\n"
                            "`s{ctx.prefix}rename <name>` - Rename ticket channel",
                            inline=True)

            embed.add_field(name="Advanced Commands",
                            value="`{ctx.prefix}move <category>` - Move to category\n"
                            "`{ctx.prefix}priority <high/medium/low>` - Set priority\n"
                            "`{ctx.prefix}transfer @staff` - Transfer to staff",
                            inline=True)

            embed.add_field(name="Quick Actions",
                            value="`{ctx.prefix}release` - Release claimed ticket\n"
                            "`{ctx.prefix}forceclose` - Force close ticket\n"
                            "`{ctx.prefix}listtickets` - List all open tickets",
                            inline=False)

            embed.add_field(
                name="Panel Management",
                value="`{ctx.prefix}panel <title>` - Create ticket panel\n"
                "`{ctx.prefix}panels` - List all panels\n"
                "`{ctx.prefix}delpanel <panel_id>` - Deletes an active panel",
                inline=False)

            embed.set_footer(text=f"Staff: {interaction.user.display_name}",
                             icon_url=interaction.user.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()

            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)

        except Exception as e:
            logger.error(f"Error in staff panel: {e}")
            await interaction.response.send_message(
                "Error accessing staff panel", ephemeral=True)


class TicketPanelView(discord.ui.View):
    """View for ticket panel reactions"""

    def __init__(self, panel_id: str):
        super().__init__(timeout=None)
        self.panel_id = panel_id

    @discord.ui.button(label="Create Ticket",
                       style=discord.ButtonStyle.primary,
                       custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        """Create ticket from panel button"""
        try:
            ticket_cog = interaction.client.get_cog('TicketSystem')
            if not ticket_cog:
                await interaction.response.send_message(
                    "Ticket system not available", ephemeral=True)
                return

            # Get panel data
            panel_data = ticket_cog.panels_data.get(self.panel_id)
            if not panel_data:
                await interaction.response.send_message(
                    "Panel configuration not found", ephemeral=True)
                return

            # Create ticket using panel data
            await ticket_cog.create_ticket_from_panel(interaction, panel_data)

        except Exception as e:
            logger.error(f"Error creating ticket from panel: {e}")
            await interaction.response.send_message("Error creating ticket",
                                                    ephemeral=True)


class TicketSetupSelect(discord.ui.Select):
    """Dropdown menu for ticket system configuration"""

    def __init__(self, ctx, ticket_cog):
        self.ctx = ctx
        self.ticket_cog = ticket_cog

        options = [
            discord.SelectOption(
                label="Set Log Channel",
                description="Configure ticket event logging",
                value="log_channel"),
            discord.SelectOption(
                label="Add Staff Role",
                description="Grant ticket access to roles",
                value="staff_role"),
            discord.SelectOption(
                label="Set Category",
                description="Organize tickets in category",
                value="category"),
            discord.SelectOption(
                label="Naming Style",
                description="Numbers or discord usernames",
                value="naming"),
            discord.SelectOption(label="Embed Settings",
                                 description="Customize ticket messages",
                                 value="embed"),
            discord.SelectOption(label="Remove Log Channel",
                                 description="Clear logging configuration",
                                 value="remove_log"),
            discord.SelectOption(label="Remove All Staff Roles",
                                 description="Clear all staff assignments",
                                 value="remove_roles"),
            discord.SelectOption(label="Remove Category",
                                 description="Reset to general channel",
                                 value="remove_category"),
            discord.SelectOption(label="Cleanup Orphaned Tickets",
                                 description="Remove orphaned data",
                                 value="cleanup")
        ]

        super().__init__(placeholder="Choose a configuration option...",
                         options=options,
                         min_values=1,
                         max_values=1,
                         row=0)

    async def callback(self, interaction: discord.Interaction):
        """Handle setup menu selection"""
        try:
            await interaction.response.defer()

            if self.values[0] == "log_channel":
                await self.setup_log_channel(interaction)
            elif self.values[0] == "staff_role":
                await self.setup_staff_role(interaction)
            elif self.values[0] == "category":
                await self.setup_category(interaction)
            elif self.values[0] == "naming":
                await self.setup_naming(interaction)
            elif self.values[0] == "embed":
                await self.setup_embeds(interaction)
            elif self.values[0] == "remove_log":
                await self.remove_log_channel(interaction)
            elif self.values[0] == "remove_roles":
                await self.remove_staff_roles(interaction)
            elif self.values[0] == "remove_category":
                await self.remove_category(interaction)
            elif self.values[0] == "cleanup":
                await self.cleanup_data(interaction)

        except Exception as e:
            logger.error(f"Error in setup callback: {e}")

    async def setup_log_channel(self, interaction):
        """Setup log channel selection"""
        channels = [
            ch for ch in self.ctx.guild.text_channels
            if ch.permissions_for(self.ctx.guild.me).send_messages
        ]

        if not channels:
            embed = discord.Embed(
                title="{SPROUTS_ERROR} No Channels",
                description="No available text channels found",
                color=EMBED_COLOR_ERROR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        view = ChannelSelectView(self.ctx, self.ticket_cog, channels[:25])
        embed = discord.Embed(
            title="Select Log Channel",
            description=
            "Choose the channel where ticket events will be logged:",
            color=EMBED_COLOR_NORMAL)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    async def setup_staff_role(self, interaction):
        """Setup staff role selection"""
        roles = [
            role for role in self.ctx.guild.roles
            if role.name != "@everyone" and not role.managed
        ]

        if not roles:
            embed = discord.Embed(title="No Roles",
                                  description="No available roles found",
                                  color=EMBED_COLOR_ERROR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        view = RoleSelectView(self.ctx, self.ticket_cog, roles[:25])
        embed = discord.Embed(
            title="Select Staff Role",
            description=
            "Choose a role that should have access to manage tickets:",
            color=EMBED_COLOR_NORMAL)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    async def setup_category(self, interaction):
        """Setup category selection"""
        categories = self.ctx.guild.categories

        if not categories:
            embed = discord.Embed(
                title="No Categories",
                description="No categories found. Create a category first.",
                color=EMBED_COLOR_ERROR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        view = CategorySelectView(self.ctx, self.ticket_cog, categories[:25])
        embed = discord.Embed(
            title="Select Category",
            description=
            "Choose the category where ticket channels will be created:",
            color=EMBED_COLOR_NORMAL)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    async def setup_naming(self, interaction):
        """Setup naming style selection"""
        view = NamingSelectView(self.ctx, self.ticket_cog)
        embed = discord.Embed(
            title="Choose Naming Style",
            description="Select how ticket channels should be named:",
            color=EMBED_COLOR_NORMAL)
        embed.add_field(
            name="Options",
            value=
            "**Numbers:** ticket-001, ticket-002, etc.\n**Discord:** ticket-username",
            inline=False)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    async def setup_embeds(self, interaction):
        """Setup embed customization"""
        embed = discord.Embed(
            title="Embed Customization",
            description=
            "Ticket embeds can be customized using the embed builder commands:",
            color=EMBED_COLOR_NORMAL)

        embed.add_field(
            name="Available Commands",
            value="`{ctx.prefix}embedcreate` - Create custom welcome embed\n"
            "`{ctx.prefix}embedlist` - List saved embeds\n"
            "`{ctx.prefix}ticketuseembed <name>` - Use saved embed for tickets",
            inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    async def cleanup_data(self, interaction):
        """Cleanup orphaned ticket data"""
        cleaned_count = await self.ticket_cog.cleanup_orphaned_tickets(
            self.ctx.guild.id)

        if cleaned_count > 0:
            embed = discord.Embed(
                title="Cleanup Complete",
                description=f"Cleaned up {cleaned_count} orphaned ticket(s)",
                color=EMBED_COLOR_NORMAL)
        else:
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} All Clean",
                description=
                "No orphaned tickets found - all ticket data is clean",
                color=EMBED_COLOR_NORMAL)

        await interaction.followup.send(embed=embed, ephemeral=True)

    async def remove_log_channel(self, interaction):
        """Remove log channel setting"""
        current_settings = self.ticket_cog.get_guild_settings(self.ctx.guild.id)
        if not current_settings.get('log_channel_id'):
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} No Log Channel",
                description="No log channel is currently set.",
                color=EMBED_COLOR_ERROR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Remove the setting
        guild_settings = {'log_channel_id': None}
        self.ticket_cog.update_guild_settings(self.ctx.guild.id, guild_settings)
        
        # Update main menu and send confirmation
        updated_embed = self.ticket_cog.create_setup_embed(self.ctx)
        main_view = TicketSetupView(self.ctx, self.ticket_cog)
        
        confirm_embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Log Channel Removed",
            description="Log channel setting has been removed.",
            color=EMBED_COLOR_NORMAL)
        
        await interaction.edit_original_response(embed=updated_embed, view=main_view)
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

    async def remove_staff_roles(self, interaction):
        """Remove all staff roles"""
        current_settings = self.ticket_cog.get_guild_settings(self.ctx.guild.id)
        if not current_settings.get('staff_role_ids'):
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} No Staff Roles",
                description="No staff roles are currently set.",
                color=EMBED_COLOR_ERROR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Remove all staff roles
        guild_settings = {'staff_role_ids': []}
        self.ticket_cog.update_guild_settings(self.ctx.guild.id, guild_settings)
        
        # Update main menu and send confirmation
        updated_embed = self.ticket_cog.create_setup_embed(self.ctx)
        main_view = TicketSetupView(self.ctx, self.ticket_cog)
        
        confirm_embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Staff Roles Removed",
            description="All staff role assignments have been removed.",
            color=EMBED_COLOR_NORMAL)
        
        await interaction.edit_original_response(embed=updated_embed, view=main_view)
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

    async def remove_category(self, interaction):
        """Remove category setting"""
        current_settings = self.ticket_cog.get_guild_settings(self.ctx.guild.id)
        if not current_settings.get('ticket_category_id'):
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} No Category",
                description="No ticket category is currently set.",
                color=EMBED_COLOR_ERROR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Remove the setting
        guild_settings = {'ticket_category_id': None}
        self.ticket_cog.update_guild_settings(self.ctx.guild.id, guild_settings)
        
        # Update main menu and send confirmation
        updated_embed = self.ticket_cog.create_setup_embed(self.ctx)
        main_view = TicketSetupView(self.ctx, self.ticket_cog)
        
        confirm_embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Category Removed",
            description="Ticket category setting has been removed.\nTickets will now be created in the general channel.",
            color=EMBED_COLOR_NORMAL)
        
        await interaction.edit_original_response(embed=updated_embed, view=main_view)
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)


class TicketSetupView(discord.ui.View):
    """View for ticket system setup"""

    def __init__(self, ctx, ticket_cog):
        super().__init__(timeout=300)
        self.add_item(TicketSetupSelect(ctx, ticket_cog))


class ChannelSelectView(discord.ui.View):
    """View for selecting log channel"""

    def __init__(self, ctx, ticket_cog, channels):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.ticket_cog = ticket_cog

        select = discord.ui.Select(
            placeholder="Choose a log channel...",
            options=[
                discord.SelectOption(
                    label=f"#{channel.name}",
                    description=
                    f"Category: {channel.category.name if channel.category else 'None'}",
                    value=str(channel.id)) for channel in channels
            ])
        select.callback = self.channel_callback
        self.add_item(select)

    async def channel_callback(self, interaction: discord.Interaction):
        """Handle channel selection"""
        try:
            channel_id = int(interaction.data['values'][0])
            channel = self.ctx.guild.get_channel(channel_id)

            guild_settings = {'log_channel_id': channel_id}
            self.ticket_cog.update_guild_settings(self.ctx.guild.id,
                                                  guild_settings)

            # Dismiss this menu with a confirmation
            confirm_embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Channel Set",
                description=f"Ticket logging channel set to {channel.mention}",
                color=EMBED_COLOR_NORMAL)
            await interaction.response.edit_message(embed=confirm_embed, view=None)

        except Exception as e:
            logger.error(f"Error setting log channel: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description="Failed to set the logging channel.",
                color=EMBED_COLOR_ERROR)
            await interaction.response.send_message(embed=error_embed,
                                                    ephemeral=True)


class RoleSelectView(discord.ui.View):
    """View for selecting staff roles"""

    def __init__(self, ctx, ticket_cog, roles):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.ticket_cog = ticket_cog

        select = discord.ui.Select(
            placeholder="Choose a staff role...",
            options=[
                discord.SelectOption(
                    label=f"@{role.name}",
                    description=f"Members: {len(role.members)}",
                    value=str(role.id)) for role in roles
            ])
        select.callback = self.role_callback
        self.add_item(select)

    async def role_callback(self, interaction: discord.Interaction):
        """Handle role selection"""
        try:
            role_id = int(interaction.data['values'][0])
            role = self.ctx.guild.get_role(role_id)

            guild_settings = self.ticket_cog.get_guild_settings(
                self.ctx.guild.id)

            if role_id not in guild_settings['staff_role_ids']:
                guild_settings['staff_role_ids'].append(role_id)
                self.ticket_cog.update_guild_settings(self.ctx.guild.id,
                                                      guild_settings)
                confirm_embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Staff Role Added",
                    description=f"{role.mention} added as staff role",
                    color=EMBED_COLOR_NORMAL)
            else:
                confirm_embed = discord.Embed(
                    title="Already Added",
                    description=f"{role.mention} is already a staff role",
                    color=EMBED_COLOR_ERROR)
            
            # Dismiss this menu with a confirmation
            await interaction.response.edit_message(embed=confirm_embed, view=None)

        except Exception as e:
            logger.error(f"Error adding staff role: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description="Failed to add the staff role.",
                color=EMBED_COLOR_ERROR)
            await interaction.response.send_message(embed=error_embed,
                                                    ephemeral=True)


class CategorySelectView(discord.ui.View):
    """View for selecting ticket category"""

    def __init__(self, ctx, ticket_cog, categories):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.ticket_cog = ticket_cog

        select = discord.ui.Select(
            placeholder="Choose a category...",
            options=[
                discord.SelectOption(
                    label=category.name,
                    description=f"Channels: {len(category.channels)}",
                    value=str(category.id)) for category in categories
            ])
        select.callback = self.category_callback
        self.add_item(select)

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        try:
            category_id = int(interaction.data['values'][0])
            category = self.ctx.guild.get_channel(category_id)

            guild_settings = {'ticket_category_id': category_id}
            self.ticket_cog.update_guild_settings(self.ctx.guild.id,
                                                  guild_settings)

            # Dismiss this menu with a confirmation
            confirm_embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Category Set",
                description=f"Ticket category set to **{category.name}**",
                color=EMBED_COLOR_NORMAL)
            await interaction.response.edit_message(embed=confirm_embed, view=None)

        except Exception as e:
            logger.error(f"Error setting category: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description="Failed to set the ticket category.",
                color=EMBED_COLOR_ERROR)
            await interaction.response.send_message(embed=error_embed,
                                                    ephemeral=True)


class NamingSelectView(discord.ui.View):
    """View for selecting naming style"""

    def __init__(self, ctx, ticket_cog):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.ticket_cog = ticket_cog

        select = discord.ui.Select(
            placeholder="Choose naming style...",
            options=[
                discord.SelectOption(
                    label="Numbers",
                    description="ticket-001, ticket-002, etc.",
                    value="numbers",
                ),
                discord.SelectOption(
                    label="Discord Username",
                    description="ticket-username",
                    value="discord_tag",
                )
            ])
        select.callback = self.naming_callback
        self.add_item(select)

    async def naming_callback(self, interaction: discord.Interaction):
        """Handle naming style selection"""
        try:
            naming_style = interaction.data['values'][0]

            guild_settings = {'naming_style': naming_style}
            self.ticket_cog.update_guild_settings(self.ctx.guild.id,
                                                  guild_settings)

            # Update the main embed with new configuration
            updated_embed = self.ticket_cog.create_setup_embed(self.ctx)
            main_view = TicketSetupView(self.ctx, self.ticket_cog)

            style_name = "Numbers" if naming_style == "numbers" else "Discord Username"
            example = "ticket-001" if naming_style == "numbers" else "ticket-username"

            # Dismiss this menu with a confirmation
            confirm_embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Naming Style Set",
                description=f"Ticket naming style set to **{style_name}**\nExample: {example}",
                color=EMBED_COLOR_NORMAL)
            await interaction.response.edit_message(embed=confirm_embed, view=None)

        except Exception as e:
            logger.error(f"Error setting naming style: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description="Failed to set the naming style.",
                color=EMBED_COLOR_ERROR)
            await interaction.response.send_message(embed=error_embed,
                                                    ephemeral=True)


class TicketData:
    """Simple file-based data storage for tickets"""

    @staticmethod
    def load_tickets():
        """Load tickets from file"""
        try:
            if os.path.exists(TICKETS_FILE):
                with open(TICKETS_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tickets: {e}")
        return {}

    @staticmethod
    def save_tickets(tickets_data):
        """Save tickets to file"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(TICKETS_FILE, 'w') as f:
                json.dump(tickets_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tickets: {e}")


class PanelData:
    """Simple file-based data storage for ticket panels"""

    @staticmethod
    def load_panels():
        """Load panels from file"""
        try:
            if os.path.exists(PANELS_FILE):
                with open(PANELS_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading panels: {e}")
        return {}

    @staticmethod
    def save_panels(panels_data):
        """Save panels to file"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(PANELS_FILE, 'w') as f:
                json.dump(panels_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving panels: {e}")


class TicketSystem(commands.Cog):
    """Complete ticket system for server support management. Create ticket panels, manage staff roles, handle user tickets with claiming, priorities, transcripts, and comprehensive moderation tools. Supports multiple ticket categories, staff permissions, automatic logging, and detailed ticket management features."""

    def __init__(self, bot):
        self.bot = bot
        self.tickets_data = TicketData.load_tickets()
        self.panels_data = PanelData.load_panels()
        self.ticket_category_id = None
        self.staff_role_ids = []
        self.ticket_settings = self.load_ticket_settings()
        self.transcript_channels = {
        }  # guild_id: channel_id for transcript logging

    async def auto_delete_message(self, message, delay: int = 30):
        """Auto-delete a message after specified delay (in seconds)"""
        try:
            await asyncio.sleep(delay)
            await message.delete()
        except:
            pass  # Message might already be deleted or we don't have permissions

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Handle when a ticket channel is manually deleted"""
        try:
            # Check if the deleted channel was a ticket
            ticket_to_remove = None
            for ticket_id, ticket_data in self.tickets_data.items():
                if ticket_data.get('channel_id') == channel.id:
                    ticket_to_remove = ticket_id
                    break

            if ticket_to_remove:
                # Remove the ticket from data
                del self.tickets_data[ticket_to_remove]
                TicketData.save_tickets(self.tickets_data)
                logger.info(
                    f"Automatically cleaned up deleted ticket channel: {channel.name} ({channel.id})"
                )

        except Exception as e:
            logger.error(f"Error handling deleted ticket channel: {e}")

    async def cleanup_orphaned_tickets(self, guild_id: int = None):
        """Clean up tickets where channels no longer exist"""
        try:
            tickets_to_remove = []

            for ticket_id, ticket_data in self.tickets_data.items():
                # If guild_id specified, only check that guild's tickets
                if guild_id and ticket_data.get('guild_id') != guild_id:
                    continue

                channel_id = ticket_data.get('channel_id')
                if channel_id:
                    ticket_channel = self.bot.get_channel(channel_id)
                    if not ticket_channel:
                        tickets_to_remove.append(ticket_id)
                        logger.info(
                            f"Found orphaned ticket {ticket_id} - channel {channel_id} no longer exists"
                        )

            # Remove orphaned tickets
            for ticket_id in tickets_to_remove:
                del self.tickets_data[ticket_id]

            if tickets_to_remove:
                TicketData.save_tickets(self.tickets_data)
                logger.info(
                    f"Cleaned up {len(tickets_to_remove)} orphaned tickets")

            return len(tickets_to_remove)

        except Exception as e:
            logger.error(f"Error cleaning up orphaned tickets: {e}")
            return 0

    def load_ticket_settings(self):
        """Load ticket system settings (per-guild)"""
        try:
            if os.path.exists("src/data/ticket_settings.json"):
                with open("src/data/ticket_settings.json", 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading ticket settings: {e}")
        return {}

    def save_ticket_settings(self):
        """Save ticket system settings (per-guild)"""
        try:
            os.makedirs("data", exist_ok=True)
            with open("src/data/ticket_settings.json", 'w') as f:
                json.dump(self.ticket_settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving ticket settings: {e}")

    def get_guild_settings(self, guild_id: int) -> dict:
        """Get ticket settings for a specific guild"""
        guild_key = str(guild_id)
        if guild_key not in self.ticket_settings:
            # Create default settings for this guild
            self.ticket_settings[guild_key] = {
                'log_channel_id': None,
                'staff_role_ids': [],
                'ticket_category_id': None,
                'naming_style': 'numbers',  # 'numbers' or 'discord_tag'
                'embed_title': 'Support Ticket',
                'embed_description':
                'Thank you for creating a ticket! Please describe your issue and a staff member will assist you shortly.',
                'embed_color': EMBED_COLOR_NORMAL,
                'embed_author_name': None,
                'embed_author_icon': None,
                'max_tickets_per_user': 10,  # Maximum open tickets per user
                'use_saved_embed': False,
                'saved_embed_name': None
            }
            self.save_ticket_settings()
        return self.ticket_settings[guild_key]

    def update_guild_settings(self, guild_id: int, settings: dict):
        """Update ticket settings for a specific guild"""
        guild_key = str(guild_id)
        if guild_key not in self.ticket_settings:
            self.ticket_settings[guild_key] = {}
        self.ticket_settings[guild_key].update(settings)
        self.save_ticket_settings()

    async def get_or_create_transcript_channel(self, guild):
        """Get existing transcript channel or create new one"""
        try:
            # Check if we have a stored channel for this guild
            if guild.id in self.transcript_channels:
                channel = self.bot.get_channel(
                    self.transcript_channels[guild.id])
                if channel:  # Channel still exists
                    return channel

            # Look for existing transcript channel
            for channel in guild.text_channels:
                if channel.name == 'ticket-transcripts':
                    self.transcript_channels[guild.id] = channel.id
                    return channel

            # Create new transcript channel
            overwrites = {
                guild.default_role:
                discord.PermissionOverwrite(read_messages=False),
                guild.me:
                discord.PermissionOverwrite(read_messages=True,
                                            send_messages=True,
                                            manage_messages=True)
            }

            # Add staff roles if configured
            settings = self.get_guild_settings(guild.id)
            staff_role_ids = settings.get('staff_role_ids', [])
            for role_id in staff_role_ids:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True)

            channel = await guild.create_text_channel(
                'ticket-transcripts',
                overwrites=overwrites,
                topic='Closed ticket transcripts are automatically posted here',
                reason='Auto-created for ticket transcript logging')

            self.transcript_channels[guild.id] = channel.id
            logger.info(
                f"Created transcript logging channel for guild {guild.name} ({guild.id})"
            )
            return channel

        except Exception as e:
            logger.error(
                f"Error creating transcript channel for guild {guild.id}: {e}")
            return None

    def set_transcript_channel(self, guild_id: int, channel_id: int):
        """Set transcript logging channel for a guild"""
        self.transcript_channels[guild_id] = channel_id

    def get_transcript_channel(self, guild_id: int):
        """Get transcript logging channel for a guild"""
        return self.transcript_channels.get(guild_id, "Not set")

    def is_staff(self, member: discord.Member) -> bool:
        """Check if user is staff"""
        if not isinstance(member, discord.Member):
            return False
        guild_settings = self.get_guild_settings(member.guild.id)
        staff_roles = guild_settings.get('staff_role_ids', [])
        return any(role.id in staff_roles for role in
                   member.roles) or member.guild_permissions.manage_channels

    def count_user_tickets(self, guild_id: int, user_id: int) -> int:
        """Count how many open tickets a user has in this guild"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return 0

            user_ticket_count = 0
            guild_settings = self.get_guild_settings(guild_id)
            category_id = guild_settings.get('ticket_category_id')

            if category_id:
                category = guild.get_channel(category_id)
                if category and isinstance(category, discord.CategoryChannel):
                    for channel in category.text_channels:
                        # Check if channel is a ticket for this user
                        if channel.topic and str(user_id) in channel.topic:
                            user_ticket_count += 1
                        elif f"ticket-{user_id}" in channel.name:
                            user_ticket_count += 1
                        elif channel.name.startswith("ticket-") and str(
                                user_id) in channel.name:
                            user_ticket_count += 1

            return user_ticket_count
        except Exception as e:
            logger.error(f"Error counting user tickets: {e}")
            return 0

    async def log_ticket_action(self,
                                action: str,
                                author: discord.Member,
                                guild: discord.Guild,
                                ticket_id: str,
                                reason: str,
                                channel: discord.TextChannel = None):
        """Log ticket actions to the logging system"""
        try:
            # Get logging channel from guild settings
            guild_settings = self.get_guild_settings(guild.id)
            log_channel_id = guild_settings.get('log_channel_id')

            if not log_channel_id:
                return  # No logging channel configured

            log_channel = self.bot.get_channel(int(log_channel_id))
            if not log_channel:
                return  # Channel not found

            # Create log embed
            action_colors = {
                "new": EMBED_COLOR_NORMAL,
                "close": 0xffa500,  # Orange
                "force-close": EMBED_COLOR_ERROR
            }

            action_emojis = {"new": "", "close": "", "force-close": ""}

            embed = discord.Embed(title=f"Ticket {action.title()}",
                                  color=action_colors.get(
                                      action, EMBED_COLOR_NORMAL),
                                  timestamp=discord.utils.utcnow())

            embed.add_field(name="Ticket ID",
                            value=f"#{ticket_id}",
                            inline=True)

            embed.add_field(name="Action By",
                            value=f"{author.mention}\n(`{author.id}`)",
                            inline=True)

            embed.add_field(name="Server",
                            value=f"{guild.name}\n(`{guild.id}`)",
                            inline=True)

            embed.add_field(name="Reason",
                            value=reason[:100] +
                            "..." if len(reason) > 100 else reason,
                            inline=False)

            if channel:
                embed.add_field(name="Channel",
                                value=f"{channel.mention}\n(`{channel.id}`)",
                                inline=True)

            embed.set_thumbnail(url=author.display_avatar.url)

            await log_channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error logging ticket action: {e}")

    def create_setup_embed(self, ctx):
        """Create the main ticket setup embed with current configuration"""
        embed = discord.Embed(
            title="Ticket System Setup",
            description=
            "Use the dropdown menu below to configure your server's ticket system.",
            color=EMBED_COLOR_NORMAL)

        current_settings = self.get_guild_settings(ctx.guild.id)

        # Show current configuration status
        log_channel = None
        if current_settings.get('log_channel_id'):
            log_channel = self.bot.get_channel(
                current_settings['log_channel_id'])

        category_display = "Not set"
        if current_settings.get('ticket_category_id'):
            category = self.bot.get_channel(
                current_settings['ticket_category_id'])
            if category:
                category_display = f"{category.mention} (`{category.name}`)"
        else:
            # Show general channel when no category is set
            general_channel = discord.utils.get(ctx.guild.channels, name='general')
            if not general_channel:
                general_channel = ctx.guild.text_channels[0] if ctx.guild.text_channels else None
            if general_channel:
                category_display = f"Not set - tickets will be created in {general_channel.mention}"

        staff_roles = []
        for role_id in current_settings.get('staff_role_ids', []):
            role = ctx.guild.get_role(role_id)
            if role:
                staff_roles.append(role.mention)

        embed.add_field(
            name="Current Configuration",
            value=
            f"**Log Channel:** {log_channel.mention if log_channel else 'Not set'}\n"
            f"**Staff Roles:** {', '.join(staff_roles) if staff_roles else 'Not set'}\n"
            f"**Category:** {category_display}\n"
            f"**Naming Style:** {current_settings.get('naming_style', 'numbers')}",
            inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                         icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        return embed

    @commands.command(
        name="ticketsetup",
        help="Complete ticket system setup with staff roles and categories")
    @commands.has_permissions(administrator=True)
    async def ticket_setup(self, ctx):
        """Interactive ticket system setup with select menus"""
        try:
            embed = self.create_setup_embed(ctx)
            view = TicketSetupView(ctx, self)
            confirmation_msg = await ctx.reply(embed=embed,
                                               view=view,
                                               mention_author=False)
            # Auto-delete setup message after 5 minutes
            asyncio.create_task(self.auto_delete_message(
                confirmation_msg, 300))

        except Exception as e:
            logger.error(f"Error in ticket setup: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description=
                f"An error occurred while setting up the ticket system: {str(e)}",
                color=EMBED_COLOR_ERROR)
            error_embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            try:
                error_msg = await ctx.reply(embed=error_embed,
                                            mention_author=False)
                # Auto-delete error message after 30 seconds
                asyncio.create_task(self.auto_delete_message(error_msg, 30))
            except:
                pass

    @ticket_setup.error
    async def ticket_setup_error(self, ctx, error):
        """Handle ticketsetup command errors"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title=
                "{SPROUTS_WARNING} Permission Denied",
                description=
                "You don't have permission to use this command. Only server administrators can configure the ticket system.",
                color=EMBED_COLOR_ERROR)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="ticketuseembed",
        help="Apply saved embed template for ticket welcome messages")
    @commands.has_permissions(administrator=True)
    async def use_saved_embed(self, ctx, *, embed_name: str):
        """Use a saved embed for ticket welcome messages"""
        try:
            # Get embed builder cog
            embed_builder = self.bot.get_cog('EmbedBuilder')
            if not embed_builder:
                await ctx.reply("Embed builder not available",
                                mention_author=False)
                return

            user_id = str(ctx.author.id)
            guild_id = str(ctx.guild.id) if ctx.guild else "dm"

            # Check for guild-level embeds if user is admin
            embed_data = None
            is_guild_embed = False

            if (ctx.guild and hasattr(ctx.author, 'guild_permissions')
                    and ctx.author.guild_permissions.administrator):
                guild_embeds = embed_builder.saved_embeds.get(guild_id, {})
                if embed_name in guild_embeds:
                    embed_data = guild_embeds[embed_name]
                    is_guild_embed = True

            # Check user embeds if not found in guild
            if not embed_data:
                user_guild_key = f"{user_id}_{guild_id}"
                user_embeds = embed_builder.saved_embeds.get(
                    user_guild_key, {})
                if embed_name not in user_embeds:
                    await ctx.reply(
                        f"Embed '{embed_name}' not found. Use `s.embedlist` to see available embeds.",
                        mention_author=False)
                    return
                embed_data = user_embeds[embed_name]

            # Set the embed as the ticket welcome embed
            guild_settings = {
                'use_saved_embed': True,
                'saved_embed_name': embed_name,
                'embed_set_by_user': user_id if not is_guild_embed else None
            }
            self.update_guild_settings(ctx.guild.id, guild_settings)

            scope_text = "server" if is_guild_embed else "personal"
            embed = discord.Embed(
                title="{SPROUTS_CHECK} Welcome Embed Set",
                description=
                f"Ticket system will now use {scope_text} embed '**{embed_name}**' for welcome messages",
                color=EMBED_COLOR_NORMAL)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()

            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error setting saved embed: {e}")

    async def create_ticket_embed(self, ctx, user: discord.Member, reason: str,
                                  ticket_data: dict) -> discord.Embed:
        """Create ticket embed using saved embed or default settings with variable processing"""
        try:
            # Get guild-specific settings
            guild_settings = self.get_guild_settings(ctx.guild.id)

            # Check if using saved embed
            if guild_settings.get('use_saved_embed', False):
                embed_builder = self.bot.get_cog('EmbedBuilder')
                if embed_builder:
                    guild_id = str(ctx.guild.id) if ctx.guild else "dm"
                    saved_embed_name = guild_settings.get('saved_embed_name')
                    embed_set_by_user = guild_settings.get('embed_set_by_user')

                    # Check guild embeds first, then user embeds (for the user who set the embed)
                    embed_data = None
                    guild_embeds = embed_builder.saved_embeds.get(guild_id, {})

                    if saved_embed_name and saved_embed_name in guild_embeds:
                        embed_data = guild_embeds[saved_embed_name]
                    elif embed_set_by_user and saved_embed_name:
                        # Check the specific user's server-specific embeds
                        user_guild_key = f"{embed_set_by_user}_{guild_id}"
                        user_embeds = embed_builder.saved_embeds.get(
                            user_guild_key, {})
                        if saved_embed_name in user_embeds:
                            embed_data = user_embeds[saved_embed_name]

                    if embed_data:

                        # Import the variable processor
                        from src.utils.variables import VariableProcessor

                        # Process variables with await
                        title = await embed_builder.variable_processor.process_variables(
                            embed_data.get('title', ''),
                            guild=ctx.guild,
                            user=user,
                            channel=ctx.channel,
                            member=user,
                            ticket_data=ticket_data)
                        description = await embed_builder.variable_processor.process_variables(
                            embed_data.get('description', ''),
                            guild=ctx.guild,
                            user=user,
                            channel=ctx.channel,
                            member=user,
                            ticket_data=ticket_data)

                        embed = discord.Embed(
                            title=title if title else None,
                            description=description if description else None,
                            color=embed_data['color'],
                            timestamp=discord.utils.utcnow())

                        # Add author if set
                        if embed_data['author_name']:
                            author_name = await embed_builder.variable_processor.process_variables(
                                embed_data['author_name'],
                                guild=ctx.guild,
                                user=user,
                                channel=ctx.channel,
                                member=user,
                                ticket_data=ticket_data)
                            author_icon = await embed_builder.variable_processor.process_variables(
                                embed_data['author_icon'],
                                guild=ctx.guild,
                                user=user,
                                channel=ctx.channel,
                                member=user,
                                ticket_data=ticket_data)
                            embed.set_author(name=author_name,
                                             icon_url=author_icon or None)

                        # Add footer if set
                        if embed_data['footer_text']:
                            footer_text = await embed_builder.variable_processor.process_variables(
                                embed_data['footer_text'],
                                guild=ctx.guild,
                                user=user,
                                channel=ctx.channel,
                                member=user,
                                ticket_data=ticket_data)
                            footer_icon = await embed_builder.variable_processor.process_variables(
                                embed_data['footer_icon'],
                                guild=ctx.guild,
                                user=user,
                                channel=ctx.channel,
                                member=user,
                                ticket_data=ticket_data)
                            embed.set_footer(text=footer_text,
                                             icon_url=footer_icon or None)

                        # Add thumbnail and image
                        if embed_data['thumbnail']:
                            thumbnail_url = await embed_builder.variable_processor.process_variables(
                                embed_data['thumbnail'],
                                guild=ctx.guild,
                                user=user,
                                channel=ctx.channel,
                                member=user,
                                ticket_data=ticket_data)
                            embed.set_thumbnail(url=thumbnail_url)

                        if embed_data['image']:
                            image_url = await embed_builder.variable_processor.process_variables(
                                embed_data['image'],
                                guild=ctx.guild,
                                user=user,
                                channel=ctx.channel,
                                member=user,
                                ticket_data=ticket_data)
                            embed.set_image(url=image_url)

                        # Add fields
                        for field in embed_data['fields']:
                            field_name = await embed_builder.variable_processor.process_variables(
                                field['name'],
                                guild=ctx.guild,
                                user=user,
                                channel=ctx.channel,
                                member=user,
                                ticket_data=ticket_data)
                            field_value = await embed_builder.variable_processor.process_variables(
                                field['value'],
                                guild=ctx.guild,
                                user=user,
                                channel=ctx.channel,
                                member=user,
                                ticket_data=ticket_data)
                            embed.add_field(name=field_name,
                                            value=field_value,
                                            inline=field['inline'])

                        return embed

            # Fall back to built-in settings with variable processing
            embed_builder = self.bot.get_cog('EmbedBuilder')
            if embed_builder:
                embed_title = await embed_builder.variable_processor.process_variables(
                    guild_settings.get('embed_title', 'Support Ticket'),
                    guild=ctx.guild,
                    user=user,
                    channel=ctx.channel,
                    member=user,
                    ticket_data=ticket_data)
                embed_description = await embed_builder.variable_processor.process_variables(
                    guild_settings.get(
                        'embed_description',
                        'Thank you for creating a ticket! Please describe your issue and a staff member will assist you shortly.'
                    ),
                    guild=ctx.guild,
                    user=user,
                    channel=ctx.channel,
                    member=user,
                    ticket_data=ticket_data)
            else:
                # Fallback if embed builder isn't available
                embed_title = guild_settings.get('embed_title',
                                                 'Support Ticket')
                embed_description = guild_settings.get(
                    'embed_description',
                    'Thank you for creating a ticket! Please describe your issue and a staff member will assist you shortly.'
                )

            embed = discord.Embed(
                title=embed_title,
                description=f"{embed_description}\n\n**Reason:** {reason}",
                color=guild_settings.get('embed_color', EMBED_COLOR_NORMAL),
                timestamp=discord.utils.utcnow())

            # Add custom author if set
            embed_author_name = guild_settings.get('embed_author_name')
            if embed_author_name and embed_builder:
                processed_name = await embed_builder.variable_processor.process_variables(
                    embed_author_name,
                    guild=ctx.guild,
                    user=user,
                    channel=ctx.channel,
                    member=user,
                    ticket_data=ticket_data)
                embed_author_icon = await embed_builder.variable_processor.process_variables(
                    guild_settings.get('embed_author_icon', ''),
                    guild=ctx.guild,
                    user=user,
                    channel=ctx.channel,
                    member=user,
                    ticket_data=ticket_data)
                embed.set_author(name=processed_name,
                                 icon_url=embed_author_icon or None)

            embed.add_field(name="Status", value="Open", inline=True)
            embed.add_field(name="Claimed By", value="None", inline=True)
            embed.add_field(name="Priority", value="Normal", inline=True)

            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(
                text=
                f"Created on {datetime.utcnow().strftime('%Y-%m-%d at %H:%M UTC')}"
            )

            return embed

        except Exception as e:
            logger.error(f"Error creating ticket embed: {e}")
            # Return basic fallback embed
            return discord.Embed(
                title="Support Ticket",
                description="Hello! Your ticket has been created.",
                color=EMBED_COLOR_NORMAL)

    async def update_ticket_embed(self, channel: discord.TextChannel,
                                  ticket_data: dict):
        """Update the ticket embed in the channel with current priority and claim status"""
        try:
            # Find the ticket embed message - look for the message with Support Ticket title or Status field
            async for message in channel.history(limit=50):
                if message.author == self.bot.user and message.embeds:
                    embed = message.embeds[0]
                    # Check if this is the ticket embed by looking for status fields or title
                    has_status_field = any(
                        field.name in ["Status", "Claimed By", "Priority"]
                        for field in embed.fields)
                    has_ticket_title = embed.title and (
                        "Support Ticket" in embed.title
                        or "Ticket" in embed.title)

                    if has_status_field or has_ticket_title:
                        # Update the status fields
                        new_embed = discord.Embed(
                            title=embed.title,
                            description=embed.description,
                            color=embed.color)

                        # Copy author, footer, thumbnail, image (with safe access)
                        try:
                            if embed.author and embed.author.name:
                                new_embed.set_author(
                                    name=embed.author.name,
                                    icon_url=embed.author.icon_url)
                        except:
                            pass

                        try:
                            if embed.footer and embed.footer.text:
                                new_embed.set_footer(
                                    text=embed.footer.text,
                                    icon_url=embed.footer.icon_url)
                        except:
                            pass

                        try:
                            if embed.thumbnail and embed.thumbnail.url:
                                new_embed.set_thumbnail(
                                    url=embed.thumbnail.url)
                        except:
                            pass

                        try:
                            if embed.image and embed.image.url:
                                new_embed.set_image(url=embed.image.url)
                        except:
                            pass

                        # Copy non-status fields first
                        for field in embed.fields:
                            if field.name not in [
                                    "Status", "Claimed By", "Priority"
                            ]:
                                new_embed.add_field(name=field.name,
                                                    value=field.value,
                                                    inline=field.inline)

                        # Add updated status fields
                        status_value = "Open" if ticket_data.get(
                            'status') == 'open' else "Closed"
                        new_embed.add_field(name="Status",
                                            value=status_value,
                                            inline=True)

                        # Claimed by field
                        claimed_by = ticket_data.get('claimed_by')
                        if claimed_by:
                            claimed_user = self.bot.get_user(claimed_by)
                            claimed_value = claimed_user.display_name if claimed_user else f"<@{claimed_by}>"
                        else:
                            claimed_value = "None"
                        new_embed.add_field(name="Claimed By",
                                            value=claimed_value,
                                            inline=True)

                        # Priority field with colors
                        priority = ticket_data.get('priority',
                                                   'medium').lower()
                        priority_display = {
                            'low': 'Low',
                            'medium': 'Medium',
                            'high': '🟠 High',
                            'urgent': 'Urgent'
                        }.get(priority, 'Medium')
                        new_embed.add_field(name="Priority",
                                            value=priority_display,
                                            inline=True)

                        # Update the message with new embed and preserve buttons
                        try:
                            # Always create fresh TicketButtons for the main embed
                            ticket_buttons = TicketButtons()
                            await message.edit(embed=new_embed,
                                               view=ticket_buttons)
                        except Exception as edit_error:
                            # If that fails, try without the view
                            try:
                                await message.edit(embed=new_embed)
                            except Exception as final_error:
                                logger.error(
                                    f"Failed to update message embed: {final_error}"
                                )
                                continue  # Skip this message and try the next one
                        logger.info(
                            f"Updated ticket embed in channel {channel.name}")
                        return True

            logger.warning(
                f"Could not find ticket embed to update in channel {channel.name}"
            )
            return False

        except Exception as e:
            import traceback
            logger.error(f"Error updating ticket embed: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def generate_ticket_name(self, guild_id: int, user: discord.Member) -> str:
        """Generate ticket name based on naming style"""
        guild_settings = self.get_guild_settings(guild_id)
        naming_style = guild_settings.get('naming_style', 'numbers')

        if naming_style == 'discord_tag':
            # Clean username for channel name
            clean_username = ''.join(c.lower() for c in user.display_name
                                     if c.isalnum() or c in '-_')
            if not clean_username:
                clean_username = str(user.id)
            return f"ticket-{clean_username}"
        else:
            # Number-based naming
            guild_tickets = [
                t for t in self.tickets_data.values()
                if t.get('guild_id') == guild_id
            ]
            ticket_number = len(guild_tickets) + 1
            return f"ticket-{ticket_number:03d}"

    @commands.command(
        name="new",
        help=
        "Create a new support ticket with automated setup and staff notification"
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def new_ticket(self, ctx, *, reason: str = "No reason provided"):
        """Create a new ticket command
        
        Usage: `{ctx.prefix}new [reason]`
        Creates a private ticket channel with automatic permissions and staff notification
        
        Examples:
        - `{ctx.prefix}new Account issues` - Create ticket with specific reason
        - `{ctx.prefix}new Cannot access premium features` - Detailed reason for better support
        - `{ctx.prefix}new Need help with billing` - Clear reason helps staff assist you better
        
        Common Errors:
        - Ticket limit reached: Close existing tickets before creating new ones
        - Permission denied: Bot needs 'Manage Channels' permission
        - Category full: Staff will move ticket to available category
        """
        try:
            guild = ctx.guild
            user = ctx.author

            if not guild:
                embed = discord.Embed(
                    description="This command can only be used in a server.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Get guild-specific settings first
            guild_settings = self.get_guild_settings(guild.id)
            max_tickets = guild_settings.get('max_tickets_per_user', 10)

            # Check ticket limit for this user
            user_ticket_count = self.count_user_tickets(guild.id, user.id)

            if user_ticket_count >= max_tickets:
                embed = discord.Embed(
                    description=
                    f"You have reached the maximum number of open tickets ({max_tickets}). Please close an existing ticket before creating a new one.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Get category from settings or create default
            category = None
            category_id = guild_settings.get('ticket_category_id')
            if category_id:
                category = guild.get_channel(category_id)

            if not category:
                # Try to find a "Tickets" category
                for cat in guild.categories:
                    if cat.name.lower() == "tickets":
                        category = cat
                        break

                # Create default category if none exists
                if not category:
                    try:
                        category = await guild.create_category_channel(
                            "Tickets")
                    except Exception as e:
                        logger.error(f"Failed to create ticket category: {e}")
                        embed = discord.Embed(
                            description="Failed to create ticket category.",
                            color=EMBED_COLOR_ERROR)
                        embed.set_footer(
                            text=f"Requested by {ctx.author.display_name}",
                            icon_url=ctx.author.display_avatar.url)
                        embed.timestamp = discord.utils.utcnow()
                        await ctx.reply(embed=embed, mention_author=False)
                        return

            # Generate channel name using new naming system
            channel_name = self.generate_ticket_name(guild.id, user)

            # Create permissions
            overwrites = {
                guild.default_role:
                discord.PermissionOverwrite(view_channel=False),
                user:
                discord.PermissionOverwrite(view_channel=True,
                                            send_messages=True,
                                            read_message_history=True),
                guild.me:
                discord.PermissionOverwrite(view_channel=True,
                                            send_messages=True,
                                            manage_messages=True)
            }

            # Add staff role permissions from settings
            staff_roles = guild_settings.get('staff_role_ids', [])
            for role_id in staff_roles:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        manage_messages=True)

            # Create channel
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=
                f"Support ticket for {user.display_name} | Reason: {reason}")

            # Get log channel from guild settings
            guild_settings = self.get_guild_settings(guild.id)
            log_channel_id = guild_settings.get('log_channel_id')
            log_channel = self.bot.get_channel(
                log_channel_id) if log_channel_id else None

            # Store ticket data
            ticket_id = channel_name  # Use channel name as ticket ID
            self.tickets_data[str(ticket_channel.id)] = {
                'id': ticket_id,
                'creator_id': user.id,
                'creator_name': str(user),
                'guild_id': guild.id,
                'channel_id': ticket_channel.id,
                'status': 'open',
                'claimed_by': None,
                'created_at': datetime.utcnow().isoformat(),
                'priority': 'medium',
                'topic': reason,
                'members': [user.id],
                'tags': [],
                'log_channel_id': log_channel.id if log_channel else None
            }
            TicketData.save_tickets(self.tickets_data)

            # Skip database registration - not required for basic functionality

            # Create ticket welcome embed (with saved embed support)
            ticket_data = self.tickets_data[str(ticket_channel.id)]
            embed = await self.create_ticket_embed(ctx, user, reason,
                                                   ticket_data)

            # Send embed and buttons to ticket channel
            ticket_buttons = TicketButtons()
            staff_panel = StaffPanel()

            # Send user ping first (outside embed for notification)
            await ticket_channel.send(f"{user.mention}")

            # Send the main ticket embed with buttons
            await ticket_channel.send(embed=embed, view=ticket_buttons)

            # Send staff panel separately
            staff_embed = discord.Embed(
                description=
                "**Staff Panel** - Click the button below for advanced ticket management",
                color=EMBED_COLOR_NORMAL)
            await ticket_channel.send(embed=staff_embed, view=staff_panel)

            # Confirmation message
            embed = discord.Embed(
                title="Ticket Created",
                description=
                f"Your ticket has been created {ticket_channel.mention}",
                color=EMBED_COLOR_NORMAL)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()

            await ctx.reply(embed=embed, mention_author=False)

            # Log the action
            await self.log_ticket_action("new", user, guild, ticket_id, reason,
                                         ticket_channel)

            logger.info(
                f"Ticket created by {user} in {guild.name}: {ticket_channel.name}"
            )

        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            # Send error message to user so they know what happened
            error_embed = discord.Embed(
                title="Error Creating Ticket",
                description=
                f"An error occurred while creating your ticket. Please try again or contact an administrator.\n\n**Error:** {str(e)[:100]}",
                color=EMBED_COLOR_ERROR)
            error_embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            try:
                await ctx.reply(embed=error_embed, mention_author=False)
            except:
                pass  # If we can't send the error message, at least we logged it

    @commands.command(
        name="add",
        help=
        "Add a member to the current ticket for collaboration and assistance")
    async def add_member(self, ctx, member: discord.Member):
        """Add member to ticket command
        
        Usage: `{ctx.prefix}add <@user|user_id>`
        Adds a user to the current ticket channel (staff or ticket owner only)
        
        Examples:
        - `{ctx.prefix}add @username` - Add user by mention
        - `{ctx.prefix}add 123456789012345678` - Add user by ID
        - `{ctx.prefix}add @TeamLead` - Add supervisor to ticket
        
        Common Errors:
        - Not in ticket channel: Command only works in ticket channels
        - Permission denied: Only staff or ticket owner can add members
        - User already added: User already has access to this ticket
        """
        try:
            # Find ticket by current channel
            ticket_data = None
            ticket_id = None
            for tid, tdata in self.tickets_data.items():
                if tdata.get('channel_id') == ctx.channel.id:
                    ticket_id = tid
                    ticket_data = tdata
                    break

            if not ticket_data:
                embed = discord.Embed(
                    title="Invalid Channel",
                    description="This is not a ticket channel.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Check if user is staff or ticket owner
            is_ticket_owner = ticket_data.get('creator_id') == ctx.author.id
            is_staff_member = isinstance(
                ctx.author, discord.Member) and self.is_staff(ctx.author)

            if not (is_staff_member or is_ticket_owner):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_WARNING} Access Denied",
                    description=
                    "Only staff members or the ticket owner can add members to tickets.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Add member to channel
            await ctx.channel.set_permissions(member,
                                              read_messages=True,
                                              send_messages=True)

            if member.id not in ticket_data['members']:
                ticket_data['members'].append(member.id)
                TicketData.save_tickets(self.tickets_data)

            embed = discord.Embed(
                description=f"{member.mention} has been added to this ticket.",
                color=EMBED_COLOR_NORMAL)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error in add_member command: {e}")
            try:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Command Error",
                    description=
                    "An error occurred while trying to add the member to this ticket.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
            except:
                pass

    @add_member.error
    async def add_member_error(self, ctx, error):
        """Handle add command errors"""
        if isinstance(error, commands.MissingRequiredArgument):
            # First check permissions - regular users should be denied regardless of channel
            is_staff_member = isinstance(
                ctx.author, discord.Member) and self.is_staff(ctx.author)

            # Get ticket data to check if user is ticket owner
            ticket_data = None
            for tid, tdata in self.tickets_data.items():
                if tdata.get('channel_id') == ctx.channel.id:
                    ticket_data = tdata
                    break

            is_ticket_owner = ticket_data and ticket_data.get(
                'creator_id') == ctx.author.id

            # If user is neither staff nor ticket owner, deny access
            if not (is_staff_member or is_ticket_owner):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_WARNING} Permission Denied",
                    description=
                    "You don't have permission to use this command. Only staff members and ticket owners can add members to tickets.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Now check if this is a ticket channel (for staff/owners)
            if not ticket_data:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_WARNING} Invalid Channel",
                    description=
                    "This is not a ticket channel. This command can only be used in ticket channels.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Show usage (only for authorized users in ticket channels)
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} add",
                description=
                "Optional arguments are marked by `[arg]` and mandatory arguments are marked by `<arg>`.",
                color=EMBED_COLOR_ERROR)
            embed.add_field(
                name="Description",
                value="This command requires a member to add to the ticket.",
                inline=False)
            embed.add_field(name="Usage",
                            value=f"```\n{ctx.prefix}add <member>\n```",
                            inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="claim",
        help=
        "Claim ownership of an unclaimed ticket to provide dedicated support")
    @commands.has_permissions(manage_channels=True)
    async def claim_ticket(self, ctx):
        """Claim ticket command
        
        Usage: claim
        Claims ownership of an unclaimed ticket (staff only)
        
        Examples:
        - claim - Take ownership of current ticket
        - Use in any unclaimed ticket channel
        
        Common Errors:
        - Already claimed: Ticket is already owned by another staff member
        - Not staff: Only staff members can claim tickets
        - Not in ticket: Command only works in ticket channels
        - Use 'transfer' to change ownership of claimed tickets
        """
        try:
            if not isinstance(ctx.author, discord.Member) or not self.is_staff(
                    ctx.author):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_WARNING} Access Denied",
                    description="Only staff members can claim tickets.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Find ticket by current channel
            ticket_data = None
            ticket_id = None
            for tid, tdata in self.tickets_data.items():
                if tdata.get('channel_id') == ctx.channel.id:
                    ticket_id = tid
                    ticket_data = tdata
                    break

            if not ticket_data:
                embed = discord.Embed(
                    title="Invalid Channel",
                    description="This is not a ticket channel.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            if ticket_data.get('claimed_by') == ctx.author.id:
                embed = discord.Embed(
                    description="You have already claimed this ticket.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Update ticket data
            ticket_data['claimed_by'] = ctx.author.id
            TicketData.save_tickets(self.tickets_data)

            # Update the ticket embed with new claim status
            await self.update_ticket_embed(ctx.channel, ticket_data)

            embed = discord.Embed(
                description=
                f"This ticket has been claimed by {ctx.author.mention}",
                color=EMBED_COLOR_NORMAL)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error claiming ticket: {e}")
            try:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Command Error",
                    description=
                    "An error occurred while trying to claim this ticket.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
            except:
                pass

    @commands.command(
        name="close",
        help="Close the current ticket with optional reason and transcript")
    async def close_ticket(self, ctx, *, reason: str = "No reason provided"):
        """Close ticket command with confirmation"""
        try:
            # Find ticket by current channel first
            ticket_data = None
            ticket_id = None
            for tid, tdata in self.tickets_data.items():
                if tdata.get('channel_id') == ctx.channel.id:
                    ticket_id = tid
                    ticket_data = tdata
                    break

            if not ticket_data:
                embed = discord.Embed(
                    title="Invalid Channel",
                    description="This is not a ticket channel.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Check if user is staff or ticket owner
            is_ticket_owner = ticket_data.get('creator_id') == ctx.author.id
            is_staff_member = isinstance(
                ctx.author, discord.Member) and self.is_staff(ctx.author)

            if not (is_staff_member or is_ticket_owner):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description=
                    "Only staff members or the ticket owner can close tickets.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Show confirmation with buttons
            embed = discord.Embed(
                title=
                f"{SPROUTS_CHECK} Close Ticket Confirmation",
                description=
                f"Are you sure you want to close this ticket?\n\n**Reason:** {reason}\n**Channel:** {ctx.channel.mention}\n\n{SPROUTS_ERROR} This action cannot be undone!",
                color=EMBED_COLOR_NORMAL)
            embed.set_footer(
                text="This confirmation will timeout in 30 seconds",
                icon_url=ctx.author.display_avatar.url)

            view = CloseConfirmation(self, ctx, reason)
            await ctx.reply(embed=embed, view=view, mention_author=False)

        except Exception as e:
            logger.error(f"Error in close command: {e}")
            try:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Command Error",
                    description=
                    "An error occurred while trying to close this ticket.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
            except:
                pass

    async def _process_ticket_close(self, ctx, reason: str):
        """Process the actual ticket closing with full transcript logging to channel"""
        try:
            # Find ticket by current channel
            ticket_data = None
            ticket_id = None
            for tid, tdata in self.tickets_data.items():
                if tdata.get('channel_id') == ctx.channel.id:
                    ticket_id = tid
                    ticket_data = tdata
                    break

            if not ticket_data:
                return

            # Get the ticket creator FIRST before any async operations
            ticket_creator = self.bot.get_user(ticket_data.get('creator_id'))
            if not ticket_creator:
                try:
                    ticket_creator = await self.bot.fetch_user(
                        ticket_data.get('creator_id'))
                except:
                    logger.error(
                        f"Could not find ticket creator with ID {ticket_data.get('creator_id')}"
                    )

            # Generate transcript for both file storage AND logging channel
            transcript_content = None
            transcript_file_path = None
            try:
                # Create transcripts directory if it doesn't exist
                transcript_dir = "transcripts"
                if not os.path.exists(transcript_dir):
                    os.makedirs(transcript_dir)

                # Generate transcript filename
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                transcript_file_path = f"{transcript_dir}/ticket_{ticket_id}_{timestamp}.txt"

                # Collect messages from the channel
                messages = []
                async for message in ctx.channel.history(limit=500,
                                                         oldest_first=True):
                    # Skip bot messages except embeds and important ones
                    if message.author.bot and not message.embeds and not message.attachments:
                        continue

                    timestamp_str = message.created_at.strftime(
                        "%Y-%m-%d %H:%M:%S UTC")
                    content = message.content if message.content else "[No text content]"

                    # Add embeds info
                    if message.embeds:
                        content += f" [Contains {len(message.embeds)} embed(s)]"

                    # Add attachments info
                    if message.attachments:
                        content += f" [Contains {len(message.attachments)} attachment(s): {', '.join([att.filename for att in message.attachments])}]"

                    messages.append(
                        f"[{timestamp_str}] {message.author.display_name}: {content}"
                    )

                # Create transcript header and content
                transcript_header = f"=== TICKET TRANSCRIPT ===\n"
                transcript_header += f"Ticket ID: {ticket_id}\n"
                transcript_header += f"Creator: {ticket_data.get('creator_name', 'Unknown')}\n"
                transcript_header += f"Created: {ticket_data.get('created_at', 'Unknown')}\n"
                transcript_header += f"Closed: {datetime.utcnow().isoformat()}\n"
                transcript_header += f"Closed by: {ctx.author.display_name}\n"
                transcript_header += f"Reason: {reason}\n"
                transcript_header += f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
                transcript_header += f"Channel: {ctx.channel.name} ({ctx.channel.id})\n"
                transcript_header += f"{'=' * 50}\n\n"

                transcript_content = transcript_header + "\n".join(messages)

                # Save transcript to file (for DMs and local backup)
                with open(transcript_file_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_content)

                logger.info(
                    f"Generated and saved transcript to {transcript_file_path}"
                )

            except Exception as e:
                logger.error(f"Error generating transcript: {e}")

            # Update ticket status
            ticket_data['status'] = 'closed'
            ticket_data['closed_by'] = ctx.author.id
            ticket_data['closed_at'] = datetime.utcnow().isoformat()
            ticket_data['close_reason'] = reason
            TicketData.save_tickets(self.tickets_data)

            # Send confirmation message in channel BEFORE closing
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Ticket Closed",
                description=
                f"This ticket has been closed by {ctx.author.mention}",
                color=EMBED_COLOR_NORMAL,
                timestamp=discord.utils.utcnow())
            embed.add_field(name="Closed by",
                            value=ctx.author.mention,
                            inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)

            # Calculate ticket duration
            try:
                created_at = datetime.fromisoformat(
                    ticket_data.get('created_at'))
                duration = datetime.utcnow() - created_at
                days = duration.days
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, _ = divmod(remainder, 60)

                duration_str = ""
                if days > 0:
                    duration_str += f"{days}d "
                if hours > 0:
                    duration_str += f"{hours}h "
                if minutes > 0:
                    duration_str += f"{minutes}m"
                if not duration_str:
                    duration_str = "< 1m"

                embed.add_field(name="Duration",
                                value=duration_str,
                                inline=True)
            except Exception as e:
                logger.error(f"Error calculating ticket duration: {e}")
                embed.add_field(name="Duration", value="Unknown", inline=True)

            await ctx.channel.send(embed=embed)

            # Send enhanced log with FULL TRANSCRIPT to transcript channel
            log_channel = await self.get_or_create_transcript_channel(ctx.guild
                                                                      )
            if log_channel:
                try:
                    log_embed = discord.Embed(
                        title=
                        f"{SPROUTS_ERROR} Ticket Closed with Full Transcript",
                        color=0xff4444,  # Red for closures
                        timestamp=discord.utils.utcnow())
                    log_embed.add_field(name="Ticket ID",
                                        value=f"#{ticket_id}",
                                        inline=True)
                    log_embed.add_field(
                        name="Closed By",
                        value=f"{ctx.author.mention}\n(`{ctx.author.id}`)",
                        inline=True)
                    log_embed.add_field(
                        name="Creator",
                        value=
                        f"{ticket_creator.mention if ticket_creator else 'Unknown'}\n(`{ticket_data.get('creator_id')}`)",
                        inline=True)
                    log_embed.add_field(name="Reason",
                                        value=reason[:100] +
                                        "..." if len(reason) > 100 else reason,
                                        inline=False)
                    log_embed.add_field(
                        name="Channel",
                        value=f"{ctx.channel.mention}\n(`{ctx.channel.id}`)",
                        inline=True)
                    log_embed.add_field(
                        name="Guild",
                        value=f"{ctx.guild.name}\n(`{ctx.guild.id}`)",
                        inline=True)

                    # Add duration if available
                    try:
                        created_at = datetime.fromisoformat(
                            ticket_data.get('created_at'))
                        duration = datetime.utcnow() - created_at
                        days = duration.days
                        hours, remainder = divmod(duration.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)

                        duration_str = ""
                        if days > 0:
                            duration_str += f"{days}d "
                        if hours > 0:
                            duration_str += f"{hours}h "
                        if minutes > 0:
                            duration_str += f"{minutes}m"
                        if not duration_str:
                            duration_str = "< 1m"

                        log_embed.add_field(name="Duration",
                                            value=duration_str,
                                            inline=True)
                    except Exception as e:
                        log_embed.add_field(name="Duration",
                                            value="Unknown",
                                            inline=True)

                    log_embed.set_thumbnail(url=ctx.author.display_avatar.url)

                    # Send transcript as attachment using the saved file
                    if transcript_file_path and os.path.exists(
                            transcript_file_path):
                        try:
                            # Check file size
                            file_size = os.path.getsize(transcript_file_path)
                            if file_size < 8 * 1024 * 1024:  # 8MB limit
                                # Create file attachment from saved file
                                transcript_filename = f"ticket_{ticket_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
                                with open(transcript_file_path, 'rb') as f:
                                    transcript_file = discord.File(
                                        f, filename=transcript_filename)
                                    log_embed.add_field(
                                        name="Transcript",
                                        value=
                                        "Full conversation attached below\n`Also saved locally for backup`",
                                        inline=False)
                                    await log_channel.send(
                                        embed=log_embed, file=transcript_file)
                                    logger.info(
                                        f"Sent ticket close log with transcript attachment to {log_channel.name}"
                                    )
                            else:
                                # File too large, send summary
                                message_count = len([
                                    line
                                    for line in transcript_content.split('\n')
                                    if line.strip()
                                    and not line.startswith('===')
                                ]) if transcript_content else 0
                                log_embed.add_field(
                                    name="Transcript",
                                    value=
                                    f"Transcript too large for Discord ({file_size} bytes)\nContained {message_count} messages\nSaved locally: `{transcript_file_path}`",
                                    inline=False)
                                await log_channel.send(embed=log_embed)
                                logger.warning(
                                    f"Transcript for ticket {ticket_id} too large for Discord attachment"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error sending transcript attachment: {e}")
                            # Fall back to sending without transcript
                            log_embed.add_field(
                                name="Transcript",
                                value=
                                f"Error sending transcript attachment\nSaved locally: `{transcript_file_path}`",
                                inline=False)
                            await log_channel.send(embed=log_embed)
                    else:
                        # No transcript file
                        log_embed.add_field(
                            name="Transcript",
                            value="No transcript file available",
                            inline=False)
                        await log_channel.send(embed=log_embed)

                    logger.info(
                        f"Sent enhanced ticket close log to {log_channel.name}"
                    )
                except Exception as e:
                    logger.error(f"Error sending log message: {e}")

            # Send DM to ticket creator with transcript info
            if ticket_creator:
                try:
                    dm_embed = discord.Embed(
                        title=
                        f"{SPROUTS_ERROR} Your Ticket Has Been Closed",
                        description=
                        f"Your ticket in **{ctx.guild.name}** has been closed.",
                        color=EMBED_COLOR_ERROR)
                    dm_embed.add_field(name="Closed By",
                                       value=ctx.author.display_name,
                                       inline=True)
                    dm_embed.add_field(name="Reason",
                                       value=reason,
                                       inline=True)
                    dm_embed.add_field(name="Server",
                                       value=ctx.guild.name,
                                       inline=True)

                    # Send transcript as attachment in DM using saved file
                    if transcript_file_path and os.path.exists(
                            transcript_file_path):
                        try:
                            file_size = os.path.getsize(transcript_file_path)
                            if file_size < 8 * 1024 * 1024:  # 8MB limit
                                # Send transcript file attachment in DM
                                transcript_filename = f"ticket_{ticket_id}_transcript.txt"
                                with open(transcript_file_path, 'rb') as f:
                                    transcript_file = discord.File(
                                        f, filename=transcript_filename)
                                    dm_embed.add_field(
                                        name="Transcript",
                                        value=
                                        "Full conversation attached below",
                                        inline=False)
                                    dm_embed.set_thumbnail(
                                        url=ctx.guild.icon.url if ctx.guild.
                                        icon else None)
                                    dm_embed.timestamp = discord.utils.utcnow()
                                    dm_embed.set_footer(
                                        text=f"Ticket ID: #{ticket_id}")

                                    await ticket_creator.send(
                                        embed=dm_embed, file=transcript_file)
                                    logger.info(
                                        f"Successfully sent DM with transcript file to ticket creator {ticket_creator.id}"
                                    )
                            else:
                                # File too large for DM
                                dm_embed.add_field(
                                    name="Transcript",
                                    value=
                                    "Transcript was too large for DM but was logged to staff channels",
                                    inline=False)
                                dm_embed.set_thumbnail(
                                    url=ctx.guild.icon.url if ctx.guild.
                                    icon else None)
                                dm_embed.timestamp = discord.utils.utcnow()
                                dm_embed.set_footer(
                                    text=f"Ticket ID: #{ticket_id}")
                                await ticket_creator.send(embed=dm_embed)
                                logger.info(
                                    f"Successfully sent DM (transcript too large) to ticket creator {ticket_creator.id}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error sending DM with transcript file: {e}")
                            # Fall back to DM without transcript
                            dm_embed.add_field(
                                name="Transcript",
                                value="Transcript was logged to staff channels",
                                inline=False)
                            dm_embed.set_thumbnail(url=ctx.guild.icon.url
                                                   if ctx.guild.icon else None)
                            dm_embed.timestamp = discord.utils.utcnow()
                            dm_embed.set_footer(
                                text=f"Ticket ID: #{ticket_id}")
                            await ticket_creator.send(embed=dm_embed)
                            logger.info(
                                f"Successfully sent DM without transcript to ticket creator {ticket_creator.id}"
                            )
                    else:
                        # No transcript file
                        dm_embed.add_field(
                            name="Transcript",
                            value="No transcript file was generated",
                            inline=False)
                        dm_embed.set_thumbnail(
                            url=ctx.guild.icon.url if ctx.guild.icon else None)
                        dm_embed.timestamp = discord.utils.utcnow()
                        dm_embed.set_footer(text=f"Ticket ID: #{ticket_id}")
                        await ticket_creator.send(embed=dm_embed)
                        logger.info(
                            f"Successfully sent DM (no transcript) to ticket creator {ticket_creator.id}"
                        )

                except discord.Forbidden:
                    logger.warning(
                        f"Could not DM ticket creator {ticket_creator.id} - DMs disabled or blocked"
                    )
                except discord.HTTPException as e:
                    logger.error(
                        f"HTTP error sending DM to ticket creator {ticket_creator.id}: {e}"
                    )
                except Exception as e:
                    logger.error(
                        f"Unexpected error sending DM to ticket creator {ticket_creator.id}: {e}"
                    )
            else:
                logger.warning(
                    f"Could not find ticket creator with ID {ticket_data.get('creator_id')} for DM"
                )

            # Wait 10 seconds before deleting channel (give time for people to see the close message)
            await asyncio.sleep(10)

            try:
                await ctx.channel.delete(
                    reason=f"Ticket closed by {ctx.author}")
                logger.info(
                    f"Ticket channel {ctx.channel.name} deleted successfully")
            except Exception as e:
                logger.error(f"Error deleting ticket channel: {e}")

        except Exception as e:
            logger.error(f"Error processing ticket close: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

    @commands.group(name="force", invoke_without_command=True)
    async def force_group(self, ctx):
        """Force command group"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title=
                f"{SPROUTS_ERROR} Invalid Command",
                description="Use `force close` to force close a ticket.",
                color=EMBED_COLOR_ERROR)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

    @force_group.command(
        name="close",
        aliases=["forceclose"],
        help="Force close a ticket immediately without confirmation prompts")
    async def force_close_ticket(self, ctx, ticket_id: str = None):
        """Force close ticket command"""
        try:
            if not isinstance(ctx.author, discord.Member) or not self.is_staff(
                    ctx.author):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description="Only staff members can force close tickets.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            if not ticket_id:
                # Use current channel
                for tid, tdata in self.tickets_data.items():
                    if tdata.get('channel_id') == ctx.channel.id:
                        ticket_id = tid
                        break

            if not ticket_id or ticket_id not in self.tickets_data:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Ticket Not Found",
                    description="This is not a valid ticket please try again",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            ticket_data = self.tickets_data[ticket_id]
            ticket_channel = self.bot.get_channel(ticket_data['channel_id'])

            # Update ticket status
            ticket_data['status'] = 'force_closed'
            ticket_data['closed_by'] = ctx.author.id
            ticket_data['closed_at'] = datetime.utcnow().isoformat()
            TicketData.save_tickets(self.tickets_data)

            # Send confirmation message
            embed = discord.Embed(
                title=
                f"{SPROUTS_CHECK} Ticket Force Closed",
                description=
                f"Ticket #{ticket_id} has been force closed by {ctx.author.mention}",
                color=EMBED_COLOR_NORMAL)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

            # Send simple log message to log channel
            ticket_creator = self.bot.get_user(ticket_data['creator_id'])
            log_channel_id = ticket_data.get('log_channel_id')
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(title="Ticket Force Closed",
                                              color=EMBED_COLOR_ERROR)
                    log_embed.add_field(name="Ticket ID",
                                        value=f"#{ticket_id}",
                                        inline=True)
                    log_embed.add_field(
                        name="Action By",
                        value=f"{ctx.author.mention}\n(`{ctx.author.id}`)",
                        inline=True)
                    log_embed.add_field(
                        name="Server",
                        value=f"{ctx.guild.name}\n(`{ctx.guild.id}`)",
                        inline=True)
                    log_embed.add_field(name="Reason",
                                        value="Force closed by staff",
                                        inline=False)
                    if ticket_channel:
                        log_embed.add_field(
                            name="Channel",
                            value=
                            f"{ticket_channel.mention}\n(`{ticket_channel.id}`)",
                            inline=True)
                    log_embed.set_thumbnail(url=ctx.author.display_avatar.url)
                    log_embed.timestamp = discord.utils.utcnow()

                    await log_channel.send(embed=log_embed)

            # Send simple DM to ticket creator (no transcript links)
            if ticket_creator:
                try:
                    dm_embed = discord.Embed(
                        title="Your Ticket Was Force Closed",
                        description=
                        f"Your ticket in **{ctx.guild.name}** was force closed by staff.",
                        color=EMBED_COLOR_ERROR)
                    dm_embed.set_footer(
                        text=
                        f"Force closed by {ctx.author.display_name} in {ctx.guild.name}"
                    )
                    dm_embed.timestamp = discord.utils.utcnow()

                    await ticket_creator.send(embed=dm_embed)
                    logger.info(
                        f"Successfully sent force close DM to ticket creator {ticket_creator.id}"
                    )

                except discord.Forbidden:
                    logger.warning(
                        f"Could not DM ticket creator {ticket_creator.id} - DMs disabled"
                    )
                except Exception as e:
                    logger.error(f"Error sending DM to ticket creator: {e}")

            # Wait 5 seconds then delete channel
            await asyncio.sleep(5)
            if ticket_channel:
                await ticket_channel.delete()

        except Exception as e:
            logger.error(f"Error force closing ticket: {e}")

    @commands.command(
        name="forceclose",
        help="Force close a ticket immediately without confirmation prompts")
    async def forceclose(self, ctx, ticket_id: str = None):
        """Force close ticket command"""
        await self.force_close_ticket(ctx, ticket_id)

    @commands.command(
        name="move",
        help="Move ticket to different category or reorganize channels")
    @commands.has_permissions(manage_channels=True)
    async def move_ticket(self, ctx, category: discord.CategoryChannel):
        """Move ticket to another category"""
        try:
            if not isinstance(ctx.author, discord.Member) or not self.is_staff(
                    ctx.author):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description="Only staff members can move tickets.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            await ctx.channel.edit(category=category)
            embed = discord.Embed(
                description=f"Ticket moved to {category.name}.",
                color=EMBED_COLOR_NORMAL)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error moving ticket: {e}")

    @move_ticket.error
    async def move_ticket_error(self, ctx, error):
        """Handle move command errors"""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Missing Category",
                description="Please specify a category to move the ticket to.\n\n**Usage:** `s.move #category-name`",
                color=EMBED_COLOR_ERROR)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", 
                           icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="You need **Manage Channels** permission to move tickets.",
                color=EMBED_COLOR_ERROR)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", 
                           icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)


    @commands.command(
        name="unclaim",
        help="Unclaim ownership of claimed ticket for other staff to handle")
    @commands.has_permissions(manage_channels=True)
    async def unclaim_ticket(self, ctx):
        """Unclaim ticket command"""
        try:
            if not isinstance(ctx.author, discord.Member) or not self.is_staff(
                    ctx.author):
                embed = discord.Embed(
                    title="Access Denied",
                    description="Only staff members can unclaim tickets.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Find ticket
            for ticket_id, ticket_data in self.tickets_data.items():
                if ticket_data.get('channel_id') == ctx.channel.id:
                    if ticket_data.get('claimed_by') != ctx.author.id:
                        embed = discord.Embed(
                            title="Access Denied",
                            description="You can only unclaim tickets you have claimed.",
                            color=EMBED_COLOR_ERROR)
                        embed.set_footer(
                            text=f"Requested by {ctx.author.display_name}",
                            icon_url=ctx.author.display_avatar.url)
                        await ctx.reply(embed=embed, mention_author=False)
                        return

                    ticket_data['claimed_by'] = None
                    TicketData.save_tickets(self.tickets_data)

                    # Update the ticket embed to show unclaimed status
                    await self.update_ticket_embed(ctx.channel, ticket_data)

                    embed = discord.Embed(
                        title="Ticket Unclaimed",
                        description="This ticket has been unclaimed and can now be claimed by other staff.",
                        color=EMBED_COLOR_NORMAL)
                    embed.set_footer(
                        text=f"Unclaimed by {ctx.author.display_name}",
                        icon_url=ctx.author.display_avatar.url)
                    await ctx.reply(embed=embed, mention_author=False)
                    return

            embed = discord.Embed(
                title="Invalid Channel",
                description="This is not a ticket channel.",
                color=EMBED_COLOR_ERROR)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error unclaiming ticket: {e}")

    @commands.command(name="remove",
                      help="Remove a member from the current ticket channel")
    async def remove_member(self, ctx, member: discord.Member):
        """Remove a member from a ticket"""
        try:
            # Find ticket
            ticket_data = None
            for ticket_id, tdata in self.tickets_data.items():
                if tdata.get('channel_id') == ctx.channel.id:
                    ticket_data = tdata
                    break

            if not ticket_data:
                embed = discord.Embed(
                    title="Invalid Channel",
                    description="This is not a ticket channel.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Check if user is staff or ticket owner
            is_ticket_owner = ticket_data.get('creator_id') == ctx.author.id
            is_staff_member = isinstance(
                ctx.author, discord.Member) and self.is_staff(ctx.author)

            if not (is_staff_member or is_ticket_owner):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description=
                    "Only staff members or the ticket owner can remove members from tickets.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Don't remove ticket creator
            if member.id == ticket_data.get('creator_id'):
                embed = discord.Embed(
                    description="Cannot remove the ticket creator.",
                    color=EMBED_COLOR_ERROR)
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Remove member from channel
            await ctx.channel.set_permissions(member, overwrite=None)

            if member.id in ticket_data['members']:
                ticket_data['members'].remove(member.id)
                TicketData.save_tickets(self.tickets_data)

            embed = discord.Embed(
                description=
                f"{member.mention} has been removed from this ticket.",
                color=EMBED_COLOR_NORMAL)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error removing member: {e}")
            try:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Command Error",
                    description=
                    "An error occurred while trying to remove the member from this ticket.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
            except:
                pass

    @remove_member.error
    async def remove_member_error(self, ctx, error):
        """Handle remove command errors"""
        if isinstance(error, commands.MissingRequiredArgument):
            # First check permissions - regular users should be denied regardless of channel
            is_staff_member = isinstance(
                ctx.author, discord.Member) and self.is_staff(ctx.author)

            # Get ticket data to check if user is ticket owner
            ticket_data = None
            for tid, tdata in self.tickets_data.items():
                if tdata.get('channel_id') == ctx.channel.id:
                    ticket_data = tdata
                    break

            is_ticket_owner = ticket_data and ticket_data.get(
                'creator_id') == ctx.author.id

            # If user is neither staff nor ticket owner, deny access
            if not (is_staff_member or is_ticket_owner):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_WARNING} Permission Denied",
                    description=
                    "You don't have permission to use this command. Only staff members and ticket owners can remove members from tickets.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Now check if this is a ticket channel (for staff/owners)
            if not ticket_data:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_WARNING} Invalid Channel",
                    description=
                    "This is not a ticket channel. This command can only be used in ticket channels.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Show usage (only for authorized users in ticket channels)
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} remove",
                description=
                "Optional arguments are marked by `[arg]` and mandatory arguments are marked by `<arg>`.",
                color=EMBED_COLOR_ERROR)
            embed.add_field(
                name="Description",
                value=
                "This command requires a member to remove from the ticket.",
                inline=False)
            embed.add_field(name="Usage",
                            value=f"```\n{ctx.prefix}remove <member>\n```",
                            inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="tag",
                      help="Add or remove tags for ticket categorization.")
    @commands.has_permissions(manage_channels=True)
    async def manage_tags(self, ctx, action: str, *, tag: str):
        """Add or remove tags from ticket"""
        try:
            if not isinstance(ctx.author, discord.Member) or not self.is_staff(
                    ctx.author):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description="Only staff members can manage ticket tags.",
                    color=EMBED_COLOR_ERROR)
                await ctx.reply(embed=embed, mention_author=False)
                return

            if action.lower() not in ["add", "remove"]:
                embed = discord.Embed(
                    description="Action must be 'add' or 'remove'.",
                    color=EMBED_COLOR_ERROR)
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Find ticket
            for ticket_id, ticket_data in self.tickets_data.items():
                if ticket_data.get('channel_id') == ctx.channel.id:
                    if action.lower() == "add":
                        if tag not in ticket_data.get('tags', []):
                            ticket_data.setdefault('tags', []).append(tag)
                            embed = discord.Embed(
                                description=
                                f"Tag '{tag}' added to this ticket.",
                                color=EMBED_COLOR_NORMAL)
                        else:
                            embed = discord.Embed(
                                description="Tag already exists.",
                                color=EMBED_COLOR_ERROR)
                    else:  # remove
                        if tag in ticket_data.get('tags', []):
                            ticket_data['tags'].remove(tag)
                            embed = discord.Embed(
                                description=
                                f"Tag '{tag}' removed from this ticket.",
                                color=EMBED_COLOR_NORMAL)
                        else:
                            embed = discord.Embed(description="Tag not found.",
                                                  color=EMBED_COLOR_ERROR)

                    TicketData.save_tickets(self.tickets_data)
                    await ctx.reply(embed=embed, mention_author=False)
                    return

            embed = discord.Embed(
                title=
                f"{SPROUTS_ERROR} Invalid Channel",
                description="This is not a ticket channel.",
                color=EMBED_COLOR_ERROR)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error managing tags: {e}")

    @commands.command(
        name="listtickets",
        help="Display all active tickets with status and staff assignments")
    @commands.has_permissions(manage_channels=True)
    async def list_tickets(self, ctx):
        """List all active tickets"""
        try:
            if not isinstance(ctx.author, discord.Member) or not self.is_staff(
                    ctx.author):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description="Only staff members can view the ticket list.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Only show tickets from current guild
            open_tickets = {
                tid: ticket
                for tid, ticket in self.tickets_data.items()
                if ticket.get('status') == 'open'
                and ticket.get('guild_id') == ctx.guild.id
            }

            if not open_tickets:
                embed = discord.Embed(
                    title="Active Tickets",
                    description="No active tickets at the moment.",
                    color=EMBED_COLOR_NORMAL)
                await ctx.reply(embed=embed, mention_author=False)
                return

            embed = discord.Embed(
                title=f"Active Tickets ({len(open_tickets)})",
                color=EMBED_COLOR_NORMAL)

            for ticket_id, ticket in list(open_tickets.items())[:10]:
                creator = self.bot.get_user(ticket.get('creator_id'))
                creator_name = creator.name if creator else "Unknown User"

                claimed_by = ticket.get('claimed_by')
                claimed_text = "Unclaimed"
                if claimed_by:
                    claimer = self.bot.get_user(claimed_by)
                    claimed_text = claimer.name if claimer else "Unknown"

                embed.add_field(
                    name=f"Ticket #{ticket_id}",
                    value=
                    f"**Creator:** {creator_name}\n**Claimed:** {claimed_text}\n**Priority:** {ticket.get('priority', 'medium').title()}",
                    inline=True)

            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error listing tickets: {e}")

    @commands.command(
        name="topic",
        help="Set or update the ticket channel topic/description")
    async def set_topic(self, ctx, *, topic: str):
        """Set ticket topic"""
        try:
            # Find ticket
            ticket_data = None
            ticket_id = None
            for tid, tdata in self.tickets_data.items():
                if tdata.get('channel_id') == ctx.channel.id:
                    ticket_id = tid
                    ticket_data = tdata
                    break

            if not ticket_data:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Invalid Channel",
                    description="This is not a ticket channel.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Check if user is staff or ticket owner
            is_ticket_owner = ticket_data.get('creator_id') == ctx.author.id
            is_staff_member = isinstance(
                ctx.author, discord.Member) and self.is_staff(ctx.author)

            if not (is_staff_member or is_ticket_owner):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description=
                    "Only staff members or the ticket owner can set ticket topics.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            ticket_data['topic'] = topic
            TicketData.save_tickets(self.tickets_data)
            current_topic = f"Ticket #{ticket_id} | Topic: {topic}"
            await ctx.channel.edit(topic=current_topic)
            embed = discord.Embed(
                description=f"Ticket topic updated to: **{topic}**",
                color=EMBED_COLOR_NORMAL)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error setting topic: {e}")
            try:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Command Error",
                    description=
                    "An error occurred while trying to set the ticket topic.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
            except:
                pass

    @set_topic.error
    async def set_topic_error(self, ctx, error):
        """Handle topic command errors"""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Command Error: Topic",
                description="Please specify a topic for the ticket.\n\n**Usage:** `s.topic <your topic here>`\n**Note:** This command only works in ticket channels.",
                color=EMBED_COLOR_ERROR)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", 
                           icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)


    @commands.command(name="rename",
                      help="Rename the current ticket channel with new name")
    @commands.has_permissions(manage_channels=True)
    async def rename_ticket(self, ctx, *, name: str):
        """Rename ticket channel"""
        try:
            if not isinstance(ctx.author, discord.Member) or not self.is_staff(
                    ctx.author):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_WARNING} Access Denied",
                    description="Only staff members can rename tickets.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            await ctx.channel.edit(name=name)
            embed = discord.Embed(description=f"Ticket renamed to **{name}**.",
                                  color=EMBED_COLOR_NORMAL)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error renaming ticket: {e}")

    async def create_ticket_from_panel(self, interaction, panel_data):
        """Create a ticket from a reaction panel"""
        try:
            # Get guild settings
            guild_id = interaction.guild.id
            guild_settings = self.get_guild_settings(guild_id)
            max_tickets = guild_settings.get('max_tickets_per_user', 10)

            # Check ticket limit for this user
            user_ticket_count = self.count_user_tickets(
                guild_id, interaction.user.id)

            if user_ticket_count >= max_tickets:
                embed = discord.Embed(
                    description=
                    f"You have reached the maximum number of open tickets ({max_tickets}). Please close an existing ticket before creating a new one.",
                    color=EMBED_COLOR_ERROR)
                await interaction.response.send_message(embed=embed,
                                                        ephemeral=True)
                return

            ticket_settings = self.ticket_settings.get(str(guild_id), {})

            # Get category and settings from panel or defaults
            category_id = panel_data.get('category_id') or ticket_settings.get(
                'category_id')
            if not category_id:
                await interaction.response.send_message(
                    "No ticket category configured", ephemeral=True)
                return

            category = interaction.guild.get_channel(category_id)
            if not category:
                await interaction.response.send_message(
                    "Ticket category not found", ephemeral=True)
                return

            # Create channel name
            ticket_id = interaction.channel.id
            channel_name = f"ticket-{interaction.user.name}".lower().replace(
                ' ', '-')

            # Create ticket channel
            overwrites = {
                interaction.guild.default_role:
                discord.PermissionOverwrite(read_messages=False),
                interaction.user:
                discord.PermissionOverwrite(read_messages=True,
                                            send_messages=True),
                interaction.guild.me:
                discord.PermissionOverwrite(read_messages=True,
                                            send_messages=True,
                                            manage_messages=True)
            }

            # Add staff roles permissions
            staff_role_ids = ticket_settings.get('staff_role_ids', [])
            for role_id in staff_role_ids:
                role = interaction.guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_messages=True)

            ticket_channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=
                f"Ticket opened by {interaction.user} | ID: {interaction.user.id}"
            )

            # Store ticket data
            self.tickets_data[str(ticket_channel.id)] = {
                'user_id': interaction.user.id,
                'user_name': str(interaction.user),
                'channel_id': ticket_channel.id,
                'guild_id': guild_id,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'open',
                'claimed_by': None,
                'priority': 'medium',
                'panel_id': panel_data.get('panel_id'),
                'reason': panel_data.get('default_reason', 'Support Request')
            }
            TicketData.save_tickets(self.tickets_data)

            # Create welcome embed
            embed = discord.Embed(
                title=
                f"{SPROUTS_CHECK} New Ticket Created",
                description=
                f"Welcome {interaction.user.mention}! Please describe your issue and our staff will assist you shortly.",
                color=EMBED_COLOR_NORMAL)
            embed.add_field(name="Created by",
                            value=interaction.user.mention,
                            inline=True)
            embed.add_field(name="Reason",
                            value=panel_data.get('default_reason',
                                                 'Support Request'),
                            inline=True)
            embed.add_field(name="Priority", value="Medium", inline=True)
            embed.set_footer(text=f"Ticket ID: {ticket_channel.id}")
            embed.timestamp = discord.utils.utcnow()

            # Add ticket buttons
            view = TicketButtons()
            await ticket_channel.send(embed=embed, view=view)

            # Send success response
            embed = discord.Embed(
                title=
                f"{SPROUTS_CHECK} Ticket Created",
                description=
                f"Your ticket has been created: {ticket_channel.mention}",
                color=EMBED_COLOR_NORMAL)
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)

            # Log to staff channel if configured
            log_channel_id = ticket_settings.get('log_channel_id')
            if log_channel_id:
                log_channel = interaction.guild.get_channel(log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title=
                        f"{SPROUTS_CHECK} New Ticket Created",
                        color=EMBED_COLOR_NORMAL)
                    log_embed.add_field(
                        name="Ticket",
                        value=f"{ticket_channel.mention} ({ticket_channel.id})",
                        inline=False)
                    log_embed.add_field(
                        name="User",
                        value=
                        f"{interaction.user.mention} ({interaction.user.id})",
                        inline=True)
                    log_embed.add_field(
                        name="Server",
                        value=
                        f"{interaction.guild.name} ({interaction.guild.id})",
                        inline=True)
                    log_embed.add_field(name="Reason",
                                        value=panel_data.get(
                                            'default_reason',
                                            'Support Request'),
                                        inline=True)
                    log_embed.set_thumbnail(
                        url=interaction.user.display_avatar.url)
                    log_embed.timestamp = discord.utils.utcnow()
                    await log_channel.send(embed=log_embed)

        except Exception as e:
            logger.error(f"Error creating ticket from panel: {e}")
            await interaction.response.send_message("Error creating ticket",
                                                    ephemeral=True)

    @commands.command(
        name="createpanel",
        aliases=["panel"],
        help="Create interactive ticket panel with buttons for users")
    @commands.has_permissions(manage_channels=True)
    async def create_panel(self, ctx, *, title: str = "Support Tickets"):
        """Create a ticket panel with button"""
        try:
            if not isinstance(ctx.author, discord.Member) or not self.is_staff(
                    ctx.author):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description="Only staff members can create ticket panels.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Generate shorter random panel ID (8 characters: letters and numbers, mixed case)
            panel_id = ''.join(
                random.choices(string.ascii_letters + string.digits, k=8))

            # Create panel embed
            embed = discord.Embed(
                title=title,
                description=
                "Click the button below to create a support ticket.\nOur staff will assist you as soon as possible!",
                color=EMBED_COLOR_NORMAL)
            embed.set_footer(text=f"Panel ID: {panel_id}")
            embed.timestamp = discord.utils.utcnow()

            # Create panel view
            view = TicketPanelView(panel_id)
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
            PanelData.save_panels(self.panels_data)

            # Confirmation message
            confirm_embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Panel Created",
                description=
                f"Ticket panel created successfully!\n\n**ID:** `{panel_id}`\n**Title:** {title}",
                color=EMBED_COLOR_NORMAL)
            confirm_embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url)
            confirm_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=confirm_embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error creating panel: {e}")

    @commands.command(name="listpanels",
                      aliases=["panels"],
                      help="Display all created ticket panels in the server")
    @commands.has_permissions(manage_channels=True)
    async def list_panels(self, ctx):
        """List all ticket panels in the server"""
        try:
            if not isinstance(ctx.author, discord.Member) or not self.is_staff(
                    ctx.author):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description="Only staff members can list ticket panels.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
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
                    channel = ctx.guild.get_channel(
                        panel_data.get('channel_id'))
                    if channel:
                        # Try to fetch the message to see if it still exists
                        message = await channel.fetch_message(
                            panel_data.get('message_id'))
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
                PanelData.save_panels(self.panels_data)

            if not active_panels:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} No Active Panels Found",
                    description="No active ticket panels found in this server.",
                    color=EMBED_COLOR_ERROR)
                if panels_to_remove:
                    embed.add_field(
                        name="Cleanup",
                        value=
                        f"Removed {len(panels_to_remove)} panel(s) with deleted messages from database.",
                        inline=False)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            embed = discord.Embed(
                title=
                f"{SPROUTS_CHECK} Active Ticket Panels",
                description=
                f"Found {len(active_panels)} active panel(s) in this server:",
                color=EMBED_COLOR_NORMAL)

            if panels_to_remove:
                embed.add_field(
                    name="Auto-Cleanup",
                    value=
                    f"Removed {len(panels_to_remove)} panel(s) with deleted messages.",
                    inline=False)

            for panel_id, panel_data in list(
                    active_panels.items())[:10]:  # Show max 10 panels
                channel = ctx.guild.get_channel(panel_data.get('channel_id'))
                channel_name = channel.mention if channel else "Deleted Channel"
                created_by = ctx.guild.get_member(panel_data.get('created_by'))
                creator_name = created_by.display_name if created_by else "Unknown User"

                embed.add_field(
                    name=f"{panel_data.get('title', 'Untitled Panel')}",
                    value=
                    f"**ID:** `{panel_id}`\n**Channel:** {channel_name}\n**Created by:** {creator_name}",
                    inline=True)

            if len(active_panels) > 10:
                embed.add_field(
                    name="Note",
                    value=
                    f"Only showing first 10 panels. Total active: {len(active_panels)}",
                    inline=False)

            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error listing panels: {e}")

    @commands.command(name="delpanel",
                      help="Delete an existing ticket panel by ID or name")
    @commands.has_permissions(manage_channels=True)
    async def delete_panel(self, ctx, panel_id: str):
        """Delete a ticket panel"""
        try:
            if not isinstance(ctx.author, discord.Member) or not self.is_staff(
                    ctx.author):
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description="Only staff members can delete ticket panels.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Check if panel exists
            if panel_id not in self.panels_data:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Panel Not Found",
                    description=f"No panel found with ID: `{panel_id}`",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            panel_data = self.panels_data[panel_id]

            # Check if panel belongs to this guild
            if panel_data.get('guild_id') != ctx.guild.id:
                embed = discord.Embed(
                    title=
                    f"{SPROUTS_ERROR} Access Denied",
                    description="You can only delete panels from this server.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
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
                        message = await channel.fetch_message(
                            panel_data.get('message_id'))
                        if message:
                            await message.delete()
                            message_status = f"{SPROUTS_CHECK} Panel message deleted"
                        else:
                            message_status = f"{SPROUTS_ERROR} Panel message not found"
                    except discord.NotFound:
                        message_status = f"{SPROUTS_ERROR} Panel message was already deleted"
                    except discord.Forbidden:
                        message_status = f"{SPROUTS_ERROR} No permission to delete message"
                    except Exception as e:
                        message_status = f"{SPROUTS_ERROR} Error deleting message: {str(e)[:50]}"
            except Exception as e:
                message_status = f"{SPROUTS_ERROR} Error accessing channel: {str(e)[:50]}"

            # Remove from data
            del self.panels_data[panel_id]
            PanelData.save_panels(self.panels_data)

            # Get panel title for display
            panel_title = panel_data.get('title', 'Untitled Panel')

            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Panel Deleted",
                description=
                f"Panel **{panel_title}** has been removed from the database.",
                color=EMBED_COLOR_NORMAL)

            embed.add_field(
                name="Panel Details",
                value=f"**ID:** `{panel_id}`\n**Title:** {panel_title}",
                inline=True)

            embed.add_field(name="Message Status",
                            value=message_status or f"{SPROUTS_WARNING} Status unknown",
                            inline=True)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error deleting panel: {e}")

    @commands.command(
        name="ticketlimit",
        help="Configure maximum number of tickets each user can create")
    @commands.has_permissions(administrator=True)
    async def ticket_limit(self, ctx, limit: Optional[int] = None):
        """Set or view the ticket limit per user"""
        try:
            guild_settings = self.get_guild_settings(ctx.guild.id)
            current_limit = guild_settings.get('max_tickets_per_user', 10)

            if limit is None:
                # View current limit
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Ticket Limit",
                    description=
                    f"**Current Maximum Tickets Per User:** `{current_limit}`\n\nTo change the limit, use: `{ctx.prefix}ticket-limit <number>`",
                    color=EMBED_COLOR_NORMAL)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Validate limit
            if limit < 1 or limit > 20:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Invalid Limit",
                    description=
                    "Ticket limit must be between **1** and **20**.",
                    color=EMBED_COLOR_ERROR)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Update the limit
            guild_settings['max_tickets_per_user'] = limit
            self.save_ticket_settings()

            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Ticket Limit Updated",
                description=
                f"Maximum tickets per user has been set to **{limit}**.\n\nUsers can now have up to {limit} open tickets at once.",
                color=EMBED_COLOR_NORMAL)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error in ticket limit command: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description="An error occurred while setting the ticket limit.",
                color=EMBED_COLOR_ERROR)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)


async def setup_ticket_system(bot):
    """Setup ticket system for the bot"""
    await bot.add_cog(TicketSystem(bot))
    logger.info("Ticket system setup completed")
