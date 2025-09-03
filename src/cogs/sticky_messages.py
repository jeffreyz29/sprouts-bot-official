"""
Sticky Messages System
Allows server staff to create sticky messages that repost when channel activity occurs
"""

import discord
from discord.ext import commands, tasks
import json
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR

logger = logging.getLogger(__name__)

class StickyMessages(commands.Cog):
    """Sticky messages system for channels"""

    def __init__(self, bot):
        self.bot = bot
        self.stickies_file = "src/data/sticky_messages.json"
        self.stickies = self.load_stickies()
        self.message_counts = {}  # Track messages per channel
        self.cleanup_stickies.start()

    def cog_unload(self):
        """Stop the cleanup task when cog is unloaded"""
        self.cleanup_stickies.cancel()

    def load_stickies(self) -> Dict:
        """Load sticky messages from file"""
        try:
            os.makedirs("data", exist_ok=True)
            if os.path.exists(self.stickies_file):
                with open(self.stickies_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading sticky messages: {e}")
            return {}

    def save_stickies(self):
        """Save sticky messages to file"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(self.stickies_file, 'w') as f:
                json.dump(self.stickies, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving sticky messages: {e}")

    @tasks.loop(hours=1)
    async def cleanup_stickies(self):
        """Clean up old sticky message data"""
        try:
            # Remove stickies for channels that no longer exist
            channels_to_remove = []
            for channel_id in self.stickies:
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    channels_to_remove.append(channel_id)

            for channel_id in channels_to_remove:
                del self.stickies[channel_id]
                logger.info(f"Removed sticky for non-existent channel {channel_id}")

            if channels_to_remove:
                self.save_stickies()

        except Exception as e:
            logger.error(f"Error in sticky cleanup: {e}")

    @cleanup_stickies.before_loop
    async def before_cleanup_stickies(self):
        """Wait until bot is ready before starting cleanup"""
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle sticky message reposting"""
        if message.author.bot or not message.guild:
            return

        channel_id = str(message.channel.id)

        # Check if channel has an active sticky
        if channel_id not in self.stickies:
            return

        sticky_data = self.stickies[channel_id]

        # Skip if sticky is not active
        if not sticky_data.get('active', True):
            return

        # Repost sticky after EVERY message
        await self.repost_sticky(message.channel, sticky_data)



    async def repost_sticky(self, channel, sticky_data):
        """Repost the sticky message"""
        try:
            # Delete old sticky message if it exists
            if sticky_data.get('message_id'):
                try:
                    old_message = await channel.fetch_message(sticky_data['message_id'])
                    await old_message.delete()
                except discord.NotFound:
                    pass
                except Exception as e:
                    logger.warning(f"Could not delete old sticky message: {e}")

            # Check if using custom embed
            if sticky_data.get('use_custom_embed'):
                embed_name = sticky_data.get('embed_name')
                user_id = sticky_data.get('embed_user_id')
                guild_id = sticky_data.get('guild_id')

                saved_embeds = self.load_saved_embeds()
                embed_data = None

                # Try to find embed (user first, then guild)
                if user_id and str(user_id) in saved_embeds:
                    user_embeds = saved_embeds[str(user_id)]
                    if embed_name in user_embeds:
                        embed_data = user_embeds[embed_name]

                if not embed_data and guild_id and str(guild_id) in saved_embeds:
                    guild_embeds = saved_embeds[str(guild_id)]
                    if embed_name in guild_embeds:
                        embed_data = guild_embeds[embed_name]

                if embed_data:
                    # Use custom embed
                    embed = self.create_embed_from_data(embed_data)
                    new_message = await channel.send(embed=embed)
                else:
                    # Fallback to simple embed if custom embed not found
                    embed = discord.Embed(
                        title=f"{SPROUTS_WARNING} Sticky Embed Not Found",
                        description=f"Custom embed '{embed_name}' not found. Please recreate the sticky.",
                        color=EMBED_COLOR_ERROR
                    )
                    new_message = await channel.send(embed=embed)

            elif sticky_data.get('embed', False):
                # Simple embed with content
                content = sticky_data['content']
                embed = discord.Embed(
                    description=content,
                    color=EMBED_COLOR_NORMAL
                )
                embed.set_footer(text="Sticky Message")
                new_message = await channel.send(embed=embed)
            else:
                # Plain text sticky with proper format
                content = sticky_data['content']
                new_message = await channel.send(f"__Stickied Message__:\n\n{content}")

            # Update sticky data with new message ID
            sticky_data['message_id'] = new_message.id
            sticky_data['last_posted'] = datetime.utcnow().isoformat()
            self.save_stickies()

        except Exception as e:
            logger.error(f"Error reposting sticky: {e}")

    @commands.command(name="stick", description="Create sticky message")
    @commands.has_permissions(manage_messages=True)
    async def stick_command(self, ctx, *, content: str):
        """Create a new sticky message (message is required)"""
        if not content.strip():
            embed = discord.Embed(
                title="Message Required",
                description="You must provide a message for the sticky.\n\n**Usage:** `s.stick <message>`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        await self.create_sticky(ctx, content, slow=False)

    async def create_sticky(self, ctx, content: str, slow: bool = False):
        """Create a sticky message"""
        try:
            channel_id = str(ctx.channel.id)

            # Remove existing sticky if any
            if channel_id in self.stickies:
                old_sticky = self.stickies[channel_id]
                if old_sticky.get('message_id'):
                    try:
                        old_message = await ctx.channel.fetch_message(old_sticky['message_id'])
                        await old_message.delete()
                    except:
                        pass

            # Create sticky data
            sticky_data = {
                'content': content,
                'active': True,
                'slow': slow,
                'speed': 15 if slow else 5,
                'embed': False,
                'created_by': ctx.author.id,
                'created_at': datetime.utcnow().isoformat(),
                'guild_id': ctx.guild.id
            }

            # Send initial sticky message in plain text format
            new_message = await ctx.channel.send(f"__Stickied Message__:\n\n{content}")

            sticky_data['message_id'] = new_message.id
            sticky_data['embed'] = False  # Changed to False for plain text format

            # Store sticky
            self.stickies[channel_id] = sticky_data
            self.message_counts[channel_id] = 0
            self.save_stickies()

            # Send confirmation
            speed_text = "slow (15 messages)" if slow else "normal (5 messages)"
            embed = discord.Embed(
                title="Sticky Message Created",
                description=f"Created {speed_text} sticky message in {ctx.channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Content",
                value=content[:1000] + ("..." if len(content) > 1000 else ""),
                inline=False
            )
            embed.set_footer(text=f"Created by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()

            # Delete the command message and send confirmation
            try:
                await ctx.message.delete()
            except:
                pass

            confirmation = await ctx.send(embed=embed)

            # Delete confirmation after 10 seconds
            await asyncio.sleep(10)
            try:
                await confirmation.delete()
            except:
                pass

        except Exception as e:
            logger.error(f"Error creating sticky: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Error",
                description="Failed to create sticky message",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)


    @commands.command(name="stickslow", description="Create slow sticky message")
    @commands.has_permissions(manage_messages=True)
    async def stick_slow(self, ctx, *, content: str):
        """Create a slow sticky message (message is required)"""
        if not content.strip():
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Message Required",
                description="You must provide a message for the sticky.\n\n**Usage:** `s.stickslow <message>`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        await self.create_sticky(ctx, content, slow=True)



    @commands.command(name="stickstop", description="Stop sticky message")
    @commands.has_permissions(manage_messages=True)
    async def stick_stop(self, ctx):
        """Stop the sticky message in current channel"""
        try:
            channel_id = str(ctx.channel.id)

            if channel_id not in self.stickies:
                embed = discord.Embed(
                    title="f"{SPROUTS_WARNING}" No Sticky Message",
                    description="There is no sticky message in this channel",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Deactivate sticky
            self.stickies[channel_id]['active'] = False
            self.save_stickies()

            embed = discord.Embed(
                title="{SPROUTS_CHECK} Sticky Stopped",
                description="Sticky message has been stopped in this channel",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_footer(text=f"Stopped by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error stopping sticky: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Error",
                description="Failed to stop sticky message",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="stickstart", description="Start sticky message")
    @commands.has_permissions(manage_messages=True)
    async def stick_start(self, ctx):
        """Start/restart the sticky message in current channel"""
        try:
            channel_id = str(ctx.channel.id)

            if channel_id not in self.stickies:
                embed = discord.Embed(
                    title="f"{SPROUTS_WARNING}" No Sticky Message",
                    description="There is no sticky message configured in this channel",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Activate sticky
            self.stickies[channel_id]['active'] = True
            self.save_stickies()

            # Repost the sticky
            await self.repost_sticky(ctx.channel, self.stickies[channel_id])

            embed = discord.Embed(
                title="Sticky Started",
                description="Sticky message has been started/restarted in this channel",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_footer(text=f"Started by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error starting sticky: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Error",
                description="Failed to start sticky message",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="stickremove", description="Remove sticky message")
    @commands.has_permissions(manage_messages=True)
    async def stick_remove(self, ctx):
        """Completely remove the sticky message from current channel"""
        try:
            channel_id = str(ctx.channel.id)

            if channel_id not in self.stickies:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} No Sticky Message",
                    description="There is no sticky message in this channel",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Delete the sticky message if it exists
            sticky_data = self.stickies[channel_id]
            if sticky_data.get('message_id'):
                try:
                    old_message = await ctx.channel.fetch_message(sticky_data['message_id'])
                    await old_message.delete()
                except:
                    pass

            # Remove from data
            del self.stickies[channel_id]
            if channel_id in self.message_counts:
                del self.message_counts[channel_id]
            self.save_stickies()

            embed = discord.Embed(
                title="{SPROUTS_ERROR} Sticky Removed",
                description="Sticky message has been completely removed from this channel",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_footer(text=f"Removed by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error removing sticky: {e}")
            embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description="Failed to remove sticky message",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="getstickies", description="List all sticky messages")
    @commands.has_permissions(manage_messages=True)
    async def get_stickies(self, ctx):
        """List all sticky messages in the server"""
        try:
            guild_stickies = {}

            for channel_id, sticky_data in self.stickies.items():
                if sticky_data.get('guild_id') == ctx.guild.id:
                    guild_stickies[channel_id] = sticky_data

            if not guild_stickies:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} No Sticky Messages",
                    description="No sticky messages configured in this server",
                    color=EMBED_COLOR_NORMAL
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            embed = discord.Embed(
                title="Server Sticky Messages",
                description=f"Total: {len(guild_stickies)}",
                color=EMBED_COLOR_NORMAL
            )

            for channel_id, sticky_data in list(guild_stickies.items())[:10]:  # Show max 10
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    continue

                status = "Active" if sticky_data.get('active', True) else "Stopped"
                speed_type = "Slow" if sticky_data.get('slow', False) else "Normal"
                speed = sticky_data.get('speed', 5)

                embed.add_field(
                    name=f"#{channel.name}",
                    value=f"**Status:** {status}\n"
                          f"**Type:** {speed_type} ({speed} messages)\n"
                          f"**Content:** {sticky_data['content'][:100]}{'...' if len(sticky_data['content']) > 100 else ''}",
                    inline=False
                )

            if len(guild_stickies) > 10:
                embed.add_field(
                    name="Note",
                    value=f"Showing first 10 of {len(guild_stickies)} stickies",
                    inline=False
                )

            embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()

            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error listing stickies: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Error",
                description="Failed to list sticky messages",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="stickspeed", description="View or change sticky speed")
    @commands.has_permissions(manage_messages=True)
    async def stick_speed(self, ctx, speed: int = None):
        """View or change the sticky message speed"""
        try:
            channel_id = str(ctx.channel.id)

            if channel_id not in self.stickies:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} No Sticky Message",
                    description="There is no sticky message in this channel",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            if speed is None:
                # Show current speed
                current_speed = self.stickies[channel_id].get('speed', 5)
                sticky_type = "Slow" if self.stickies[channel_id].get('slow', False) else "Normal"

                embed = discord.Embed(
                    title="Sticky Speed Settings",
                    color=EMBED_COLOR_NORMAL
                )
                embed.add_field(
                    name="Current Speed",
                    value=f"**{current_speed}** messages\n**Type:** {sticky_type}",
                    inline=False
                )
                embed.add_field(
                    name="Change Speed",
                    value=f"Use `s.stickspeed <number>` to change\n**Range:** 1-50 messages",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Validate speed
            if speed < 1 or speed > 50:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} Invalid Speed",
                    description="Speed must be between 1 and 50 messages",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Update speed
            self.stickies[channel_id]['speed'] = speed
            if speed >= 10:
                self.stickies[channel_id]['slow'] = True
            else:
                self.stickies[channel_id]['slow'] = False

            self.save_stickies()

            speed_type = "Slow" if speed >= 10 else "Normal"

            embed = discord.Embed(
                title="Speed Updated",
                description=f"Sticky speed set to **{speed}** messages ({speed_type})",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_footer(text=f"Updated by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            logger.error(f"Error changing sticky speed: {e}")
            embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description="Failed to change sticky speed",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)

async def setup_stickymessages(bot):
    """Setup sticky messages cog"""
    await bot.add_cog(StickyMessages(bot))
    logger.info("Sticky messages setup completed")
