"""
Auto Responders System - Simplified with Only 3 Commands
Modern UI auto responder system with trigger and reply functionality
"""

import discord
from discord.ext import commands
import json
import os
import logging
from datetime import datetime
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from src.emojis import SPROUTS_ERROR, SPROUTS_CHECK, SPROUTS_WARNING

logger = logging.getLogger(__name__)

class AutoResponderCreateModal(discord.ui.Modal):
    """Modern UI modal for creating auto responders"""
    
    def __init__(self, cog):
        self.cog = cog
        super().__init__(title="Create Auto Responder", timeout=300)
        
        self.trigger_input = discord.ui.TextInput(
            label="Trigger Word/Phrase",
            placeholder="Enter the word or phrase that will trigger the response...",
            style=discord.TextStyle.short,
            max_length=100,
            required=True
        )
        self.add_item(self.trigger_input)
        
        self.response_input = discord.ui.TextInput(
            label="Response Message",
            placeholder="Enter the message to send when triggered...\nSupports variables like $(user.name), $(server.name)",
            style=discord.TextStyle.paragraph,
            max_length=2000,
            required=True
        )
        self.add_item(self.response_input)
        
        self.notes_input = discord.ui.TextInput(
            label="Additional Notes (Optional)",
            placeholder="Internal notes about this auto responder (not shown to users)",
            style=discord.TextStyle.short,
            max_length=200,
            required=False
        )
        self.add_item(self.notes_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission"""
        try:
            trigger = self.trigger_input.value.strip()
            response = self.response_input.value.strip()
            notes = self.notes_input.value.strip()
            
            if not trigger or not response:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Missing Information",
                    description="Both trigger and response are required!",
                    color=EMBED_COLOR_ERROR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            guild_id = str(interaction.guild_id)
            if guild_id not in self.cog.autoresponders:
                self.cog.autoresponders[guild_id] = {}
            
            # Check if trigger already exists
            if trigger in self.cog.autoresponders[guild_id]:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Auto Responder Already Exists",
                    description=f"An auto responder for trigger `{trigger}` already exists!\n\n"
                               f"Use `autoresponderlist` to view existing responders or try a different trigger.",
                    color=EMBED_COLOR_ERROR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Add the responder
            self.cog.autoresponders[guild_id][trigger] = {
                'response': response,
                'enabled': True,
                'created_by': str(interaction.user.id),
                'created_at': datetime.utcnow().isoformat(),
                'notes': notes
            }
            
            self.cog.save_autoresponders()
            
            # Create success embed with preview
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Auto Responder Created",
                description=f"Successfully created auto responder!",
                color=0x2ecc71  # SPROUTS_CHECK color - success
            )
            embed.add_field(name="Trigger", value=f"`{trigger}`", inline=True)
            embed.add_field(name="Status", value=f"{SPROUTS_CHECK} Enabled", inline=True)
            embed.add_field(name="Response Preview", 
                           value=response[:100] + "..." if len(response) > 100 else response, 
                           inline=False)
            
            if notes:
                embed.add_field(name="Notes", value=notes, inline=False)
            
            embed.set_footer(text="The auto responder is now active and will respond when the trigger is detected.")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error creating auto responder: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description="Failed to create auto responder. Please try again.",
                color=EMBED_COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class AutoResponders(commands.Cog):
    """Auto responders system with only 3 commands and modern UI"""
    
    def __init__(self, bot):
        self.bot = bot
        self.responders_file = "src/data/autoresponders.json"
        self.autoresponders = self.load_autoresponders()
    
    def load_autoresponders(self) -> dict:
        """Load auto responders from file"""
        try:
            os.makedirs("src/data", exist_ok=True)
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
            os.makedirs("src/data", exist_ok=True)
            with open(self.responders_file, 'w') as f:
                json.dump(self.autoresponders, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving auto responders: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for auto responder triggers - DO NOT PROCESS COMMANDS"""
        if not message.guild or message.author.bot:
            return
        
        # Check if this is a command - if so, don't trigger autoresponders
        ctx = await self.bot.get_context(message)
        if ctx.command:
            return  # Don't respond to commands
        
        guild_id = str(message.guild.id)
        if guild_id not in self.autoresponders:
            return
        
        guild_responders = self.autoresponders[guild_id]
        
        for trigger, responder_data in guild_responders.items():
            if not responder_data.get('enabled', True):
                continue
            
            # Check if message matches trigger (case-insensitive contains)
            if trigger.lower() in message.content.lower():
                response = responder_data['response']
                
                # Process variables in the response
                try:
                    from src.utils.variables import VariableProcessor
                    var_processor = VariableProcessor(self.bot)
                    processed_response = await var_processor.process_variables(
                        response,
                        user=message.author,
                        guild=message.guild,
                        channel=message.channel
                    )
                    # Ensure we got a string, not a coroutine
                    if isinstance(processed_response, str):
                        response = processed_response
                    else:
                        logger.warning(f"Variable processor returned non-string: {type(processed_response)}")
                        # Keep original response if processing failed
                except Exception as e:
                    logger.error(f"Error processing variables in autoresponder: {e}")
                    # Fall back to original response if variable processing fails
                
                # Check for embed references {embed: embed_name}
                embed_to_send = None
                if "{embed:" in response:
                    try:
                        import re
                        embed_pattern = r'\{embed:\s*([^}]+)\}'
                        embed_match = re.search(embed_pattern, response)
                        if embed_match:
                            embed_name = embed_match.group(1).strip()
                            
                            # Load saved embeds
                            saved_embeds_file = "src/data/saved_embeds.json"
                            try:
                                with open(saved_embeds_file, 'r') as f:
                                    saved_embeds = json.load(f)
                                
                                if embed_name in saved_embeds:
                                    embed_data = saved_embeds[embed_name]
                                    
                                    # Create embed from saved data
                                    embed_to_send = discord.Embed(
                                        title=embed_data.get("title"),
                                        description=embed_data.get("description"),
                                        color=embed_data.get("color", 0xCCFFD1)
                                    )
                                    
                                    # Add footer if present
                                    if "footer" in embed_data and embed_data["footer"].get("text"):
                                        embed_to_send.set_footer(text=embed_data["footer"]["text"])
                                    
                                    # Add image if present
                                    if "image" in embed_data and embed_data["image"].get("url"):
                                        embed_to_send.set_image(url=embed_data["image"]["url"])
                                    
                                    # Add thumbnail if present
                                    if "thumbnail" in embed_data and embed_data["thumbnail"].get("url"):
                                        embed_to_send.set_thumbnail(url=embed_data["thumbnail"]["url"])
                                    
                                    # Add fields if present
                                    if "fields" in embed_data:
                                        for field in embed_data["fields"]:
                                            embed_to_send.add_field(
                                                name=field.get("name", "Field"),
                                                value=field.get("value", "Value"),
                                                inline=field.get("inline", False)
                                            )
                                    
                                    # Remove embed reference from response
                                    response = re.sub(embed_pattern, "", response).strip()
                                
                            except FileNotFoundError:
                                logger.warning("No saved embeds file found")
                    except Exception as e:
                        logger.error(f"Error processing embed reference: {e}")
                
                # Send response and embed
                if embed_to_send and response:
                    # Send both text and embed
                    await message.channel.send(content=response, embed=embed_to_send)
                elif embed_to_send:
                    # Send only embed
                    await message.channel.send(embed=embed_to_send)
                elif response:
                    # Send only text
                    await message.channel.send(response)
                
                break  # Only trigger the first matching responder
    
    @commands.command(name="autoresponder", help="Create new auto responder with modern UI")
    @commands.has_permissions(administrator=True)
    async def autoresponder_create(self, ctx):
        """Create new auto responder with modern interactive UI
        
        Usage: `s.autoresponder`
        Opens modern interactive interface for creating auto responders
        
        Features:
        - Interactive modal forms for easy input
        - Real-time preview of trigger and response
        - Variable support with live examples
        - Built-in validation and error checking
        - Modern Discord UI components
        
        This is the recommended way to create auto responders.
        """
        # Create button view to open modal
        view = AutoResponderButtonView(self)
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Auto Responder Creator",
            description="Click the button below to create a new auto responder!",
            color=0xCCFFD1
        )
        await ctx.send(embed=embed, view=view, mention_author=False)
    
    @commands.command(name="autoresponderlist", help="List all server auto responders")
    @commands.has_permissions(administrator=True)
    async def autoresponderlist(self, ctx):
        """List all auto responders
        
        Usage: `s.autoresponderlist`
        Shows all configured auto responders with triggers, responses, and status
        
        Features:
        - Shows enabled/disabled status for each
        - Displays first 50 characters of each response
        - Shows up to 10 responders per page
        - Perfect for managing large collections
        """
        try:
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.autoresponders or not self.autoresponders[guild_id]:
                embed = discord.Embed(
                    title="No Auto Responders",
                    description=f"This server has no auto responders configured.\n\n"
                               f"**Get started:**\n"
                               f"`{ctx.prefix}autoresponder` - Create your first auto responder",
                    color=0xCCFFD1  # Bot's original embed color
                )
                embed.add_field(
                    name="Example Usage",
                    value=f"1. Run `{ctx.prefix}autoresponder`\n"
                          f"2. Fill in trigger: `hello`\n"
                          f"3. Fill in response: `Hello there! Welcome!`\n"
                          f"4. Submit the form",
                    inline=False
                )
                await ctx.send(embed=embed, mention_author=False)
                return
            
            responders = self.autoresponders[guild_id]
            
            # Create paginated embed
            embed = discord.Embed(
                title=f"Auto Responders ({len(responders)} total)",
                description=f"All configured auto responders for **{ctx.guild.name}**",
                color=0xCCFFD1  # Bot's original embed color
            )
            
            for i, (trigger, data) in enumerate(responders.items(), 1):
                status = f"{SPROUTS_CHECK} Enabled" if data.get('enabled', True) else f"Disabled"
                response_preview = data['response'][:50] + "..." if len(data['response']) > 50 else data['response']
                
                embed.add_field(
                    name=f"{i}. `{trigger}`",
                    value=f"**Status:** {status}\n**Response:** {response_preview}",
                    inline=False
                )
                
                # Limit to 10 responders per page
                if i >= 10:
                    embed.add_field(
                        name="More responders...",
                        value=f"Only showing first 10 responders. Total: {len(responders)}",
                        inline=False
                    )
                    break
            
            embed.set_footer(text=f"Use {ctx.prefix}autoresponderdelete <trigger> to remove a responder")
            await ctx.send(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error listing auto responders: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description="Failed to list auto responders.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, mention_author=False)
    
    @commands.command(name="autoresponderdelete", help="Delete an auto responder by trigger")
    @commands.has_permissions(administrator=True)
    async def autoresponderdelete(self, ctx, *, responder_id: str):
        """Delete an auto responder
        
        Usage: `s.autoresponderdelete <trigger>`
        Permanently removes an auto responder by its trigger word/phrase
        
        Examples:
        - `s.autoresponderdelete hello`
        - `s.autoresponderdelete welcome message`
        
        Features:
        - Permanent deletion with confirmation
        - Shows what was deleted for verification
        - Case-sensitive trigger matching
        """
        try:
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.autoresponders or responder_id not in self.autoresponders[guild_id]:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Auto Responder Not Found",
                    description=f"**No auto responder found for trigger:** `{responder_id}`\n\n"
                               f"**Available commands:**\n"
                               f"`{ctx.prefix}autoresponderlist` - View all auto responders\n"
                               f"`{ctx.prefix}autoresponder` - Create new responder",
                    color=EMBED_COLOR_ERROR
                )
                embed.add_field(
                    name="What you searched for:",
                    value=f"`{responder_id}`",
                    inline=False
                )
                await ctx.send(embed=embed, mention_author=False)
                return
            
            # Remove the responder
            removed_responder = self.autoresponders[guild_id].pop(responder_id)
            self.save_autoresponders()
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Auto Responder Deleted",
                description=f"Successfully deleted auto responder for trigger: `{responder_id}`",
                color=0x2ecc71  # SPROUTS_CHECK color - success
            )
            embed.add_field(name="Response", value=removed_responder['response'][:100] + "..." if len(removed_responder['response']) > 100 else removed_responder['response'], inline=False)
            
            await ctx.send(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error deleting auto responder: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description="Failed to delete auto responder.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, mention_author=False)

# Discord-based Auto Responder Creation System

class AutoResponderBuilderView(discord.ui.View):
    """Advanced Discord UI for auto responder creation"""
    
    def __init__(self, author, guild_id):
        super().__init__(timeout=600)
        self.author = author
        self.guild_id = guild_id
        self.responder_data = {
            "trigger": None,
            "response": None,
            "enabled": True
        }
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.author
    
    @discord.ui.button(label="Set Trigger", style=discord.ButtonStyle.primary)
    async def set_trigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Set auto responder trigger"""
        modal = AutoResponderTriggerModal(self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Set Response", style=discord.ButtonStyle.primary)
    async def set_response(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Set auto responder response"""
        modal = AutoResponderResponseModal(self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Preview", style=discord.ButtonStyle.secondary)
    async def preview_responder(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Preview the auto responder"""
        if not self.responder_data["trigger"] or not self.responder_data["response"]:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Incomplete Auto Responder",
                description="Please set both trigger and response first.",
                color=0xffea69
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Auto Responder Preview",
            color=0xCCFFD1
        )
        embed.add_field(
            name="Trigger",
            value=f"`{self.responder_data['trigger']}`",
            inline=False
        )
        embed.add_field(
            name="Response",
            value=self.responder_data["response"],
            inline=False
        )
        embed.add_field(
            name="Status",
            value="✅ Enabled" if self.responder_data["enabled"] else "❌ Disabled",
            inline=True
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Save Auto Responder", style=discord.ButtonStyle.success)
    async def save_responder(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Save the auto responder"""
        if not self.responder_data["trigger"] or not self.responder_data["response"]:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Cannot Save",
                description="Please set both trigger and response first.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get the auto responder cog
        auto_cog = interaction.client.get_cog('AutoResponders')
        if not auto_cog:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} System Error",
                description="Auto responder system not available.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Save the auto responder
        guild_id = str(self.guild_id)
        if guild_id not in auto_cog.autoresponders:
            auto_cog.autoresponders[guild_id] = {}
        
        auto_cog.autoresponders[guild_id][self.responder_data["trigger"]] = {
            "response": self.responder_data["response"],
            "enabled": self.responder_data["enabled"]
        }
        auto_cog.save_autoresponders()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Auto Responder Saved",
            description=f"Auto responder for `{self.responder_data['trigger']}` has been saved successfully!",
            color=0xCCFFD1
        )
        await interaction.response.send_message(embed=embed)
        self.stop()


class AutoResponderTriggerModal(discord.ui.Modal, title="Set Auto Responder Trigger"):
    def __init__(self, builder):
        super().__init__()
        self.builder = builder
    
    trigger_input = discord.ui.TextInput(
        label="Trigger Word/Phrase",
        placeholder="hello",
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        self.builder.responder_data["trigger"] = self.trigger_input.value.lower()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Trigger Set",
            description=f"Trigger set to: `{self.trigger_input.value}`",
            color=0xCCFFD1
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class AutoResponderResponseModal(discord.ui.Modal, title="Set Auto Responder Response"):
    def __init__(self, builder):
        super().__init__()
        self.builder = builder
    
    response_input = discord.ui.TextInput(
        label="Response Message",
        style=discord.TextStyle.paragraph,
        placeholder="Hello! How can I help you today?",
        max_length=2000
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        self.builder.responder_data["response"] = self.response_input.value
        
        preview = self.response_input.value[:100] + "..." if len(self.response_input.value) > 100 else self.response_input.value
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Response Set",
            description=f"Response set to:\n```{preview}```",
            color=0xCCFFD1
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class AutoResponderButtonView(discord.ui.View):
    """Simple button view to open autoresponder modal"""
    
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog
    
    @discord.ui.button(label="Create Auto Responder", style=discord.ButtonStyle.primary)
    async def create_autoresponder(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open the autoresponder creation modal"""
        modal = AutoResponderCreateModal(self.cog)
        await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(AutoResponders(bot))