import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime, timezone
import logging
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR, SPROUTS_WARNING
from src.cogs.guild_settings import guild_settings

logger = logging.getLogger(__name__)

class DMLogging:
    def __init__(self):
        self.settings_file = "dm_logging_settings.json"
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load DM logging settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading DM logging settings: {e}")
            return {}
    
    def save_settings(self):
        """Save DM logging settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving DM logging settings: {e}")
    
    def set_dm_log_channel(self, guild_id: int, channel_id: int):
        """Set DM logging channel for a guild"""
        guild_key = str(guild_id)
        if guild_key not in self.settings:
            self.settings[guild_key] = {}
        self.settings[guild_key]['dm_log_channel'] = channel_id
        self.settings[guild_key]['enabled'] = True
        self.save_settings()
    
    def get_dm_log_channel(self, guild_id: int):
        """Get DM logging channel for a guild"""
        guild_key = str(guild_id)
        if guild_key in self.settings and self.settings[guild_key].get('enabled', False):
            return self.settings[guild_key].get('dm_log_channel')
        return None
    
    def set_log_channel(self, guild_id: int, channel_id: int):
        """Set logging channel - compatibility method for devonly commands"""
        self.set_dm_log_channel(guild_id, channel_id)
    
    def get_log_channel(self, guild_id: int):
        """Get logging channel - compatibility method for devonly commands"""
        channel = self.get_dm_log_channel(guild_id)
        return channel if channel else "Not set"
    
    def disable_dm_logging(self, guild_id: int):
        """Disable DM logging for a guild"""
        guild_key = str(guild_id)
        if guild_key in self.settings:
            self.settings[guild_key]['enabled'] = False
            self.save_settings()
    
    def get_all_dm_logging_guilds(self):
        """Get all guilds with DM logging enabled"""
        enabled_guilds = {}
        for guild_id, settings in self.settings.items():
            if settings.get('enabled', False):
                enabled_guilds[int(guild_id)] = settings.get('dm_log_channel')
        return enabled_guilds

# Global instance
dm_logging = DMLogging()

class DMLoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # NOTE: dmlogs commands moved to devonly.py for global logging
    # Original per-server dmlogs commands are disabled to prevent conflicts
    # @commands.group(name="dmlogs", invoke_without_command=True)
    # @commands.has_permissions(administrator=True) 
    async def dmlogs_disabled(self, ctx):
        """DM logging system - requires Administrator permissions"""
        try:
            prefix = guild_settings.get_prefix(ctx.guild.id) if ctx.guild else "s."
            
            embed = discord.Embed(
                title="DM Logging System",
                description="Advanced DM monitoring and auto-reply system",
                color=EMBED_COLOR_NORMAL
            )
            
            # Current status
            current_channel = dm_logging.get_dm_log_channel(ctx.guild.id)
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
            
            # Available commands
            commands_list = [
                f"`{prefix}dmlogs set <#channel|ID>` - Set DM logging channel",
                f"`{prefix}dmlogs disable` - Disable DM logging",
                f"`{prefix}dmlogs status` - View current configuration",
                f"`{prefix}dmlogs test` - Send test DM log message"
            ]
            
            embed.add_field(
                name="**Available Commands**",
                value="\n".join(commands_list),
                inline=False
            )
            
            # Features
            features = [
                "**Detailed DM Monitoring** - Logs all DMs sent to the bot",
                "**Auto-Reply System** - Automatically responds to users who DM",
                "**Rich Embed Logs** - Beautiful, detailed log messages",
                "**User Information** - Shows user details, mutual servers",
                "**Attachment Support** - Logs files, images, and other attachments",
                "**Timestamp Tracking** - Precise time logging with timezone",
                "**Message Links** - Direct links to original messages when possible"
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
            logger.error(f"Error in dmlog command: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} DM Logging Error",
                description="An error occurred while accessing DM logging settings.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    # @dmlogs.command(name="set")
    # @commands.has_permissions(administrator=True)
    async def dmlog_set_disabled(self, ctx, *, channel_input: str):
        """Set the DM logging channel"""
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
                    title="Invalid Channel",
                    description="Please specify a text channel from this server.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            # Check bot permissions in target channel
            bot_perms = channel.permissions_for(ctx.guild.me)
            if not bot_perms.send_messages or not bot_perms.embed_links:
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} Insufficient Permissions",
                    description=f"I need **Send Messages** and **Embed Links** permissions in {channel.mention}",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Set the channel
            dm_logging.set_dm_log_channel(ctx.guild.id, channel.id)
            
            embed = discord.Embed(
                title="DM Logging Configured",
                description=f"DM logging has been set to {channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="**What happens now?**",
                value="• All DMs sent to the bot will be logged to this channel\n"
                      "• Users will receive an auto-reply when they DM the bot\n"
                      "• Detailed information including attachments will be captured",
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
                title="DM Logging System Activated",
                description="This channel will now receive all DM logs.",
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
            
            logger.info(f"DM logging set to {channel.name} in {ctx.guild.name} by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error setting DM log channel: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Configuration Error",
                description="An error occurred while setting the DM logging channel.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    # @dmlogs.command(name="disable")
    # @commands.has_permissions(administrator=True)
    async def dmlog_disable_disabled(self, ctx):
        """Disable DM logging for this server"""
        try:
            current_channel = dm_logging.get_dm_log_channel(ctx.guild.id)
            if not current_channel:
                embed = discord.Embed(
                    title="Already Disabled",
                    description="DM logging is not currently enabled in this server.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            dm_logging.disable_dm_logging(ctx.guild.id)
            
            embed = discord.Embed(
                title="DM Logging Disabled",
                description="DM logging has been disabled for this server.",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="**What changed?**",
                value="• DMs will no longer be logged to any channel\n"
                      "• Auto-reply system is still active\n"
                      "• You can re-enable anytime with `dmlogs set <#channel|ID>`",
                inline=False
            )
            
            embed.set_footer(
                text=f"Disabled by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"DM logging disabled in {ctx.guild.name} by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error disabling DM logging: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Configuration Error",
                description="An error occurred while disabling DM logging.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    # @dmlogs.command(name="status")
    # @commands.has_permissions(administrator=True)
    async def dmlog_status_disabled(self, ctx):
        """View current DM logging configuration"""
        try:
            embed = discord.Embed(
                title="DM Logging Status",
                color=EMBED_COLOR_NORMAL
            )
            
            current_channel = dm_logging.get_dm_log_channel(ctx.guild.id)
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
                    value="No DM logging channel set",
                    inline=False
                )
            
            # Global stats
            all_guilds = dm_logging.get_all_dm_logging_guilds()
            embed.add_field(
                name="**Global Statistics**",
                value=f"DM logging active in **{len(all_guilds)}** servers",
                inline=False
            )
            
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error in dmlog status: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Status Error",
                description="An error occurred while checking DM logging status.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    # @dmlogs.command(name="test")
    # @commands.has_permissions(administrator=True)
    async def dmlog_test_disabled(self, ctx):
        """Send a test DM log message"""
        try:
            current_channel = dm_logging.get_dm_log_channel(ctx.guild.id)
            if not current_channel:
                embed = discord.Embed(
                    title="DM Logging Disabled",
                    description="DM logging is not enabled. Use `dmlogs set <#channel|ID>` first.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            channel = ctx.guild.get_channel(current_channel)
            if not channel:
                embed = discord.Embed(
                    title="Channel Not Found",
                    description="The configured DM logging channel no longer exists.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Create test log message
            log_embed = discord.Embed(
                title="DM LOG (TEST MESSAGE)",
                description="This is a test of the DM logging system.",
                color=0x00ff00
            )
            
            log_embed.add_field(
                name="**Test User**",
                value=f"{ctx.author.mention}\n`{ctx.author}` (ID: {ctx.author.id})",
                inline=True
            )
            
            log_embed.add_field(
                name="**Test Message**",
                value="This is a sample DM that would be logged.",
                inline=False
            )
            
            log_embed.add_field(
                name="**Mutual Servers**",
                value=f"This server and {len([g for g in self.bot.guilds if ctx.author in g.members]) - 1} others",
                inline=True
            )
            
            log_embed.add_field(
                name="**Test Triggered By**",
                value=f"{ctx.author.mention} in {ctx.channel.mention}",
                inline=False
            )
            
            log_embed.set_thumbnail(url=ctx.author.display_avatar.url)
            log_embed.set_footer(text="DM Logging System Test")
            log_embed.timestamp = discord.utils.utcnow()
            
            await channel.send(embed=log_embed)
            
            embed = discord.Embed(
                title="Test Message Sent",
                description=f"A test DM log has been sent to {channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"DM logging test sent by {ctx.author} in {ctx.guild.name}")
            
        except Exception as e:
            logger.error(f"Error in dmlog test: {e}")
            error_embed = discord.Embed(
                title="{SPROUTS_ERROR} Test Error",
                description="An error occurred while sending the test message.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle DM messages - log and auto-reply"""
        try:
            # Only process DMs to the bot
            if not isinstance(message.channel, discord.DMChannel):
                return
            
            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                return
            
            # Ignore messages from other bots
            if message.author.bot:
                return
            
            # Auto-reply to the user
            await self.send_auto_reply(message.author)
            
            # Log the DM to all configured channels
            await self.log_dm(message)
            
        except Exception as e:
            logger.error(f"Error processing DM: {e}")
    
    async def send_auto_reply(self, user):
        """Send auto-reply to user who DMed the bot"""
        try:
            embed = discord.Embed(
                title="Auto-Reply: Please Don't DM",
                description="Hello! I'm a Discord bot and I don't respond to direct messages.",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="**Need Help?**",
                value="Please use my commands in a server where I'm present.\n"
                      "Use `s.help` to see available commands.",
                inline=False
            )
            
            embed.add_field(
                name="**Support**",
                value="If you need assistance, please ask in the server where you want to use my features.",
                inline=False
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text="This message was sent automatically")
            embed.timestamp = discord.utils.utcnow()
            
            await user.send(embed=embed)
            
        except discord.Forbidden:
            # User has DMs disabled
            logger.info(f"Could not send auto-reply to {user} - DMs disabled")
        except Exception as e:
            logger.error(f"Error sending auto-reply to {user}: {e}")
    
    async def send_dm_log_embed(self, message, channel, is_global=False, guild=None):
        """Send DM log embed to a specific channel"""
        try:
            # Check if user is in the guild (for per-server logging)
            user_in_guild = None
            if guild:
                user_in_guild = guild.get_member(message.author.id)
            
            # Create detailed log embed
            content_text = message.content[:1000] if message.content else '*No text content*'
            log_embed = discord.Embed(
                title="DM LOG",
                description=f"**User:** {message.author.mention}\n**Content:**\n```{content_text}```",
                color=0xff6b6b if guild and not user_in_guild else EMBED_COLOR_NORMAL
            )
            
            # User information
            log_embed.add_field(
                name="**User Details**",
                value=f"**Name:** `{message.author}`\n"
                      f"**ID:** `{message.author.id}`\n"
                      f"**Account Created:** <t:{int(message.author.created_at.timestamp())}:R>",
                inline=True
            )
            
            # Server relationship (only for per-server logging)
            if guild:
                if user_in_guild:
                    joined_at = user_in_guild.joined_at
                    log_embed.add_field(
                        name="**Server Member**",
                        value=f"**Yes**\n"
                              f"**Joined:** <t:{int(joined_at.timestamp()) if joined_at else 0}:R>\n"
                              f"**Roles:** {len(user_in_guild.roles) - 1}",
                        inline=True
                    )
                else:
                    log_embed.add_field(
                        name="**Server Member**",
                        value="**No**\n*User is not in this server*",
                        inline=True
                    )
            
            # Mutual servers
            mutual_servers = [g for g in self.bot.guilds if message.author in g.members]
            log_embed.add_field(
                name="**Mutual Servers**",
                value=f"**Count:** {len(mutual_servers)}\n"
                      f"**Examples:** {', '.join([g.name for g in mutual_servers[:3]])}{'...' if len(mutual_servers) > 3 else ''}",
                inline=False
            )
            
            # Message details
            log_embed.add_field(
                name="**Message Info**",
                value=f"**Time:** <t:{int(message.created_at.timestamp())}:F>\n"
                      f"**Length:** {len(message.content)} characters\n"
                      f"**Attachments:** {len(message.attachments)}",
                inline=True
            )
            
            # Auto-reply status
            log_embed.add_field(
                name="**Auto-Reply**",
                value="**Sent**\nUser was automatically informed not to DM",
                inline=True
            )
            
            log_embed.set_thumbnail(url=message.author.display_avatar.url)
            
            # Set footer based on logging type
            if is_global:
                log_embed.set_footer(text="Global DM Logging System")
            elif guild:
                log_embed.set_footer(text=f"DM Logging System • Guild: {guild.name}")
            else:
                log_embed.set_footer(text="DM Logging System")
                
            log_embed.timestamp = message.created_at
            
            await channel.send(embed=log_embed)
            
            # Handle attachments
            if message.attachments:
                for attachment in message.attachments:
                    attachment_embed = discord.Embed(
                        title="DM Attachment",
                        description=f"**Filename:** `{attachment.filename}`\n"
                                  f"**Size:** {attachment.size:,} bytes\n"
                                  f"**URL:** [Download]({attachment.url})",
                        color=0xffa500
                    )
                    
                    attachment_embed.add_field(
                        name="**From User**",
                        value=f"{message.author.mention} (`{message.author}`)",
                        inline=True
                    )
                    
                    if is_global:
                        attachment_embed.set_footer(text="Global DM Attachment Log")
                    else:
                        attachment_embed.set_footer(text="DM Attachment Log")
                    attachment_embed.timestamp = message.created_at
                    
                    # Try to set image if it's an image file
                    if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        attachment_embed.set_image(url=attachment.url)
                    
                    await channel.send(embed=attachment_embed)
                    
        except Exception as e:
            logger.error(f"Error sending DM log embed to channel {channel.id}: {e}")
    
    async def log_dm(self, message):
        """Log DM to all configured channels"""
        try:
            # Check for global DM logging channel first (only in bot support server)
            global_dm_channel_id = os.getenv('LOG_DMS_CHANNEL')
            if global_dm_channel_id:
                try:
                    global_channel = self.bot.get_channel(int(global_dm_channel_id))
                    # Only log globally if the channel is in the bot support server
                    if global_channel and global_channel.guild.id == 1411324489333215267:
                        await self.send_dm_log_embed(message, global_channel, is_global=True)
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid global DM logging channel ID: {global_dm_channel_id}")
            
            # Then check per-server DM logging channels
            all_guilds = dm_logging.get_all_dm_logging_guilds()
            
            for guild_id, channel_id in all_guilds.items():
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                
                await self.send_dm_log_embed(message, channel, is_global=False, guild=guild)
                
        except Exception as e:
            logger.error(f"Error logging DM: {e}")

async def setup_dm_logging(bot):
    """Setup function for DM logging"""
    await bot.add_cog(DMLoggingCog(bot))
    logger.info("DM logging system setup completed")
