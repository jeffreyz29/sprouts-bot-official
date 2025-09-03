"""
Discord Bot Event Handlers
Contains all event listeners for the bot
"""

import discord
from discord.ext import commands
import logging
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR

logger = logging.getLogger(__name__)

# Import bot_stats for guild count tracking
try:
    from web_viewer import bot_stats
except ImportError:
    bot_stats = None

class BotEvents(commands.Cog):
    """Event handlers for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.guild_log_channels = {}  # guild_id: channel_id for guild event logging
        
    def set_log_channel(self, guild_id: int, channel_id: int):
        """Set guild event logging channel"""
        self.guild_log_channels[guild_id] = channel_id
        
    def get_log_channel(self, guild_id: int):
        """Get guild event logging channel"""
        return self.guild_log_channels.get(guild_id, "Not set")
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild"""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id}) with {guild.member_count} members")
        
        # No automatic welcome messages sent to guilds
        
        # Global guild join logging 
        await self._send_guild_join_log(guild)
        
        # Update guild count for web dashboard
        if bot_stats:
            bot_stats.update_guild_count(len(self.bot.guilds))
    
    async def _send_guild_join_log(self, guild):
        """Send guild join log to global logging channel"""
        try:
            # Check for global guild logging channel
            import os
            global_channel_id = os.getenv('LOG_GUILD_EVENTS')
            if not global_channel_id:
                return  # Guild logging not configured
                
            try:
                log_channel = self.bot.get_channel(int(global_channel_id))
                if not log_channel:
                    logger.warning(f"Guild logging channel not found: {global_channel_id}")
                    return
            except (ValueError, TypeError):
                logger.error(f"Invalid guild logging channel ID: {global_channel_id}")
                return
            
            # Try to create an invite link
            invite_url = "No invite available"
            invite_channel = None
            
            # Try system channel first, then any channel with create instant invite permission
            if guild.system_channel and guild.system_channel.permissions_for(guild.me).create_instant_invite:
                invite_channel = guild.system_channel
            else:
                # Find first channel where bot can create invites
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).create_instant_invite:
                        invite_channel = channel
                        break
            
            # Create invite if we found a suitable channel
            if invite_channel:
                try:
                    invite = await invite_channel.create_invite(
                        max_age=0,  # Never expires
                        max_uses=0,  # Unlimited uses
                        unique=False,  # Don't create a new invite if one exists
                        reason="Bot join logging"
                    )
                    invite_url = f"[Server Invite]({invite.url})"
                except Exception as e:
                    logger.warning(f"Failed to create invite for {guild.name}: {e}")
                    invite_url = "Failed to create invite"
            
            # Create detailed server join log embed
            join_embed = discord.Embed(
                title="Bot Joined Server",
                description=f"Sprouts bot has been added to a new server!",
                color=0x00ff00  # Green for join
            )
            
            # Server information
            join_embed.add_field(
                name="Server Information",
                value=f"**Name:** {guild.name}\n"
                      f"**ID:** `{guild.id}`\n"
                      f"**Owner:** {guild.owner.mention} (`{guild.owner.id}`)\n"
                      f"**Members:** {guild.member_count:,}\n"
                      f"**Verification Level:** {guild.verification_level.name.title()}\n"
                      f"**Created:** <t:{int(guild.created_at.timestamp())}:F>",
                inline=False
            )
            
            # Channel and role counts
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            roles = len(guild.roles)
            
            join_embed.add_field(
                name="Server Statistics",
                value=f"**Text Channels:** {text_channels}\n"
                      f"**Voice Channels:** {voice_channels}\n"
                      f"**Categories:** {categories}\n"
                      f"**Roles:** {roles}",
                inline=True
            )
            
            # Features and boost info
            features = ", ".join(guild.features) if guild.features else "None"
            if len(features) > 100:
                features = features[:97] + "..."
            
            join_embed.add_field(
                name="Server Features",
                value=f"**Features:** {features}\n"
                      f"**Boost Level:** {guild.premium_tier}\n"
                      f"**Boost Count:** {guild.premium_subscription_count or 0}",
                inline=True
            )
            
            # Server invite
            join_embed.add_field(
                name="Server Access",
                value=f"**Invite:** {invite_url}",
                inline=False
            )
            
            # Add server icon if available
            if guild.icon:
                join_embed.set_thumbnail(url=guild.icon.url)
            
            # Add banner if available
            if guild.banner:
                join_embed.set_image(url=guild.banner.url)
            
            join_embed.set_footer(text=f"Total servers: {len(self.bot.guilds)}")
            join_embed.timestamp = discord.utils.utcnow()
            
            await log_channel.send(embed=join_embed)
            logger.info(f"Sent guild join log for {guild.name} to global channel")
            
        except Exception as e:
            logger.error(f"Error sending guild join log: {e}")
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Called when the bot is removed from a guild"""
        logger.info(f"Removed from guild: {guild.name} (ID: {guild.id})")
        
        # Global guild leave logging
        await self._send_guild_leave_log(guild)
        
        # Update guild count for web dashboard
        if bot_stats:
            bot_stats.update_guild_count(len(self.bot.guilds))
    
    async def _send_guild_leave_log(self, guild):
        """Send guild leave log to global logging channel"""
        try:
            # Check for global guild logging channel
            import os
            global_channel_id = os.getenv('LOG_GUILD_EVENTS')
            if not global_channel_id:
                return  # Guild logging not configured
                
            try:
                log_channel = self.bot.get_channel(int(global_channel_id))
                if not log_channel:
                    logger.warning(f"Guild logging channel not found: {global_channel_id}")
                    return
            except (ValueError, TypeError):
                logger.error(f"Invalid guild logging channel ID: {global_channel_id}")
                return
                
            # Create detailed server leave log embed
            leave_embed = discord.Embed(
                title="Bot Left Server",
                description=f"Sprouts bot has been removed from a server.",
                color=0xff0000  # Red for leave
            )
            
            # Server information
            leave_embed.add_field(
                name="Server Details",
                value=f"**Name:** {guild.name}\n"
                      f"**ID:** `{guild.id}`\n"
                      f"**Members:** {guild.member_count:,}",
                inline=False
            )
            
            # Owner information
            owner_info = "Unknown"
            if guild.owner:
                owner_info = f"{guild.owner.mention} ({guild.owner})"
            
            leave_embed.add_field(
                name="Server Owner",
                value=owner_info,
                inline=False
            )
            
            # Server features
            features = guild.features
            if features:
                feature_list = ", ".join([feature.replace("_", " ").title() for feature in features[:5]])
                if len(features) > 5:
                    feature_list += f" +{len(features) - 5} more"
                leave_embed.add_field(
                    name="Server Features",
                    value=feature_list,
                    inline=False
                )
            
            # Add server icon if available
            if guild.icon:
                leave_embed.set_thumbnail(url=guild.icon.url)
            
            leave_embed.set_footer(text=f"Total servers: {len(self.bot.guilds)}")
            leave_embed.timestamp = discord.utils.utcnow()
            
            await log_channel.send(embed=leave_embed)
            logger.info(f"Sent guild leave log for {guild.name} to global channel")
            
        except Exception as e:
            logger.error(f"Error sending guild leave log: {e}")
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Check for disabled commands before processing (maintenance mode handled in global_check)"""
        # Skip check for developers
        devonly_cog = self.bot.get_cog('DevOnly')
        if devonly_cog and ctx.author.id in devonly_cog.developer_ids:
            return
        
        # Check if command is disabled (maintenance mode is handled in bot.py global_check)
        if devonly_cog and ctx.command.name in devonly_cog.disabled_commands:
            embed = discord.Embed(
                title="<a:sprouts_warning_dns:1412200379206336522> Command Disabled",
                description=f"The `{ctx.command.name}` command is currently disabled.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            # Prevent command from executing
            raise commands.CommandError(f"Command {ctx.command.name} is disabled")
    
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle DM messages and bot mentions - DO NOT PROCESS COMMANDS"""
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return
        
        # Handle DMs (not guild messages)
        if isinstance(message.channel, discord.DMChannel):
            try:
                # Load DM settings
                import json
                import os
                
                settings_file = "dm_settings.json"
                if os.path.exists(settings_file):
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                else:
                    settings = {"log_dms": False}
                
                # DM logging is now handled by the DM logging cog
                
                logger.info(f"DM received from {message.author} and logged to configured channels")
                
            except Exception as e:
                logger.error(f"Error handling DM from {message.author}: {e}")
        else:
            # Log mentions of the bot (no auto-response) in guild messages
            if self.bot.user in message.mentions:
                logger.info(f"Bot mentioned by {message.author} in {message.guild.name if message.guild else 'DM'}")
        
        # DO NOT CALL self.bot.process_commands(message) HERE
        # The main bot.py on_message handler already does this
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors with proper embeds and usage instructions"""
        # Check if command has its own error handler
        if hasattr(ctx.command, 'on_error'):
            return
            
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        if isinstance(error, commands.CheckFailure):
            # Ignore check failures - they should be handled by cog-specific error handlers
            return
        
        # Get command prefix for usage instructions
        prefix = ctx.prefix
        
        if isinstance(error, commands.MissingRequiredArgument):
            # Skip DevOnly cog commands - they have their own error handler
            if ctx.command and ctx.command.cog_name == "DevOnly":
                return
            
            # Skip ticket commands - they handle their own permission checks
            if ctx.command and ctx.command.cog_name == "TicketSystem":
                return
            
            # Get command usage info for helpful error messages
            command_name = ctx.command.name if ctx.command else "unknown"
            
            # Clean format like s.help command
            usage_patterns = {
                "inviteinfo": "inviteinfo <invite>",
                "userinfo": "userinfo [user]", 
                "avatar": "avatar [user]",
                "roleinfo": "roleinfo <role>",
                "channelinfo": "channelinfo <#channelID>",
                "setprefix": "setprefix <new_prefix>",
                # Ticket system commands
                "new": "new [reason]",
                "add": "add <member>",
                "remove": "remove <member>",
                "move": "move <category>",
                "priority": "priority <level>",
                "topic": "topic <new_topic>",
                "transfer": "transfer <member>",
                "rename": "rename <new_name>",
                "createpanel": "createpanel <name>",
                "delpanel": "delpanel <panel_id>",
                "ticketlimit": "ticketlimit [number]",
                "ticketuseembed": "ticketuseembed <embed_name>",
                # Auto responder commands
                "add_responder": "ar add <trigger> | <response>",
                "remove_responder": "ar remove <trigger>",
                "list_responders": "ar list",
                "toggle_responder": "ar toggle <trigger>",
                "responder_stats": "ar stats <trigger>",
                # Other commands
                "reminder": "reminder <time> <message>",
                "delreminder": "delreminder <reminder_id>",
                "stick": "stick <#channelID> <message>",
                "stickslow": "stickslow <#channelID> <message>",
                "stickstop": "stickstop <#channelID>",
                "stickstart": "stickstart <#channelID>",
                "stickremove": "stickremove <#channelID>",
                "stickspeed": "stickspeed <#channelID> [speed]"
            }
            
            embed = discord.Embed(
                title=f"<a:sprouts_error_dns:1411790004652605500> {command_name}",
                description="Optional arguments are marked by `[arg]` and mandatory arguments are marked by `<arg>`.",
                color=EMBED_COLOR_ERROR
            )
            
            # Get usage pattern or default
            usage_pattern = usage_patterns.get(command_name, f"{command_name} <argument>")
            
            embed.add_field(
                name="How to Use This Command",
                value=f"**Correct Usage:**\n```\n{prefix}{usage_pattern}\n```",
                inline=False
            )
            
            # Add specific examples based on command
            examples = {
                "userinfo": f"Examples:\n`{prefix}userinfo` - Your info\n`{prefix}userinfo @user` - User's info\n`{prefix}userinfo username` - By name",
                "avatar": f"Examples:\n`{prefix}avatar` - Your avatar\n`{prefix}avatar @user` - User's avatar",
                "setprefix": f"Examples:\n`{prefix}setprefix !` - Change to !\n`{prefix}setprefix ?` - Change to ?",
                "new": f"Examples:\n`{prefix}new` - Simple ticket\n`{prefix}new I need help` - With reason",
                "add": f"Examples:\n`{prefix}add @user` - Add user to ticket",
                "roleinfo": f"Examples:\n`{prefix}roleinfo @role` - Role info\n`{prefix}roleinfo Admin` - By name",
                "channelinfo": f"Examples:\n`{prefix}channelinfo #channel` - Channel info",
                "remind": f"Examples:\n`{prefix}remind 1h Take break` - 1 hour reminder\n`{prefix}remind 30m Check oven` - 30 min reminder"
            }
            
            if command_name in examples:
                embed.add_field(
                    name="Examples",
                    value=examples[command_name],
                    inline=False
                )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        elif isinstance(error, commands.BadArgument):
            command_name = ctx.command.name if ctx.command else "unknown"
            embed = discord.Embed(
                title=f"<a:sprouts_error_dns:1411790004652605500> {command_name}",
                description="Optional arguments are marked by `[arg]` and mandatory arguments are marked by `<arg>`.",
                color=EMBED_COLOR_ERROR
            )
            
            embed.add_field(
                name="Invalid Argument",
                value=f"The argument you provided is not valid for this command.\n\n**Get detailed help:**\n```\n{prefix}help {command_name}\n```",
                inline=False
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        elif isinstance(error, commands.MissingPermissions):
            command_name = ctx.command.name if ctx.command else "unknown"
            embed = discord.Embed(
                title=f"<a:sprouts_error_dns:1411790004652605500> {command_name}",
                description="Optional arguments are marked by `[arg]` and mandatory arguments are marked by `<arg>`.",
                color=EMBED_COLOR_ERROR
            )
            
            embed.add_field(
                name="Description",
                value="You don't have permission to use this command.",
                inline=False
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        elif isinstance(error, commands.BotMissingPermissions):
            command_name = ctx.command.name if ctx.command else "unknown"
            embed = discord.Embed(
                title=f"<a:sprouts_error_dns:1411790004652605500> {command_name}",
                description="Optional arguments are marked by `[arg]` and mandatory arguments are marked by `<arg>`.",
                color=EMBED_COLOR_ERROR
            )
            
            embed.add_field(
                name="Description",
                value="I don't have the required permissions to execute this command.",
                inline=False
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="<a:sprouts_error_dns:1411790004652605500> Command Cooldown",
                description=f"Please wait {error.retry_after:.1f} seconds before using this command again.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        elif isinstance(error, commands.NotOwner):
            command_name = ctx.command.name if ctx.command else "unknown"
            embed = discord.Embed(
                title=f"<a:sprouts_error_dns:1411790004652605500> {command_name}",
                description="Optional arguments are marked by `[arg]` and mandatory arguments are marked by `<arg>`.",
                color=EMBED_COLOR_ERROR
            )
            
            embed.add_field(
                name="Description",
                value="This command can only be used by the bot owner.",
                inline=False
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        else:
            logger.error(f"Unhandled command error: {error}")
            command_name = ctx.command.name if ctx.command else "unknown"
            embed = discord.Embed(
                title=f"<a:sprouts_error_dns:1411790004652605500> {command_name}",
                description="Optional arguments are marked by `[arg]` and mandatory arguments are marked by `<arg>`.",
                color=EMBED_COLOR_ERROR
            )
            
            embed.add_field(
                name="Description",
                value="An unexpected error occurred while processing your command.",
                inline=False
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
    
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Log command usage when command logging is enabled"""
        try:
            # Load command logging settings
            import json
            import os
            
            settings_file = "dm_settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {"log_commands": False}
            
            # Only log if command logging is enabled
            if settings.get("log_commands", False):
                # Get the event logger cog
                event_logger = self.bot.get_cog('EventLogger')
                if event_logger:
                    log_embed = discord.Embed(
                        title="Command Used",
                        color=EMBED_COLOR_NORMAL
                    )
                    log_embed.add_field(
                        name="User",
                        value=f"{ctx.author} ({ctx.author.id})",
                        inline=True
                    )
                    log_embed.add_field(
                        name="Command",
                        value=f"`{ctx.message.content}`",
                        inline=False
                    )
                    log_embed.add_field(
                        name="Channel",
                        value=f"#{ctx.channel.name}" if hasattr(ctx.channel, 'name') else "DM",
                        inline=True
                    )
                    if ctx.guild:
                        log_embed.add_field(
                            name="Server",
                            value=f"{ctx.guild.name} ({ctx.guild.id})",
                            inline=True
                        )
                    log_embed.set_thumbnail(url=ctx.author.display_avatar.url)
                    log_embed.timestamp = ctx.message.created_at
                    
                    await event_logger.send_command_log(log_embed)
                    
        except Exception as e:
            logger.error(f"Error logging command usage: {e}")

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """Handle general errors"""
        logger.error(f"An error occurred in event {event}", exc_info=True)

async def setup_events(bot):
    """Setup all event handlers for the bot"""
    await bot.add_cog(BotEvents(bot))
    logger.info("Event handlers setup completed")
