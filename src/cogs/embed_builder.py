"""
Discord Bot Embed Builder - Enhanced Select Menu System
A powerful embed builder with organized select menus and modals
"""

import discord
from discord.ext import commands
import logging
import json
import os
import yaml
import asyncio
import io
from datetime import datetime
from typing import Optional, Dict, Any
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from src.emojis import SPROUTS_CHECK, SPROUTS_ERROR, SPROUTS_WARNING
from src.utils.variables import VariableProcessor

logger = logging.getLogger(__name__)

class EmbedData:
    """Simple file-based data storage for embeds"""
    
    @staticmethod
    def load_embeds():
        """Load saved embeds from file"""
        try:
            if os.path.exists("src/data/saved_embeds.json"):
                with open("src/data/saved_embeds.json", 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading embeds: {e}")
        return {}
    
    @staticmethod
    def save_embeds(embeds_data):
        """Save embeds to file"""
        try:
            os.makedirs("src/data", exist_ok=True)
            with open("src/data/saved_embeds.json", 'w') as f:
                json.dump(embeds_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving embeds: {e}")


class EmbedEditor:
    """Interactive embed editor with enhanced select menu interface"""
    
    def __init__(self, bot, embed_data, user_id):
        self.bot = bot
        self.embed_data = embed_data
        self.user_id = user_id
        self.timeout_task = None
    
    def create_view(self):
        """Create the interactive view with organized select menus"""
        view = EmbedEditorView(self)
        return view
    
    def generate_preview_embed(self, ctx):
        """Generate preview embed"""
        title = self.embed_data.get('title')
        description = self.embed_data.get('description')
        
        # Ensure at least one of title or description exists
        if not title and not description:
            description = "*Preview will appear here as you add content*"
        
        embed = discord.Embed(
            title=title or None,
            description=description or None,
            color=self.embed_data.get('color', EMBED_COLOR_NORMAL)
        )
        
        # Add author
        if self.embed_data.get('author_name'):
            embed.set_author(
                name=self.embed_data['author_name'],
                icon_url=self.embed_data.get('author_icon') or None
            )
        
        # Add footer
        if self.embed_data.get('footer_text'):
            embed.set_footer(
                text=self.embed_data['footer_text'],
                icon_url=self.embed_data.get('footer_icon') or None
            )
        
        # Add thumbnail and image
        if self.embed_data.get('thumbnail'):
            embed.set_thumbnail(url=self.embed_data['thumbnail'])
        
        if self.embed_data.get('image'):
            embed.set_image(url=self.embed_data['image'])
        
        # Add fields
        for field in self.embed_data.get('fields', []):
            embed.add_field(
                name=field['name'],
                value=field['value'],
                inline=field.get('inline', False)
            )
        
        return embed
    
    def generate_info_embed(self, ctx, message="Use the organized dropdowns below to edit your embed."):
        """Generate the editing interface info embed"""
        fields_count = len(self.embed_data.get('fields', []))
        
        embed = discord.Embed(
            title=f"Editing: {self.embed_data.get('name', 'untitled')}",
            description=f"{message}\n\n**Tip:** Variables like `$(user.name)` are supported!",
            color=EMBED_COLOR_NORMAL
        )
        
        # Show current content summary
        content_summary = []
        if self.embed_data.get('title'):
            content_summary.append("Title")
        if self.embed_data.get('description'):
            content_summary.append("Description")
        if self.embed_data.get('author_name'):
            content_summary.append("Author")
        if self.embed_data.get('footer_text'):
            content_summary.append("Footer")
        if self.embed_data.get('thumbnail'):
            content_summary.append("Thumbnail")
        if self.embed_data.get('image'):
            content_summary.append("Image")
        if fields_count > 0:
            content_summary.append(f"{fields_count} Field{'s' if fields_count != 1 else ''}")
        
        if content_summary:
            embed.add_field(
                name="Current Content",
                value=" • ".join(content_summary) if content_summary else "None",
                inline=False
            )
        
        embed.set_footer(text="Pro tip: Use the Preview option to see exactly how your embed will look!")
        
        return embed

class EmbedEditorView(discord.ui.View):
    """Simplified view for embed editing with single select menu"""
    
    def __init__(self, editor):
        super().__init__(timeout=900)  # 15 minute timeout
        self.editor = editor
    
    @discord.ui.select(
        placeholder="Choose what to edit...",
        options=[
            discord.SelectOption(label="Edit Title", value="title", description="Set embed title"),
            discord.SelectOption(label="Edit Description", value="description", description="Set embed text"),
            discord.SelectOption(label="Edit Color", value="color", description="Change embed color"),
            discord.SelectOption(label="Set Author", value="author", description="Set author name/icon"),
            discord.SelectOption(label="Set Footer", value="footer", description="Set footer text/icon"),
            discord.SelectOption(label="Set Thumbnail", value="thumbnail", description="Add thumbnail"),
            discord.SelectOption(label="Set Image", value="image", description="Add main image"),
            discord.SelectOption(label="Add Field", value="add_field", description="Add new field"),
            discord.SelectOption(label="Edit Field", value="edit_field", description="Modify field"),
            discord.SelectOption(label="Remove Field", value="remove_field", description="Delete field"),
            discord.SelectOption(label="Clear Fields", value="clear_fields", description="Remove all fields"),
            discord.SelectOption(label="Preview Embed", value="preview", description="See embed preview"),
            discord.SelectOption(label="Clear Embed", value="clear", description="Reset embed"),
            discord.SelectOption(label="Rename Embed", value="rename", description="Change embed name"),
        ],
        row=0
    )
    async def main_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Handle all embed editing actions"""
        if interaction.user.id != self.editor.user_id:
            await interaction.response.send_message("You cannot edit someone else's embed!", ephemeral=True)
            return
        
        action = select.values[0]
        
        # Handle special actions directly
        if action == "clear":
            self.editor.embed_data = {
                'name': self.editor.embed_data.get('name', 'untitled'),
                'title': '',
                'description': '',
                'color': EMBED_COLOR_NORMAL,
                'author_name': '',
                'author_icon': '',
                'footer_text': '',
                'footer_icon': '',
                'thumbnail': '',
                'image': '',
                'fields': []
            }
            await self.update_embed(interaction, "Embed cleared! Ready for new content.")
        elif action == "preview":
            preview_embed = self.editor.generate_preview_embed(interaction)
            preview_embed.set_footer(text="This is how your embed will look when sent")
            await interaction.response.send_message(embed=preview_embed, ephemeral=True)
        elif action == "clear_fields":
            self.editor.embed_data['fields'] = []
            await self.update_embed(interaction, "All fields cleared!")
        elif action == "edit_field":
            if not self.editor.embed_data.get('fields'):
                await interaction.response.send_message("No fields to edit! Add a field first.", ephemeral=True)
                return
            modal = FieldSelectModal(self.editor, "edit")
            await interaction.response.send_modal(modal)
        elif action == "remove_field":
            if not self.editor.embed_data.get('fields'):
                await interaction.response.send_message("No fields to remove!", ephemeral=True)
                return
            modal = FieldSelectModal(self.editor, "remove")
            await interaction.response.send_modal(modal)
        elif action == "add_field":
            modal = EmbedEditModal(self.editor, "field")
            await interaction.response.send_modal(modal)
        elif action == "rename":
            modal = EmbedEditModal(self.editor, "rename")
            await interaction.response.send_modal(modal)
        else:
            modal = EmbedEditModal(self.editor, action)
            await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Save & Finish", style=discord.ButtonStyle.green, row=1)
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Finish editing and save"""
        if interaction.user.id != self.editor.user_id:
            await interaction.response.send_message("You cannot edit someone else's embed!", ephemeral=True)
            return
        
        # Auto-save the embed
        user_id = str(interaction.user.id)
        embed_name = self.editor.embed_data.get('name', 'untitled')
        
        # Get the cog instance to save
        embed_cog = interaction.client.get_cog('EmbedBuilder')
        if embed_cog:
            # Check if user is admin and save to guild-level embeds
            if interaction.guild and hasattr(interaction.user, 'guild_permissions') and interaction.user.guild_permissions.administrator:
                guild_id = str(interaction.guild.id)
                if guild_id not in embed_cog.saved_embeds:
                    embed_cog.saved_embeds[guild_id] = {}
                embed_cog.saved_embeds[guild_id][embed_name] = self.editor.embed_data.copy()
            else:
                # Save to user-level embeds for regular users (server-specific)
                guild_id = str(interaction.guild.id) if interaction.guild else "dm"
                user_guild_key = f"{user_id}_{guild_id}"
                if user_guild_key not in embed_cog.saved_embeds:
                    embed_cog.saved_embeds[user_guild_key] = {}
                embed_cog.saved_embeds[user_guild_key][embed_name] = self.editor.embed_data.copy()
            
            embed_cog.save_embeds()
        
        embed = discord.Embed(
            description=f"Embed '**{embed_name}**' saved successfully!\n\n"
                       f"Use `{ctx.prefix}embedlist` to see your saved embeds\n"
                       f"Use `{ctx.prefix}embedview {embed_name}` to preview it",
            color=EMBED_COLOR_NORMAL
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, row=1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel editing"""
        if interaction.user.id != self.editor.user_id:
            await interaction.response.send_message("You cannot edit someone else's embed!", ephemeral=True)
            return
        
        embed = discord.Embed(
            description="Embed editing cancelled.",
            color=EMBED_COLOR_ERROR
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def update_embed(self, interaction, message=None):
        """Update the embed display"""
        info_embed = self.editor.generate_info_embed(interaction, message)
        preview_embed = self.editor.generate_preview_embed(interaction)
        view = EmbedEditorView(self.editor)
        await interaction.response.edit_message(embeds=[info_embed, preview_embed], view=view)

class FieldSelectModal(discord.ui.Modal):
    """Modal for selecting which field to edit or remove"""
    
    def __init__(self, editor, action_type):
        self.editor = editor
        self.action_type = action_type  # "edit" or "remove"
        
        title = "Select Field to Edit" if action_type == "edit" else "Select Field to Remove"
        super().__init__(title=title)
        
        # Create field selection text input
        field_list = "\n".join([
            f"{i+1}. {field['name'][:50]}{'...' if len(field['name']) > 50 else ''}"
            for i, field in enumerate(editor.embed_data.get('fields', []))
        ])
        
        self.add_item(discord.ui.TextInput(
            label=f"Enter number (1-{len(editor.embed_data.get('fields', []))})",
            placeholder="Enter the field number to edit/remove...",
            default="",
            max_length=2
        ))
        
        # Show current fields as read-only
        if field_list:
            self.add_item(discord.ui.TextInput(
                label="Available Fields:",
                default=field_list,
                style=discord.TextStyle.paragraph,
                required=False,
                max_length=1000
            ))
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle field selection"""
        try:
            field_num = int(self.children[0].value) - 1
            fields = self.editor.embed_data.get('fields', [])
            
            if field_num < 0 or field_num >= len(fields):
                await interaction.response.send_message("Invalid field number!", ephemeral=True)
                return
            
            if self.action_type == "remove":
                removed_field = fields.pop(field_num)
                self.editor.embed_data['fields'] = fields
                
                # Update the embed display
                info_embed = self.editor.generate_info_embed(interaction, f"Field '{removed_field['name']}' removed successfully!")
                preview_embed = self.editor.generate_preview_embed(interaction)
                view = EmbedEditorView(self.editor)
                await interaction.response.edit_message(embeds=[info_embed, preview_embed], view=view)
                
            elif self.action_type == "edit":
                # Open modal to edit the selected field
                selected_field = fields[field_num]
                modal = EmbedEditModal(self.editor, "edit_existing_field", field_num, selected_field)
                await interaction.response.send_modal(modal)
                
        except ValueError:
            await interaction.response.send_message("Please enter a valid number!", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in field selection: {e}")
            await interaction.response.send_message("An error occurred while processing the field selection.", ephemeral=True)

class EmbedEditModal(discord.ui.Modal):
    """Enhanced modal for editing embed properties"""
    
    def __init__(self, editor, action, field_index=None, field_data=None):
        self.editor = editor
        self.action = action
        self.field_index = field_index
        self.field_data = field_data
        
        title_map = {
            "title": "Edit Embed Title",
            "description": "Edit Embed Description", 
            "color": "Set Embed Color",
            "author": "Set Embed Author",
            "footer": "Set Embed Footer",
            "thumbnail": "Set Thumbnail URL",
            "image": "Set Image URL",
            "field": "Add Embed Field",
            "edit_existing_field": "Edit Existing Field",
            "rename": "Rename Embed"
        }
        
        super().__init__(title=title_map.get(action, "Edit Embed"))
        
        # Add appropriate inputs based on action
        if action == "title":
            self.add_item(discord.ui.TextInput(
                label="Title",
                placeholder="Enter embed title...",
                default=self.editor.embed_data.get('title', ''),
                max_length=256
            ))
        
        elif action == "description":
            self.add_item(discord.ui.TextInput(
                label="Description",
                placeholder="Enter embed description...",
                default=self.editor.embed_data.get('description', ''),
                style=discord.TextStyle.paragraph,
                max_length=4000
            ))
        
        elif action == "color":
            current_color = self.editor.embed_data.get('color', EMBED_COLOR_NORMAL)
            self.add_item(discord.ui.TextInput(
                label="Color (hex code)",
                placeholder="#c2ffe0 or c2ffe0",
                default=f"#{current_color:06x}",
                max_length=7
            ))
        
        elif action == "author":
            self.add_item(discord.ui.TextInput(
                label="Author Name",
                placeholder="Enter author name...",
                default=self.editor.embed_data.get('author_name', ''),
                max_length=256
            ))
            self.add_item(discord.ui.TextInput(
                label="Author Icon URL (optional)",
                placeholder="https://example.com/icon.png",
                default=self.editor.embed_data.get('author_icon', ''),
                required=False,
                max_length=500
            ))
        
        elif action == "footer":
            self.add_item(discord.ui.TextInput(
                label="Footer Text",
                placeholder="Enter footer text...",
                default=self.editor.embed_data.get('footer_text', ''),
                max_length=2048
            ))
            self.add_item(discord.ui.TextInput(
                label="Footer Icon URL (optional)",
                placeholder="https://example.com/icon.png",
                default=self.editor.embed_data.get('footer_icon', ''),
                required=False,
                max_length=500
            ))
        
        elif action in ["thumbnail", "image"]:
            self.add_item(discord.ui.TextInput(
                label=f"{action.title()} URL",
                placeholder="https://example.com/image.png",
                default=self.editor.embed_data.get(action, ''),
                max_length=500
            ))
        
        elif action == "rename":
            self.add_item(discord.ui.TextInput(
                label="New Embed Name",
                placeholder="Enter new name for this embed...",
                default=self.editor.embed_data.get('name', ''),
                max_length=50
            ))
        
        elif action == "field":
            self.add_item(discord.ui.TextInput(
                label="Field Name",
                placeholder="Enter field name...",
                max_length=256
            ))
            self.add_item(discord.ui.TextInput(
                label="Field Value",
                placeholder="Enter field value...",
                style=discord.TextStyle.paragraph,
                max_length=1024
            ))
            self.add_item(discord.ui.TextInput(
                label="Inline (true/false)",
                placeholder="true or false",
                default="false",
                max_length=5
            ))
        
        elif action == "edit_existing_field" and field_data:
            self.add_item(discord.ui.TextInput(
                label="Field Name",
                placeholder="Enter field name...",
                default=field_data.get('name', ''),
                max_length=256
            ))
            self.add_item(discord.ui.TextInput(
                label="Field Value",
                placeholder="Enter field value...",
                default=field_data.get('value', ''),
                style=discord.TextStyle.paragraph,
                max_length=1024
            ))
            self.add_item(discord.ui.TextInput(
                label="Inline (true/false)",
                placeholder="true or false",
                default="true" if field_data.get('inline', False) else "false",
                max_length=5
            ))
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        try:
            # Get form values safely
            def get_form_value(index, default=""):
                try:
                    if len(self.children) > index and hasattr(self.children[index], 'value'):
                        return self.children[index].value or default
                    return default
                except:
                    return default
            
            if self.action == "title":
                self.editor.embed_data['title'] = get_form_value(0)
            
            elif self.action == "description":
                self.editor.embed_data['description'] = get_form_value(0)
            
            elif self.action == "color":
                color_str = get_form_value(0).strip().replace('#', '')
                try:
                    if color_str:
                        self.editor.embed_data['color'] = int(color_str, 16)
                except ValueError:
                    await interaction.response.send_message("Invalid color format! Use hex like #c2ffe0", ephemeral=True)
                    return
            
            elif self.action == "author":
                self.editor.embed_data['author_name'] = get_form_value(0)
                self.editor.embed_data['author_icon'] = get_form_value(1)
            
            elif self.action == "footer":
                self.editor.embed_data['footer_text'] = get_form_value(0)
                self.editor.embed_data['footer_icon'] = get_form_value(1)
            
            elif self.action in ["thumbnail", "image"]:
                self.editor.embed_data[self.action] = get_form_value(0)
            
            elif self.action == "rename":
                new_name = get_form_value(0, "untitled").strip()
                if new_name:
                    self.editor.embed_data['name'] = new_name
                else:
                    await interaction.response.send_message("Embed name cannot be empty!", ephemeral=True)
                    return
            
            elif self.action == "field":
                field_name = get_form_value(0, "Untitled Field")
                field_value = get_form_value(1, "No value")
                inline = get_form_value(2, "false").lower() == "true"
                
                if 'fields' not in self.editor.embed_data:
                    self.editor.embed_data['fields'] = []
                
                self.editor.embed_data['fields'].append({
                    'name': field_name,
                    'value': field_value,
                    'inline': inline
                })
            
            elif self.action == "edit_existing_field" and self.field_index is not None:
                field_name = get_form_value(0, "Untitled Field")
                field_value = get_form_value(1, "No value")
                inline = get_form_value(2, "false").lower() == "true"
                
                if 'fields' not in self.editor.embed_data:
                    self.editor.embed_data['fields'] = []
                
                # Update the existing field
                if self.field_index < len(self.editor.embed_data['fields']):
                    self.editor.embed_data['fields'][self.field_index] = {
                        'name': field_name,
                        'value': field_value,
                        'inline': inline
                    }
            
            # Update the embed display
            if self.action == "edit_existing_field":
                success_msg = "Field updated successfully!"
            elif self.action == "rename":
                success_msg = f"Embed renamed to '{self.editor.embed_data.get('name', 'untitled')}'!"
            else:
                success_msg = "Changes saved!"
            info_embed = self.editor.generate_info_embed(interaction, success_msg)
            preview_embed = self.editor.generate_preview_embed(interaction)
            
            view = EmbedEditorView(self.editor)
            await interaction.response.edit_message(embeds=[info_embed, preview_embed], view=view)
            
        except Exception as e:
            logger.error(f"Error in modal submission: {e}")
            await interaction.response.send_message("An error occurred while updating the embed.", ephemeral=True)

class EmbedBuilder(commands.Cog):
    """Enhanced embed builder with organized select menus and powerful interface"""
    
    def __init__(self, bot):
        self.bot = bot
        self.current_embeds = {}  # Active editing sessions
        self.saved_embeds = EmbedData.load_embeds()
        self.variable_processor = VariableProcessor(bot)
    
    def save_embeds(self):
        """Save embeds to file"""
        EmbedData.save_embeds(self.saved_embeds)
    
    # Main embed command group
    @commands.group(name="embed", invoke_without_command=True, help="Creating and managing embeds")
    async def embed(self, ctx, *, args=None):
        """Main embed command group"""
        try:
            logger.info(f"Embed command invoked by {ctx.author}")
            
            # Check if there are any arguments after 'embed'
            if args:
                # This means they typed something like 's.embed d' or 's.embed f'
                # Extract the first word as the invalid subcommand
                invalid_cmd = args.split()[0] if args.split() else args
                
                embed = discord.Embed(
                    title="{SPROUTS_WARNING} Invalid Subcommand",
                    description=f"**`{invalid_cmd}`** is not a valid embed subcommand.",
                    color=EMBED_COLOR_ERROR
                )
                
                # Core Commands
                embed.add_field(
                    name="Core Commands",
                    value="``{ctx.prefix}embedcreate [name]` - Create a new embed\n"
                          "`{ctx.prefix}embedlist` - List your saved embeds\n"
                          "`{ctx.prefix}embedview <name>` - View a saved embed\n"
                          "`{ctx.prefix}embededit <name>` - Edit an existing embed",
                    inline=False
                )
                
                # Management Commands
                embed.add_field(
                    name="Management",
                    value="`{ctx.prefix}embeddelete <name>` - Delete a saved embed\n"
                          "`{ctx.prefix}embedexport <name>` - Export as YAML\n"
                          "`{ctx.prefix}embedimport <yaml>` - Import from YAML",
                    inline=False
                )
                
                # Help Reference
                embed.add_field(
                    name="Need More Help?",
                    value="Use `{ctx.prefix}embed` to see all available commands with detailed descriptions.",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Show help if no arguments
            embed = discord.Embed(
                title="Embed Builder - Enhanced Interface",
                description="Create and manage custom Discord embeds with an organized select menu interface.",
                color=EMBED_COLOR_NORMAL
            )
            
            # Core Commands
            embed.add_field(
                name="Core Commands",
                value="`{ctx.prefix}embedcreate [name]` - Create a new embed with enhanced editor\n"
                      "`{ctx.prefix}embedlist` - List your saved embeds\n"
                      "`{ctx.prefix}embedview <name>` - View a saved embed\n"
                      "`{ctx.prefix}embededit <name>` - Edit an existing embed",
                inline=False
            )
            
            # Management Commands
            embed.add_field(
                name="Management",
                value="`{ctx.prefix}embeddelete <name>` - Delete a saved embed\n"
                      "`{ctx.prefix}embedexport <name>` - Export as YAML template\n"
                      "`{ctx.prefix}embedimport <yaml>` - Import from YAML template",
                inline=False
            )
            
            # Variables and Help
            embed.add_field(
                name="Additional Help",
                value="`variables` - View all available variables\n"
                      "`{ctx.prefix}embedoldedit <name>` - Use legacy editing mode",
                inline=False
            )
            
            # Features highlight
            embed.add_field(
                name="New Features",
                value="**Organized Select Menus** - No more button clutter\n"
                      "**Live Preview** - See changes instantly\n"
                      "**Enhanced Field Management** - Add, edit, remove fields easily\n"
                      "**Quick Actions** - Clear, preview, and manage with ease",
                inline=False
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error in embed command: {e}")
            await ctx.reply("An error occurred while processing the embed command.", mention_author=False)
    
    @commands.command(name="embedcreate", help="Create a new embed with interactive visual editor and dropdown menus")
    async def embed_create(self, ctx, *, name: str = None):
        """Create a new embed with enhanced interface
        
        Usage: `{ctx.prefix}embedcreate [name]`
        Opens interactive visual editor with organized dropdowns for all embed elements
        
        Examples:
        - `{ctx.prefix}embedcreate` - Auto-generates name (embed_1, embed_2, etc.)
        - `{ctx.prefix}embedcreate` welcome - Creates embed named 'welcome'
        - `{ctx.prefix}embedcreate` support_info - Creates embed with specific name
        
        Common Errors:
        - Name exists: Use embededit to modify existing embeds
        - Name too long: Maximum 32 characters allowed
        - Use variables like $(user.name) for dynamic content
        """
        try:
            # Use provided name or generate default
            user_id = str(ctx.author.id)
            if not name:
                embed_count = len(self.saved_embeds.get(user_id, {}))
                name = f"embed_{embed_count + 1}"
            
            # Clean the name
            name = name.strip()[:32]
            
            # Check if name already exists
            if user_id in self.saved_embeds and name in self.saved_embeds[user_id]:
                embed = discord.Embed(
                    title="Name Already Exists",
                    description=f"An embed named '**{name}**' already exists.\n\n"
                               f"Use `s.embededit {name}` to edit it or choose a different name.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Create new embed data with the enhanced structure
            embed_data = {
                'name': name,
                'title': '',
                'description': '',
                'color': EMBED_COLOR_NORMAL,
                'author_name': '',
                'author_icon': '',
                'footer_text': '',
                'footer_icon': '',
                'thumbnail': '',
                'image': '',
                'fields': []
            }
            
            # Create editor instance
            editor = EmbedEditor(self.bot, embed_data, ctx.author.id)
            
            # Generate info and preview embeds
            info_embed = editor.generate_info_embed(ctx, "Welcome to the enhanced embed editor! Start customizing your embed using the organized dropdowns below.")
            preview_embed = editor.generate_preview_embed(ctx)
            
            # Create enhanced view
            view = editor.create_view()
            
            await ctx.reply(embeds=[info_embed, preview_embed], view=view, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error creating embed: {e}")
            await ctx.reply("An error occurred while creating the embed.", mention_author=False)
    
    @commands.command(name="embededit", help="Edit an existing embed with interactive visual editor interface")
    async def embed_edit(self, ctx, *, name: str):
        """Edit an existing embed with enhanced interface
        
        Usage: `{ctx.prefix}embededit <name>`
        Opens visual editor to modify existing embed with dropdown menus
        
        Examples:
        - `{ctx.prefix}embededit welcome` - Edit the 'welcome' embed
        - `{ctx.prefix}embededit support_info` - Modify support information embed
        - `{ctx.prefix}embededit rules` - Update server rules embed
        
        Common Errors:
        - Embed not found: Use embedlist to see available embeds
        - Permission denied: Server embeds require Administrator permission
        - Case sensitive: Embed names must match exactly
        """
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id) if ctx.guild else "dm"
        user_guild_key = f"{user_id}_{guild_id}"
        
        # Check for guild-level embeds if user is admin
        embed_data = None
        is_guild_embed = False
        
        if (ctx.guild and hasattr(ctx.author, 'guild_permissions') and 
            ctx.author.guild_permissions.administrator):
            if (guild_id in self.saved_embeds and 
                name in self.saved_embeds[guild_id]):
                embed_data = self.saved_embeds[guild_id][name].copy()
                is_guild_embed = True
        
        # Check user embeds if not found in guild
        if not embed_data:
            if user_guild_key not in self.saved_embeds or name not in self.saved_embeds[user_guild_key]:
                embed = discord.Embed(
                    title="Embed Not Found",
                    description=f"Embed '**{name}**' not found.\n\nUse `s.embedlist` to see your saved embeds.",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            embed_data = self.saved_embeds[user_guild_key][name].copy()
        
        # Create editor instance with enhanced interface
        editor = EmbedEditor(self.bot, embed_data, ctx.author.id)
        
        # Generate info and preview embeds
        scope_text = "server-wide" if is_guild_embed else "personal"
        info_embed = editor.generate_info_embed(ctx, f"Editing {scope_text} embed '**{name}**'. Use the organized dropdowns below to customize your embed.")
        preview_embed = editor.generate_preview_embed(ctx)
        
        # Create enhanced view
        view = editor.create_view()
        
        await ctx.reply(embeds=[info_embed, preview_embed], view=view, mention_author=False)
    
    @commands.command(name="embedlist", help="Display all your personal and server embeds with management options")
    async def embed_list(self, ctx):
        """List saved embeds
        
        Usage: `{ctx.prefix}embedlist`
        Shows all personal embeds and server embeds (if Administrator)
        
        Examples:
        - `{ctx.prefix}embedlist` - View all your saved embeds
        - Shows personal embeds for your account
        - Shows server embeds if you're Administrator
        
        Features:

        """
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id) if ctx.guild else "dm"
        user_guild_key = f"{user_id}_{guild_id}"
        user_embeds = self.saved_embeds.get(user_guild_key, {})
        
        # Check for guild embeds if user is admin
        guild_embeds = {}
        if (ctx.guild and hasattr(ctx.author, 'guild_permissions') and 
            ctx.author.guild_permissions.administrator):
            guild_embeds = self.saved_embeds.get(guild_id, {})
        
        embed = discord.Embed(
            title="Your Saved Embeds",
            color=EMBED_COLOR_NORMAL
        )
        
        if user_embeds:
            embed_list = "\n".join([f"• `{name}`" for name in user_embeds.keys()])
            embed.add_field(
                name=f"Personal Embeds ({len(user_embeds)})",
                value=embed_list,
                inline=False
            )
        
        if guild_embeds:
            guild_embed_list = "\n".join([f"• `{name}` (Server)" for name in guild_embeds.keys()])
            embed.add_field(
                name=f"Server Embeds ({len(guild_embeds)})",
                value=guild_embed_list,
                inline=False
            )
        
        if not user_embeds and not guild_embeds:
            embed.description = "No saved embeds found.\n\nUse `s.embedcreate` to create your first embed!"
        else:
            embed.add_field(
                name="Commands",
                value="`{ctx.prefix}embedview <name>` - Preview an embed\n"
                      "`{ctx.prefix}embededit <name>` - Edit an embed\n"
                      "`{ctx.prefix}embeddelete <name>` - Delete an embed",
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="embedview", help="Preview a saved embed with processed variables and live formatting")
    async def embed_view(self, ctx, *, name: str):
        """View a saved embed
        
        Usage: `{ctx.prefix}embedview <name>`
        Displays saved embed with all variables processed and formatted
        
        Examples:
        - `{ctx.prefix}embedview welcome` - Preview welcome embed with current data
        - `{ctx.prefix}embedview rules` - Show rules embed as it would appear
        - `{ctx.prefix}embedview support_info` - View support information with variables
        
        Features:
        - Processes all variables like `$(user.name)`, `$(server.name)`
        - Shows exactly how embed appears to users
        - Works with both personal and server embeds
        """
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id) if ctx.guild else "dm"
        user_guild_key = f"{user_id}_{guild_id}"
        
        # Check for guild-level embeds if user is admin
        embed_data = None
        is_guild_embed = False
        
        if (ctx.guild and hasattr(ctx.author, 'guild_permissions') and 
            ctx.author.guild_permissions.administrator):
            if (guild_id in self.saved_embeds and 
                name in self.saved_embeds[guild_id]):
                embed_data = self.saved_embeds[guild_id][name]
                is_guild_embed = True
        
        # Check user embeds if not found in guild
        if not embed_data:
            if user_guild_key not in self.saved_embeds or name not in self.saved_embeds[user_guild_key]:
                embed = discord.Embed(
                    title="Embed Not Found",
                    description=f"Embed '**{name}**' not found.\n\nUse `s.embedlist` to see your saved embeds.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            embed_data = self.saved_embeds[user_guild_key][name]
        
        try:
            # Process variables in the embed data
            processed_data = {}
            for key, value in embed_data.items():
                if isinstance(value, str):
                    processed_data[key] = await self.variable_processor.process_variables(value, guild=ctx.guild, user=ctx.author, channel=ctx.channel, member=ctx.author)
                elif key == 'fields' and isinstance(value, list):
                    processed_fields = []
                    for field in value:
                        processed_field = {
                            'name': await self.variable_processor.process_variables(field.get('name', ''), guild=ctx.guild, user=ctx.author, channel=ctx.channel, member=ctx.author),
                            'value': await self.variable_processor.process_variables(field.get('value', ''), guild=ctx.guild, user=ctx.author, channel=ctx.channel, member=ctx.author),
                            'inline': field.get('inline', False)
                        }
                        processed_fields.append(processed_field)
                    processed_data[key] = processed_fields
                else:
                    processed_data[key] = value
            
            # Create the embed
            embed = discord.Embed(
                title=processed_data.get('title') or None,
                description=processed_data.get('description') or None,
                color=processed_data.get('color', EMBED_COLOR_NORMAL)
            )
            
            # Add author
            if processed_data.get('author_name'):
                embed.set_author(
                    name=processed_data['author_name'],
                    icon_url=processed_data.get('author_icon') or None
                )
            
            # Add footer
            if processed_data.get('footer_text'):
                embed.set_footer(
                    text=processed_data['footer_text'],
                    icon_url=processed_data.get('footer_icon') or None
                )
            
            # Add thumbnail and image
            if processed_data.get('thumbnail'):
                embed.set_thumbnail(url=processed_data['thumbnail'])
            
            if processed_data.get('image'):
                embed.set_image(url=processed_data['image'])
            
            # Add fields
            for field in processed_data.get('fields', []):
                embed.add_field(
                    name=field['name'],
                    value=field['value'],
                    inline=field.get('inline', False)
                )
            
            # Send with additional info
            info_embed = discord.Embed(
                title="Embed Preview",
                description=f"Showing {'server' if is_guild_embed else 'personal'} embed: **{name}**",
                color=EMBED_COLOR_NORMAL
            )
            info_embed.set_footer(text="This is how your embed looks with variables processed")
            
            await ctx.reply(embeds=[info_embed, embed], mention_author=False)
            
        except Exception as e:
            logger.error(f"Error viewing embed: {e}")
            await ctx.reply("An error occurred while viewing the embed.", mention_author=False)
    
    @commands.command(name="embeddelete", help="Permanently delete a saved embed (cannot be undone)")
    async def embed_delete(self, ctx, *, name: str):
        """Delete a saved embed
        
        Usage: ``{ctx.prefix}embeddelete <name>`
        Permanently removes an embed from your saved collection
        
        Examples:
        - `{ctx.prefix}embeddelete old_welcome` - Delete outdated welcome embed
        - `{ctx.prefix}embeddelete test_embed` - Remove test/experimental embed
        - `{ctx.prefix}embeddelete unused_rules` - Clean up unused embed
        
        Warning:
        - This action cannot be undone
        - Export embed first if you want backup
        - Server embeds require Administrator permission
        """
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id) if ctx.guild else "dm"
        user_guild_key = f"{user_id}_{guild_id}"
        
        # Check for guild-level embeds if user is admin
        is_guild_embed = False
        embed_exists = False
        
        if (ctx.guild and hasattr(ctx.author, 'guild_permissions') and 
            ctx.author.guild_permissions.administrator):
            if (guild_id in self.saved_embeds and 
                name in self.saved_embeds[guild_id]):
                del self.saved_embeds[guild_id][name]
                is_guild_embed = True
                embed_exists = True
        
        # Check user embeds if not found in guild
        if not embed_exists:
            if user_guild_key in self.saved_embeds and name in self.saved_embeds[user_guild_key]:
                del self.saved_embeds[user_guild_key][name]
                embed_exists = True
        
        if not embed_exists:
            embed = discord.Embed(
                title="Embed Not Found",
                description=f"Embed '**{name}**' not found.\n\nUse `s.embedlist` to see your saved embeds.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Save changes
        self.save_embeds()
        
        scope_text = "server" if is_guild_embed else "personal"
        embed = discord.Embed(
            description=f"{scope_text.title()} embed '**{name}**' deleted successfully!",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="embedcreateempty", help="Create blank embed template for later customization")
    async def embed_create_empty(self, ctx, *, name: str = None):
        """Create an empty embed to edit later
        
        Usage: `{ctx.prefix}embedcreateempty [name]`
        Creates blank embed template saved for later editing
        
        Examples:
        - `{ctx.prefix}embedcreateempt`y - Auto-generates name (empty_embed_1, etc.)
        - `{ctx.prefix}embedcreateempty draft_rules` - Create named empty embed
        - `{ctx.prefix}embedcreateempty template_info` - Blank template for future use
        
        Features:
        - Saves empty embed structure immediately
        - Use embededit later to add content
        - Perfect for planning embed layouts
        """
        try:
            user_id = str(ctx.author.id)
            guild_id = str(ctx.guild.id) if ctx.guild else "dm"
            user_guild_key = f"{user_id}_{guild_id}"
            is_admin = (ctx.guild and hasattr(ctx.author, 'guild_permissions') and 
                       ctx.author.guild_permissions.administrator)
            
            if not name:
                if is_admin:
                    embed_count = len(self.saved_embeds.get(guild_id, {}))
                else:
                    embed_count = len(self.saved_embeds.get(user_guild_key, {}))
                name = f"empty_embed_{embed_count + 1}"
            
            name = name.strip()[:32]
            
            # Check if name already exists in guild embeds (for admins) or user embeds
            name_exists = False
            
            if is_admin:
                if guild_id in self.saved_embeds and name in self.saved_embeds[guild_id]:
                    name_exists = True
            
            if not name_exists and user_guild_key in self.saved_embeds and name in self.saved_embeds[user_guild_key]:
                name_exists = True
            
            if name_exists:
                embed = discord.Embed(
                    title="Name Already Exists",
                    description=f"An embed named '**{name}**' already exists.\n\nUse `s.embededit {name}` to edit it or choose a different name.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Create empty embed data
            embed_data = {
                'name': name,
                'title': '',
                'description': '',
                'color': EMBED_COLOR_NORMAL,
                'author_name': '',
                'author_icon': '',
                'footer_text': '',
                'footer_icon': '',
                'thumbnail': '',
                'image': '',
                'fields': []
            }
            
            # Save the empty embed (to guild if admin, otherwise to user)
            if is_admin:
                if guild_id not in self.saved_embeds:
                    self.saved_embeds[guild_id] = {}
                self.saved_embeds[guild_id][name] = embed_data
                scope_text = "server"
            else:
                if user_guild_key not in self.saved_embeds:
                    self.saved_embeds[user_guild_key] = {}
                self.saved_embeds[user_guild_key][name] = embed_data
                scope_text = "personal"
            
            self.save_embeds()
            
            embed = discord.Embed(
                title="Empty Embed Created",
                description=f"Empty {scope_text} embed '**{name}**' created successfully!\n\nUse `s.embededit {name}` to start editing it.",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error creating empty embed: {e}")
            await ctx.reply("An error occurred while creating the empty embed.", mention_author=False)
    
    @commands.command(name="embedexport", help="Export embed as YAML file for backup or sharing")
    async def embed_export(self, ctx, *, name: str):
        """Export embed as YAML template
        
        Usage: `{ctx.prefix}embedexport <name>`
        Downloads embed as YAML file for backup, sharing, or migration
        
        Examples:
        - `{ctx.prefix}embedexport` welcome - Export welcome embed as YAML
        - `{ctx.prefix}embedexport server_rules` - Backup rules embed to file
        - `{ctx.prefix}embedexport support_template` - Share template with others
        
        Features:
        - Downloads .yaml file automatically
        - Preserves all embed data and formatting
        - Use with embedimport to restore or share
        """
        try:
            user_id = str(ctx.author.id)
            guild_id = str(ctx.guild.id) if ctx.guild else "dm"
            user_guild_key = f"{user_id}_{guild_id}"
            
            # Check for guild-level embeds if user is admin
            embed_data = None
            is_guild_embed = False
            
            if (ctx.guild and hasattr(ctx.author, 'guild_permissions') and 
                ctx.author.guild_permissions.administrator):
                if (guild_id in self.saved_embeds and 
                    name in self.saved_embeds[guild_id]):
                    embed_data = self.saved_embeds[guild_id][name]
                    is_guild_embed = True
            
            # Check user embeds if not found in guild
            if not embed_data:
                if user_guild_key not in self.saved_embeds or name not in self.saved_embeds[user_guild_key]:
                    embed = discord.Embed(
                        title="Embed Not Found",
                        description=f"Embed '**{name}**' not found.\n\nUse `s.embedlist` to see your saved embeds.",
                        color=EMBED_COLOR_ERROR
                    )
                    await ctx.reply(embed=embed, mention_author=False)
                    return
                
                embed_data = self.saved_embeds[user_guild_key][name]
            
            # Convert to YAML
            yaml_content = yaml.dump(embed_data, default_flow_style=False, sort_keys=False)
            
            # Create file buffer
            buffer = io.StringIO(yaml_content)
            file = discord.File(buffer, filename=f"{name}.yaml")
            
            scope_text = "server" if is_guild_embed else "personal"
            embed = discord.Embed(
                title="Embed Exported",
                description=f"{scope_text.title()} embed '**{name}**' exported as YAML template.",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.reply(embed=embed, file=file, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error exporting embed: {e}")
            await ctx.reply("An error occurred while exporting the embed.", mention_author=False)
    
    @commands.command(name="embedimport", help="Import embed from YAML file attachment")
    async def embed_import(self, ctx, *, name: str = None):
        """Import embed from YAML template
        
        Usage: `{ctx.prefix}embedimport [name] (attach YAML file)`
        Imports embed from attached YAML file to your collection
        
        Examples:
        - `{ctx.prefix}embedimport welcome` - Import with custom name
        - `{ctx.prefix}embedimport` - Use filename as embed name
        - Must attach .yaml file to message
        
        Common Errors:
        - No file attached: Must attach YAML file to message
        - Invalid YAML: File must be valid YAML format
        - Name exists: Choose different name or delete existing
        """
        try:
            if not ctx.message.attachments:
                embed = discord.Embed(
                    title="No File Attached",
                    description="Please attach a YAML file to import.\n\n**Usage:** `s.embedimport [name]` (with YAML file attached)",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            attachment = ctx.message.attachments[0]
            
            if not attachment.filename.endswith(('.yaml', '.yml')):
                embed = discord.Embed(
                    title="{SPROUTS_WARNING} Invalid File Type",
                    description="Please attach a YAML file (.yaml or .yml).",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Read and parse YAML
            content = await attachment.read()
            yaml_data = yaml.safe_load(content.decode('utf-8'))
            
            # Use provided name or filename
            embed_name = name or attachment.filename.replace('.yaml', '').replace('.yml', '')
            embed_name = embed_name.strip()[:32]
            
            user_id = str(ctx.author.id)
            guild_id = str(ctx.guild.id) if ctx.guild else "dm"
            user_guild_key = f"{user_id}_{guild_id}"
            
            # Check if name already exists in guild embeds (for admins) or user embeds
            name_exists = False
            is_admin = (ctx.guild and hasattr(ctx.author, 'guild_permissions') and 
                       ctx.author.guild_permissions.administrator)
            
            if is_admin:
                if guild_id in self.saved_embeds and embed_name in self.saved_embeds[guild_id]:
                    name_exists = True
            
            if not name_exists and user_guild_key in self.saved_embeds and embed_name in self.saved_embeds[user_guild_key]:
                name_exists = True
            
            if name_exists:
                embed = discord.Embed(
                    title="Name Already Exists",
                    description=f"An embed named '**{embed_name}**' already exists.\n\nUse a different name or delete the existing embed first.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Validate YAML structure
            required_fields = ['name', 'title', 'description', 'color']
            if not all(field in yaml_data for field in required_fields):
                embed = discord.Embed(
                    title="{SPROUTS_WARNING} Invalid YAML Structure",
                    description="The YAML file doesn't have the required embed structure.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Save imported embed (to guild if admin, otherwise to user)
            yaml_data['name'] = embed_name
            
            if is_admin:
                if guild_id not in self.saved_embeds:
                    self.saved_embeds[guild_id] = {}
                self.saved_embeds[guild_id][embed_name] = yaml_data
                scope_text = "server"
            else:
                if user_guild_key not in self.saved_embeds:
                    self.saved_embeds[user_guild_key] = {}
                self.saved_embeds[user_guild_key][embed_name] = yaml_data
                scope_text = "personal"
            
            self.save_embeds()
            
            embed = discord.Embed(
                title="Embed Imported",
                description=f"Embed '**{embed_name}**' imported successfully as {scope_text} embed from YAML!",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error importing embed: {e}")
            await ctx.reply("An error occurred while importing the embed. Please check the YAML format.", mention_author=False)
    
    @commands.command(name="embedoldedit", help="Legacy text-based embed editor")
    async def embed_old_edit(self, ctx, *, name: str):
        """Legacy text-based embed editor
        
        Usage: `{ctx.prefix}embedoldedit <name>`
        Opens text-based editor for quick embed editing
        
        Examples:
        - `{ctx.prefix}embedoldedit welcome` - Edit with text interface
        - Simple line-by-line editing approach
        """
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            user_id = ctx.author.id
            is_admin = ctx.author.guild_permissions.administrator if ctx.guild else False
            
            # Check for existing embed
            existing_embed = None
            if guild_id and is_admin and guild_id in self.saved_embeds and name in self.saved_embeds[guild_id]:
                existing_embed = self.saved_embeds[guild_id][name]
            elif f"{user_id}_{guild_id}" in self.saved_embeds and name in self.saved_embeds[f"{user_id}_{guild_id}"]:
                existing_embed = self.saved_embeds[f"{user_id}_{guild_id}"][name]
            
            if not existing_embed:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Embed Not Found",
                    description=f"No embed named '**{name}**' exists. Use `{ctx.prefix}embedcreate {name}` to create it first.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Start legacy editing session
            edit_embed = discord.Embed(
                title="Legacy Text Editor",
                description=f"Editing embed: **{name}**\n\n"
                           f"**Current Title:** {existing_embed.get('title', 'None')}\n"
                           f"**Current Description:** {existing_embed.get('description', 'None')[:100]}{'...' if existing_embed.get('description', '') and len(existing_embed.get('description', '')) > 100 else ''}\n"
                           f"**Current Color:** {existing_embed.get('color', 'Default')}\n\n"
                           f"Reply with:\n"
                           f"`title: Your new title` - Set title\n"
                           f"`desc: Your description` - Set description\n"
                           f"`color: #hex` - Set color\n"
                           f"`save` - Save changes\n"
                           f"`cancel` - Cancel editing",
                color=EMBED_COLOR_NORMAL
            )
            
            await ctx.reply(embed=edit_embed, mention_author=False)
            
            # Create copy for editing
            editing_embed = existing_embed.copy()
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            while True:
                try:
                    msg = await self.bot.wait_for('message', timeout=300.0, check=check)
                    content = msg.content.strip()
                    
                    if content.lower() == 'cancel':
                        cancel_embed = discord.Embed(
                            title=f"{SPROUTS_ERROR} Editing Cancelled",
                            description="No changes were saved.",
                            color=EMBED_COLOR_ERROR
                        )
                        await msg.reply(embed=cancel_embed, mention_author=False)
                        break
                    
                    elif content.lower() == 'save':
                        # Save the edited embed
                        user_guild_key = f"{user_id}_{guild_id}"
                        
                        if is_admin:
                            if guild_id not in self.saved_embeds:
                                self.saved_embeds[guild_id] = {}
                            self.saved_embeds[guild_id][name] = editing_embed
                            scope_text = "server"
                        else:
                            if user_guild_key not in self.saved_embeds:
                                self.saved_embeds[user_guild_key] = {}
                            self.saved_embeds[user_guild_key][name] = editing_embed
                            scope_text = "personal"
                        
                        self.save_embeds()
                        
                        save_embed = discord.Embed(
                            title=f"{SPROUTS_CHECK} Embed Saved",
                            description=f"Embed '**{name}**' saved as {scope_text} embed!",
                            color=EMBED_COLOR_NORMAL
                        )
                        await msg.reply(embed=save_embed, mention_author=False)
                        break
                    
                    elif content.lower().startswith('title:'):
                        new_title = content[6:].strip()
                        if len(new_title) > 256:
                            await msg.reply("Title too long! Maximum 256 characters.", mention_author=False)
                            continue
                        editing_embed['title'] = new_title
                        await msg.reply(f"✅ Title updated to: **{new_title}**", mention_author=False)
                    
                    elif content.lower().startswith('desc:'):
                        new_desc = content[5:].strip()
                        if len(new_desc) > 4096:
                            await msg.reply("Description too long! Maximum 4096 characters.", mention_author=False)
                            continue
                        editing_embed['description'] = new_desc
                        preview = new_desc[:100] + ('...' if len(new_desc) > 100 else '')
                        await msg.reply(f"✅ Description updated: {preview}", mention_author=False)
                    
                    elif content.lower().startswith('color:'):
                        new_color = content[6:].strip()
                        if new_color.startswith('#'):
                            new_color = new_color[1:]
                        
                        try:
                            color_int = int(new_color, 16)
                            editing_embed['color'] = color_int
                            await msg.reply(f"✅ Color updated to: #{new_color}", mention_author=False)
                        except ValueError:
                            await msg.reply("Invalid color! Use hex format like #ff0000", mention_author=False)
                    
                    else:
                        help_embed = discord.Embed(
                            title="Invalid Command",
                            description="Use:\n"
                                       "`title: Your title` - Set title\n"
                                       "`desc: Your description` - Set description\n"
                                       "`color: #hex` - Set color\n"
                                       "`save` - Save changes\n"
                                       "`cancel` - Cancel editing",
                            color=EMBED_COLOR_ERROR
                        )
                        await msg.reply(embed=help_embed, mention_author=False)
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(
                        title="Session Timeout",
                        description="Editing session timed out. No changes saved.",
                        color=EMBED_COLOR_ERROR
                    )
                    await ctx.send(embed=timeout_embed)
                    break
            
        except Exception as e:
            logger.error(f"Error in legacy editor: {e}")
            await ctx.reply("An error occurred in the legacy editor.", mention_author=False)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
    logger.info("Enhanced embed builder setup completed")
