"""
Reminders System
Allows users to set reminders that DM them when time is up with channel links
"""

import discord
from discord.ext import commands, tasks
import json
import os
import logging
import asyncio
from datetime import datetime, timedelta
import re
import random
import string
from typing import Dict, List, Optional
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR

logger = logging.getLogger(__name__)

class Reminders(commands.Cog):
    """Reminders system for setting personal reminders"""
    
    def __init__(self, bot):
        self.bot = bot
        self.reminders_file = "src/data/reminders.json"
        self.counter_file = "src/data/reminder_counter.json"
        self.reminders = self.load_reminders()
        self.reminder_counter = self.load_counter()
        self.check_reminders.start()
    
    async def cog_unload(self):
        """Stop the reminder check task when cog is unloaded"""
        self.check_reminders.cancel()
    
    def load_reminders(self) -> Dict:
        """Load reminders from file"""
        try:
            os.makedirs("data", exist_ok=True)
            if os.path.exists(self.reminders_file):
                with open(self.reminders_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading reminders: {e}")
            return {}
    
    def load_counter(self) -> int:
        """Load reminder counter from file"""
        try:
            os.makedirs("data", exist_ok=True)
            if os.path.exists(self.counter_file):
                with open(self.counter_file, 'r') as f:
                    data = json.load(f)
                    return data.get('total_reminders', 0)
            return 0
        except Exception as e:
            logger.error(f"Error loading reminder counter: {e}")
            return 0
    
    def save_reminders(self):
        """Save reminders to file"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(self.reminders_file, 'w') as f:
                json.dump(self.reminders, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving reminders: {e}")
    
    def save_counter(self):
        """Save reminder counter to file"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(self.counter_file, 'w') as f:
                json.dump({'total_reminders': self.reminder_counter}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving reminder counter: {e}")
    
    def get_next_reminder_number(self) -> int:
        """Get the next reminder number and increment counter"""
        self.reminder_counter += 1
        self.save_counter()
        return self.reminder_counter
    
    def generate_reminder_id(self, length: int = 6) -> str:
        """Generate a random reminder ID with mixed letters and numbers"""
        # Use both uppercase, lowercase letters and numbers
        characters = string.ascii_letters + string.digits
        
        # Keep generating until we get a unique ID
        while True:
            reminder_id = ''.join(random.choice(characters) for _ in range(length))
            
            # Check if this ID already exists for any user
            id_exists = False
            for user_reminders in self.reminders.values():
                if reminder_id in user_reminders:
                    id_exists = True
                    break
            
            if not id_exists:
                return reminder_id
    
    def parse_time(self, time_str: str) -> Optional[timedelta]:
        """Parse time string into timedelta"""
        try:
            # Remove spaces and convert to lowercase
            time_str = time_str.replace(' ', '').lower()
            
            # Parse different time formats
            total_seconds = 0
            
            # Match patterns like 1d, 2h, 30m, 45s
            patterns = {
                r'(\d+)d': 86400,  # days
                r'(\d+)h': 3600,   # hours
                r'(\d+)m': 60,     # minutes
                r'(\d+)s': 1       # seconds
            }
            
            for pattern, multiplier in patterns.items():
                matches = re.findall(pattern, time_str)
                for match in matches:
                    total_seconds += int(match) * multiplier
            
            if total_seconds == 0:
                return None
                
            return timedelta(seconds=total_seconds)
            
        except Exception as e:
            logger.error(f"Error parsing time: {e}")
            return None
    
    def format_time_remaining(self, reminder_time: datetime) -> str:
        """Format time remaining until reminder"""
        try:
            now = datetime.utcnow()
            if reminder_time <= now:
                return "Due now"
            
            delta = reminder_time - now
            
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            parts = []
            if days > 0:
                parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0:
                parts.append(f"{minutes}m")
            if seconds > 0 and not parts:  # Only show seconds if no larger units
                parts.append(f"{seconds}s")
            
            return " ".join(parts) if parts else "Less than 1 minute"
            
        except Exception as e:
            logger.error(f"Error formatting time: {e}")
            return "Unknown"
    
    @tasks.loop(seconds=30)
    async def check_reminders(self):
        """Check for due reminders every 30 seconds"""
        try:
            current_time = datetime.utcnow()
            due_reminders = []
            
            for user_id, user_reminders in self.reminders.items():
                for reminder_id, reminder_data in list(user_reminders.items()):
                    reminder_time = datetime.fromisoformat(reminder_data['time'])
                    if current_time >= reminder_time:
                        due_reminders.append((user_id, reminder_id, reminder_data))
            
            # Process due reminders
            for user_id, reminder_id, reminder_data in due_reminders:
                await self.send_reminder_dm(user_id, reminder_data)
                # Remove the reminder after sending
                del self.reminders[user_id][reminder_id]
                if not self.reminders[user_id]:  # Remove user if no more reminders
                    del self.reminders[user_id]
            
            if due_reminders:
                self.save_reminders()
                
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
    
    @check_reminders.before_loop
    async def before_check_reminders(self):
        """Wait until bot is ready before starting reminder checks"""
        await self.bot.wait_until_ready()
    
    async def send_reminder_dm(self, user_id: str, reminder_data: dict):
        """Send reminder DM to user"""
        try:
            user = self.bot.get_user(int(user_id))
            if not user:
                return
            
            # Get channel and guild info
            channel = self.bot.get_channel(reminder_data['channel_id'])
            guild = self.bot.get_guild(reminder_data['guild_id']) if reminder_data.get('guild_id') else None
            
            # Get reminder number (fallback to 0 if not present in old reminders)
            reminder_number = reminder_data.get('reminder_number', 0)
            
            # Create unix timestamp for when reminder was set
            created_timestamp = int(datetime.fromisoformat(reminder_data['created_at']).timestamp())
            
            embed = discord.Embed(
                title=f"Reminder #{reminder_number}",
                description=f"<t:{created_timestamp}:R> you asked to be reminded of \"{reminder_data['message']}\"",
                color=EMBED_COLOR_NORMAL,
                timestamp=discord.utils.utcnow()
            )
            
            # Add original message field
            embed.add_field(
                name="Original message",
                value=reminder_data['message'],
                inline=False
            )
            
            # Add jump link if from a server
            if channel and guild:
                jump_url = f"https://discord.com/channels/{guild.id}/{channel.id}"
                embed.add_field(
                    name="Message Link",
                    value=f"[Jump to #{channel.name}]({jump_url})",
                    inline=False
                )
            elif channel and not guild:
                embed.add_field(
                    name="Message Link",
                    value="Set in DM",
                    inline=False
                )
            
            embed.set_footer(text="Sprouts Reminder System")
            
            await user.send(embed=embed)
            logger.info(f"Sent reminder #{reminder_number} to {user} ({user_id})")
            
        except discord.Forbidden:
            logger.warning(f"Cannot send DM to user {user_id} - DMs disabled")
        except Exception as e:
            logger.error(f"Error sending reminder DM: {e}")
    
    @commands.command(name="remind", aliases=["remindme", "setr"], help="Set personal reminder with flexible time format")
    async def set_reminder(self, ctx, time: str, *, message: str):
        """Set a reminder
        
        Usage: remind <time> <message>
        Creates personal reminder that alerts you after specified time
        
        Examples:
        - remind 1h Take a break
        - remind 30m Check the oven  
        - remind 1d2h30m Meeting tomorrow
        - remind 2w Project deadline
        
        Time Formats:
        - s/sec/seconds, m/min/minutes, h/hour/hours
        - d/day/days, w/week/weeks
        - Combinations: 1d2h30m (1 day, 2 hours, 30 minutes)
        
        Limits:
        - Minimum: 1 minute
        - Maximum: 1 year
        """
        try:
            # Parse the time
            time_delta = self.parse_time(time)
            if not time_delta:
                embed = discord.Embed(
                    title="<a:sprouts_error_dns:1411790004652605500> Invalid Time Format",
                    description="Use formats like: `1d`, `2h`, `30m`, `45s` or combinations like `1d2h30m`",
                    color=EMBED_COLOR_ERROR
                )
                embed.add_field(
                    name="Examples",
                    value="`s.remind <time> <message>`\n\n"
                          "`s.remind 1h Take a break`\n"
                          "`s.remind 30m Check the oven`\n"
                          "`s.remind 1d2h Meeting tomorrow`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Check time limits
            if time_delta.total_seconds() < 60:  # Minimum 1 minute
                embed = discord.Embed(
                    title="<a:sprouts_warning_dns:1412200379206336522> Time Too Short",
                    description="Reminders must be at least 1 minute in the future",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            if time_delta.total_seconds() > 31536000:  # Maximum 1 year
                embed = discord.Embed(
                    title="<a:sprouts_warning_dns:1412200379206336522> Time Too Long",
                    description="Reminders cannot be more than 1 year in the future",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Calculate reminder time
            reminder_time = datetime.utcnow() + time_delta
            
            # Create reminder data
            user_id = str(ctx.author.id)
            reminder_id = self.generate_reminder_id()  # Generate random ID
            reminder_number = self.get_next_reminder_number()  # Get unique reminder number
            
            reminder_data = {
                'message': message,
                'time': reminder_time.isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'channel_id': ctx.channel.id,
                'guild_id': ctx.guild.id if ctx.guild else None,
                'reminder_number': reminder_number
            }
            
            # Store reminder
            if user_id not in self.reminders:
                self.reminders[user_id] = {}
            
            self.reminders[user_id][reminder_id] = reminder_data
            self.save_reminders()
            
            # Send confirmation
            embed = discord.Embed(
                title="Reminder Set",
                description=f"I'll remind you about: **{message}**",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="When",
                value=f"<t:{int(reminder_time.timestamp())}:F>\n(<t:{int(reminder_time.timestamp())}:R>)",
                inline=False
            )
            embed.set_footer(text=f"Reminder ID: {reminder_id}")
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error setting reminder: {e}")
            embed = discord.Embed(
                title="<a:sprouts_error_dns:1411790004652605500> Error",
                description="Failed to set reminder",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="reminders", aliases=["myreminders"], help="Display all your active reminders with time remaining")
    async def list_reminders(self, ctx):
        """List user's active reminders
        
        Usage: reminders
        Shows all your personal reminders with time remaining and IDs
        
        Examples:
        - reminders - View all your active reminders
        - Shows up to 10 reminders with details
        - Displays time remaining and full messages
        
        Features:
        - Shows reminder IDs for deletion
        - Displays time remaining in human format
        - Includes jump links to original channels
        """
        try:
            user_id = str(ctx.author.id)
            
            if user_id not in self.reminders or not self.reminders[user_id]:
                embed = discord.Embed(
                    title="<a:sprouts_warning_dns:1412200379206336522> No Reminders",
                    description="You don't have any active reminders",
                    color=EMBED_COLOR_NORMAL
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            user_reminders = self.reminders[user_id]
            
            embed = discord.Embed(
                title="Your Reminders",
                description=f"You have {len(user_reminders)} active reminder(s)",
                color=EMBED_COLOR_NORMAL
            )
            
            for reminder_id, reminder_data in list(user_reminders.items())[:10]:  # Show max 10
                reminder_time = datetime.fromisoformat(reminder_data['time'])
                time_remaining = self.format_time_remaining(reminder_time)
                
                embed.add_field(
                    name=f"ID: {reminder_id}",  # Show full short ID
                    value=f"**Message:** {reminder_data['message'][:100]}{'...' if len(reminder_data['message']) > 100 else ''}\n"
                          f"**Due:** <t:{int(reminder_time.timestamp())}:R>\n"
                          f"**Time Left:** {time_remaining}",
                    inline=False
                )
            
            if len(user_reminders) > 10:
                embed.add_field(
                    name="Note",
                    value=f"Showing first 10 of {len(user_reminders)} reminders",
                    inline=False
                )
            
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error listing reminders: {e}")
            embed = discord.Embed(
                title="<a:sprouts_error_dns:1411790004652605500> Error",
                description="Failed to list reminders",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="delreminder", aliases=["removereminder"], help="Delete specific reminder by ID")
    async def delete_reminder(self, ctx, reminder_id: str):
        """Delete a specific reminder
        
        Usage: delreminder <id>
        Permanently removes reminder using its unique ID
        
        Examples:
        - delreminder abc123 - Delete reminder with ID abc123
        
        Common Errors:
        - ID not found: Use 'reminders' to see valid IDs
        - Case sensitive: ID must match exactly
        - Cannot undo: Deletion is permanent
        
        Note: Use 'reminders' command to see valid IDs
        """
        try:
            user_id = str(ctx.author.id)
            
            if user_id not in self.reminders:
                embed = discord.Embed(
                    title="<a:sprouts_warning_dns:1412200379206336522> No Reminders",
                    description="You don't have any active reminders",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Find reminder by exact ID match or partial match
            found_reminder = None
            for full_id, reminder_data in self.reminders[user_id].items():
                if full_id == reminder_id or full_id.lower() == reminder_id.lower():
                    found_reminder = (full_id, reminder_data)
                    break
            
            if not found_reminder:
                embed = discord.Embed(
                    title="<a:sprouts_warning_dns:1412200379206336522> Reminder Not Found",
                    description=f"No reminder found with ID `{reminder_id}`",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            full_id, reminder_data = found_reminder
            
            # Delete the reminder
            del self.reminders[user_id][full_id]
            if not self.reminders[user_id]:  # Remove user if no more reminders
                del self.reminders[user_id]
            
            self.save_reminders()
            
            embed = discord.Embed(
                title="Reminder Deleted",
                description=f"Deleted reminder: **{reminder_data['message'][:100]}{'...' if len(reminder_data['message']) > 100 else ''}**",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_footer(text=f"Deleted by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            embed = discord.Embed(
                title="<a:sprouts_error_dns:1411790004652605500> Error",
                description="Failed to delete reminder",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)

async def setup_reminders(bot):
    """Setup reminders cog"""
    await bot.add_cog(Reminders(bot))
    logger.info("Reminders setup completed")