"""
Advanced Auto Responders System - SPROUTS Professional Implementation
Complete autoresponder management with match modes, editing, and comprehensive features
"""

import discord
from discord.ext import commands
import json
import os
import logging
import re
from datetime import datetime
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from emojis import SPROUTS_ERROR, SPROUTS_CHECK, SPROUTS_WARNING

logger = logging.getLogger(__name__)

class AutoResponderCreateModal(discord.ui.Modal):
    """Advanced modal for creating autoresponders with match modes"""
    
    def __init__(self, cog):
        self.cog = cog
        super().__init__(title="Create Auto Responder", timeout=300)
        
        self.trigger_input = discord.ui.TextInput(
            label="Trigger Word/Phrase",
            placeholder="Enter the word or phrase that will trigger the response...",
            style=discord.TextStyle.short,
            max_length=200,
            required=True
        )
        self.add_item(self.trigger_input)
        
        self.response_input = discord.ui.TextInput(
            label="Response Message",
            placeholder="Enter the message to send when triggered",
            style=discord.TextStyle.paragraph,
            max_length=2000,
            required=True
        )
        self.add_item(self.response_input)
        
        self.match_mode_input = discord.ui.TextInput(
            label="Match Mode",
            placeholder="exact, contains, startswith, endswith, regex",
            style=discord.TextStyle.short,
            max_length=20,
            required=False,
            default="contains"
        )
        self.add_item(self.match_mode_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission"""
        try:
            trigger = self.trigger_input.value.strip()
            response = self.response_input.value.strip()
            match_mode = self.match_mode_input.value.strip().lower()
            
            # Validate match mode
            valid_modes = ["exact", "contains", "startswith", "endswith", "regex"]
            if match_mode not in valid_modes:
                match_mode = "contains"
            
            guild_id = str(interaction.guild_id)
            if guild_id not in self.cog.autoresponders:
                self.cog.autoresponders[guild_id] = {}
            
            # Generate unique ID
            responder_id = len(self.cog.autoresponders[guild_id]) + 1
            while str(responder_id) in self.cog.autoresponders[guild_id]:
                responder_id += 1
            
            # Add the responder
            self.cog.autoresponders[guild_id][str(responder_id)] = {
                'trigger': trigger,
                'response': response,
                'match_mode': match_mode,
                'enabled': True,
                'created_by': str(interaction.user.id),
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.cog.save_autoresponders()
            
            # Create success embed
            embed = discord.Embed(
                title="Auto Responder Created",
                description=f"Successfully created autoresponder with ID `{responder_id}`!",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(name="ID", value=str(responder_id), inline=True)
            embed.add_field(name="Trigger", value=f"`{trigger}`", inline=True)
            embed.add_field(name="Match Mode", value=match_mode.title(), inline=True)
            embed.add_field(name="Response", 
                           value=response[:100] + "..." if len(response) > 100 else response, 
                           inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error creating auto responder: {e}")
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Failed to create autoresponder. Please try again.",
                ephemeral=True
            )

class AutoResponderEditModal(discord.ui.Modal):
    """Modal for editing autoresponder properties"""
    
    def __init__(self, cog, responder_id: str, current_data: dict, edit_type: str):
        self.cog = cog
        self.responder_id = responder_id
        self.current_data = current_data
        self.edit_type = edit_type
        
        super().__init__(title=f"Edit {edit_type.title()}", timeout=300)
        
        if edit_type == "reply":
            self.input = discord.ui.TextInput(
                label="Response Message",
                placeholder="Enter the new response message...",
                style=discord.TextStyle.paragraph,
                max_length=2000,
                default=current_data.get('response', ''),
                required=True
            )
        elif edit_type == "matchmode":
            self.input = discord.ui.TextInput(
                label="Match Mode",
                placeholder="exact, contains, startswith, endswith, or regex",
                style=discord.TextStyle.short,
                max_length=20,
                default=current_data.get('match_mode', 'contains'),
                required=True
            )
        
        self.add_item(self.input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            guild_id = str(interaction.guild_id)
            new_value = self.input.value.strip()
            
            if self.edit_type == "reply":
                self.cog.autoresponders[guild_id][self.responder_id]['response'] = new_value
                field_name = "Response"
            elif self.edit_type == "matchmode":
                valid_modes = ["exact", "contains", "startswith", "endswith", "regex"]
                if new_value.lower() not in valid_modes:
                    await interaction.response.send_message(
                        f"{SPROUTS_ERROR} Invalid match mode! Use: {', '.join(valid_modes)}",
                        ephemeral=True
                    )
                    return
                self.cog.autoresponders[guild_id][self.responder_id]['match_mode'] = new_value.lower()
                field_name = "Match Mode"
            
            self.cog.save_autoresponders()
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Autoresponder Updated",
                description=f"Successfully updated {field_name.lower()} for autoresponder ID `{self.responder_id}`!",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(name=field_name, value=new_value[:100] + ("..." if len(new_value) > 100 else ""), inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error editing autoresponder: {e}")
            await interaction.response.send_message(f"{SPROUTS_ERROR} Error updating autoresponder!", ephemeral=True)

class AutoResponderButtonView(discord.ui.View):
    """Button view for autoresponder creation"""
    
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog
    
    @discord.ui.button(label="Create Auto Responder", style=discord.ButtonStyle.primary)
    async def create_responder(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AutoResponderCreateModal(self.cog)
        await interaction.response.send_modal(modal)

class AutoResponders(commands.Cog):
    """Advanced SPROUTS autoresponder system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.responders_file = "data/autoresponders.json"
        self.autoresponders = self.load_autoresponders()
    
    def load_autoresponders(self) -> dict:
        """Load auto responders from file"""
        try:
            os.makedirs("data", exist_ok=True)
            if os.path.exists(self.responders_file):
                with open(self.responders_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading auto responders: {e}")
            return {}
    
    def save_autoresponders(self):
        """Save auto responders to file"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(self.responders_file, 'w') as f:
                json.dump(self.autoresponders, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving auto responders: {e}")
    
    def check_trigger_match(self, message_content: str, trigger: str, match_mode: str) -> bool:
        """Check if message matches trigger based on match mode"""
        try:
            message_lower = message_content.lower()
            trigger_lower = trigger.lower()
            
            if match_mode == "exact":
                return message_lower == trigger_lower
            elif match_mode == "contains":
                return trigger_lower in message_lower
            elif match_mode == "startswith":
                return message_lower.startswith(trigger_lower)
            elif match_mode == "endswith":
                return message_lower.endswith(trigger_lower)
            elif match_mode == "regex":
                return bool(re.search(trigger, message_content, re.IGNORECASE))
            else:
                return trigger_lower in message_lower  # Default to contains
        except Exception as e:
            logger.error(f"Error checking trigger match: {e}")
            return False
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Process autoresponder triggers"""
        if not message.guild or message.author.bot:
            return
        
        # Don't trigger on commands
        ctx = await self.bot.get_context(message)
        if ctx.command:
            return
        
        guild_id = str(message.guild.id)
        if guild_id not in self.autoresponders:
            return
        
        for responder_id, data in self.autoresponders[guild_id].items():
            if not data.get('enabled', True):
                continue
            
            trigger = data['trigger']
            match_mode = data.get('match_mode', 'contains')
            
            if self.check_trigger_match(message.content, trigger, match_mode):
                response = data['response']
                
                # Process variables
                try:
                    from utils.variables import VariableProcessor
                    var_processor = VariableProcessor(self.bot)
                    processed_response = await var_processor.process_variables(
                        response, user=message.author, guild=message.guild, channel=message.channel
                    )
                    if isinstance(processed_response, str):
                        response = processed_response
                except Exception as e:
                    logger.error(f"Error processing variables: {e}")
                
                # Embed builder removed - {embed:name} references no longer supported
                embed_to_send = None
                
                # Send response
                if embed_to_send and response:
                    await message.channel.send(content=response, embed=embed_to_send)
                elif embed_to_send:
                    await message.channel.send(embed=embed_to_send)
                elif response:
                    await message.channel.send(response)
                
                break  # Only trigger first matching responder

    @commands.group(name="autoresponder", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def autoresponder_group(self, ctx):
        """Advanced autoresponder system - SPROUTS professional commands"""
        embed = discord.Embed(
            title="SPROUTS Auto Responder System",
            description="Advanced autoresponder management with comprehensive features!",
            color=EMBED_COLOR_NORMAL
        )
        
        embed.add_field(
            name="Creation & Management",
            value=(
                "`s.autoresponder add` - Add new autoresponder\n"
                "`s.autoresponder remove <id>` - Remove autoresponder\n"
                "`s.autoresponder list` - List all autoresponders\n"
                "`s.autoresponder show <id>` - Show autoresponder details"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Advanced Editing",
            value=(
                "`s.autoresponder editreply <id>` - Edit response text\n"
                "`s.autoresponder editmatchmode <id>` - Change match mode\n"
                "`s.autoresponder showraw <id>` - Show raw response\n"
                "`s.reset server autoresponders` - Reset all autoresponders"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Match Modes Available",
            value=(
                "**exact** - Trigger must match exactly\n"
                "**contains** - Message contains trigger\n"
                "**startswith** - Message starts with trigger\n"
                "**endswith** - Message ends with trigger\n"
                "**regex** - Use regular expressions"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @autoresponder_group.command(name="add")
    @commands.has_permissions(administrator=True)
    async def autoresponder_add(self, ctx):
        """Add new autoresponder with advanced options"""
        view = AutoResponderButtonView(self)
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Create Auto Responder",
            description="Click the button below to create a new autoresponder with advanced settings!",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed, view=view)
    
    @autoresponder_group.command(name="list")
    @commands.has_permissions(administrator=True)
    async def autoresponder_list(self, ctx):
        """List all autoresponders"""
        try:
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.autoresponders or not self.autoresponders[guild_id]:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} No Auto Responders",
                    description="This server has no autoresponders configured.\n\nUse `s.autoresponder add` to create your first one!",
                    color=EMBED_COLOR_NORMAL
                )
                await ctx.send(embed=embed)
                return
            
            responders = self.autoresponders[guild_id]
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Auto Responders ({len(responders)} total)",
                description=f"All configured autoresponders for **{ctx.guild.name}**",
                color=EMBED_COLOR_NORMAL
            )
            
            for responder_id, data in responders.items():
                status = f"{SPROUTS_CHECK} Enabled" if data.get('enabled', True) else f"{SPROUTS_ERROR} Disabled"
                trigger = data['trigger']
                match_mode = data.get('match_mode', 'contains').title()
                response_preview = data['response'][:50] + "..." if len(data['response']) > 50 else data['response']
                
                embed.add_field(
                    name=f"ID {responder_id}: `{trigger}`",
                    value=f"**Status:** {status}\n**Mode:** {match_mode}\n**Response:** {response_preview}",
                    inline=False
                )
            
            embed.set_footer(text="Use 's.autoresponder show <id>' for full details")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing autoresponders: {e}")
            await ctx.send(f"{SPROUTS_ERROR} Error loading autoresponder list.")
    
    @autoresponder_group.command(name="show")
    @commands.has_permissions(administrator=True)
    async def autoresponder_show(self, ctx, responder_id: str):
        """Show detailed autoresponder information"""
        try:
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.autoresponders or responder_id not in self.autoresponders[guild_id]:
                await ctx.send(f"{SPROUTS_ERROR} Autoresponder ID `{responder_id}` not found!")
                return
            
            data = self.autoresponders[guild_id][responder_id]
            creator = self.bot.get_user(int(data.get('created_by', 0)))
            
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Autoresponder Details",
                description=f"Complete information for autoresponder ID `{responder_id}`",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(name="ID", value=responder_id, inline=True)
            embed.add_field(name="Trigger", value=f"`{data['trigger']}`", inline=True)
            embed.add_field(name="Match Mode", value=data.get('match_mode', 'contains').title(), inline=True)
            embed.add_field(name="Status", value=f"{SPROUTS_CHECK} Enabled" if data.get('enabled', True) else f"{SPROUTS_ERROR} Disabled", inline=True)
            embed.add_field(name="Creator", value=creator.mention if creator else "Unknown", inline=True)
            embed.add_field(name="Created", value=data.get('created_at', 'Unknown')[:10], inline=True)
            embed.add_field(name="Response", value=data['response'], inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing autoresponder: {e}")
            await ctx.send(f"{SPROUTS_ERROR} Error loading autoresponder details.")
    
    @autoresponder_group.command(name="showraw")
    @commands.has_permissions(administrator=True)
    async def autoresponder_showraw(self, ctx, responder_id: str):
        """Show raw autoresponder response"""
        try:
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.autoresponders or responder_id not in self.autoresponders[guild_id]:
                await ctx.send(f"{SPROUTS_ERROR} Autoresponder ID `{responder_id}` not found!")
                return
            
            data = self.autoresponders[guild_id][responder_id]
            raw_response = data['response']
            
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Raw Response",
                description=f"Raw response text for autoresponder ID `{responder_id}`",
                color=EMBED_COLOR_NORMAL
            )
            
            # Use code block to show raw text
            embed.add_field(
                name="Raw Response Text",
                value=f"```\n{raw_response}\n```",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing raw response: {e}")
            await ctx.send(f"{SPROUTS_ERROR} Error loading raw response.")
    
    @autoresponder_group.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def autoresponder_remove(self, ctx, responder_id: str):
        """Remove autoresponder by ID"""
        try:
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.autoresponders or responder_id not in self.autoresponders[guild_id]:
                await ctx.send(f"{SPROUTS_ERROR} Autoresponder ID `{responder_id}` not found!")
                return
            
            data = self.autoresponders[guild_id][responder_id]
            del self.autoresponders[guild_id][responder_id]
            self.save_autoresponders()
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Autoresponder Removed",
                description=f"Successfully removed autoresponder ID `{responder_id}`",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(name="Trigger", value=f"`{data['trigger']}`", inline=True)
            embed.add_field(name="Match Mode", value=data.get('match_mode', 'contains').title(), inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error removing autoresponder: {e}")
            await ctx.send(f"{SPROUTS_ERROR} Error removing autoresponder.")
    
    @autoresponder_group.command(name="editreply")
    @commands.has_permissions(administrator=True)
    async def autoresponder_editreply(self, ctx, responder_id: str):
        """Edit autoresponder response"""
        try:
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.autoresponders or responder_id not in self.autoresponders[guild_id]:
                await ctx.send(f"{SPROUTS_ERROR} Autoresponder ID `{responder_id}` not found!")
                return
            
            data = self.autoresponders[guild_id][responder_id]
            modal = AutoResponderEditModal(self, responder_id, data, "reply")
            
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Edit Response",
                description=f"Click the button below to edit the response for autoresponder ID `{responder_id}`",
                color=EMBED_COLOR_NORMAL
            )
            
            view = discord.ui.View()
            button = discord.ui.Button(label="Edit Response", style=discord.ButtonStyle.primary)
            
            async def button_callback(interaction):
                await interaction.response.send_modal(modal)
            
            button.callback = button_callback
            view.add_item(button)
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error editing reply: {e}")
            await ctx.send(f"{SPROUTS_ERROR} Error editing autoresponder reply.")
    
    @autoresponder_group.command(name="editmatchmode")
    @commands.has_permissions(administrator=True)
    async def autoresponder_editmatchmode(self, ctx, responder_id: str):
        """Edit autoresponder match mode"""
        try:
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.autoresponders or responder_id not in self.autoresponders[guild_id]:
                await ctx.send(f"{SPROUTS_ERROR} Autoresponder ID `{responder_id}` not found!")
                return
            
            data = self.autoresponders[guild_id][responder_id]
            modal = AutoResponderEditModal(self, responder_id, data, "matchmode")
            
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Edit Match Mode",
                description=f"Click the button below to change the match mode for autoresponder ID `{responder_id}`\n\nCurrent mode: **{data.get('match_mode', 'contains').title()}**",
                color=EMBED_COLOR_NORMAL
            )
            
            view = discord.ui.View()
            button = discord.ui.Button(label="Edit Match Mode", style=discord.ButtonStyle.primary)
            
            async def button_callback(interaction):
                await interaction.response.send_modal(modal)
            
            button.callback = button_callback
            view.add_item(button)
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error editing match mode: {e}")
            await ctx.send(f"{SPROUTS_ERROR} Error editing match mode.")

    @commands.group(name="reset")
    @commands.has_permissions(administrator=True)
    async def reset_group(self, ctx):
        """Reset various server settings"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Reset Commands",
                description="Available reset options:",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Available Commands",
                value="`s.reset server autoresponders` - Reset all autoresponders",
                inline=False
            )
            await ctx.send(embed=embed)

    @reset_group.group(name="server")
    @commands.has_permissions(administrator=True) 
    async def reset_server_group(self, ctx):
        """Server-specific reset commands"""
        pass

    @reset_server_group.command(name="autoresponders")
    @commands.has_permissions(administrator=True)
    async def reset_server_autoresponders(self, ctx):
        """Reset all server autoresponders"""
        try:
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.autoresponders or not self.autoresponders[guild_id]:
                await ctx.send(f"{SPROUTS_ERROR} No autoresponders to reset!")
                return
            
            count = len(self.autoresponders[guild_id])
            self.autoresponders[guild_id] = {}
            self.save_autoresponders()
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Autoresponders Reset",
                description=f"Successfully removed all {count} autoresponders from this server!",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error resetting autoresponders: {e}")
            await ctx.send(f"{SPROUTS_ERROR} Error resetting autoresponders.")

async def setup(bot):
    await bot.add_cog(AutoResponders(bot))
    logger.info("Advanced autoresponders system setup completed")