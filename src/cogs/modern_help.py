import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from src.cogs.guild_settings import guild_settings
import logging

logger = logging.getLogger(__name__)

class ModernCommandHelpView(discord.ui.View):
    """Modern command help view matching the exact layout shown in the image"""
    
    def __init__(self, command, prefix, user):
        super().__init__(timeout=300)
        self.command = command
        self.prefix = prefix
        self.user = user
        self.current_page = "main"
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the user who ran the command to use buttons"""
        return interaction.user.id == self.user.id

    def get_command_category(self):
        """Get the category for the command"""
        cog_name = self.command.cog_name if self.command.cog else "General"
        
        category_mapping = {
            "Ticket": "Tickets",
            "EmbedBuilder": "Embed Builder", 
            "AutoResponders": "Auto Responders",
            "StickyMessages": "Sticky Messages",
            "Reminders": "Reminders",
            "Utilities": "Utilities",
            "Uncategorized": "Bot Info",
            "Help": "Bot Info"
        }
        
        return category_mapping.get(cog_name, cog_name)

    def get_command_cooldown(self):
        """Get the cooldown information for the command"""
        if hasattr(self.command, '_buckets') and self.command._buckets:
            cooldown = self.command._buckets._cooldown
            if cooldown:
                if cooldown.rate == 1:
                    return f"{cooldown.per} seconds per user"
                else:
                    return f"{cooldown.per}s ({cooldown.rate} uses)"
        return "No cooldown"

    def get_command_permissions(self):
        """Get permission requirements for the command"""
        if not hasattr(self.command, 'checks') or not self.command.checks:
            return "None required"
            
        permissions = []
        for check in self.command.checks:
            check_str = str(check)
            if 'administrator' in check_str.lower():
                permissions.append("Administrator")
            elif 'manage_messages' in check_str.lower():
                permissions.append("Manage Messages")
            elif 'manage_channels' in check_str.lower():
                permissions.append("Manage Channels")
            elif 'manage_guild' in check_str.lower():
                permissions.append("Manage Server")
            elif 'is_owner' in check_str:
                permissions.append("Bot Owner Only")
            elif 'has_permissions' in check_str:
                permissions.append("Special permissions")
        
        return "Permissions: " + ", ".join(permissions) if permissions else "None required"

    def extract_examples_from_docstring(self):
        """Extract examples from the command's docstring"""
        if not hasattr(self.command, 'callback') or not self.command.callback.__doc__:
            return [f"s.{self.command.name} - Basic usage"]
            
        docstring = self.command.callback.__doc__
        lines = docstring.split('\n')
        examples = []
        
        in_examples = False
        for line in lines:
            line = line.strip()
            if 'Examples:' in line:
                in_examples = True
                continue
            elif in_examples:
                if line.startswith('- '):
                    examples.append(line[2:])  # Remove "- " prefix
                elif line and not line.startswith(' ') and ':' in line:
                    break  # Hit another section
                    
        if not examples:
            # Fallback to basic example with proper qualified name
            examples = [f"s.{self.command.qualified_name} - {self.command.help or 'Basic usage'}"]
            
        return examples[:2]  # Limit to 2 examples for the main view

    def create_main_embed(self):
        """Create the main help embed matching the image layout exactly"""
        # Get command name and format title
        cmd_name = self.command.qualified_name
        title = f"{cmd_name.title()} Command"
        
        # Get description from help
        description = self.command.help or "No description available"
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=EMBED_COLOR_NORMAL
        )
        
        # Quick Usage section
        signature = f"{self.command.qualified_name}"
        if hasattr(self.command, 'signature') and self.command.signature:
            signature += f" {self.command.signature}"
        
        embed.add_field(
            name="Quick Usage",
            value=f"`{self.prefix}{signature}`",
            inline=False
        )
        
        # Examples section
        examples = self.extract_examples_from_docstring()
        examples_text = "\n".join([f"• {example}" for example in examples])
        
        embed.add_field(
            name="Examples",
            value=examples_text,
            inline=False
        )
        
        # Three-column layout: Requirements | Cooldown | Category
        requirements = self.get_command_permissions()
        cooldown = self.get_command_cooldown()
        category = self.get_command_category()
        
        embed.add_field(
            name="Requirements",
            value=requirements,
            inline=True
        )
        
        embed.add_field(
            name="Cooldown", 
            value=cooldown,
            inline=True
        )
        
        embed.add_field(
            name="Category",
            value=category,
            inline=True
        )
        
        # More Information section
        embed.add_field(
            name="More Information",
            value="Use the buttons below to see detailed usage, all examples, or troubleshooting help.",
            inline=False
        )
        
        # Footer with page info
        embed.set_footer(
            text=f"Requested by {self.user.display_name} • Page 1/4 • Today at {datetime.now().strftime('%I:%M %p')}",
            icon_url=self.user.display_avatar.url
        )
        
        return embed

    def create_detailed_usage_embed(self):
        """Create comprehensive detailed usage embed"""
        embed = discord.Embed(
            title=f"Detailed Usage: {self.command.qualified_name}",
            description=self.command.help or "No description available",
            color=EMBED_COLOR_NORMAL
        )
        
        # Command signature with detailed explanation
        signature = f"{self.command.qualified_name}"
        if hasattr(self.command, 'signature') and self.command.signature:
            signature += f" {self.command.signature}"
        
        embed.add_field(
            name="Command Signature",
            value=f"`{self.prefix}{signature}`",
            inline=False
        )
        
        # Extract and display comprehensive usage from docstring
        usage_info = self._extract_detailed_sections()
        
        if usage_info.get('usage'):
            # Format usage as `[prefix]command [args]` - description
            usage_text = usage_info['usage']
            usage_lines = []
            for line in usage_text.split('\n'):
                line = line.strip()
                if line and not line.startswith('`') and not line.startswith('Usage:'):
                    # Check if line looks like a command
                    if any(line.startswith(word) for word in [self.command.qualified_name, self.command.name, 'new', 'stick', 'autoresponder', 'embed']):
                        if not line.startswith(self.prefix):
                            line = f"{self.prefix}{line}"
                        usage_lines.append(f"`{line}`")
                    else:
                        usage_lines.append(line)
                else:
                    usage_lines.append(line)
            
            embed.add_field(
                name="Detailed Usage Instructions",
                value='\n'.join(usage_lines),
                inline=False
            )
        
        # Parameter explanations
        if hasattr(self.command, 'signature') and self.command.signature:
            param_explanation = self._generate_parameter_explanation()
            if param_explanation:
                embed.add_field(
                    name="Parameter Details",
                    value=param_explanation,
                    inline=False
                )
        
        # Permission requirements in detail
        permissions = self._get_detailed_permissions()
        if permissions:
            embed.add_field(
                name="Permission Requirements",
                value=permissions,
                inline=False
            )
        
        # Usage examples with explanations
        if usage_info.get('examples'):
            # Format examples as `[prefix]command [args]` - description
            examples_text = usage_info['examples']
            example_lines = []
            for line in examples_text.split('\n'):
                line = line.strip()
                if line and line.startswith('-'):
                    # Extract command and description from "- command args - description" format
                    parts = line[1:].strip().split(' - ', 1)
                    if len(parts) >= 2:
                        command_part = parts[0].strip()
                        description = parts[1].strip()
                        
                        # Ensure command has prefix
                        if not command_part.startswith(self.prefix):
                            command_part = f"{self.prefix}{command_part}"
                        
                        example_lines.append(f"`{command_part}` - {description}")
                    else:
                        # Single part, treat as command only
                        command_part = parts[0].strip()
                        if not command_part.startswith(self.prefix):
                            command_part = f"{self.prefix}{command_part}"
                        example_lines.append(f"`{command_part}`")
                elif line and not line.startswith('`'):
                    # Try to parse as command - description
                    if ' - ' in line:
                        command_part, description = line.split(' - ', 1)
                        if not command_part.startswith(self.prefix):
                            command_part = f"{self.prefix}{command_part.strip()}"
                        example_lines.append(f"`{command_part}` - {description.strip()}")
                    else:
                        # Single command
                        if not line.startswith(self.prefix):
                            line = f"{self.prefix}{line}"
                        example_lines.append(f"`{line}`")
                else:
                    example_lines.append(line)
            
            embed.add_field(
                name="Usage Examples",
                value='\n'.join(example_lines),
                inline=False
            )
        
        # Special notes and tips
        if usage_info.get('notes'):
            embed.add_field(
                name="Important Notes",
                value=usage_info['notes'],
                inline=False
            )
        
        # Command behavior explanation
        if usage_info.get('behavior'):
            embed.add_field(
                name="What This Command Does",
                value=usage_info['behavior'],
                inline=False
            )
        
        # Add aliases if any
        if hasattr(self.command, 'aliases') and self.command.aliases:
            aliases = ", ".join([f"`{self.prefix}{alias}`" for alias in self.command.aliases])
            embed.add_field(name="Alternative Commands", value=aliases, inline=False)
        
        # Cooldown information
        cooldown_info = self.get_command_cooldown()
        if cooldown_info != "No cooldown":
            embed.add_field(
                name="Usage Limitations",
                value=f"Cooldown: {cooldown_info}",
                inline=False
            )
        
        embed.set_footer(
            text=f"Requested by {self.user.display_name} • Detailed Usage Guide",
            icon_url=self.user.display_avatar.url
        )
        
        return embed

    def create_all_examples_embed(self):
        """Create all examples embed"""
        embed = discord.Embed(
            title=f"All Examples: {self.command.qualified_name}",
            description=self.command.help or "No description available",
            color=EMBED_COLOR_NORMAL
        )
        
        # Extract all examples from docstring
        examples = []
        if hasattr(self.command, 'callback') and self.command.callback.__doc__:
            docstring = self.command.callback.__doc__
            lines = docstring.split('\n')
            
            in_examples = False
            for line in lines:
                line = line.strip()
                if 'Examples:' in line:
                    in_examples = True
                    continue
                elif in_examples:
                    if line.startswith('- '):
                        examples.append(line[2:])
                    elif line and not line.startswith(' ') and ':' in line:
                        break
        
        if examples:
            examples_text = '\n'.join([f"• {example}" for example in examples])
        else:
            examples_text = f"• {self.prefix}{self.command.name} - Basic usage example"
        
        embed.add_field(
            name="All Examples",
            value=examples_text,
            inline=False
        )
        
        embed.set_footer(
            text=f"Requested by {self.user.display_name} • Page 3/4",
            icon_url=self.user.display_avatar.url
        )
        
        return embed

    def create_common_errors_embed(self):
        """Create common errors embed"""
        embed = discord.Embed(
            title=f"Common Errors: {self.command.qualified_name}",
            description=self.command.help or "No description available",
            color=EMBED_COLOR_NORMAL
        )
        
        # Extract common errors from docstring
        errors = []
        if hasattr(self.command, 'callback') and self.command.callback.__doc__:
            docstring = self.command.callback.__doc__
            lines = docstring.split('\n')
            
            in_errors = False
            for line in lines:
                line = line.strip()
                if 'Common Errors:' in line:
                    in_errors = True
                    continue
                elif in_errors:
                    if line.startswith('- '):
                        errors.append(line[2:])
                    elif line and not line.startswith(' ') and ':' in line:
                        break
        
        if errors:
            errors_text = '\n'.join([f"• {error}" for error in errors])
        else:
            # Generic common errors
            errors_text = f"• Missing permissions: Make sure you have the required permissions\n"
            errors_text += f"• Invalid syntax: Check the command usage format\n"
            errors_text += f"• Cooldown active: Wait before using the command again"
        
        embed.add_field(
            name="Common Errors & Solutions",
            value=errors_text,
            inline=False
        )
        
        embed.set_footer(
            text=f"Requested by {self.user.display_name} • Page 4/4",
            icon_url=self.user.display_avatar.url
        )
        
        return embed

    def _extract_detailed_sections(self):
        """Extract detailed sections from command docstring"""
        if not hasattr(self.command, 'callback') or not self.command.callback.__doc__:
            return {}
            
        docstring = self.command.callback.__doc__
        lines = docstring.split('\n')
        
        sections = {
            'usage': '',
            'examples': '',
            'notes': '',
            'behavior': ''
        }
        
        current_section = None
        content_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Detect section headers
            if 'Usage:' in line:
                current_section = 'usage'
                content_lines = []
            elif 'Examples:' in line:
                current_section = 'examples'
                content_lines = []
            elif 'Note:' in line or 'Notes:' in line:
                current_section = 'notes'
                content_lines = []
            elif 'What this does:' in line or 'What it does:' in line:
                current_section = 'behavior'
                content_lines = []
            elif current_section and line and not any(header in line for header in ['Common Errors:', 'Requirements:', 'Features:']):
                if line.startswith('- '):
                    content_lines.append(line[2:])
                elif line:
                    content_lines.append(line)
            elif line and ':' in line and current_section:
                # Hit another section, save current
                if content_lines:
                    sections[current_section] = '\n'.join(content_lines)
                current_section = None
                content_lines = []
        
        # Save final section
        if current_section and content_lines:
            sections[current_section] = '\n'.join(content_lines)
        
        return sections

    def _generate_parameter_explanation(self):
        """Generate detailed parameter explanations"""
        if not hasattr(self.command, 'signature') or not self.command.signature:
            return None
            
        signature = self.command.signature
        explanations = []
        
        # Parse signature for parameters
        import re
        
        # Look for angle brackets (required) and square brackets (optional)
        required_params = re.findall(r'<([^>]+)>', signature)
        optional_params = re.findall(r'\[([^\]]+)\]', signature)
        
        if required_params:
            explanations.append("**Required Parameters:**")
            for param in required_params:
                explanations.append(f"• `{param}` - Must be provided")
        
        if optional_params:
            explanations.append("**Optional Parameters:**")
            for param in optional_params:
                explanations.append(f"• `{param}` - Can be provided")
        
        # Add parameter type hints if available
        if hasattr(self.command, 'params'):
            type_hints = []
            for param_name, param in self.command.params.items():
                if param_name != 'ctx':  # Skip context parameter
                    param_type = getattr(param.annotation, '__name__', str(param.annotation))
                    if param_type != 'Parameter.empty':
                        type_hints.append(f"• `{param_name}`: {param_type}")
            
            if type_hints:
                explanations.append("**Parameter Types:**")
                explanations.extend(type_hints)
        
        return '\n'.join(explanations) if explanations else None

    def _get_detailed_permissions(self):
        """Get detailed permission requirements"""
        if not hasattr(self.command, 'checks') or not self.command.checks:
            return "No special permissions required - any user can use this command"
            
        permissions = []
        details = []
        
        for check in self.command.checks:
            check_str = str(check)
            check_name = getattr(check, '__name__', str(check))
            
            # Check for owner-only commands by looking at cog or check details
            if ('is_owner' in check_str or 'owner' in check_str.lower() or 
                hasattr(check, 'predicate') and 'owner' in str(check.predicate).lower()):
                permissions.append("Bot Owner Only")
                details.append("• Only the bot owner/developer can use this command")
            elif 'administrator' in check_str.lower():
                permissions.append("Administrator")
                details.append("• Must have Administrator permission in the server")
            elif 'manage_messages' in check_str.lower():
                permissions.append("Manage Messages")
                details.append("• Must have Manage Messages permission")
            elif 'manage_channels' in check_str.lower():
                permissions.append("Manage Channels") 
                details.append("• Must have Manage Channels permission")
            elif 'manage_guild' in check_str.lower():
                permissions.append("Manage Server")
                details.append("• Must have Manage Server permission")
            elif 'has_permissions' in check_str:
                permissions.append("Special Permissions")
                details.append("• Requires specific Discord permissions")
        
        
        if permissions:
            result = f"**Required Permissions:** {', '.join(permissions)}\n\n"
            result += "**Details:**\n" + '\n'.join(details)
            return result
        
        return "No special permissions required"

    def create_format_guide_embed(self):
        """Create format guide embed"""
        embed = discord.Embed(
            title=f"Format Guide: {self.command.qualified_name}",
            description="Understanding command syntax formatting:",
            color=EMBED_COLOR_NORMAL
        )
        
        format_guide = "```"
        format_guide += "<required>  - Must provide this\n"
        format_guide += "[optional]  - Can provide this\n"
        format_guide += "|           - Choose one option\n"
        format_guide += "...         - Can repeat multiple times"
        format_guide += "```"
        
        embed.add_field(
            name="Syntax Legend",
            value=format_guide,
            inline=False
        )
        
        # Add command-specific syntax explanation
        signature = f"{self.command.qualified_name}"
        if hasattr(self.command, 'signature') and self.command.signature:
            signature += f" {self.command.signature}"
        
        embed.add_field(
            name="This Command",
            value=f"`{self.prefix}{signature}`",
            inline=False
        )
        
        embed.set_footer(
            text=f"Requested by {self.user.display_name} • Format Guide",
            icon_url=self.user.display_avatar.url
        )
        
        return embed

    @discord.ui.button(label="Format Guide", style=discord.ButtonStyle.primary, row=0)
    async def format_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show format guide"""
        self.current_page = "format"
        embed = self.create_format_guide_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Detailed Usage", style=discord.ButtonStyle.primary, row=0)
    async def detailed_usage(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show detailed usage information"""
        self.current_page = "detailed"
        embed = self.create_detailed_usage_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Common Errors", style=discord.ButtonStyle.danger, row=0)
    async def common_errors(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show common errors and solutions"""
        self.current_page = "errors"
        embed = self.create_common_errors_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.secondary, row=0)
    async def close_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete the help message"""
        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except Exception:
            # Fallback if deletion fails
            try:
                embed = discord.Embed(
                    title="Help Closed",
                    description="This help message has been closed.",
                    color=EMBED_COLOR_NORMAL
                )
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            except Exception:
                pass

    async def on_timeout(self):
        """Disable all buttons when view times out"""
        for item in self.children:
            item.disabled = True