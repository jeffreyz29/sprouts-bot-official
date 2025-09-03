"""
Server Stats Monitoring System
Real-time server statistics with auto-updating embeds
Similar to modmail bot server stats display
"""

import discord
from discord.ext import commands, tasks
import psutil
import platform
import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from src.emojis import SPROUTS_ERROR, SPROUTS_WARNING, SPROUTS_CHECK
from src.emojis import SPROUTS_CHECK, SPROUTS_ERROR
from src.utils.variables import VariableParser

logger = logging.getLogger(__name__)

class ServerStatsMonitor(commands.Cog):
    """Server statistics monitoring and display system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.variable_parser = VariableParser(bot)
        self.active_monitors = {}  # channel_id: message_id mapping
        self.stats_file = "src/data/server_stats.json"
        self.boot_time = datetime.now()
        try:
            self.network_io_start = psutil.net_io_counters()
        except (FileNotFoundError, OSError):
            # Handle systems without /proc/net/dev
            self.network_io_start = None
        
        # Rate limit monitoring
        self.rate_limit_count = 0
        self.last_rate_limit = None
        self.rate_limit_threshold = 5  # Alert after 5 rate limits
        self.notification_channel_id = None  # Set via command
        
        self.load_stats_config()
        
        # Start the auto-update task
        self.update_stats_displays.start()
    
    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.update_stats_displays.cancel()
    
    def load_stats_config(self):
        """Load server stats configuration"""
        try:
            os.makedirs("data", exist_ok=True)
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    config = json.load(f)
                    # Handle both old and new config formats
                    if isinstance(config, dict) and "active_monitors" in config:
                        self.active_monitors = config.get("active_monitors", {})
                        self.notification_channel_id = config.get("notification_channel_id")
                        self.rate_limit_threshold = config.get("rate_limit_threshold", 5)
                    else:
                        # Old format, just active monitors
                        self.active_monitors = config
            else:
                self.active_monitors = {}
        except Exception as e:
            logger.error(f"Error loading stats config: {e}")
            self.active_monitors = {}
    
    def save_stats_config(self):
        """Save server stats configuration"""
        try:
            os.makedirs("data", exist_ok=True)
            config = {
                "active_monitors": self.active_monitors,
                "notification_channel_id": self.notification_channel_id,
                "rate_limit_threshold": self.rate_limit_threshold
            }
            with open(self.stats_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats config: {e}")
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        try:
            # CPU Information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_info = platform.processor()
            cpu_cores = psutil.cpu_count(logical=False)
            cpu_threads = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            # Memory Information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk Information
            disk = psutil.disk_usage('/')
            
            # Network Information
            net_io = psutil.net_io_counters()
            
            # Calculate network transfer rates (since bot start)
            time_delta = (datetime.now() - self.boot_time).total_seconds()
            bytes_sent_rate = (net_io.bytes_sent - self.network_io_start.bytes_sent) / time_delta if time_delta > 0 else 0
            bytes_recv_rate = (net_io.bytes_recv - self.network_io_start.bytes_recv) / time_delta if time_delta > 0 else 0
            
            # System Information
            uptime = datetime.now() - self.boot_time
            bot_uptime = datetime.now() - self.bot.start_time.replace(tzinfo=None)
            
            # Bot Statistics
            guild_count = len(self.bot.guilds)
            user_count = len(set(self.bot.get_all_members()))
            channel_count = sum(len(guild.channels) for guild in self.bot.guilds)
            
            return {
                'cpu': {
                    'usage': cpu_percent,
                    'info': cpu_info,
                    'cores_physical': cpu_cores,
                    'cores_logical': cpu_threads,
                    'frequency': cpu_freq.current if cpu_freq else 0,
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent,
                    'swap_total': swap.total,
                    'swap_used': swap.used,
                    'swap_percent': swap.percent if swap.total > 0 else 0,
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100,
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'transfer_rate_up': bytes_sent_rate,
                    'transfer_rate_down': bytes_recv_rate,
                },
                'uptime': {
                    'system': uptime,
                    'bot': bot_uptime,
                },
                'bot': {
                    'guilds': guild_count,
                    'users': user_count,
                    'channels': channel_count,
                    'latency': round(self.bot.latency * 1000, 2),
                }
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def format_uptime(self, uptime: timedelta) -> str:
        """Format uptime to human readable format"""
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes, {seconds} seconds"
        elif minutes > 0:
            return f"{minutes} minutes, {seconds} seconds"
        else:
            return f"{seconds} seconds"
    
    def create_stats_embed(self, stats: Dict) -> discord.Embed:
        """Create the server stats embed"""
        embed = discord.Embed(
            title="Server Statistics",
            description="Real-time server monitoring",
            color=EMBED_COLOR_NORMAL,
            timestamp=discord.utils.utcnow()
        )
        
        # System Information
        cpu_info = stats['cpu']['info'][:40] + '...' if len(stats['cpu']['info']) > 40 else stats['cpu']['info']
        embed.add_field(
            name="System Information",
            value=f"```"
                  f"CPU: {cpu_info}\n"
                  f"CPU Usage: {stats['cpu']['usage']:.1f}%\n"
                  f"Cores (Physical): {stats['cpu']['cores_physical']}\n"
                  f"Cores (Total): {stats['cpu']['cores_logical']}"
                  f"```",
            inline=False
        )
        
        # Memory & Storage
        embed.add_field(
            name="Memory & Storage",
            value=f"```"
                  f"Memory Used: {self.format_bytes(stats['memory']['used'])}\n"
                  f"Memory Available: {self.format_bytes(stats['memory']['available'])}\n"
                  f"Memory Usage: {stats['memory']['percent']:.1f}%\n"
                  f"\n"
                  f"Disk Used: {self.format_bytes(stats['disk']['used'])}\n"
                  f"Disk Total: {self.format_bytes(stats['disk']['total'])}\n"
                  f"Disk Usage: {stats['disk']['percent']:.1f}%"
                  f"```",
            inline=False
        )
        
        # Network Activity
        embed.add_field(
            name="Network Activity",
            value=f"```"
                  f"Upload Rate: {self.format_bytes(stats['network']['transfer_rate_up'])}/s\n"
                  f"Download Rate: {self.format_bytes(stats['network']['transfer_rate_down'])}/s\n"
                  f"\n"
                  f"Total Sent: {self.format_bytes(stats['network']['bytes_sent'])}\n"
                  f"Total Received: {self.format_bytes(stats['network']['bytes_recv'])}"
                  f"```",
            inline=False
        )
        
        # Bot Performance and Bot Statistics (side by side)
        embed.add_field(
            name="Bot Performance",
            value=f"```"
                  f"WebSocket Ping: {stats['bot']['latency']} ms\n"
                  f"Bot Uptime: {self.format_uptime(stats['uptime']['bot'])}"
                  f"```",
            inline=True
        )
        
        embed.add_field(
            name="Bot Statistics",
            value=f"```"
                  f"Guilds: {stats['bot']['guilds']}\n"
                  f"Users: {stats['bot']['users']}\n"
                  f"Channels: {stats['bot']['channels']}"
                  f"```",
            inline=True
        )
        
        # System Uptime
        embed.add_field(
            name="System Uptime",
            value=f"```{self.format_uptime(stats['uptime']['system'])}```",
            inline=False
        )
        
        current_time = datetime.now()
        embed.set_footer(text=f"Last updated: {current_time.strftime('%Y-%m-%d %H:%M:%S')} • Today at {current_time.strftime('%I:%M %p')}")
        
        return embed
    
    @tasks.loop(seconds=20)
    async def update_stats_displays(self):
        """Update all active stats displays every 20 seconds"""
        if not self.active_monitors:
            return
            
        try:
            stats = self.get_system_stats()
            if not stats:
                return
                
            embed = self.create_stats_embed(stats)
            
            # Update all active monitors with rate limiting protection
            to_remove = []
            monitor_count = 0
            for channel_id, message_id in self.active_monitors.items():
                try:
                    channel = self.bot.get_channel(int(channel_id))
                    if not channel:
                        to_remove.append(channel_id)
                        continue
                        
                    message = await channel.fetch_message(int(message_id))
                    await message.edit(embed=embed)
                    
                    # Add small delay between updates to prevent rate limiting
                    monitor_count += 1
                    if monitor_count > 1:  # Only delay after the first update
                        await asyncio.sleep(2)  # 2 second delay between updates
                    
                except discord.NotFound:
                    # Message was deleted
                    to_remove.append(channel_id)
                except discord.Forbidden:
                    # No permission to edit
                    to_remove.append(channel_id)
                except discord.HTTPException as e:
                    if e.status == 429:  # Rate limited
                        logger.warning(f"Rate limited when updating stats in channel {channel_id}, skipping this update")
                        continue
                    logger.error(f"HTTP error updating stats display in channel {channel_id}: {e}")
                except Exception as e:
                    logger.error(f"Error updating stats display in channel {channel_id}: {e}")
            
            # Remove invalid monitors
            for channel_id in to_remove:
                del self.active_monitors[channel_id]
            
            if to_remove:
                self.save_stats_config()
                
        except Exception as e:
            logger.error(f"Error in stats update loop: {e}")
    
    @update_stats_displays.before_loop
    async def before_update_loop(self):
        """Wait for bot to be ready before starting the update loop"""
        await self.bot.wait_until_ready()
    
    @commands.group(name="serverstats", aliases=["stats", "monitor"], description="Server monitoring commands")
    @commands.has_permissions(manage_guild=True)
    async def serverstats(self, ctx):
        """Server statistics and monitoring commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Server Stats Commands",
                description="Monitor and display real-time server statistics",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Commands",
                value="`{ctx.prefix}serverstats start` - Start monitoring in this channel\n"
                      "`{ctx.prefix}serverstats stop` - Stop monitoring in this channel\n"
                      "`{ctx.prefix}serverstats show` - Show current stats (one-time)\n"
                      "`{ctx.prefix}serverstats list` - List all active monitors",
                inline=False
            )
            embed.add_field(
                name="Features",
                value="• Real-time CPU, memory, and disk usage\n"
                      "• Network transfer statistics\n"
                      "• Bot uptime and Discord API latency\n"
                      "• Auto-updates every 20 seconds\n"
                      "• Bot and server statistics",
                inline=False
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
    
    @serverstats.command(name="start", description="Start server stats monitoring")
    @commands.has_permissions(manage_guild=True)
    async def start_monitoring(self, ctx):
        """Start server stats monitoring in this channel"""
        try:
            channel_id = str(ctx.channel.id)
            
            if channel_id in self.active_monitors:
                embed = discord.Embed(
                    title="Already Monitoring",
                    description="Server stats are already being monitored in this channel.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Get initial stats and create embed
            stats = self.get_system_stats()
            if not stats:
                embed = discord.Embed(
                    title="Error",
                    description="Failed to get system statistics.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            stats_embed = self.create_stats_embed(stats)
            
            # Send the initial stats message
            message = await ctx.send(embed=stats_embed)
            
            # Save the monitor configuration
            self.active_monitors[channel_id] = str(message.id)
            self.save_stats_config()
            
            # Confirm monitoring started
            confirm_embed = discord.Embed(
                title="{SPROUTS_CHECK} Monitoring Started",
                description=f"Server stats monitoring started in {ctx.channel.mention}.\n"
                           f"Stats will update automatically every 30 seconds.",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.reply(embed=confirm_embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error starting server stats monitoring: {e}")
            embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description="Failed to start server stats monitoring.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
    
    @serverstats.command(name="stop", description="Stop server stats monitoring")
    @commands.has_permissions(manage_guild=True)
    async def stop_monitoring(self, ctx):
        """Stop server stats monitoring in this channel"""
        try:
            channel_id = str(ctx.channel.id)
            
            if channel_id not in self.active_monitors:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} Error",
                    description="Server stats are not being monitored in this channel.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Try to delete the stats message
            try:
                message_id = self.active_monitors[channel_id]
                message = await ctx.channel.fetch_message(int(message_id))
                await message.delete()
            except:
                pass  # Message might already be deleted
            
            # Remove from monitors
            del self.active_monitors[channel_id]
            self.save_stats_config()
            
            embed = discord.Embed(
                title="{SPROUTS_CHECK} Monitoring Stopped",
                description="Server stats monitoring has been stopped in this channel.",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error stopping server stats monitoring: {e}")
            embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description="Failed to stop server stats monitoring.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
    
    @serverstats.command(name="show", description="Show current server stats")
    async def show_stats(self, ctx):
        """Show current server stats (one-time display)"""
        try:
            stats = self.get_system_stats()
            if not stats:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} Error",
                    description="Failed to get system statistics.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            stats_embed = self.create_stats_embed(stats)
            await ctx.reply(embed=stats_embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error showing server stats: {e}")
            embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description="Failed to get server statistics.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
    
    @serverstats.command(name="list", description="List all active monitors")
    @commands.has_permissions(manage_guild=True)
    async def list_monitors(self, ctx):
        """List all active server stats monitors"""
        try:
            if not self.active_monitors:
                embed = discord.Embed(
                    title="{SPROUTS_ERROR} No Active Monitors",
                    description="There are no active server stats monitors.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            embed = discord.Embed(
                title="{SPROUTS_CHECK} Active Server Stats Monitors",
                description=f"Total: {len(self.active_monitors)}",
                color=EMBED_COLOR_NORMAL
            )
            
            for i, (channel_id, message_id) in enumerate(self.active_monitors.items()):
                channel = self.bot.get_channel(int(channel_id))
                channel_name = channel.mention if channel else f"Unknown Channel ({channel_id})"
                
                embed.add_field(
                    name=f"{i+1}. {channel_name}",
                    value=f"Message ID: {message_id}",
                    inline=False
                )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error listing monitors: {e}")
            embed = discord.Embed(
                title="{SPROUTS_ERROR} Error",
                description="Failed to list active monitors.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
    
    # Rate Limit Monitoring Commands
    @commands.group(name="ratelimit", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def ratelimit(self, ctx):
        """Rate limit monitoring commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Rate Limit Monitoring",
                description="Monitor and get notified about bot rate limits",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Commands",
                value="`{ctx.prefix}ratelimit status` - Show current rate limit stats\n"
                      "`{ctx.prefix}ratelimit setchannel <#channelID>` - Set notification channel\n"
                      "`{ctx.prefix}ratelimit threshold <number>` - Set alert threshold\n"
                      "`{ctx.prefix}ratelimit reset` - Reset rate limit counters",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=False)
    
    @ratelimit.command(name="status", help="Show rate limit monitoring status")
    @commands.has_permissions(manage_guild=True)
    async def ratelimit_status(self, ctx):
        """Show current rate limit statistics"""
        try:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Rate Limit Monitor Status",
                color=EMBED_COLOR_NORMAL
            )
            
            # Rate limit stats
            embed.add_field(
                name="Current Statistics",
                value=f"**Rate Limits Today:** {self.rate_limit_count}\n"
                      f"**Alert Threshold:** {self.rate_limit_threshold}\n"
                      f"**Last Rate Limit:** {self.last_rate_limit.strftime('%H:%M:%S UTC') if self.last_rate_limit else 'Never'}",
                inline=False
            )
            
            # Notification channel
            notification_channel = self.bot.get_channel(self.notification_channel_id) if self.notification_channel_id else None
            embed.add_field(
                name="Notifications",
                value=f"**Channel:** {notification_channel.mention if notification_channel else 'Not set'}\n"
                      f"**Status:** {'f"{SPROUTS_CHECK}" Active' if notification_channel else 'f"{SPROUTS_ERROR}" Disabled'}",
                inline=False
            )
            
            # Performance tips
            if self.rate_limit_count > 0:
                embed.add_field(
                    name="Performance Tips",
                    value="• Consider increasing command cooldowns\n"
                          "• Review auto-updating features frequency\n"
                          "• Monitor during peak usage times\n"
                          "• Use bulk operations where possible",
                    inline=False
                )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Monitoring since {self.boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error showing rate limit status: {e}")
            await ctx.reply("Failed to get rate limit status.", mention_author=False)
    
    @ratelimit.command(name="setchannel", help="Set notification channel for rate limit alerts")
    @commands.has_permissions(manage_guild=True)
    async def set_notification_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for rate limit notifications"""
        try:
            self.notification_channel_id = channel.id
            self.save_stats_config()  # Save the notification channel
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Notification Channel Set",
                description=f"Rate limit alerts will now be sent to {channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Alert Threshold",
                value=f"You'll be notified after **{self.rate_limit_threshold}** rate limits",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error setting notification channel: {e}")
            await ctx.reply(f"{SPROUTS_ERROR} Failed to set notification channel.", mention_author=False)
    
    @ratelimit.command(name="threshold", help="Set rate limit alert threshold")
    @commands.has_permissions(manage_guild=True)
    async def set_threshold(self, ctx, threshold: int):
        """Set the rate limit threshold for alerts"""
        try:
            if threshold < 1 or threshold > 100:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Invalid Threshold",
                    description="Threshold must be between 1 and 100.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            self.rate_limit_threshold = threshold
            self.save_stats_config()
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Threshold Updated",
                description=f"Rate limit alert threshold set to **{threshold}**",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.reply(embed=embed, mention_author=False)
            
        except ValueError:
            await ctx.reply(f"{SPROUTS_ERROR} Please provide a valid number for the threshold.", mention_author=False)
        except Exception as e:
            logger.error(f"Error setting threshold: {e}")
            await ctx.reply(f"{SPROUTS_ERROR} Failed to set threshold.", mention_author=False)
    
    @ratelimit.command(name="reset", help="Reset rate limit counters")
    @commands.has_permissions(manage_guild=True)
    async def reset_counters(self, ctx):
        """Reset rate limit counters"""
        try:
            old_count = self.rate_limit_count
            self.rate_limit_count = 0
            self.last_rate_limit = None
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Counters Reset",
                description=f"Rate limit counters have been reset.\n"
                           f"Previous count: **{old_count}**",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error resetting counters: {e}")
            await ctx.reply(f"{SPROUTS_ERROR} Failed to reset counters.", mention_author=False)
    
    # Rate limit event listeners
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Monitor for rate limit errors"""
        if isinstance(error, discord.HTTPException) and error.status == 429:
            await self.handle_rate_limit("Command execution rate limited")
    
    async def handle_rate_limit(self, reason: str = "Rate limit detected"):
        """Handle rate limit detection and notifications"""
        try:
            self.rate_limit_count += 1
            self.last_rate_limit = datetime.utcnow()
            
            logger.warning(f"Rate limit detected: {reason} (Count: {self.rate_limit_count})")
            
            # Send notification if threshold reached and channel is set
            if (self.rate_limit_count >= self.rate_limit_threshold and 
                self.notification_channel_id and 
                self.rate_limit_count % self.rate_limit_threshold == 0):  # Prevent spam
                
                await self.send_rate_limit_alert(reason)
                
        except Exception as e:
            logger.error(f"Error handling rate limit: {e}")
    
    async def send_rate_limit_alert(self, reason: str):
        """Send rate limit alert to notification channel"""
        try:
            channel = self.bot.get_channel(self.notification_channel_id)
            if not channel:
                logger.error("Rate limit notification channel not found")
                return
            
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Rate Limit Alert",
                description=f"**Bot is experiencing rate limits**\n\n"
                           f"**Reason:** {reason}\n"
                           f"**Count Today:** {self.rate_limit_count}\n"
                           f"**Time:** {self.last_rate_limit.strftime('%H:%M:%S UTC')}\n"
                           f"**Threshold:** {self.rate_limit_threshold}",
                color=0xFFA500  # Orange warning color
            )
            
            # Add performance recommendations
            embed.add_field(
                name="Recommended Actions",
                value="• Check auto-updating features\n"
                      "• Review command usage patterns\n"
                      "• Consider increasing cooldowns\n"
                      "• Monitor bot performance",
                inline=False
            )
            
            # Add guild information
            guild_info = f"**Guilds:** {len(self.bot.guilds)}\n"
            guild_info += f"**Users:** {len(set(self.bot.get_all_members()))}"
            embed.add_field(
                name="Bot Stats",
                value=guild_info,
                inline=True
            )
            
            embed.set_footer(text="Keep your bot minimal and efficient!")
            embed.timestamp = discord.utils.utcnow()
            
            await channel.send(embed=embed)
            logger.info(f"Rate limit alert sent to channel {channel.id}")
            
        except Exception as e:
            logger.error(f"Error sending rate limit alert: {e}")

async def setup_server_stats(bot):
    """Setup server stats cog"""
    await bot.add_cog(ServerStatsMonitor(bot))
    logger.info("Server stats monitor setup completed")
