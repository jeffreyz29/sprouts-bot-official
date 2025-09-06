"""
Additional View Classes for SPROUTS Ticket System
"""

import discord
import logging
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from emojis import SPROUTS_ERROR, SPROUTS_CHECK, SPROUTS_WARNING, SPROUTS_INFORMATION

logger = logging.getLogger(__name__)

class JumpToTopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Jump to Top", style=discord.ButtonStyle.primary, emoji=f"{SPROUTS_CHECK}")
    async def jump_to_top(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Create a link to the first message in the channel
        channel = interaction.channel
        async for message in channel.history(limit=1, oldest_first=True):
            first_message_url = f"https://discord.com/channels/{interaction.guild_id}/{channel.id}/{message.id}"
            embed = discord.Embed(
                title=f"{SPROUTS_INFORMATION} Jump to Top",
                description=f"[Click here to jump to the beginning of this ticket]({first_message_url})",
                color=EMBED_COLOR_NORMAL
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Fallback if no messages found
        await interaction.response.send_message("No messages found in this ticket.", ephemeral=True)

class CloseRequestView(discord.ui.View):
    def __init__(self, close_delay: int, reason: str, ticket_system):
        super().__init__(timeout=close_delay * 3600)  # Convert hours to seconds
        self.close_delay = close_delay
        self.reason = reason
        self.ticket_system = ticket_system
    
    @discord.ui.button(label="Approve Close", style=discord.ButtonStyle.danger, emoji=f"{SPROUTS_CHECK}")
    async def approve_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket_data = self.ticket_system.get_ticket_data(interaction.channel.id)
        if not ticket_data:
            await interaction.response.send_message("This is not a valid ticket channel.", ephemeral=True)
            return
        
        # Check if user is the ticket creator
        if interaction.user.id != ticket_data['creator_id']:
            await interaction.response.send_message("Only the ticket creator can approve closure.", ephemeral=True)
            return
        
        # Close the ticket
        await self.ticket_system.close_ticket(interaction.channel, interaction.user, f"Approved closure: {self.reason}")
        
        # Disable the view
        for item in self.children:
            item.disabled = True
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Close Request Approved",
            description=f"The ticket will be closed momentarily.",
            color=EMBED_COLOR_NORMAL
        )
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Deny Close", style=discord.ButtonStyle.secondary, emoji=f"{SPROUTS_ERROR}")
    async def deny_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket_data = self.ticket_system.get_ticket_data(interaction.channel.id)
        if not ticket_data:
            await interaction.response.send_message("This is not a valid ticket channel.", ephemeral=True)
            return
        
        # Check if user is the ticket creator
        if interaction.user.id != ticket_data['creator_id']:
            await interaction.response.send_message("Only the ticket creator can deny closure.", ephemeral=True)
            return
        
        # Disable the view
        for item in self.children:
            item.disabled = True
        
        embed = discord.Embed(
            title=f"{SPROUTS_WARNING} Close Request Denied",
            description="The ticket will remain open.",
            color=EMBED_COLOR_ERROR
        )
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        # Auto-close after timeout
        try:
            # This is a simplified timeout handler since we can't easily access the channel
            pass
        except Exception as e:
            logger.error(f"Error auto-closing ticket: {e}")