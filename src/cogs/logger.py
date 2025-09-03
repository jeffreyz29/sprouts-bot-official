"""
Event Logger System
Logs all bot events and forwards DMs to the developer
"""

import discord
from discord.ext import commands
import logging
import json
import os
from datetime import datetime
from typing import Optional
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR

logger = logging.getLogger(__name__)

class EventLogger(commands.Cog):
    """Event logging system for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.developer_id = None  # Set your Discord user ID here
        self.log_channel_id = None  # Set your logging channel ID here
        self.log_guild_id = None  # Set your logging guild ID here
        
        # Load settings from file
        self.load_logger_settings()
    
    def load_logger_settings(self):
        """Load logger settings from file"""
        try:
            if os.path.exists("logger_settings.json"):
                with open("logger_settings.json", 'r') as f:
                    settings = json.load(f)
                    self.developer_id = settings.get('developer_id')
                    self.log_channel_id = settings.get('log_channel_id')
                    self.log_guild_id = settings.get('log_guild_id')
        except Exception as e:
            logger.error(f"Error loading logger settings: {e}")
    
    def save_logger_settings(self):
        """Save logger settings to file"""
        try:
            settings = {
                'developer_id': self.developer_id,
                'log_channel_id': self.log_channel_id,
                'log_guild_id': self.log_guild_id
            }
            with open("logger_settings.json", 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving logger settings: {e}")
    
    async def send_log_message(self, embed: discord.Embed):
        """Send log message to developer via DM and/or log channel"""
        try:
            # Send to developer DM
            if self.developer_id:
                try:
                    developer = self.bot.get_user(self.developer_id)
                    if developer:
                        await developer.send(embed=embed)
                except discord.Forbidden:
                    logger.warning("Cannot send DM to developer - DMs may be disabled")
                except Exception as e:
                    logger.error(f"Error sending DM to developer: {e}")
            
            # Send to log channel
            if self.log_channel_id:
                try:
                    channel = self.bot.get_channel(self.log_channel_id)
                    if channel:
                        await channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"Error sending to log channel: {e}")
                    
        except Exception as e:
            logger.error(f"Error in send_log_message: {e}")
    
    async def send_dm_log(self, embed: discord.Embed):
        """Send DM log specifically to the configured DM log channel"""
        try:
            # Load DM log channel from environment variables
            dm_log_channel_id = os.getenv('LOG_DMS_CHANNEL')
            if dm_log_channel_id:
                try:
                    channel = self.bot.get_channel(int(dm_log_channel_id))
                    if channel:
                        await channel.send(embed=embed)
                        logger.info("DM log sent to configured channel")
                    else:
                        logger.warning(f"DM log channel {dm_log_channel_id} not found")
                except Exception as e:
                    logger.error(f"Error sending to DM log channel: {e}")
            else:
                # Fallback to regular log method
                await self.send_log_message(embed)
        except Exception as e:
            logger.error(f"Error in send_dm_log: {e}")
    
    async def send_command_log(self, embed: discord.Embed):
        """Send command log specifically to the configured command log channel"""
        try:
            # Load command log channel from environment variables
            cmd_log_channel_id = os.getenv('LOG_COMMANDS_CHANNEL')
            if cmd_log_channel_id:
                try:
                    channel = self.bot.get_channel(int(cmd_log_channel_id))
                    if channel:
                        await channel.send(embed=embed)
                        logger.info("Command log sent to configured channel")
                    else:
                        logger.warning(f"Command log channel {cmd_log_channel_id} not found")
                except Exception as e:
                    logger.error(f"Error sending to command log channel: {e}")
            else:
                # Fallback to regular log method
                await self.send_log_message(embed)
        except Exception as e:
            logger.error(f"Error in send_command_log: {e}")
    
    # DM handling moved to events.py to avoid conflicts
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Log when bot joins a guild"""
        try:
            embed = discord.Embed(
                title="Joined New Guild",
                color=EMBED_COLOR_NORMAL,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="Guild",
                value=f"{guild.name} (`{guild.id}`)",
                inline=True
            )
            embed.add_field(
                name="Owner",
                value=f"{guild.owner} (`{guild.owner.id}`)" if guild.owner else "Unknown",
                inline=True
            )
            embed.add_field(
                name="Members",
                value=f"{guild.member_count:,}",
                inline=True
            )
            embed.add_field(
                name="Created",
                value=f"<t:{int(guild.created_at.timestamp())}:F>",
                inline=False
            )
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            await self.send_log_message(embed)
            logger.info(f"Bot joined guild: {guild.name} ({guild.id})")
            
        except Exception as e:
            logger.error(f"Error logging guild join: {e}")
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Log when bot leaves a guild"""
        try:
            embed = discord.Embed(
                title="Left Guild",
                color=EMBED_COLOR_NORMAL,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="Guild",
                value=f"{guild.name} (`{guild.id}`)",
                inline=True
            )
            embed.add_field(
                name="Members",
                value=f"{guild.member_count:,}",
                inline=True
            )
            
            await self.send_log_message(embed)
            logger.info(f"Bot left guild: {guild.name} ({guild.id})")
            
        except Exception as e:
            logger.error(f"Error logging guild remove: {e}")
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Log command errors (logging only, not user-facing responses)"""
        try:
            # Skip logging for common/handled errors to reduce spam
            if isinstance(error, (commands.CommandNotFound, commands.CommandOnCooldown, commands.MissingRequiredArgument, commands.CheckFailure)):
                return
                
            embed = discord.Embed(
                title="<a:sprouts_error_dns:1411790004652605500> Command Error",
                color=EMBED_COLOR_ERROR,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="User",
                value=f"{ctx.author} (`{ctx.author.id}`)",
                inline=True
            )
            embed.add_field(
                name="Command",
                value=f"`{ctx.command}`" if ctx.command else "Unknown",
                inline=True
            )
            embed.add_field(
                name="Guild",
                value=f"{ctx.guild.name} (`{ctx.guild.id}`)" if ctx.guild else "DM",
                inline=True
            )
            embed.add_field(
                name="Error",
                value=str(error)[:1000],
                inline=False
            )
            
            await self.send_log_message(embed)
            logger.error(f"Command error logged: {error}")
            
        except Exception as e:
            logger.error(f"Error logging command error: {e}")
    
    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        """Log slash command errors"""
        try:
            embed = discord.Embed(
                title="Slash Command Error",
                color=EMBED_COLOR_ERROR,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="User",
                value=f"{interaction.user} (`{interaction.user.id}`)",
                inline=True
            )
            embed.add_field(
                name="Command",
                value=f"`/{interaction.command.name}`" if interaction.command else "Unknown",
                inline=True
            )
            embed.add_field(
                name="Guild",
                value=f"{interaction.guild.name} (`{interaction.guild.id}`)" if interaction.guild else "DM",
                inline=True
            )
            embed.add_field(
                name="Error",
                value=str(error)[:1000],
                inline=False
            )
            
            await self.send_log_message(embed)
            logger.error(f"Slash command error logged: {error}")
            
        except Exception as e:
            logger.error(f"Error logging slash command error: {e}")

async def setup_logger(bot):
    """Setup event logger for the bot"""
    await bot.add_cog(EventLogger(bot))
    logger.info("Event logger setup completed")