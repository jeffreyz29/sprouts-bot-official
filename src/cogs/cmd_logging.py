import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime, timezone
import logging
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from src.cogs.guild_settings import guild_settings

logger = logging.getLogger(__name__)

class CommandLogging:
    def __init__(self):
        self.settings_file = "cmd_logging_settings.json"
        self.settings = self.load_settings()
        self.command_stats = {}  # Track command usage statistics
    
    def load_settings(self):
        """Load command logging settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading command logging settings: {e}")
            return {}
    
    def save_settings(self):
        """Save command logging settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving command logging settings: {e}")
    
    def set_cmd_log_channel(self, guild_id: int, channel_id: int):
        """Set command logging channel for a guild"""
        guild_key = str(guild_id)
        if guild_key not in self.settings:
            self.settings[guild_key] = {}
        self.settings[guild_key]['cmd_log_channel'] = channel_id
        self.settings[guild_key]['enabled'] = True
        self.settings[guild_key]['log_successful'] = True
        self.settings[guild_key]['log_failed'] = True
        self.settings[guild_key]['log_cooldowns'] = True
        self.settings[guild_key]['log_permissions'] = True
        self.save_settings()
    
    def get_cmd_log_channel(self, guild_id: int):
        """Get command logging channel for a guild"""
        guild_key = str(guild_id)
        if guild_key in self.settings and self.settings[guild_key].get('enabled', False):
            return self.settings[guild_key].get('cmd_log_channel')
        return None
    
    def set_log_channel(self, guild_id: int, channel_id: int):
        """Set logging channel - compatibility method for devonly commands"""
        self.set_cmd_log_channel(guild_id, channel_id)
    
    def get_log_channel(self, guild_id: int):
        """Get logging channel - compatibility method for devonly commands"""
        channel = self.get_cmd_log_channel(guild_id)
        return channel if channel else "Not set"
    
    def get_log_settings(self, guild_id: int):
        """Get detailed logging settings for a guild"""
        guild_key = str(guild_id)
        if guild_key in self.settings:
            return self.settings[guild_key]
        return {}
    
    def update_log_setting(self, guild_id: int, setting: str, value: bool):
        """Update a specific logging setting"""
        guild_key = str(guild_id)
        if guild_key in self.settings:
            self.settings[guild_key][setting] = value
            self.save_settings()
    
    def disable_cmd_logging(self, guild_id: int):
        """Disable command logging for a guild"""
        guild_key = str(guild_id)
        if guild_key in self.settings:
            self.settings[guild_key]['enabled'] = False
            self.save_settings()
    
    def get_all_cmd_logging_guilds(self):
        """Get all guilds with command logging enabled"""
        enabled_guilds = {}
        for guild_id, settings in self.settings.items():
            if settings.get('enabled', False):
                enabled_guilds[int(guild_id)] = settings.get('cmd_log_channel')
        return enabled_guilds
    
    def track_command(self, command_name: str, guild_id: int, success: bool):
        """Track command usage statistics"""
        guild_key = str(guild_id)
        if guild_key not in self.command_stats:
            self.command_stats[guild_key] = {}
        
        if command_name not in self.command_stats[guild_key]:
            self.command_stats[guild_key][command_name] = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'last_used': None
            }
        
        self.command_stats[guild_key][command_name]['total'] += 1
        if success:
            self.command_stats[guild_key][command_name]['successful'] += 1
        else:
            self.command_stats[guild_key][command_name]['failed'] += 1
        
        self.command_stats[guild_key][command_name]['last_used'] = datetime.now(timezone.utc).isoformat()

# Global instance
cmd_logging = CommandLogging()

class CommandLoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # NOTE: cmdlogs commands moved to devonly.py for global logging
    # Original per-server cmdlogs commands are disabled to prevent conflicts
    # @commands.group(name="cmdlogs", invoke_without_command=True)
    # @commands.has_permissions(administrator=True)
    async def cmdlogs_disabled(self, ctx):
        """Command logging system - requires Administrator permissions"""
        try:
            prefix = guild_settings.get_prefix(ctx.guild.id) if ctx.guild else "s."
            
            embed = discord.Embed(
                title="Command Logging System",
                description="Advanced command monitoring and analytics system",
                color=EMBED_COLOR_NORMAL
            )
            
            # Current status
            current_channel = cmd_logging.get_cmd_log_channel(ctx.guild.id)
            settings = cmd_logging.get_log_settings(ctx.guild.id)
            
            if current_channel:
                channel = ctx.guild.get_channel(current_channel)
                status = f"Enabled in {channel.mention if channel else 'Unknown Channel'}"
            else:
                status = "Disabled"
            
            embed.add_field(
                name="**Current Status**",
                value=status,
                inline=False
            )
            
            # Current settings if enabled
            if current_channel and settings:
                settings_text = []
                settings_text.append(f"Successful Commands" if settings.get('log_successful', True) else "Successful Commands (Disabled)")
                settings_text.append(f"Failed Commands" if settings.get('log_failed', True) else "Failed Commands (Disabled)")
                settings_text.append(f"Cooldown Errors" if settings.get('log_cooldowns', True) else "Cooldown Errors (Disabled)")
                settings_text.append(f"Permission Errors" if settings.get('log_permissions', True) else "Permission Errors (Disabled)")
                
                embed.add_field(
                    name="**Log Settings**",
                    value="\n".join(settings_text),
                    inline=False
                )
            
            # Available commands
            commands_list = [
                f"`{ctx.prefix}cmdlogs set <#channel|ID>` - Set command logging channel",
                f"`{ctx.prefix}cmdlogs disable` - Disable command logging",
                f"`{ctx.prefix}cmdlogs status` - View current configuration",
                f"`{ctx.prefix}cmdlogs settings` - Configure what to log",
                f"`{ctx.prefix}cmdlogs stats` - View command usage statistics",
                f"`{ctx.prefix}cmdlogs test` - Send test command log message"
            ]
            
            embed.add_field(
                name="**Available Commands**",
                value="\n".join(commands_list),
                inline=False
            )
            
            # Features
            features = [
                "**Detailed Command Tracking** - Logs all command executions",
                "**Success/Failure Monitoring** - Tracks command outcomes",
                "**Error Logging** - Records permission and cooldown errors",
                "**Usage Analytics** - Command usage statistics and trends",
                "**User Activity** - Detailed user command history",
                "**Execution Time Tracking** - Command response time monitoring",
                "**Context Information** - Channel, server, and message details",
                "**Configurable Filters** - Choose what types of events to log"
            ]
            
            embed.add_field(
                name="**System Features**",
                value="\n".join(features),
                inline=False
            )
            
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error in cmdlog command: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Command Logging Error",
                description="An error occurred while accessing command logging settings.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    # @cmdlogs.command(name="set")
    # @commands.has_permissions(administrator=True)
    async def cmdlog_set_disabled(self, ctx, *, channel_input: str):
        """Set the command logging channel"""
        try:
            # Try to get channel from mention or ID
            channel = None
            
            # Remove mention characters if present
            channel_input = channel_input.strip('<#>')
            
            # Try to convert to int (channel ID)
            try:
                channel_id = int(channel_input)
                channel = self.bot.get_channel(channel_id)
                
                # If not found, try to fetch it
                if not channel:
                    channel = await self.bot.fetch_channel(channel_id)
                    
            except (ValueError, discord.NotFound, discord.HTTPException):
                # If not a valid ID, try to find by name
                channel = discord.utils.get(ctx.guild.text_channels, name=channel_input)
                
            if not channel:
                embed = discord.Embed(
                    title="Invalid Channel",
                    description="Could not find the specified channel. Please provide a valid channel mention, channel ID, or channel name.",
                    color=EMBED_COLOR_ERROR
                )
                embed.add_field(
                    name="**Valid formats:**",
                    value="• Channel mention: `#general`\n"
                          "• Channel ID: `123456789012345678`\n"
                          "• Channel name: `general`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
                
            # Make sure it's a text channel in this guild
            if not isinstance(channel, discord.TextChannel) or channel.guild.id != ctx.guild.id:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} Invalid Channel",
                    description="Please specify a text channel from this server.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            # Check bot permissions in target channel
            bot_perms = channel.permissions_for(ctx.guild.me)
            if not bot_perms.send_messages or not bot_perms.embed_links:
                embed = discord.Embed(
                    title="{SPROUTS_WARNING} Insufficient Permissions",
                    description=f"I need **Send Messages** and **Embed Links** permissions in {channel.mention}",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Set the channel
            cmd_logging.set_cmd_log_channel(ctx.guild.id, channel.id)
            
            embed = discord.Embed(
                title="{SPROUTS_CHECK} Command Logging Configured",
                description=f"Command logging has been set to {channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="**What will be logged?**",
                value="• Successful command executions\n"
                      "• Failed command attempts\n"
                      "• Permission and cooldown errors\n"
                      "• Detailed usage analytics\n"
                      "• User activity and context",
                inline=False
            )
            
            embed.add_field(
                name="**Configuration**",
                value=f"Use `{guild_settings.get_prefix(ctx.guild.id)}cmdlogs settings` to customize what gets logged.",
                inline=False
            )
            
            embed.set_footer(
                text=f"Configured by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
            # Send test message to the channel
            test_embed = discord.Embed(
                title="{SPROUTS_CHECK} Command Logging System Activated",
                description="This channel will now receive all command logs.",
                color=EMBED_COLOR_NORMAL
            )
            test_embed.add_field(
                name="**Configured by**",
                value=f"{ctx.author.mention} ({ctx.author})",
                inline=True
            )
            test_embed.add_field(
                name="**Configuration Time**",
                value=f"<t:{int(datetime.now(timezone.utc).timestamp())}:F>",
                inline=True
            )
            test_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            
            await channel.send(embed=test_embed)
            
            logger.info(f"Command logging set to {channel.name} in {ctx.guild.name} by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error setting command log channel: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Configuration Error",
                description="An error occurred while setting the command logging channel.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    # @cmdlogs.command(name="disable")
    # @commands.has_permissions(administrator=True)
    async def cmdlog_disable_disabled(self, ctx):
        """Disable command logging for this server"""
        try:
            current_channel = cmd_logging.get_cmd_log_channel(ctx.guild.id)
            if not current_channel:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} Already Disabled",
                    description="Command logging is not currently enabled in this server.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            cmd_logging.disable_cmd_logging(ctx.guild.id)
            
            embed = discord.Embed(
                title="{SPROUTS_CHECK} Command Logging Disabled",
                description="Command logging has been disabled for this server.",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="**What changed?**",
                value="• Commands will no longer be logged to any channel\n"
                      "• Usage statistics will no longer be tracked\n"
                      "• You can re-enable anytime with `cmdlogs set <#channel|ID>`",
                inline=False
            )
            
            embed.set_footer(
                text=f"Disabled by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"Command logging disabled in {ctx.guild.name} by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error disabling command logging: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Configuration Error",
                description="An error occurred while disabling command logging.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    # @cmdlogs.command(name="status")
    # @commands.has_permissions(administrator=True)
    async def cmdlog_status_disabled(self, ctx):
        """View current command logging configuration"""
        try:
            embed = discord.Embed(
                title="{SPROUTS_CHECK} Command Logging Status",
                color=EMBED_COLOR_NORMAL
            )
            
            current_channel = cmd_logging.get_cmd_log_channel(ctx.guild.id)
            settings = cmd_logging.get_log_settings(ctx.guild.id)
            
            if current_channel:
                channel = ctx.guild.get_channel(current_channel)
                if channel:
                    embed.add_field(
                        name="**Status**",
                        value="Enabled",
                        inline=True
                    )
                    embed.add_field(
                        name="**Log Channel**",
                        value=channel.mention,
                        inline=True
                    )
                    embed.add_field(
                        name="**Channel ID**",
                        value=f"`{channel.id}`",
                        inline=True
                    )
                    
                    # Check permissions
                    bot_perms = channel.permissions_for(ctx.guild.me)
                    perms_status = "All required permissions" if (bot_perms.send_messages and bot_perms.embed_links) else "Missing permissions"
                    
                    embed.add_field(
                        name="**Permissions**",
                        value=perms_status,
                        inline=False
                    )
                    
                    # Detailed settings
                    if settings:
                        settings_text = []
                        settings_text.append(f"Successful Commands" if settings.get('log_successful', True) else "Successful Commands (Disabled)")
                        settings_text.append(f"Failed Commands" if settings.get('log_failed', True) else "Failed Commands (Disabled)")
                        settings_text.append(f"Cooldown Errors" if settings.get('log_cooldowns', True) else "Cooldown Errors (Disabled)")
                        settings_text.append(f"Permission Errors" if settings.get('log_permissions', True) else "Permission Errors (Disabled)")
                        
                        embed.add_field(
                            name="**Logging Filters**",
                            value="\n".join(settings_text),
                            inline=False
                        )
                else:
                    embed.add_field(
                        name="**Status**",
                        value="Channel not found",
                        inline=True
                    )
                    embed.add_field(
                        name="**Issue**",
                        value="The configured channel no longer exists",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="**Status**",
                    value="Disabled",
                    inline=True
                )
                embed.add_field(
                    name="**Configuration**",
                    value="No command logging channel set",
                    inline=False
                )
            
            # Global stats
            all_guilds = cmd_logging.get_all_cmd_logging_guilds()
            embed.add_field(
                name="{SPROUTS_CHECK} Global Statistics",
                value=f"Command logging active in **{len(all_guilds)}** servers",
                inline=False
            )
            
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error in cmdlog status: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Status Error",
                description="An error occurred while checking command logging status.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    # @cmdlogs.command(name="stats")
    # @commands.has_permissions(administrator=True)
    async def cmdlog_stats_disabled(self, ctx):
        """View command usage statistics"""
        try:
            guild_key = str(ctx.guild.id)
            
            if guild_key not in cmd_logging.command_stats or not cmd_logging.command_stats[guild_key]:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} Command Statistics",
                    description="No command usage data available yet.",
                    color=EMBED_COLOR_ERROR
                )
                embed.add_field(
                    name="Note",
                    value="Statistics are tracked from when command logging was first enabled.",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            stats = cmd_logging.command_stats[guild_key]
            
            # Sort by total usage
            sorted_commands = sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True)
            
            embed = discord.Embed(
                title="Command Usage Statistics",
                description=f"Statistics for **{ctx.guild.name}**",
                color=EMBED_COLOR_NORMAL
            )
            
            # Top commands
            top_commands = []
            for i, (cmd_name, cmd_stats) in enumerate(sorted_commands[:10]):
                success_rate = (cmd_stats['successful'] / cmd_stats['total'] * 100) if cmd_stats['total'] > 0 else 0
                top_commands.append(
                    f"**{i+1}.** `{cmd_name}` - {cmd_stats['total']} uses ({success_rate:.1f}% success)"
                )
            
            embed.add_field(
                name="Top Commands",
                value="\n".join(top_commands) if top_commands else "No data available",
                inline=False
            )
            
            # Overall stats
            total_commands = sum(cmd['total'] for cmd in stats.values())
            total_successful = sum(cmd['successful'] for cmd in stats.values())
            total_failed = sum(cmd['failed'] for cmd in stats.values())
            overall_success_rate = (total_successful / total_commands * 100) if total_commands > 0 else 0
            
            embed.add_field(
                name="**Overall Statistics**",
                value=f"**Total Commands:** {total_commands:,}\n"
                      f"**Successful:** {total_successful:,}\n"
                      f"**Failed:** {total_failed:,}\n"
                      f"**Success Rate:** {overall_success_rate:.1f}%",
                inline=True
            )
            
            embed.add_field(
                name="**Command Diversity**",
                value=f"**Unique Commands:** {len(stats)}\n"
                      f"**Most Used:** `{sorted_commands[0][0]}`\n"
                      f"**Usage Count:** {sorted_commands[0][1]['total']}",
                inline=True
            )
            
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error in cmdlog stats: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Statistics Error",
                description="An error occurred while fetching command statistics.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    # @cmdlogs.command(name="test")
    # @commands.has_permissions(administrator=True)
    async def cmdlog_test_disabled(self, ctx):
        """Send a test command log message"""
        try:
            current_channel = cmd_logging.get_cmd_log_channel(ctx.guild.id)
            if not current_channel:
                embed = discord.Embed(
                    title="{SPROUTS_CHECK} Command Logging Disabled",
                    description="Command logging is not enabled. Use `{ctx.prefix}cmdlogs set <#channel_ID>` first.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            channel = ctx.guild.get_channel(current_channel)
            if not channel:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} Channel Not Found",
                    description="The configured command logging channel no longer exists.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Create test log message
            log_embed = discord.Embed(
                title="COMMAND LOG (TEST MESSAGE)",
                description="**Command:** `cmdlog test`\n**Status:** **Successful**",
                color=0x00ff00
            )
            
            log_embed.add_field(
                name="**User**",
                value=f"{ctx.author.mention}\n`{ctx.author}` (ID: {ctx.author.id})",
                inline=True
            )
            
            log_embed.add_field(
                name="**Channel**",
                value=f"{ctx.channel.mention}\n`#{ctx.channel.name}` (ID: {ctx.channel.id})",
                inline=True
            )
            
            log_embed.add_field(
                name="**Execution Details**",
                value=f"**Response Time:** 0.05s\n**Message ID:** {ctx.message.id}\n**Prefix Used:** `{guild_settings.get_prefix(ctx.guild.id)}`",
                inline=False
            )
            
            log_embed.add_field(
                name="**User Permissions**",
                value="Administrator\nCan execute command",
                inline=True
            )
            
            log_embed.add_field(
                name="**Test Information**",
                value=f"This is a test command log triggered by {ctx.author.mention}",
                inline=False
            )
            
            log_embed.set_thumbnail(url=ctx.author.display_avatar.url)
            log_embed.set_footer(text="Command Logging System Test")
            log_embed.timestamp = discord.utils.utcnow()
            
            await channel.send(embed=log_embed)
            
            embed = discord.Embed(
                title="{SPROUTS_CHECK} Test Message Sent",
                description=f"A test command log has been sent to {channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"Command logging test sent by {ctx.author} in {ctx.guild.name}")
            
        except Exception as e:
            logger.error(f"Error in cmdlog test: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Test Error",
                description="An error occurred while sending the test message.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Log successful command execution"""
        try:
            # Always log for global logging, don't skip DM commands anymore
            pass
            
            # For global command logging, check if there's a configured channel
            # If guild has specific settings, use those. Otherwise, use global logging to support server
            settings = cmd_logging.get_log_settings(ctx.guild.id) if ctx.guild else {}
            channel_id = cmd_logging.get_cmd_log_channel(ctx.guild.id) if ctx.guild else None
            
            # If no guild-specific settings, check for global command logging (only in bot support server)
            if not channel_id:
                # Use environment variable for global command logging
                import os
                global_channel_id = os.getenv('LOG_COMMANDS_CHANNEL')
                if global_channel_id:
                    try:
                        test_channel = self.bot.get_channel(int(global_channel_id))
                        # Only use global logging if the channel is in the bot support server
                        if test_channel and test_channel.guild.id == 1411324489333215267:
                            channel_id = int(global_channel_id)
                            # Use default settings for global logging
                            settings = {'enabled': True, 'log_successful': True}
                        else:
                            return
                    except (ValueError, TypeError):
                        return
                else:
                    return
            
            # For global logging, always log successful commands regardless of settings
            if not channel_id:
                return
            
            # Get the channel (could be in current guild or global)
            channel = None
            if ctx.guild:
                channel = ctx.guild.get_channel(channel_id)
            if not channel:
                # Try to get channel from bot (for global logging)
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    return
            
            # Track statistics
            cmd_logging.track_command(ctx.command.name, ctx.guild.id, True)
            
            # Create log embed for successful command
            embed = discord.Embed(
                title="Command Executed",
                color=0x00ff00
            )
            
            embed.add_field(
                name="Command",
                value=f"`{ctx.prefix}{ctx.command.qualified_name}`",
                inline=True
            )
            
            embed.add_field(
                name="User",
                value=f"{ctx.author.mention} ({ctx.author})",
                inline=True
            )
            
            embed.add_field(
                name="Channel",
                value=f"{ctx.channel.mention} ({ctx.channel.name})",
                inline=True
            )
            
            # Add arguments if any
            if ctx.args[2:] or ctx.kwargs:  # Skip self and ctx
                args_str = " ".join(str(arg) for arg in ctx.args[2:])
                if ctx.kwargs:
                    kwargs_str = " ".join(f"{k}={v}" for k, v in ctx.kwargs.items())
                    args_str += f" {kwargs_str}" if args_str else kwargs_str
                
                if args_str:
                    embed.add_field(
                        name="Arguments",
                        value=f"`{args_str[:1000]}`",  # Limit length
                        inline=False
                    )
            
            embed.add_field(
                name="Message Link",
                value=f"[Jump to message]({ctx.message.jump_url})",
                inline=True
            )
            
            embed.set_footer(
                text=f"ID: {ctx.message.id}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error logging successful command: {e}")
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Log command errors"""
        try:
            # Always log for global logging, don't skip DM commands anymore
            pass
            
            # For global command logging, check if there's a configured channel
            settings = cmd_logging.get_log_settings(ctx.guild.id) if ctx.guild else {}
            channel_id = cmd_logging.get_cmd_log_channel(ctx.guild.id) if ctx.guild else None
            
            # If no guild-specific settings, check for global command logging (only in bot support server)
            if not channel_id:
                # Use environment variable for global command logging
                import os
                global_channel_id = os.getenv('LOG_COMMANDS_CHANNEL')
                if global_channel_id:
                    try:
                        test_channel = self.bot.get_channel(int(global_channel_id))
                        # Only use global logging if the channel is in the bot support server
                        if test_channel and test_channel.guild.id == 1411324489333215267:
                            channel_id = int(global_channel_id)
                            # For global logging, always enable all logging types
                            settings = {'enabled': True, 'log_failed': True, 'log_cooldowns': True, 'log_permissions': True}
                        else:
                            return
                    except (ValueError, TypeError):
                        return
                else:
                    return
            
            # For global logging, always log regardless of settings
            if not channel_id:
                return
            
            # For global logging, log ALL errors without filtering
            should_log = True
            error_type = ""
            error_color = 0xff6b6b
            
            if isinstance(error, commands.CommandOnCooldown):
                error_type = "**Cooldown Error**"
                error_color = 0xffa500
            elif isinstance(error, (commands.MissingPermissions, commands.BotMissingPermissions, commands.MissingRole)):
                error_type = "**Permission Error**"
                error_color = 0xff0000
            else:
                error_type = "**Command Failed**"
            
            # Get the channel (could be in current guild or global)
            channel = None
            if ctx.guild:
                channel = ctx.guild.get_channel(channel_id)
            if not channel:
                # Try to get channel from bot (for global logging)
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    return
            
            # Track statistics
            cmd_logging.track_command(ctx.command.name if ctx.command else ctx.invoked_with, ctx.guild.id, False)
            
            # Create log embed for command error
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} {error_type}",
                color=error_color
            )
            
            embed.add_field(
                name="Command",
                value=f"`{ctx.prefix}{ctx.invoked_with}`",
                inline=True
            )
            
            embed.add_field(
                name="User",
                value=f"{ctx.author.mention} ({ctx.author})",
                inline=True
            )
            
            embed.add_field(
                name="Channel",
                value=f"{ctx.channel.mention} ({ctx.channel.name})",
                inline=True
            )
            
            # Add error details
            error_description = str(error)
            if len(error_description) > 1000:
                error_description = error_description[:1000] + "..."
            
            embed.add_field(
                name="Error Details",
                value=f"```{error_description}```",
                inline=False
            )
            
            embed.add_field(
                name="Message Link",
                value=f"[Jump to message]({ctx.message.jump_url})",
                inline=True
            )
            
            embed.set_footer(
                text=f"ID: {ctx.message.id}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error logging command error: {e}")

async def setup_cmd_logging(bot):
    """Setup function for command logging"""
    await bot.add_cog(CommandLoggingCog(bot))
    logger.info("Command logging system setup completed")
