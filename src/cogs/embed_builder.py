"""
SPROUTS Advanced Embed Builder System
Discord-native embed creation with modal forms, live preview, and professional features
"""

import discord
from discord.ext import commands
import json
import logging
import os
import re
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..emojis import SPROUTS_CHECK, SPROUTS_ERROR, SPROUTS_WARNING, SPROUTS_INFORMATION

# Define colors directly since config import may not work
EMBED_COLOR_NORMAL = 0x2ecc71
EMBED_COLOR_ERROR = 0xe74c3c  
EMBED_COLOR_SUCCESS = 0x57F287

logger = logging.getLogger(__name__)

class EmbedBuilder(commands.Cog):
    """SPROUTS Advanced Discord-Native Embed Builder"""
    
    def __init__(self, bot):
        self.bot = bot
        self.saved_embeds_file = "src/data/saved_embeds.json"
        self.templates_file = "src/data/embed_templates.json"
        self.ensure_files_exist()
        self.create_default_templates()
        logger.info("SPROUTS Embed Builder initialized")
    
    def ensure_files_exist(self):
        """Ensure embed data files exist"""
        for file_path in [self.saved_embeds_file, self.templates_file]:
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    json.dump({}, f, indent=2)

    def create_default_templates(self):
        """Create default professional templates"""
        try:
            with open(self.templates_file, 'r') as f:
                templates = json.load(f)
            
            if not templates:  # Only create if empty
                default_templates = {
                    "announcement": {
                        "title": f"{SPROUTS_CHECK} Server Announcement",
                        "description": "Important server information and updates",
                        "color": 0x5865F2,
                        "fields": [
                            {"name": "What's New", "value": "Add your announcement details here", "inline": False}
                        ],
                        "footer": {"text": "Stay updated with server news"}
                    },
                    "welcome": {
                        "title": f"{SPROUTS_CHECK} Welcome to the Server!",
                        "description": "We're excited to have you join our community",
                        "color": 0x57F287,
                        "fields": [
                            {"name": "Getting Started", "value": "Check out our rules and guides", "inline": False},
                            {"name": "Need Help?", "value": "Ask in our support channels", "inline": False}
                        ],
                        "footer": {"text": "Enjoy your stay!"}
                    },
                    "rules": {
                        "title": f"{SPROUTS_WARNING} Server Rules",
                        "description": "Please follow these rules to maintain a positive environment",
                        "color": 0xFEE75C,
                        "fields": [
                            {"name": "Rule 1", "value": "Be respectful to all members", "inline": False},
                            {"name": "Rule 2", "value": "No spam or inappropriate content", "inline": False},
                            {"name": "Rule 3", "value": "Use appropriate channels for discussions", "inline": False}
                        ],
                        "footer": {"text": "Thank you for keeping our community safe"}
                    },
                    "event": {
                        "title": f"{SPROUTS_INFORMATION} Upcoming Event",
                        "description": "Join us for an exciting community event!",
                        "color": 0xEB459E,
                        "fields": [
                            {"name": "📅 Date", "value": "Add event date here", "inline": True},
                            {"name": "⏰ Time", "value": "Add event time here", "inline": True},
                            {"name": "📍 Location", "value": "Add event location/channel", "inline": True},
                            {"name": "📝 Details", "value": "Add event description and requirements", "inline": False}
                        ],
                        "footer": {"text": "Don't miss out on the fun!"}
                    },
                    "support": {
                        "title": f"{SPROUTS_ERROR} Support Ticket",
                        "description": "We're here to help you with any questions or issues",
                        "color": 0xED4245,
                        "fields": [
                            {"name": "📞 Contact Info", "value": "Please provide your contact details", "inline": False},
                            {"name": "❓ Issue Description", "value": "Describe your problem in detail", "inline": False},
                            {"name": "📸 Screenshots", "value": "Include any relevant screenshots if applicable", "inline": False}
                        ],
                        "footer": {"text": "We'll respond as soon as possible"}
                    },
                    "info": {
                        "title": f"{SPROUTS_INFORMATION} Information",
                        "description": "Important information for our community",
                        "color": 0x00D9FF,
                        "fields": [
                            {"name": "📊 Key Points", "value": "Add your main information here", "inline": False},
                            {"name": "🔗 Resources", "value": "Include helpful links and resources", "inline": False}
                        ],
                        "footer": {"text": "Stay informed"}
                    }
                }
                
                with open(self.templates_file, 'w') as f:
                    json.dump(default_templates, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Error creating default templates: {e}")

    @commands.command(name="embed", aliases=["createembed", "embedcreate"])
    async def embed_create(self, ctx):
        """Create a professional embed using SPROUTS advanced system"""
        try:
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} SPROUTS Embed Builder",
                description="Professional Discord-native embed creation with advanced features and live preview.",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="Creation Methods",
                value=(
                    f"{SPROUTS_CHECK} **Interactive Builder** - Complete embed configuration\n"
                    f"{SPROUTS_INFORMATION} **Quick Builder** - Fast single-modal creation\n"
                    f"{SPROUTS_WARNING} **JSON Import** - Import from Glitchii's Embed Builder\n"
                    f"{SPROUTS_CHECK} **Templates** - Professional pre-made designs"
                ),
                inline=False
            )
            
            embed.add_field(
                name="Advanced Features",
                value=(
                    "• **Complete Configuration** - Title, description, author, footer, images\n"
                    "• **Field Management** - Add up to 25 custom fields with inline options\n"
                    "• **Live Preview** - See your embed before sending\n"
                    "• **Template System** - 6 professional templates included\n"
                    "• **JSON Export** - Export for external use\n"
                    "• **Advanced Colors** - Named colors + hex support"
                ),
                inline=False
            )
            
            embed.set_footer(
                text="Powered by SPROUTS Advanced Embed System",
                icon_url=ctx.author.display_avatar.url
            )
            
            view = EmbedBuilderView(ctx.author)
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error in embed command: {e}")
            await ctx.send(f"{SPROUTS_ERROR} An error occurred while starting the embed builder.")

    @commands.command(name="embedquick")
    async def embed_quick(self, ctx):
        """Quick embed creation modal"""
        try:
            modal = EmbedQuickModal()
            embed = discord.Embed(
                title=f"{SPROUTS_INFORMATION} Quick Embed Builder",
                description="Use the main `s.embed` command and select **Quick Builder** for fast embed creation.",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in embedquick command: {e}")
            await ctx.send(f"{SPROUTS_ERROR} An error occurred.")

class EmbedBuilderView(discord.ui.View):
    """Main embed builder interface with professional buttons"""
    
    def __init__(self, author):
        super().__init__(timeout=300)
        self.author = author
        self.embed_data = {
            "title": "",
            "description": "",
            "color": EMBED_COLOR_NORMAL,
            "fields": [],
            "footer": "",
            "image": "",
            "thumbnail": "",
            "author": ""
        }
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Only the command user can use this embed builder!", 
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(label="Interactive Builder", style=discord.ButtonStyle.primary, emoji=SPROUTS_CHECK)
    async def interactive_builder(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open complete embed configuration modal"""
        modal = EmbedCompleteModal(self.embed_data)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Quick Builder", style=discord.ButtonStyle.secondary, emoji=SPROUTS_INFORMATION)
    async def quick_builder(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open fast single-modal embed builder"""
        modal = EmbedQuickModal(self.embed_data)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Templates", style=discord.ButtonStyle.success, emoji=SPROUTS_CHECK)
    async def templates(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show embed templates"""
        try:
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Professional Embed Templates",
                description="Choose from carefully crafted professional templates:",
                color=EMBED_COLOR_NORMAL
            )
            
            templates = {
                "announcement": f"{SPROUTS_CHECK} Server Announcement - Important updates and news",
                "welcome": f"{SPROUTS_CHECK} Welcome Message - New member greetings", 
                "rules": f"{SPROUTS_WARNING} Server Rules - Community guidelines",
                "event": f"{SPROUTS_INFORMATION} Event Announcement - Community events",
                "support": f"{SPROUTS_ERROR} Support Ticket - Help and assistance",
                "info": f"{SPROUTS_INFORMATION} Information Display - General information"
            }
            
            template_list = "\n".join([f"• **{name.title()}** - {desc}" for name, desc in templates.items()])
            embed.add_field(name="Available Templates", value=template_list, inline=False)
            
            view = TemplateSelectView(self.author, self.embed_data)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing templates: {e}")
            await interaction.followup.send(f"{SPROUTS_ERROR} Error loading templates.", ephemeral=True)
    
    @discord.ui.button(label="JSON Import", style=discord.ButtonStyle.danger, emoji=SPROUTS_WARNING)
    async def json_import(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Import embed from JSON"""
        embed = discord.Embed(
            title=f"{SPROUTS_WARNING} JSON Import",
            description="Import embed JSON from external builders:",
            color=EMBED_COLOR_NORMAL
        )
        
        embed.add_field(
            name="External Builder",
            value="Use [Glitchii's Embed Builder](https://glitchii.github.io/embedbuilder/) to create your embed, then get the JSON and paste it below.",
            inline=False
        )
        
        embed.add_field(
            name="How to Import",
            value="1. Create your embed on the external website\n2. Get the JSON output\n3. Click 'Import JSON' below and paste it",
            inline=False
        )
        
        modal = JSONImportModal(self.embed_data)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji=SPROUTS_ERROR)
    async def cancel_builder(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the embed builder"""
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Embed Builder Cancelled",
            description="Embed builder session has been cancelled.",
            color=EMBED_COLOR_NORMAL
        )
        await interaction.response.edit_message(embed=embed, view=None)

class EmbedCompleteModal(discord.ui.Modal):
    """Complete embed configuration modal with all options"""
    
    def __init__(self, embed_data: dict):
        super().__init__(title="Complete Embed Builder")
        self.embed_data = embed_data
        
        self.title_input = discord.ui.TextInput(
            label="Embed Title",
            placeholder="Enter the main title for your embed...",
            max_length=256,
            required=False
        )
        
        self.description_input = discord.ui.TextInput(
            label="Description",
            placeholder="Enter the main content/description...",
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=False
        )
        
        self.author_input = discord.ui.TextInput(
            label="Author Text",
            placeholder="Author name (optional)...",
            max_length=256,
            required=False
        )
        
        self.footer_input = discord.ui.TextInput(
            label="Footer Text",
            placeholder="Footer text (optional)...",
            max_length=2048,
            required=False
        )
        
        self.config_input = discord.ui.TextInput(
            label="Config (image=url,thumbnail=url,color=hex)",
            placeholder="image=https://example.com/img.png,thumbnail=https://example.com/thumb.png,color=#5865F2",
            style=discord.TextStyle.paragraph,
            max_length=2000,
            required=False
        )
        
        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.author_input)
        self.add_item(self.footer_input)
        self.add_item(self.config_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Update embed data with all fields
            if self.title_input.value:
                self.embed_data["title"] = self.title_input.value
            if self.description_input.value:
                self.embed_data["description"] = self.description_input.value
            if self.author_input.value:
                self.embed_data["author"] = {"name": self.author_input.value}
            if self.footer_input.value:
                self.embed_data["footer"] = {"text": self.footer_input.value}
            
            # Parse configuration
            if self.config_input.value:
                self.parse_configuration(self.config_input.value)
            
            # Show preview with field management options
            view = EmbedAdvancedPreviewView(interaction.user, self.embed_data)
            embed = self.create_preview_embed()
            
            await interaction.response.send_message(
                content=f"{SPROUTS_CHECK} **Complete Embed Preview** - Add fields or send as-is:",
                embed=embed, 
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error in complete embed modal: {e}")
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} An error occurred while creating your embed.", 
                ephemeral=True
            )
    
    def parse_configuration(self, config_text: str):
        """Parse configuration from comma-separated format"""
        try:
            for item in config_text.split(','):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'image' and value.startswith('http'):
                        self.embed_data["image"] = {"url": value}
                    elif key == 'thumbnail' and value.startswith('http'):
                        self.embed_data["thumbnail"] = {"url": value}
                    elif key == 'color':
                        color = self.parse_color(value)
                        if color is not None:
                            self.embed_data["color"] = color
        except Exception as e:
            logger.error(f"Error parsing configuration: {e}")
    
    def parse_color(self, color_str: str):
        """Parse color string to hex integer"""
        color_str = color_str.strip().lower()
        
        # Color name mapping
        color_names = {
            "red": 0xED4245, "green": 0x57F287, "blue": 0x5865F2,
            "yellow": 0xFEE75C, "purple": 0x9B59B6, "orange": 0xE67E22,
            "pink": 0xEB459E, "cyan": 0x1ABC9C, "grey": 0x95A5A6,
            "gray": 0x95A5A6, "black": 0x2C2F33, "white": 0xFFFFFF,
            "discord": 0x5865F2, "success": 0x57F287, "warning": 0xFEE75C,
            "error": 0xED4245, "info": 0x00D9FF, "sprouts": 0x2ecc71
        }
        
        if color_str in color_names:
            return color_names[color_str]
        
        # Parse hex color
        if color_str.startswith('#'):
            try:
                return int(color_str[1:], 16)
            except ValueError:
                return None
        
        # Try as direct hex
        try:
            return int(color_str, 16) if len(color_str) <= 6 else None
        except ValueError:
            return None
    
    def create_preview_embed(self) -> discord.Embed:
        """Create comprehensive embed preview"""
        embed = discord.Embed(
            title=self.embed_data.get("title") or None,
            description=self.embed_data.get("description") or None,
            color=self.embed_data.get("color", EMBED_COLOR_NORMAL)
        )
        
        # Add author
        if self.embed_data.get("author"):
            author_data = self.embed_data["author"]
            embed.set_author(name=author_data.get("name", ""))
        
        # Add footer
        if self.embed_data.get("footer"):
            footer_data = self.embed_data["footer"]
            embed.set_footer(text=footer_data.get("text", ""))
        
        # Add image
        if self.embed_data.get("image"):
            embed.set_image(url=self.embed_data["image"]["url"])
        
        # Add thumbnail
        if self.embed_data.get("thumbnail"):
            embed.set_thumbnail(url=self.embed_data["thumbnail"]["url"])
        
        # Add fields
        for field in self.embed_data.get("fields", []):
            embed.add_field(
                name=field.get("name", "Field"),
                value=field.get("value", "Value"),
                inline=field.get("inline", False)
            )
        
        return embed

class EmbedQuickModal(discord.ui.Modal):
    """Quick all-in-one embed creation modal"""
    
    def __init__(self, embed_data: dict = None):
        super().__init__(title="Quick Embed Builder")
        self.embed_data = embed_data or {}
        
        self.content_input = discord.ui.TextInput(
            label="Embed Content (JSON or simple text)",
            placeholder='{"title": "My Title", "description": "My content"} OR just type your message...',
            style=discord.TextStyle.paragraph,
            max_length=2000,
            required=True
        )
        
        self.add_item(self.content_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            content = self.content_input.value.strip()
            
            # Try to parse as JSON first
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    embed = discord.Embed.from_dict(data)
                    await interaction.response.send_message(
                        f"{SPROUTS_CHECK} **Quick Embed Created!**",
                        embed=embed
                    )
                    return
            except json.JSONDecodeError:
                pass
            
            # Create simple text embed
            embed = discord.Embed(
                description=content,
                color=EMBED_COLOR_NORMAL
            )
            
            await interaction.response.send_message(
                f"{SPROUTS_CHECK} **Quick Embed Created!**",
                embed=embed
            )
            
        except Exception as e:
            logger.error(f"Error in quick embed modal: {e}")
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Error creating embed: {str(e)}", 
                ephemeral=True
            )

class EmbedAdvancedPreviewView(discord.ui.View):
    """Advanced preview with field management and final actions"""
    
    def __init__(self, author, embed_data: dict):
        super().__init__(timeout=300)
        self.author = author
        self.embed_data = embed_data
    
    @discord.ui.button(label="Add Field", style=discord.ButtonStyle.primary, emoji=SPROUTS_CHECK)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add a field to the embed"""
        modal = FieldAddModal(self.embed_data)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Send Embed", style=discord.ButtonStyle.success, emoji=SPROUTS_CHECK)
    async def send_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Send the embed to the channel"""
        try:
            embed = self.create_final_embed()
            
            # Get the original channel from the interaction
            channel = interaction.channel
            if channel and hasattr(channel, 'send'):
                await channel.send(embed=embed)
                await interaction.response.send_message(
                    f"{SPROUTS_CHECK} Embed sent successfully!", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{SPROUTS_ERROR} Could not send embed to this channel.", ephemeral=True
                )
            
        except Exception as e:
            logger.error(f"Error sending embed: {e}")
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Error sending embed: {str(e)}", ephemeral=True
            )
    
    @discord.ui.button(label="Export JSON", style=discord.ButtonStyle.secondary, emoji=SPROUTS_INFORMATION)
    async def export_json(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Export embed as JSON"""
        try:
            # Create clean embed dict for export
            export_data = {
                "embeds": [self.embed_data]
            }
            json_str = json.dumps(export_data, indent=2)
            
            await interaction.response.send_message(
                f"{SPROUTS_CHECK} **Embed JSON Export:**\n```json\n{json_str[:1800]}{'...' if len(json_str) > 1800 else ''}\n```\n\n"
                f"**Tip:** Use this JSON with [Glitchii's Embed Builder](https://glitchii.github.io/embedbuilder/) for advanced editing!",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Error exporting JSON.", ephemeral=True
            )
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji=SPROUTS_ERROR)
    async def cancel_preview(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the embed preview"""
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Embed Builder Cancelled",
            description="Embed preview session has been cancelled.",
            color=EMBED_COLOR_NORMAL
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    def create_final_embed(self) -> discord.Embed:
        """Create the final embed for sending"""
        embed = discord.Embed(
            title=self.embed_data.get("title"),
            description=self.embed_data.get("description"),
            color=self.embed_data.get("color", EMBED_COLOR_NORMAL)
        )
        
        # Add author
        if self.embed_data.get("author"):
            author_data = self.embed_data["author"]
            embed.set_author(name=author_data.get("name", ""))
        
        # Add footer
        if self.embed_data.get("footer"):
            footer_data = self.embed_data["footer"]
            embed.set_footer(text=footer_data.get("text", ""))
        
        # Add image
        if self.embed_data.get("image"):
            embed.set_image(url=self.embed_data["image"]["url"])
        
        # Add thumbnail
        if self.embed_data.get("thumbnail"):
            embed.set_thumbnail(url=self.embed_data["thumbnail"]["url"])
        
        # Add fields
        for field in self.embed_data.get("fields", []):
            embed.add_field(
                name=field.get("name", "Field"),
                value=field.get("value", "Value"),
                inline=field.get("inline", False)
            )
        
        return embed

class FieldAddModal(discord.ui.Modal):
    """Modal for adding fields to embeds"""
    
    def __init__(self, embed_data: dict):
        super().__init__(title="Add Embed Field")
        self.embed_data = embed_data
        
        self.name_input = discord.ui.TextInput(
            label="Field Name",
            placeholder="Enter field title...",
            max_length=256,
            required=True
        )
        
        self.value_input = discord.ui.TextInput(
            label="Field Value",
            placeholder="Enter field content...",
            style=discord.TextStyle.paragraph,
            max_length=1024,
            required=True
        )
        
        self.inline_input = discord.ui.TextInput(
            label="Inline (yes/no)",
            placeholder="Type 'yes' for inline, 'no' for full width",
            max_length=3,
            required=False
        )
        
        self.add_item(self.name_input)
        self.add_item(self.value_input)
        self.add_item(self.inline_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parse inline setting
            inline = self.inline_input.value.lower().strip() in ['yes', 'y', 'true', '1']
            
            # Add field to embed data
            if "fields" not in self.embed_data:
                self.embed_data["fields"] = []
            
            self.embed_data["fields"].append({
                "name": self.name_input.value,
                "value": self.value_input.value,
                "inline": inline
            })
            
            # Create updated preview
            embed = discord.Embed(
                title=self.embed_data.get("title"),
                description=self.embed_data.get("description"),
                color=self.embed_data.get("color", EMBED_COLOR_NORMAL)
            )
            
            # Add all components
            if self.embed_data.get("author"):
                embed.set_author(name=self.embed_data["author"]["name"])
            if self.embed_data.get("footer"):
                embed.set_footer(text=self.embed_data["footer"]["text"])
            if self.embed_data.get("image"):
                embed.set_image(url=self.embed_data["image"]["url"])
            if self.embed_data.get("thumbnail"):
                embed.set_thumbnail(url=self.embed_data["thumbnail"]["url"])
            
            for field in self.embed_data.get("fields", []):
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field["inline"]
                )
            
            view = EmbedAdvancedPreviewView(interaction.user, self.embed_data)
            await interaction.response.send_message(
                f"{SPROUTS_CHECK} **Field Added!** Updated embed preview:",
                embed=embed,
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error adding field: {e}")
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Error adding field.", ephemeral=True
            )

class TemplateSelectView(discord.ui.View):
    """Template selection interface"""
    
    def __init__(self, author, embed_data: dict):
        super().__init__(timeout=300)
        self.author = author
        self.embed_data = embed_data
    
    @discord.ui.select(
        placeholder="Choose a template...",
        options=[
            discord.SelectOption(label="Announcement", value="announcement", emoji=SPROUTS_CHECK),
            discord.SelectOption(label="Welcome", value="welcome", emoji=SPROUTS_CHECK),
            discord.SelectOption(label="Rules", value="rules", emoji=SPROUTS_WARNING),
            discord.SelectOption(label="Event", value="event", emoji=SPROUTS_INFORMATION),
            discord.SelectOption(label="Support", value="support", emoji=SPROUTS_ERROR),
            discord.SelectOption(label="Info", value="info", emoji=SPROUTS_INFORMATION)
        ]
    )
    async def template_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        try:
            # Load template
            with open("src/data/embed_templates.json", 'r') as f:
                templates = json.load(f)
            
            template_name = select.values[0]
            if template_name in templates:
                template = templates[template_name]
                
                # Create embed from template
                embed = discord.Embed(
                    title=template.get("title", ""),
                    description=template.get("description", ""),
                    color=template.get("color", EMBED_COLOR_NORMAL)
                )
                
                # Add fields
                for field in template.get("fields", []):
                    embed.add_field(
                        name=field["name"],
                        value=field["value"],
                        inline=field.get("inline", False)
                    )
                
                if template.get("footer"):
                    embed.set_footer(text=template["footer"]["text"])
                
                # Show template preview with edit options
                view = TemplateEditView(interaction.user, template, template_name)
                
                await interaction.response.send_message(
                    f"{SPROUTS_CHECK} **Template Preview: {template_name.title()}**\n"
                    "You can edit this template or send it as-is:",
                    embed=embed,
                    view=view,
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{SPROUTS_ERROR} Template not found.", ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Error loading template.", ephemeral=True
            )

class TemplateEditView(discord.ui.View):
    """Template editing and sending interface"""
    
    def __init__(self, author, template_data: dict, template_name: str):
        super().__init__(timeout=300)
        self.author = author
        self.template_data = template_data
        self.template_name = template_name
    
    @discord.ui.button(label="Send Template", style=discord.ButtonStyle.success, emoji=SPROUTS_CHECK)
    async def send_template(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Send the template as-is"""
        try:
            embed = discord.Embed(
                title=self.template_data.get("title", ""),
                description=self.template_data.get("description", ""),
                color=self.template_data.get("color", EMBED_COLOR_NORMAL)
            )
            
            for field in self.template_data.get("fields", []):
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )
            
            if self.template_data.get("footer"):
                embed.set_footer(text=self.template_data["footer"]["text"])
            
            # Send to original channel
            channel = interaction.channel
            if channel and hasattr(channel, 'send'):
                await channel.send(embed=embed)
                await interaction.response.send_message(
                    f"{SPROUTS_CHECK} Template sent successfully!", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{SPROUTS_ERROR} Could not send to channel.", ephemeral=True
                )
            
        except Exception as e:
            logger.error(f"Error sending template: {e}")
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Error sending template.", ephemeral=True
            )
    
    @discord.ui.button(label="Edit Template", style=discord.ButtonStyle.primary, emoji=SPROUTS_WARNING)
    async def edit_template(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open template for editing"""
        modal = TemplateEditModal(self.template_data)
        await interaction.response.send_modal(modal)

class TemplateEditModal(discord.ui.Modal):
    """Modal for editing template content"""
    
    def __init__(self, template_data: dict):
        super().__init__(title="Edit Template")
        self.template_data = template_data
        
        self.title_input = discord.ui.TextInput(
            label="Title",
            default=template_data.get("title", ""),
            max_length=256,
            required=False
        )
        
        self.description_input = discord.ui.TextInput(
            label="Description",
            default=template_data.get("description", ""),
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=False
        )
        
        footer_text = ""
        if template_data.get("footer") and isinstance(template_data["footer"], dict):
            footer_text = template_data["footer"].get("text", "")
        
        self.footer_input = discord.ui.TextInput(
            label="Footer",
            default=footer_text,
            max_length=2048,
            required=False
        )
        
        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.footer_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Update template data
            updated_template = self.template_data.copy()
            updated_template["title"] = self.title_input.value
            updated_template["description"] = self.description_input.value
            updated_template["footer"] = {"text": self.footer_input.value}
            
            # Create updated embed
            embed = discord.Embed(
                title=updated_template["title"],
                description=updated_template["description"],
                color=updated_template.get("color", EMBED_COLOR_NORMAL)
            )
            
            for field in updated_template.get("fields", []):
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )
            
            if updated_template["footer"]["text"]:
                embed.set_footer(text=updated_template["footer"]["text"])
            
            # Send updated embed
            channel = interaction.channel
            if channel and hasattr(channel, 'send'):
                await channel.send(embed=embed)
                await interaction.response.send_message(
                    f"{SPROUTS_CHECK} **Updated Template Sent!**", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{SPROUTS_ERROR} Could not send to channel.", ephemeral=True
                )
            
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Error updating template.", ephemeral=True
            )

class JSONImportModal(discord.ui.Modal):
    """Modal for importing embed from JSON"""
    
    def __init__(self, embed_data: dict):
        super().__init__(title="JSON Import")
        self.embed_data = embed_data
        
        self.json_input = discord.ui.TextInput(
            label="Embed JSON",
            placeholder='Get JSON from: https://glitchii.github.io/embedbuilder/ - Paste here...',
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=True
        )
        
        self.add_item(self.json_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            json_data = json.loads(self.json_input.value)
            
            # Handle different JSON formats
            embed_dict = None
            if "embeds" in json_data and isinstance(json_data["embeds"], list) and json_data["embeds"]:
                embed_dict = json_data["embeds"][0]
            elif "embed" in json_data:
                embed_dict = json_data["embed"]
            else:
                embed_dict = json_data
            
            # Create embed from JSON
            embed = discord.Embed.from_dict(embed_dict)
            
            view = EmbedAdvancedPreviewView(interaction.user, embed_dict)
            
            await interaction.response.send_message(
                f"{SPROUTS_CHECK} **JSON Import Successful!** Here's your embed:",
                embed=embed,
                view=view,
                ephemeral=True
            )
            
        except json.JSONDecodeError as e:
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Invalid JSON format: {str(e)}", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error importing JSON: {e}")
            await interaction.response.send_message(
                f"{SPROUTS_ERROR} Error importing embed: {str(e)}", ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))