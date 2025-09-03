"""
Utilities Commands for Sprouts Bot
Provides various utility commands including server info, user info, and variable listings
"""

import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_SUCCESS, EMBED_COLOR_ERROR, EMBED_COLOR_WARNING, SPROUTS_ERROR, SPROUTS_CHECK, SPROUTS_WARNING

logger = logging.getLogger(__name__)

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="variables", help="Show all available variables for embeds and messages")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def variables(self, ctx):
        """Show comprehensive list of available variables for embeds and auto responses

        Usage: `{ctx.prefix}variables`
        Displays all 40+ available variables with descriptions and usage syntax

        Examples:
        - `{ctx.prefix}variables` - View complete variable reference guide

        Variable Categories:
        - User Variables: Display user information like name, avatar, join date
        - Server Variables: Show server details like name, member count, boosts
        - Channel Variables: Reference channel data like name, topic, category
        - Date/Time Variables: Current timestamps and formatted dates
        - Ticket Variables: Special variables for ticket system integration

        Usage Format:
        - Wrap variables in `$(variable.name)` syntax
        - Variables are case-sensitive and must match exactly
        - Works in embeds, auto-responses, sticky messages, and welcome system
        - Variables are processed in real-time when content is displayed

        Common Errors:
        - Invalid syntax: Must use `$(variable.name)` format exactly
        - Unknown variable: Check spelling and available variable list
        - Missing context: Some variables only work in specific contexts
        """
        try:
            embed = discord.Embed(
                title="Available Variables",
                description="Usage: Wrap variables in `$(variable.name)` syntax\n"
                           "Example: `$(user.name)` displays the username\n\n"
                           "Available for: Embeds, Custom Replies, Sticky Messages, Welcome System",
                color=EMBED_COLOR_NORMAL
            )
            
            # User Variables
            user_vars = [
                "`$(user.name)` - User's username",
                "`$(user.mention)` - Mentions the user",
                "`$(user.id)` - User's Discord ID",
                "`$(user.nick)` - User's server nickname",
                "`$(user.tag)` - Full username with discriminator",
                "`$(user.avatar)` - User's avatar image URL",
                "`$(user.joined)` - Date user joined the server",
                "`$(user.created)` - Date user account was created"
            ]
            
            embed.add_field(
                name="User Variables",
                value="\n".join(user_vars),
                inline=False
            )
            
            # Server Variables
            server_vars = [
                "`$(server.name)` - Server name",
                "`$(server.membercount)` - Total member count",
                "`$(server.owner)` - Server owner's name",
                "`$(server.id)` - Server's Discord ID",
                "`$(server.icon)` - Server icon image URL",
                "`$(server.created)` - Date server was created",
                "`$(server.boosts)` - Number of server boosts",
                "`$(server.channels)` - Total channel count"
            ]
            
            embed.add_field(
                name="Server Variables",
                value="\n".join(server_vars),
                inline=False
            )
            
            # Channel Variables
            channel_vars = [
                "`$(channel.name)` - Current channel name",
                "`$(channel.id)` - Channel's Discord ID",
                "`$(channel.mention)` - Mentions the current channel", 
                "`$(channel.topic)` - Channel's topic description",
                "`$(channel.category)` - Channel's category name",
                "`$(channel.position)` - Channel's position in list",
                "`$(channel.created)` - Date channel was created",
                "`$(channel.nsfw)` - Whether channel is NSFW",
                "`$(channel.slowmode)` - Channel slowmode delay"
            ]
            
            embed.add_field(
                name="Channel Variables",
                value="\n".join(channel_vars),
                inline=False
            )
            
            # Time Variables  
            time_vars = [
                "`$(time)` - Current time",
                "`$(date)` - Current date",
                "`$(datetime)` - Current date and time",
                "`$(year)` - Current year",
                "`$(month)` - Current month name",
                "`$(day)` - Current day of month"
            ]
            
            embed.add_field(
                name="Time Variables",
                value="\n".join(time_vars),
                inline=False
            )
            
            # Special Variables
            special_vars = [
                "`$(random:1-100)` - Random number between range",
                "`$(random:word1|word2)` - Random choice from options",
                "`$(choose:a|b|c)` - Randomly selects from list",
                "`$(math:5+5)` - Performs basic math calculations"
            ]
            
            embed.add_field(
                name="Special Variables",
                value="\n".join(special_vars),
                inline=False
            )
            
            # Ticket Variables
            ticket_vars = [
                "`$(ticket.id)` - Ticket's unique ID number",
                "`$(ticket.creator)` - User who created ticket",
                "`$(ticket.category)` - Ticket category name",
                "`$(ticket.status)` - Current ticket status",
                "`$(ticket.created)` - Date ticket was created",
                "`$(ticket.staff)` - Staff member assigned to ticket",
                "`$(ticket.channel)` - Ticket channel name",
                "`$(ticket.reason)` - Reason for creating ticket",
                "`$(ticket.priority)` - Ticket priority level"
            ]
            
            embed.add_field(
                name="Ticket Variables", 
                value="\n".join(ticket_vars),
                inline=False
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Variables command used by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error in variables command: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description="An error occurred while fetching variables.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)

    @commands.command(name="ping", help="Check bot response time and API latency")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        """Check bot latency and response time with detailed statistics

        Usage: `{ctx.prefix}ping`
        Shows bot latency, API response time, and system performance metrics

        Examples:
        - `{ctx.prefix}ping` - Check if bot is responsive and view performance stats

        Performance metrics:
        - Heartbeat latency to Discord
        - Response time measurement
        - Bot uptime since last restart
        - Memory usage and system stats
        """
        try:
            import time
            import psutil
            
            # Measure response time
            start_time = time.perf_counter()
            temp_message = await ctx.send("Pinging...")
            
            # Add delay to calculate ping properly
            await asyncio.sleep(0.5)
            
            end_time = time.perf_counter()
            response_time = round((end_time - start_time) * 1000)
            
            # Get latencies
            heartbeat = round(self.bot.latency * 1000)
            
            # Get uptime
            uptime_seconds = (discord.utils.utcnow() - self.bot.start_time).total_seconds()
            uptime_hours = int(uptime_seconds // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)
            uptime_secs = int(uptime_seconds % 60)
            uptime_display = f"{uptime_hours:02d}:{uptime_minutes:02d}:{uptime_secs:02d}"
            
            embed = discord.Embed(
                title="🏓 Pong!",
                color=EMBED_COLOR_NORMAL
            )
            
            # Main ping stats
            ping_stats = f"💟 HB: {heartbeat} ms\n"
            ping_stats += f"🔁 RTT: {response_time} ms\n"
            ping_stats += f"⬆️ UT: {uptime_display}"
            
            embed.add_field(
                name="",
                value=ping_stats,
                inline=False
            )
            
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await temp_message.edit(content=None, embed=embed)
            logger.info(f"Ping command used by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Ping Error",
                description="An error occurred while checking latency.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)

    @commands.command(name="avatar", help="Get user's avatar (defaults to yourself)")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def avatar(self, ctx, member: discord.Member = None):
        """Display user's avatar in high resolution

        Usage: `{ctx.prefix}avatar [@user]`
        Shows high-quality avatar image with download links (defaults to yourself)

        Examples:
        - `{ctx.prefix}avatar` - View your own avatar
        - `{ctx.prefix}avatar` @username - View specific user's avatar
        - `{ctx.prefix}avatar 123456789` - View user avatar by user id

        Features:
        - High-resolution image display
        - Multiple format download links (PNG, JPG, WebP)
        - Shows both server and global avatars if different
        - Animated GIF support for Nitro users
        """
        try:
            target = member or ctx.author
            embed = discord.Embed(
                title=f"{target.display_name}'s Avatar",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_image(url=target.display_avatar.url)
            embed.add_field(
                name="Download Links",
                value=f"[PNG]({target.display_avatar.with_format('png').url}) | "
                      f"[JPG]({target.display_avatar.with_format('jpg').url}) | "
                      f"[WEBP]({target.display_avatar.with_format('webp').url})",
                inline=False
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Avatar command used by {ctx.author}")
        except Exception as e:
            logger.error(f"Error in avatar command: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Avatar Error",
                description="An error occurred while fetching avatar.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)

    @commands.command(name="userinfo", help="Get detailed user information (defaults to yourself)")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def userinfo(self, ctx, member: discord.Member = None):
        """Display detailed user information

        Usage: `{ctx.prefix}userinfo [@user]`
        Shows comprehensive information about user (defaults to yourself)

        Examples:
        - `{ctx.prefix}userinfo` - View your own information
        - `{ctx.prefix}userinfo @username` - View specific user's info
        - `{ctx.prefix}userinfo 1234567890` - View user info by user id

        Information shown:
        - Account creation date and join date
        - User roles and permissions
        - Avatar and presence status
        - Boost status and acknowledgments
        """
        try:
            target = member or ctx.author
            
            embed = discord.Embed(
                title=f"User Information - {target.display_name}",
                color=target.color if target.color != discord.Color.default() else EMBED_COLOR_NORMAL
            )
            
            # Basic info
            embed.add_field(
                name="User Details",
                value=f"**Username:** {target.name}\n"
                      f"**Display Name:** {target.display_name}\n"
                      f"**ID:** `{target.id}`\n"
                      f"**Bot:** {'Yes' if target.bot else 'No'}",
                inline=True
            )
            
            # Server info
            if target.joined_at:
                embed.add_field(
                    name="Server Info",
                    value=f"**Joined:** <t:{int(target.joined_at.timestamp())}:F>\n"
                          f"**Nickname:** {target.nick or 'None'}\n"
                          f"**Top Role:** {target.top_role.name}",
                    inline=True
                )
            
            # Account info with proper presence
            status_emoji = {
                discord.Status.online: "",
                discord.Status.idle: "", 
                discord.Status.dnd: "",
                discord.Status.offline: ""
            }
            
            # Get user activity
            activity_text = "None"
            if target.activities:
                activity = target.activities[0]  # Get primary activity
                if activity.type == discord.ActivityType.playing:
                    activity_text = f"Playing {activity.name}"
                elif activity.type == discord.ActivityType.listening:
                    activity_text = f"Listening to {activity.name}"
                elif activity.type == discord.ActivityType.watching:
                    activity_text = f"Watching {activity.name}"
                elif activity.type == discord.ActivityType.streaming:
                    activity_text = f"Streaming {activity.name}"
                elif activity.type == discord.ActivityType.custom:
                    activity_text = str(activity) if activity else "None"
            
            embed.add_field(
                name="Account Info",
                value=f"**Created:** <t:{int(target.created_at.timestamp())}:F>\n"
                      f"**Status:** {status_emoji.get(target.status, '')} {str(target.status).title()}\n"
                      f"**Activity:** {activity_text}",
                inline=True
            )
            
            # Role list (max 10)
            roles = [role.name for role in target.roles[1:]]  # Skip @everyone
            if roles:
                role_list = ", ".join(roles[:10])
                if len(roles) > 10:
                    role_list += f" +{len(roles) - 10} more"
                embed.add_field(
                    name=f"Roles ({len(roles)})",
                    value=role_list,
                    inline=False
                )
            
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Userinfo command used by {ctx.author}")
        except Exception as e:
            logger.error(f"Error in userinfo command: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} User Info Error",
                description="An error occurred while fetching user information.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)

    @commands.command(name="serverinfo", help="Get detailed server information and statistics")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def serverinfo(self, ctx):
        """Display comprehensive server information

        Usage: `{ctx.prefix}serverinfo`
        Shows detailed information about the current server

        Examples:
        - `{ctx.prefix}serverinfo` - View complete server statistics

        Information shown:
        - Basic server details (name, ID, owner)
        - Member statistics and online counts
        - Server boost level and features
        - Channel counts by type
        - Role information and permissions
        """
        try:
            guild = ctx.guild
            if not guild:
                await ctx.reply("This command can only be used in a server.", mention_author=False)
                return
            
            embed = discord.Embed(
                title=f"Server Information - {guild.name}",
                color=EMBED_COLOR_NORMAL
            )
            
            # Basic info
            embed.add_field(
                name="Server Details",
                value=f"**Name:** {guild.name}\n"
                      f"**ID:** `{guild.id}`\n"
                      f"**Owner:** {guild.owner.mention if guild.owner else 'Unknown'}\n"
                      f"**Created:** <t:{int(guild.created_at.timestamp())}:F>",
                inline=True
            )
            
            # Member info
            embed.add_field(
                name="Members",
                value=f"**Total:** {guild.member_count:,}\n"
                      f"**Verification:** {guild.verification_level.name.title()}\n"
                      f"**Boost Tier:** {guild.premium_tier}\n"
                      f"**Boosts:** {guild.premium_subscription_count or 0}",
                inline=True
            )
            
            # Channel counts
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            
            embed.add_field(
                name="Channels",
                value=f"**Text:** {text_channels}\n"
                      f"**Voice:** {voice_channels}\n"
                      f"**Categories:** {categories}\n"
                      f"**Total:** {len(guild.channels)}",
                inline=True
            )
            
            # Role and emoji counts
            embed.add_field(
                name="Other",
                value=f"**Roles:** {len(guild.roles)}\n"
                      f"**Emojis:** {len(guild.emojis)}\n"
                      f"**Features:** {len(guild.features)}",
                inline=True
            )
            
            # Features
            if guild.features:
                features = ", ".join([feature.replace("_", " ").title() for feature in guild.features[:5]])
                if len(guild.features) > 5:
                    features += f" +{len(guild.features) - 5} more"
                embed.add_field(
                    name="Features",
                    value=features,
                    inline=False
                )
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Serverinfo command used by {ctx.author}")
        except Exception as e:
            logger.error(f"Error in serverinfo command: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Server Info Error",
                description="An error occurred while fetching server information.",
                color=EMBED_COLOR_ERROR
            )
            error_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=error_embed, mention_author=False)

    @commands.command(name="channelinfo", help="Get detailed channel information")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def channelinfo(self, ctx, channel: discord.TextChannel = None):
        """Display detailed channel information

        Usage: `{ctx.prefix}channelinfo [#channel]`
        Shows comprehensive information about channel

        Examples:
        - `{ctx.prefix}channelinfo` - View current channel information
        - `{ctx.prefix}channelinfo #general` - View specific channel info
        - `{ctx.prefix}channelinfo 123456789` - View channel info by a specific channel id

        Information shown:
        - Channel type, creation date, and category
        - Permission overwrites and access controls
        - Topic, slowmode, and special settings
        - Member access and restriction details
        """
        try:
            target_channel = channel or ctx.channel
            
            embed = discord.Embed(
                title=f"Channel Information - #{target_channel.name}",
                color=EMBED_COLOR_NORMAL
            )
            
            # Basic info
            embed.add_field(
                name="Channel Details",
                value=f"**Name:** {target_channel.name}\n"
                      f"**ID:** `{target_channel.id}`\n"
                      f"**Type:** {str(target_channel.type).title()}\n"
                      f"**Created:** <t:{int(target_channel.created_at.timestamp())}:F>",
                inline=True
            )
            
            # Channel settings
            embed.add_field(
                name="Settings",
                value=f"**Category:** {target_channel.category.name if target_channel.category else 'None'}\n"
                      f"**Position:** {target_channel.position}\n"
                      f"**NSFW:** {'Yes' if target_channel.nsfw else 'No'}\n"
                      f"**Slowmode:** {target_channel.slowmode_delay}s",
                inline=True
            )
            
            # Topic
            if target_channel.topic:
                embed.add_field(
                    name="Topic",
                    value=target_channel.topic[:1024],
                    inline=False
                )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Channelinfo command used by {ctx.author}")
        except Exception as e:
            logger.error(f"Error in channelinfo command: {e}")
            await ctx.reply("An error occurred while fetching channel information.", mention_author=False)

    @commands.command(name="roleinfo", help="Get detailed role information and permissions")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def roleinfo(self, ctx, *, role: discord.Role):
        """Display detailed role information

        Usage: `{ctx.prefix}roleinfo <@role|role_name>`
        Shows comprehensive information about server role

        Examples:
        - `{ctx.prefix}roleinfo @Moderator` - View role details by mention
        - `{ctx.prefix}roleinfo Admin` - View role by name
        - {ctx.prefix}roleinfo 123456789 - View role by role id

        Information shown:
        - Role permissions and hierarchy position
        - Member count and role color
        - Creation date and mentionable status
        - Integration and bot role information
        """
        try:
            embed = discord.Embed(
                title=f"Role Information - {role.name}",
                color=role.color if role.color != discord.Color.default() else EMBED_COLOR_NORMAL
            )
            
            # Basic info
            embed.add_field(
                name="Role Details",
                value=f"**Name:** {role.name}\n"
                      f"**ID:** `{role.id}`\n"
                      f"**Color:** {str(role.color)}\n"
                      f"**Created:** <t:{int(role.created_at.timestamp())}:F>",
                inline=True
            )
            
            # Role settings
            embed.add_field(
                name="Settings",
                value=f"**Position:** {role.position}\n"
                      f"**Mentionable:** {'Yes' if role.mentionable else 'No'}\n"
                      f"**Hoisted:** {'Yes' if role.hoist else 'No'}\n"
                      f"**Members:** {len(role.members)}",
                inline=True
            )
            
            # Permissions
            if role.permissions.administrator:
                perms = "Administrator (All Permissions)"
            else:
                important_perms = []
                if role.permissions.manage_guild: important_perms.append("Manage Server")
                if role.permissions.manage_channels: important_perms.append("Manage Channels")
                if role.permissions.manage_roles: important_perms.append("Manage Roles")
                if role.permissions.manage_messages: important_perms.append("Manage Messages")
                if role.permissions.kick_members: important_perms.append("Kick Members")
                if role.permissions.ban_members: important_perms.append("Ban Members")
                
                perms = ", ".join(important_perms[:5]) if important_perms else "Standard permissions"
                if len(important_perms) > 5:
                    perms += f" +{len(important_perms) - 5} more"
            
            embed.add_field(
                name="Key Permissions",
                value=perms,
                inline=False
            )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Roleinfo command used by {ctx.author}")
        except Exception as e:
            logger.error(f"Error in roleinfo command: {e}")
            await ctx.reply("An error occurred while fetching role information.", mention_author=False)

    @commands.command(name="inviteinfo", help="Get information about Discord invite")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def inviteinfo(self, ctx, invite_url: str):
        """Display information about Discord invite link

        Usage: `{ctx.prefix}inviteinfo <invite_code>`
        Shows detailed information about invite

        Examples:
        - `{ctx.prefix}inviteinfo discord.gg/abc123` - Check invite details
        - `{ctx.prefix}inviteinfo abc123` - Check invite by code only

        Information shown:
        - Target server name and description
        - Member and online counts
        - Invite creator and expiration
        - Channel destination and features
        """
        try:
            # Extract invite code from URL
            invite_code = invite_url.split('/')[-1]
            
            try:
                invite = await self.bot.fetch_invite(invite_code)
            except discord.NotFound:
                embed = discord.Embed(
                    title="<a:sprouts_error_dns:1411790004652605500> Invalid Invite",
                    description="The invite link is invalid or has expired.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            embed = discord.Embed(
                title=f"Invite Information - {invite.guild.name}",
                color=EMBED_COLOR_NORMAL
            )
            
            # Server info
            embed.add_field(
                name="Server Details",
                value=f"**Name:** {invite.guild.name}\n"
                      f"**ID:** `{invite.guild.id}`\n"
                      f"**Members:** {invite.approximate_member_count:,}\n"
                      f"**Online:** {invite.approximate_presence_count:,}",
                inline=True
            )
            
            # Invite info
            embed.add_field(
                name="Invite Details",
                value=f"**Code:** `{invite.code}`\n"
                      f"**Channel:** #{invite.channel.name}\n"
                      f"**Inviter:** {invite.inviter.name if invite.inviter else 'Unknown'}\n"
                      f"**Created:** <t:{int(invite.created_at.timestamp())}:F>" if invite.created_at else "**Created:** Unknown",
                inline=True
            )
            
            # Expiry and usage
            expire_info = "Never" if invite.max_age == 0 else f"<t:{int((invite.created_at.timestamp() + invite.max_age))}:F>" if invite.created_at else "Unknown"
            usage_info = "Unlimited" if invite.max_uses == 0 else f"{invite.uses}/{invite.max_uses}"
            
            embed.add_field(
                name="Usage & Expiry",
                value=f"**Uses:** {usage_info}\n"
                      f"**Expires:** {expire_info}\n"
                      f"**Temporary:** {'Yes' if invite.temporary else 'No'}",
                inline=True
            )
            
            if invite.guild.icon:
                embed.set_thumbnail(url=invite.guild.icon.url)
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Inviteinfo command used by {ctx.author}")
        except Exception as e:
            logger.error(f"Error in inviteinfo command: {e}")
            await ctx.reply("An error occurred while fetching invite information.", mention_author=False)

    @commands.command(name="setprefix", help="Set custom command prefix for this server")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def setprefix(self, ctx, *, new_prefix: str):
        """Set a custom prefix for this server

        Usage: {`ctx.prefix}setprefix <new_prefix>`
        Changes bot prefix for this server (Administrator permission required)

        Examples:
        - `{ctx.prefix}setprefix !` - Sets prefix to !
        - `{ctx.prefix}setprefix >>` - Sets prefix to >>
        - `{ctx.prefix}setprefix bot.` - Sets prefix to bot.

        Common Errors:
        - Prefix too long: Must be 5 characters or less
        - Administrator only: Requires Administrator permission
        - Invalid characters: Some special characters may not work
        """
        try:
            if len(new_prefix) > 5:
                embed = discord.Embed(
                    title="<a:sprouts_error_dns:1411790004652605500> Prefix Too Long",
                    description="Prefix must be 5 characters or less.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            from src.cogs.guild_settings import guild_settings
            old_prefix = guild_settings.get_prefix(ctx.guild.id)
            guild_settings.set_prefix(ctx.guild.id, new_prefix)
            
            embed = discord.Embed(
                title="<a:sprouts_check_dns:1411790001565466725> Prefix Updated",
                description=f"Server prefix changed from `{old_prefix}` to `{new_prefix}`",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Usage",
                value=f"You can now use `{new_prefix}help` or mention me <@{self.bot.user.id}>",
                inline=False
            )
            embed.set_footer(text=f"Changed by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Prefix changed in {ctx.guild.name} from {old_prefix} to {new_prefix}")
        except Exception as e:
            logger.error(f"Error in setprefix command: {e}")
            await ctx.reply("An error occurred while setting prefix.", mention_author=False)
    
    @setprefix.error
    async def setprefix_error(self, ctx, error):
        """Handle setprefix command errors"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="<a:sprouts_error_dns:1411790004652605500> Missing Permissions",
                description="You need **Administrator** permissions to change the server prefix.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="prefix", help="Show current server prefix")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def prefix(self, ctx):
        """Show the current server prefix

        Usage: `{ctx.prefix}prefix`
        Displays the current bot prefix for this server with usage instructions

        Examples:
        - `{ctx.prefix}prefix` - Shows current prefix (default: s.)

        Notes:
        - Bot mention (@bot) always works as backup prefix
        - Use setprefix command to change (Administrator only)
        - Each server can have different prefix
        """
        try:
            from src.cogs.guild_settings import guild_settings
            current_prefix = guild_settings.get_prefix(ctx.guild.id) if ctx.guild else 's.'
            
            embed = discord.Embed(
                title="Current Prefix",
                description=f"The current prefix for this server is: `{current_prefix}`",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Usage",
                value=f"Use `{current_prefix}help` for commands\n"
                      f"**Note:** You can always mention me <@{self.bot.user.id}> regardless of prefix changes",
                inline=False
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
        except Exception as e:
            logger.error(f"Error in prefix command: {e}")
            await ctx.reply("An error occurred while fetching prefix.", mention_author=False)

async def setup_utilities(bot):
    """Setup utilities commands for the bot"""
    await bot.add_cog(Utilities(bot))
    logger.info("Utilities cog setup completed")
