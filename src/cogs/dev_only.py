"""
Developer-Only Commands (Text Commands Only)
Hidden commands that only the bot developer can access
"""

import discord
from discord.ext import commands
import logging
import os
import sys
import asyncio
import json
import time
import re
import shutil
from pathlib import Path
from typing import Optional
from config import BOT_CONFIG, EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR, EMBED_COLOR_SUCCESS, SPROUTS_CHECK, SPROUTS_ERROR, SPROUTS_WARNING

# Add missing color constant
EMBED_COLOR_WARNING = 0xFFE682

logger = logging.getLogger(__name__)

# Global cooldown storage
COOLDOWN_FILE = "config/global_cooldown.json"


class GlobalCooldown:
    """Global cooldown manager for all bot commands"""
    
    def __init__(self):
        self.cooldown_seconds = 0  # 0 means no cooldown
        self.user_cooldowns = {}  # user_id: last_command_time
        self.load_cooldown_config()
    
    def load_cooldown_config(self):
        """Load cooldown configuration from file"""
        try:
            if os.path.exists(COOLDOWN_FILE):
                with open(COOLDOWN_FILE, 'r') as f:
                    data = json.load(f)
                    self.cooldown_seconds = data.get('cooldown_seconds', 0)
        except Exception as e:
            logger.error(f"Error loading cooldown config: {e}")
            self.cooldown_seconds = 0
    
    def save_cooldown_config(self):
        """Save cooldown configuration to file"""
        try:
            with open(COOLDOWN_FILE, 'w') as f:
                json.dump({'cooldown_seconds': self.cooldown_seconds}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cooldown config: {e}")
    
    def set_cooldown(self, seconds: int):
        """Set global cooldown in seconds"""
        self.cooldown_seconds = seconds
        # Clear existing user cooldowns when setting new cooldown
        self.user_cooldowns.clear()
        self.save_cooldown_config()
    
    def remove_cooldown(self):
        """Remove global cooldown"""
        self.cooldown_seconds = 0
        self.user_cooldowns.clear()
        self.save_cooldown_config()
    
    def check_cooldown(self, user_id: int) -> float:
        """Check if user is on cooldown. Returns remaining time or 0 if not on cooldown"""
        if self.cooldown_seconds == 0:
            return 0
        
        current_time = time.time()
        last_command_time = self.user_cooldowns.get(user_id, 0)
        time_since_last = current_time - last_command_time
        
        if time_since_last < self.cooldown_seconds:
            return self.cooldown_seconds - time_since_last
        
        return 0
    
    def update_user_cooldown(self, user_id: int):
        """Update user's last command time"""
        if self.cooldown_seconds > 0:
            self.user_cooldowns[user_id] = time.time()

# Global cooldown instance
global_cooldown = GlobalCooldown()

class GuildsPaginationView(discord.ui.View):
    """Pagination view for guilds list"""
    
    def __init__(self, guilds, author):
        super().__init__(timeout=300)  # 5 minute timeout
        self.guilds = guilds
        self.author = author
        self.current_page = 0
        self.per_page = 5
        self.max_pages = (len(guilds) - 1) // self.per_page + 1
        self.message = None
        
        # Update button states for single page
        if self.max_pages == 1:
            self.next_page.disabled = True
        
    async def create_embed(self, page):
        """Create embed for specific page"""
        start_idx = page * self.per_page
        end_idx = start_idx + self.per_page
        guilds_slice = self.guilds[start_idx:end_idx]
        
        embed = discord.Embed(
            title=f"Server List ({len(self.guilds)} total)",
            color=EMBED_COLOR_NORMAL
        )
        embed.set_thumbnail(url=self.guilds[0].me.display_avatar.url if self.guilds else None)
        
        # Create clean server list
        for i, guild in enumerate(guilds_slice):
            # Try to create an invite for the guild
            invite_text = "No invite available"
            try:
                # Find a channel where we can create invites
                invite_channel = None
                
                # Try system channel first
                if guild.system_channel and guild.system_channel.permissions_for(guild.me).create_instant_invite:
                    invite_channel = guild.system_channel
                else:
                    # Find first text channel where bot can create invites
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).create_instant_invite:
                            invite_channel = channel
                            break
                
                if invite_channel:
                    invite = await invite_channel.create_invite(
                        max_age=0,  # Never expires
                        max_uses=0,  # Unlimited uses
                        unique=False
                    )
                    invite_text = f"[Join Server]({invite.url})"
            
            except Exception:
                invite_text = "No invite permissions"
            
            guild_number = start_idx + i + 1
            
            # Add each guild as a separate field for clean display
            embed.add_field(
                name=f"{guild_number}. {guild.name}",
                value=f"**ID:** `{guild.id}`\n"
                      f"**Members:** {guild.member_count:,}\n"
                      f"**Owner:** {guild.owner.display_name if guild.owner else 'Unknown'}\n"
                      f"**Invite:** {invite_text}",
                inline=True
            )
        embed.set_footer(text=f"Page {page + 1}/{self.max_pages} • Requested by {self.author.display_name}", 
                        icon_url=self.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    async def interaction_check(self, interaction):
        """Only allow the command author to use buttons"""
        return interaction.user == self.author
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.grey, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        self.current_page -= 1
        embed = await self.create_embed(self.current_page)
        
        # Update button states
        self.previous_page.disabled = (self.current_page == 0)
        self.next_page.disabled = (self.current_page == self.max_pages - 1)
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stop pagination and disable all buttons"""
        for item in self.children:
            item.disabled = True
        
        embed = await self.create_embed(self.current_page)
        embed.set_footer(text=f"Pagination ended • Requested by {self.author.display_name}", 
                        icon_url=self.author.display_avatar.url)
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
    
    @discord.ui.button(label="▶", style=discord.ButtonStyle.grey)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        self.current_page += 1
        embed = await self.create_embed(self.current_page)
        
        # Update button states
        self.previous_page.disabled = (self.current_page == 0)
        self.next_page.disabled = (self.current_page == self.max_pages - 1)
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        """Disable all buttons when view times out"""
        for item in self.children:
            item.disabled = True
        
        if self.message:
            try:
                embed = await self.create_embed(self.current_page)
                embed.set_footer(text=f"Pagination timed out • Requested by {self.author.display_name}", 
                               icon_url=self.author.display_avatar.url)
                await self.message.edit(embed=embed, view=self)
            except Exception:
                pass

class DevOnly(commands.Cog):
    """Developer-only commands - hidden from help"""
    
    def __init__(self, bot):
        self.bot = bot
        # Track current presence state independently
        self.current_status = discord.Status.online
        self.current_activity = None
        # Track original activity text for variable processing
        self.current_activity_text = None
        self.current_activity_type = None
        # Get developer ID from environment variables
        try:
            from config import BOT_OWNER_ID
            self.developer_ids = [
                BOT_OWNER_ID,  # Bot owner from environment
                764874247646085151  # Your hardcoded ID as backup
            ]
        except:
            # Fallback if config fails
            self.developer_ids = [764874247646085151]
        # Track maintenance mode and disabled commands with persistence
        self.maintenance_file = 'data/maintenance.json'
        self.maintenance_mode = self.load_maintenance_state()
        self.disabled_commands = set()
    
    async def _process_activity_variables(self, text: str) -> str:
        """Process variables in activity text"""
        if not text:
            return text
        
        try:
            # Replace server count variable
            if '$(server.count)' in text:
                server_count = len(self.bot.guilds)
                text = text.replace('$(server.count)', str(server_count))
            
            # Replace shard ID variable
            if '$(shard.id)' in text:
                # For AutoShardedBot, get the first shard ID or show count
                if hasattr(self.bot, 'shards') and self.bot.shards:
                    shard_id = list(self.bot.shards.keys())[0]  # Get first shard ID
                    text = text.replace('$(shard.id)', str(shard_id))
                elif hasattr(self.bot, 'shard_count') and self.bot.shard_count:
                    # Show shard count if multiple shards
                    text = text.replace('$(shard.id)', f"0-{self.bot.shard_count-1}")
                else:
                    # Single shard bot
                    text = text.replace('$(shard.id)', "0")
            
            return text
        except Exception as e:
            logger.error(f"Error processing activity variables: {e}")
            return text
    
    async def update_activity_variables(self):
        """Update current activity with fresh variable values"""
        if not self.current_activity_text:
            return
        
        try:
            # Process variables again with current values
            processed_text = await self._process_activity_variables(self.current_activity_text)
            
            # Recreate activity with updated text
            if self.current_activity_type == "streaming":
                new_activity = discord.Streaming(
                    name=processed_text,
                    url="https://twitch.tv/example"
                )
            else:
                activity_types = {
                    'playing': discord.ActivityType.playing,
                    'watching': discord.ActivityType.watching,
                    'listening': discord.ActivityType.listening,
                    'competing': discord.ActivityType.competing
                }
                activity_type_obj = activity_types.get(self.current_activity_type, discord.ActivityType.playing)
                new_activity = discord.Activity(
                    type=activity_type_obj,
                    name=processed_text
                )
            
            # Update presence
            self.current_activity = new_activity
            await self.bot.change_presence(status=self.current_status, activity=self.current_activity)
            logger.info(f"Activity variables updated: {processed_text}")
            
        except Exception as e:
            logger.error(f"Error updating activity variables: {e}")
    
    def load_maintenance_state(self):
        """Load maintenance mode state from file"""
        try:
            import os
            import json
            if os.path.exists(self.maintenance_file):
                with open(self.maintenance_file, 'r') as f:
                    data = json.load(f)
                    return data.get('maintenance_mode', False)
        except Exception as e:
            logger.warning(f"Could not load maintenance state: {e}")
        return False
    
    def save_maintenance_state(self):
        """Save maintenance mode state to file"""
        try:
            import os
            import json
            os.makedirs(os.path.dirname(self.maintenance_file), exist_ok=True)
            with open(self.maintenance_file, 'w') as f:
                json.dump({'maintenance_mode': self.maintenance_mode}, f)
        except Exception as e:
            logger.error(f"Could not save maintenance state: {e}")

    def cog_check(self, ctx):
        """Check if user is developer for all commands in this cog"""
        logger.info(f"Dev check - User ID: {ctx.author.id} (type: {type(ctx.author.id)})")
        logger.info(f"Dev check - Developer IDs: {self.developer_ids} (types: {[type(x) for x in self.developer_ids]})")
        result = ctx.author.id in self.developer_ids
        logger.info(f"Dev check result: {result}")
        return result
    
    async def cog_command_error(self, ctx, error):
        """Handle errors in this cog"""
        if isinstance(error, commands.CheckFailure):
            # User is not a developer
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Access Denied",
                description="This command is only available to bot developers.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            # Don't re-raise the error since we handled it
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            # Handle missing arguments with helpful message
            if ctx.command.name == "setactivity":
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Set Activity Error",
                    description="This command requires an argument to work properly.\n\n"
                               "**Valid activity types:** playing, watching, listening, competing, streaming\n\n"
                               "**Example:** `s.setactivity playing with code`",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            else:
                # For other commands, show generic missing argument message
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Missing Argument",
                    description=f"Missing required argument: `{error.param.name}`\n\nUse `s.help {ctx.command.name}` for usage information.",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
        else:
            # For other errors, let the global error handler deal with it
            raise error
    
    @commands.command(name="reload", description="Reload a specific cog", hidden=True)
    @commands.is_owner()
    async def reload_cog(self, ctx, cog: str):
        """Reload a cog"""
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            
            embed = discord.Embed(
                title="Cog Reloaded",
                description=f"Successfully reloaded `{cog}` cog",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"Cog {cog} reloaded by {ctx.author}")
            
        except Exception as e:
            embed = discord.Embed(
                title="Reload Failed",
                description=f"Failed to reload cog: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.error(f"Failed to reload cog {cog}: {e}")
    
    @commands.command(name="reloadall", description="Reload all cogs", hidden=True)
    @commands.is_owner()
    async def reload_all_cogs(self, ctx):
        """Reload all cogs"""
        try:
            # Get list of loaded extensions
            extensions = list(self.bot.extensions.keys())
            reloaded = []
            failed = []
            
            for extension in extensions:
                try:
                    await self.bot.reload_extension(extension)
                    reloaded.append(extension)
                    logger.info(f"Reloaded extension: {extension}")
                except Exception as e:
                    failed.append(f"{extension}: {str(e)}")
                    logger.error(f"Failed to reload {extension}: {e}")
            
            # Create result embed
            embed = discord.Embed(
                title="Reload All Cogs",
                color=EMBED_COLOR_NORMAL if not failed else EMBED_COLOR_ERROR
            )
            
            if reloaded:
                embed.add_field(
                    name=f"Reloaded ({len(reloaded)}):",
                    value="```\n" + "\n".join([ext.split('.')[-1] for ext in reloaded]) + "\n```",
                    inline=False
                )
            
            if failed:
                embed.add_field(
                    name=f"Failed ({len(failed)}):",
                    value="```\n" + "\n".join(failed) + "\n```",
                    inline=False
                )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            embed = discord.Embed(
                title="Reload All Failed",
                description=f"Failed to reload all cogs: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.error(f"Failed to reload all cogs: {e}")
    
    @commands.command(name="shutdown", description="Shutdown the bot", hidden=True)
    @commands.is_owner()
    async def shutdown_bot(self, ctx):
        """Shutdown the bot"""
        try:
            embed = discord.Embed(
                title="Bot Shutdown",
                description="Bot is shutting down...",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"Bot shutdown initiated by {ctx.author}")
            await self.bot.close()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    @commands.command(name="eval", description="Evaluate Python code", hidden=True)
    @commands.is_owner()
    async def eval_code(self, ctx, *, code: str):
        """Evaluate Python code"""
        try:
            # Remove code blocks if present
            if code.startswith('```py') or code.startswith('```python'):
                code = code[5:-3]
            elif code.startswith('```'):
                code = code[3:-3]
            
            # Setup local variables
            local_vars = {
                'bot': self.bot,
                'ctx': ctx,
                'channel': ctx.channel,
                'author': ctx.author,
                'guild': ctx.guild,
                'message': ctx.message,
                'discord': discord,
                'commands': commands
            }
            
            # Execute code
            try:
                result = eval(code, globals(), local_vars)
                if asyncio.iscoroutine(result):
                    result = await result
            except SyntaxError:
                # Try exec instead
                exec(code, globals(), local_vars)
                result = "Code executed successfully (no return value)"
            
            # Format result
            if result is None:
                result = "None"
            elif isinstance(result, str) and len(result) > 1990:
                result = result[:1990] + "..."
            
            embed = discord.Embed(
                title="Code Evaluation",
                description=f"```py\n{code}\n```",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Result",
                value=f"```py\n{result}\n```",
                inline=False
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            embed = discord.Embed(
                title="Evaluation Error",
                description=f"```py\n{code}\n```",
                color=EMBED_COLOR_ERROR
            )
            embed.add_field(
                name="Error",
                value=f"```py\n{str(e)}\n```",
                inline=False
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="setstatus", description="Change bot status", hidden=True)
    @commands.is_owner()
    async def set_status(self, ctx, status: str):
        """Change bot status"""
        try:
            # Define valid statuses
            valid_statuses = {
                'online': discord.Status.online,
                'idle': discord.Status.idle,
                'dnd': discord.Status.dnd,
                'invisible': discord.Status.invisible
            }
            
            # Validate status
            if status.lower() not in valid_statuses:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Invalid Status",
                    description="Valid statuses: online, idle, dnd, invisible",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Get the status
            new_status = valid_statuses[status.lower()]
            
            # Update tracked status
            self.current_status = new_status
            
            # Only change the status, preserve current activity
            logger.info(f"Setting status to: {status.lower()}")
            
            await self.bot.change_presence(status=self.current_status, activity=self.current_activity)
            
            # Success message
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Status Updated",
                description=f"Status: {status.lower()}",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"Bot status changed by {ctx.author}: {status.lower()}")
            
        except Exception as e:
            logger.error(f"Error changing status: {e}")
            embed = discord.Embed(
                title="Error",
                description="An error occurred while changing status.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="setactivity", description="Change bot activity", hidden=True)
    @commands.is_owner()
    async def set_activity(self, ctx, activity_type: str, *, activity_text: str):
        """Change bot activity with support for $(server.count) and $(shard.id) variables"""
        try:
            # Define valid activity types
            valid_activities = {
                'playing': discord.ActivityType.playing,
                'watching': discord.ActivityType.watching,
                'listening': discord.ActivityType.listening,
                'competing': discord.ActivityType.competing,
                'streaming': discord.ActivityType.streaming
            }
            
            # Validate activity type
            if activity_type.lower() not in valid_activities:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Invalid Activity Type",
                    description="Valid activity types: playing, watching, listening, competing, streaming\n\n"
                               "**Supported Variables:**\n"
                               "`$(server.count)` - Total number of servers\n"
                               "`$(shard.id)` - Current shard ID",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Process variables in activity text
            processed_text = await self._process_activity_variables(activity_text)
            
            # Create activity
            activity_type_obj = valid_activities[activity_type.lower()]
            if activity_type.lower() == "streaming":
                discord_activity = discord.Streaming(
                    name=processed_text,
                    url="https://twitch.tv/example"
                )
            else:
                discord_activity = discord.Activity(
                    type=activity_type_obj,
                    name=processed_text
                )
            
            # Store the original text with variables for future updates
            self.current_activity_text = activity_text
            self.current_activity_type = activity_type.lower()
            
            # Update tracked activity
            self.current_activity = discord_activity
            
            # Only change the activity, preserve current status  
            logger.info(f"Setting activity to: {activity_type.lower()} {processed_text}")
            
            await self.bot.change_presence(status=self.current_status, activity=self.current_activity)
            
            # Success message
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Activity Updated",
                description=f"Activity: {activity_type.lower()} {processed_text}\n\n"
                           f"Raw input: `{activity_text}`",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"Bot activity changed by {ctx.author}: {activity_type.lower()} {activity_text}")
            
        except Exception as e:
            logger.error(f"Error changing activity: {e}")
            embed = discord.Embed(
                title="Error",
                description="An error occurred while changing activity.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
    
    
    @commands.command(name="guilds", description="List all guilds", hidden=True)
    @commands.is_owner()
    async def list_guilds(self, ctx):
        """List all guilds the bot is in with pagination"""
        try:
            guilds = list(self.bot.guilds)
            
            if not guilds:
                embed = discord.Embed(
                    title="No Guilds",
                    description="Bot is not in any guilds.",
                    color=EMBED_COLOR_NORMAL
                )
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Sort guilds by member count (descending)
            guilds.sort(key=lambda g: g.member_count, reverse=True)
            
            # Create pagination view
            view = GuildsPaginationView(guilds, ctx.author)
            embed = await view.create_embed(0)
            
            # Send initial message
            message = await ctx.reply(embed=embed, view=view, mention_author=False)
            view.message = message
            
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Error listing guilds: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="leaveguild", description="Leave a guild", hidden=True)
    @commands.is_owner()
    async def leave_guild(self, ctx, guild_id: int):
        """Leave a guild by ID"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                embed = discord.Embed(
                    title="Guild Not Found",
                    description=f"Guild with ID `{guild_id}` not found.",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            guild_name = guild.name
            await guild.leave()
            
            embed = discord.Embed(
                title="Guild Left",
                description=f"Successfully left guild: **{guild_name}** (`{guild_id}`)",
                color=EMBED_COLOR_NORMAL
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"Left guild {guild_name} ({guild_id}) by {ctx.author}")
            
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Error leaving guild: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="maintenance", description="Toggle maintenance mode", hidden=True)
    @commands.is_owner()
    async def maintenance_mode(self, ctx):
        """Toggle maintenance mode on/off"""
        try:
            # Simple toggle - flip the current state
            self.maintenance_mode = not self.maintenance_mode
            
            # Save the state to persist across restarts
            self.save_maintenance_state()
            
            if self.maintenance_mode:
                status = "enabled"
                color = EMBED_COLOR_ERROR  # Red for maintenance enabled
                description = "Bot is now in maintenance mode. Only you can use commands."
                emoji = SPROUTS_ERROR
            else:
                status = "disabled"
                color = EMBED_COLOR_SUCCESS  # Green for maintenance disabled
                description = "Bot is now available to all users."
                emoji = SPROUTS_CHECK
            
            embed = discord.Embed(
                title=f"{emoji} Maintenance Mode {status.title()}",
                description=description,
                color=color
            )
            embed.set_footer(text=f"Toggled by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"Maintenance mode {status} by {ctx.author} (persisted)")
            
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Error toggling maintenance mode: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
    
    def parse_time(self, time_str):
        """Parse time string like '5m', '1h', '30s' into seconds"""
        if not time_str or time_str == "0":
            return 0
        
        # If it's just a number, treat as seconds
        if time_str.isdigit():
            return int(time_str)
        
        # Parse time units
        time_str = time_str.lower().strip()
        if not time_str:
            return None
            
        # Extract number and unit
        import re
        match = re.match(r'^(\d+)([smhd]?)$', time_str)
        if not match:
            return None
            
        value, unit = match.groups()
        value = int(value)
        
        # Convert to seconds
        if unit == 's' or unit == '':  # seconds (default if no unit)
            return value
        elif unit == 'm':  # minutes
            return value * 60
        elif unit == 'h':  # hours
            return value * 3600
        elif unit == 'd':  # days
            return value * 86400
        else:
            return None
    
    def format_time(self, seconds):
        """Format seconds into human readable format"""
        if seconds == 0:
            return "0 seconds"
        elif seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining = seconds % 60
            result = f"{minutes} minute{'s' if minutes != 1 else ''}"
            if remaining > 0:
                result += f", {remaining} second{'s' if remaining != 1 else ''}"
            return result
        elif seconds < 86400:
            hours = seconds // 3600
            remaining = seconds % 3600
            minutes = remaining // 60
            result = f"{hours} hour{'s' if hours != 1 else ''}"
            if minutes > 0:
                result += f", {minutes} minute{'s' if minutes != 1 else ''}"
            return result
        else:
            days = seconds // 86400
            remaining = seconds % 86400
            hours = remaining // 3600
            result = f"{days} day{'s' if days != 1 else ''}"
            if hours > 0:
                result += f", {hours} hour{'s' if hours != 1 else ''}"
            return result

    # Global Logging Commands (Developer Only)
    
    @commands.command(name="settings", description="List all configured bot settings", hidden=True)
    @commands.is_owner()
    async def list_bot_settings(self, ctx):
        """Display all current bot configuration settings"""
        try:
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Bot Configuration Settings",
                description="Current configuration status for all bot systems",
                color=EMBED_COLOR_NORMAL
            )
            
            # Bot Status Settings
            status_text = f"Online ({self.bot.status.name})"
            if self.bot.activity:
                activity_type = self.bot.activity.type.name.title()
                activity_name = self.bot.activity.name
                status_text += f" - {activity_type}: {activity_name}"
            
            embed.add_field(
                name="Bot Status",
                value=status_text,
                inline=False
            )
            
            # Environment Variables
            env_settings = []
            env_vars = {
                "DEFAULT_PREFIX": os.getenv('DEFAULT_PREFIX', 's.'),
                "LOG_COMMANDS_CHANNEL": os.getenv('LOG_COMMANDS_CHANNEL', 'Not set'),
                "LOG_DMS_CHANNEL": os.getenv('LOG_DMS_CHANNEL', 'Not set'),
                "LOG_GUILD_EVENTS": os.getenv('LOG_GUILD_EVENTS', 'Not set'),
                "EMBED_COLOR_NORMAL": os.getenv('EMBED_COLOR_NORMAL', '0x2ecc71'),
                "EMBED_COLOR_ERROR": os.getenv('EMBED_COLOR_ERROR', '0xe74c3c')
            }
            
            for var, value in env_vars.items():
                if var.startswith('LOG_') and value != 'Not set':
                    try:
                        channel = self.bot.get_channel(int(value))
                        value = f"{channel.mention}" if channel else f"Channel ID: {value} (not found)"
                    except (ValueError, TypeError):
                        value = f"Invalid ID: {value}"
                env_settings.append(f"**{var.replace('_', ' ').title()}:** {value}")
            
            embed.add_field(
                name="Environment Settings",
                value="\n".join(env_settings),
                inline=False
            )
            
            # Global Cooldown Status
            try:
                from src.utils.global_cooldown import global_cooldown
                if hasattr(global_cooldown, 'cooldown_seconds') and global_cooldown.cooldown_seconds:
                    cooldown_text = f"Active - {self.format_time(global_cooldown.cooldown_seconds)}"
                else:
                    cooldown_text = "Disabled"
            except ImportError:
                cooldown_text = "Not configured"
            
            embed.add_field(
                name="Global Cooldown",
                value=cooldown_text,
                inline=True
            )
            
            # Maintenance Mode Status
            maintenance_status = "Disabled"
            try:
                maintenance_file = "config/maintenance.json"
                if os.path.exists(maintenance_file):
                    with open(maintenance_file, 'r') as f:
                        maintenance_data = json.load(f)
                        if maintenance_data.get('enabled', False):
                            maintenance_status = f"Active - {maintenance_data.get('reason', 'No reason')}"
            except Exception:
                pass
            
            embed.add_field(
                name="Maintenance Mode",
                value=maintenance_status,
                inline=True
            )
            
            # Server Stats
            total_guilds = len(self.bot.guilds)
            total_users = sum(guild.member_count for guild in self.bot.guilds if guild.member_count)
            
            embed.add_field(
                name="Bot Statistics",
                value=f"**Guilds:** {total_guilds}\n**Users:** {total_users:,}",
                inline=True
            )
            
            # Data File Counts
            data_counts = []
            data_files = {
                "Saved Embeds": "src/data/saved_embeds.json",
                "Auto Responders": "src/data/autoresponders.json", 
                "Sticky Messages": "src/data/stickies.json",
                "Reminders": "src/data/reminders.json",
                "Tickets": "src/data/tickets.json"
            }
            
            for name, file_path in data_files.items():
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            count = len(data) if isinstance(data, dict) else 0
                            data_counts.append(f"**{name}:** {count}")
                    else:
                        data_counts.append(f"**{name}:** 0")
                except Exception:
                    data_counts.append(f"**{name}:** Error")
            
            embed.add_field(
                name="Data File Status",
                value="\n".join(data_counts),
                inline=False
            )
            
            embed.set_footer(text=f"Settings requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Bot settings displayed for {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error displaying bot settings: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Settings Error",
                description=f"Error retrieving bot settings: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=error_embed, mention_author=False)

    @commands.command(name="globalcooldown", aliases=["cooldown"], description="Set global command cooldown", hidden=True)
    @commands.is_owner()
    async def set_global_cooldown(self, ctx, time_input: str = None):
        """Set global cooldown for all commands
        
        Time format examples:
        - 5 or 5s = 5 seconds
        - 2m = 2 minutes
        - 1h = 1 hour
        - 0 = remove cooldown
        """
        try:
            if time_input is None:
                # Show current cooldown
                current = global_cooldown.cooldown_seconds
                if current == 0:
                    description = "No global cooldown is currently set."
                else:
                    formatted_time = self.format_time(current)
                    description = f"Global cooldown is set to **{formatted_time}** ({current} seconds)"
                
                embed = discord.Embed(
                    title="Global Cooldown Status",
                    description=description,
                    color=EMBED_COLOR_NORMAL
                )
                embed.add_field(
                    name="Supported Time Formats", 
                    value="• `5` or `5s` = 5 seconds\n• `2m` = 2 minutes\n• `1h` = 1 hour\n• `1d` = 1 day\n• `0` = remove cooldown",
                    inline=False
                )
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Parse the time input
            seconds = self.parse_time(time_input)
            
            if seconds is None:
                embed = discord.Embed(
                    title="Invalid Time Format",
                    description="Please use a valid time format:\n"
                               "• `5` or `5s` = 5 seconds\n"
                               "• `2m` = 2 minutes\n"
                               "• `1h` = 1 hour\n"
                               "• `1d` = 1 day\n"
                               "• `0` = remove cooldown",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            if seconds < 0:
                embed = discord.Embed(
                    title="Invalid Cooldown",
                    description="Cooldown must be 0 or greater (0 = no cooldown)",
                    color=EMBED_COLOR_ERROR
                )
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            if seconds == 0:
                global_cooldown.remove_cooldown()
                description = "Global cooldown has been **removed**"
            else:
                global_cooldown.set_cooldown(seconds)
                formatted_time = self.format_time(seconds)
                description = f"Global cooldown set to **{formatted_time}** ({seconds} seconds)"
            
            embed = discord.Embed(
                title="Global Cooldown Updated",
                description=description,
                color=EMBED_COLOR_NORMAL
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"Global cooldown set to {seconds} seconds ({time_input}) by {ctx.author}")
            
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Error setting global cooldown: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
    
    

    # Global Logging Commands (Developer Only)
    
    @commands.group(name="cmdlogs", invoke_without_command=True, hidden=True)
    async def cmdlogs(self, ctx):
        """Global command logging system - Developer only"""
        embed = discord.Embed(
            title="Global Command Logging System",
            description="Bot-wide command monitoring (Developer Only)",
            color=EMBED_COLOR_NORMAL
        )
        
        # Check current global command logging channel
        global_channel_id = os.getenv('LOG_COMMANDS_CHANNEL')
        if global_channel_id:
            try:
                channel = self.bot.get_channel(int(global_channel_id))
                status = f"Enabled in {channel.mention if channel else 'Unknown Channel'}"
            except (ValueError, TypeError):
                status = "Configured but invalid channel ID"
        else:
            status = "Disabled"
        
        embed.add_field(
            name="**Current Status**",
            value=status,
            inline=False
        )
        
        embed.add_field(
            name="**Available Commands**",
            value=(
                "`s.cmdlogs set <#channel>` - Set global command logging channel\n"
                "`s.cmdlogs status` - View current configuration\n"
                "**Note**: All command logs from all servers go to this one channel"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Developer: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)
    
    @cmdlogs.command(name="set", hidden=True)
    async def cmdlogs_set(self, ctx, channel: discord.TextChannel):
        """Set global command logging channel"""
        try:
            # Update environment variable (this will require manual .env update for persistence)
            os.environ['LOG_COMMANDS_CHANNEL'] = str(channel.id)
            
            # Also write to a config file for persistence
            config_file = "config/global_logging.json"
            os.makedirs("config", exist_ok=True)
            
            config = {}
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                except:
                    config = {}
            
            config['LOG_COMMANDS_CHANNEL'] = str(channel.id)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            embed = discord.Embed(
                title="Global Command Logging Configured",
                description=f"All command logs will now be sent to {channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="**Channel Set**", 
                value=f"{channel.mention} (`{channel.id}`)",
                inline=False
            )
            embed.add_field(
                name="**Scope**",
                value="All commands from all servers will be logged here",
                inline=False
            )
            embed.set_footer(text=f"Set by {ctx.author.display_name}")
            await ctx.reply(embed=embed, mention_author=False)
            
            # Send confirmation to the configured logging channel
            try:
                test_embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Command Logging Test",
                    description=f"Global command logging has been configured by {ctx.author.mention}\n\nAll future command logs will appear in this channel.",
                    color=EMBED_COLOR_NORMAL
                )
                test_embed.add_field(
                    name="Setup Details",
                    value=f"**Configured by:** {ctx.author} (`{ctx.author.id}`)\n**From channel:** {ctx.channel.mention}\n**Server:** {ctx.guild.name}",
                    inline=False
                )
                test_embed.set_footer(text="This is a test message to confirm logging is working")
                await channel.send(embed=test_embed)
                logger.info(f"Sent test message to command logging channel {channel}")
            except Exception as e:
                logger.warning(f"Could not send test message to command logging channel: {e}")
                
            logger.info(f"Global command logging set to {channel} by {ctx.author}")
            
        except Exception as e:
            embed = discord.Embed(
                title="Error Setting Command Logging",
                description=f"Failed to configure command logging: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            logger.error(f"Error setting global command logging: {e}")
    
    @cmdlogs.command(name="status", hidden=True)
    async def cmdlogs_status(self, ctx):
        """Check global command logging status"""
        embed = discord.Embed(
            title="Global Command Logging Status",
            color=EMBED_COLOR_NORMAL
        )
        
        global_channel_id = os.getenv('LOG_COMMANDS_CHANNEL')
        if global_channel_id:
            try:
                channel = self.bot.get_channel(int(global_channel_id))
                if channel:
                    embed.add_field(name="**Status**", value="Enabled", inline=True)
                    embed.add_field(name="**Channel**", value=channel.mention, inline=True)
                    embed.add_field(name="**Server**", value=channel.guild.name, inline=True)
                else:
                    embed.add_field(name="**Status**", value="Channel Not Found", inline=False)
                    embed.add_field(name="**Channel ID**", value=global_channel_id, inline=False)
            except (ValueError, TypeError):
                embed.add_field(name="**Status**", value="Invalid Channel ID", inline=False)
        else:
            embed.add_field(name="**Status**", value="Disabled", inline=False)
        
        embed.set_footer(text=f"Checked by {ctx.author.display_name}")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.group(name="dmlogs", invoke_without_command=True, hidden=True)
    async def dmlogs(self, ctx):
        """Global DM logging system - Developer only"""
        embed = discord.Embed(
            title="Global DM Logging System",
            description="Bot-wide DM monitoring (Developer Only)",
            color=EMBED_COLOR_NORMAL
        )
        
        # Check current global DM logging channel
        global_channel_id = os.getenv('LOG_DMS_CHANNEL')
        if global_channel_id:
            try:
                channel = self.bot.get_channel(int(global_channel_id))
                status = f"Enabled in {channel.mention if channel else 'Unknown Channel'}"
            except (ValueError, TypeError):
                status = "Configured but invalid channel ID"
        else:
            status = "Disabled"
        
        embed.add_field(
            name="**Current Status**",
            value=status,
            inline=False
        )
        
        embed.add_field(
            name="**Available Commands**",
            value=(
                "`{ctx.prefix}dmlogs set <#channel>` - Set global DM logging channel\n"
                "`{ctx.prefix}dmlogs status` - View current configuration\n"
                "**Note**: All DMs to the bot will be logged to this one channel"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Developer: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)
    
    @dmlogs.command(name="set", hidden=True)
    async def dmlogs_set(self, ctx, channel: discord.TextChannel):
        """Set global DM logging channel"""
        try:
            # Update environment variable
            os.environ['LOG_DMS_CHANNEL'] = str(channel.id)
            
            # Also write to config file for persistence
            config_file = "config/global_logging.json"
            os.makedirs("config", exist_ok=True)
            
            config = {}
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                except:
                    config = {}
            
            config['LOG_DMS_CHANNEL'] = str(channel.id)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            embed = discord.Embed(
                title="Global DM Logging Configured",
                description=f"All DM logs will now be sent to {channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="**Channel Set**", 
                value=f"{channel.mention} (`{channel.id}`)",
                inline=False
            )
            embed.add_field(
                name="**Scope**",
                value="All DMs to the bot will be logged here",
                inline=False
            )
            embed.set_footer(text=f"Set by {ctx.author.display_name}")
            await ctx.reply(embed=embed, mention_author=False)
            
            # Send confirmation to the configured logging channel
            try:
                test_embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} DM Logging Test",
                    description=f"Global DM logging has been configured by {ctx.author.mention}\n\nAll future DMs to the bot will appear in this channel.",
                    color=EMBED_COLOR_NORMAL
                )
                test_embed.add_field(
                    name="Setup Details",
                    value=f"**Configured by:** {ctx.author} (`{ctx.author.id}`)\n**From channel:** {ctx.channel.mention}\n**Server:** {ctx.guild.name}",
                    inline=False
                )
                test_embed.set_footer(text="This is a test message to confirm DM logging is working")
                await channel.send(embed=test_embed)
                logger.info(f"Sent test message to DM logging channel {channel}")
            except Exception as e:
                logger.warning(f"Could not send test message to DM logging channel: {e}")
                
            logger.info(f"Global DM logging set to {channel} by {ctx.author}")
            
        except Exception as e:
            embed = discord.Embed(
                title="Error Setting DM Logging",
                description=f"Failed to configure DM logging: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            logger.error(f"Error setting global DM logging: {e}")
    
    @dmlogs.command(name="status", hidden=True)
    async def dmlogs_status(self, ctx):
        """Check global DM logging status"""
        embed = discord.Embed(
            title="Global DM Logging Status",
            color=EMBED_COLOR_NORMAL
        )
        
        global_channel_id = os.getenv('LOG_DMS_CHANNEL')
        if global_channel_id:
            try:
                channel = self.bot.get_channel(int(global_channel_id))
                if channel:
                    embed.add_field(name="**Status**", value="Enabled", inline=True)
                    embed.add_field(name="**Channel**", value=channel.mention, inline=True)
                    embed.add_field(name="**Server**", value=channel.guild.name, inline=True)
                else:
                    embed.add_field(name="**Status**", value="Channel Not Found", inline=False)
                    embed.add_field(name="**Channel ID**", value=global_channel_id, inline=False)
            except (ValueError, TypeError):
                embed.add_field(name="**Status**", value="Invalid Channel ID", inline=False)
        else:
            embed.add_field(name="**Status**", value="Disabled", inline=False)
        
        embed.set_footer(text=f"Checked by {ctx.author.display_name}")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.group(name="guildlogs", invoke_without_command=True, hidden=True)
    async def guildlogs(self, ctx):
        """Global guild join/leave logging system - Developer only"""
        embed = discord.Embed(
            title="Global Guild Logging System",
            description="Bot join/leave event monitoring (Developer Only)",
            color=EMBED_COLOR_NORMAL
        )
        
        # Check current global guild logging channel
        global_channel_id = os.getenv('LOG_GUILD_EVENTS')
        if global_channel_id:
            try:
                channel = self.bot.get_channel(int(global_channel_id))
                status = f"Enabled in {channel.mention if channel else 'Unknown Channel'}"
            except (ValueError, TypeError):
                status = "Configured but invalid channel ID"
        else:
            status = "Disabled"
        
        embed.add_field(
            name="**Current Status**",
            value=status,
            inline=False
        )
        
        embed.add_field(
            name="**Available Commands**",
            value=(
                "`s.guildlogs set <#channel>` - Set global guild logging channel\n"
                "`s.guildlogs status` - View current configuration\n"
                "**Note**: Bot join/leave events will be logged to this channel"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Developer: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)
    
    @guildlogs.command(name="set", hidden=True)
    async def guildlogs_set(self, ctx, channel: discord.TextChannel):
        """Set global guild logging channel"""
        try:
            # Update environment variable
            os.environ['LOG_GUILD_EVENTS'] = str(channel.id)
            
            # Also write to config file for persistence
            config_file = "config/global_logging.json"
            os.makedirs("config", exist_ok=True)
            
            config = {}
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                except:
                    config = {}
            
            config['LOG_GUILD_EVENTS'] = str(channel.id)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            embed = discord.Embed(
                title="Global Guild Logging Configured",
                description=f"All guild join/leave events will now be sent to {channel.mention}",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="**Channel Set**", 
                value=f"{channel.mention} (`{channel.id}`)",
                inline=False
            )
            embed.add_field(
                name="**Events Logged**",
                value="• Bot joins new servers\n• Bot leaves/gets kicked from servers",
                inline=False
            )
            embed.set_footer(text=f"Set by {ctx.author.display_name}")
            await ctx.reply(embed=embed, mention_author=False)
            
            # Send confirmation to the configured logging channel
            try:
                test_embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Guild Logging Test",
                    description=f"Global guild event logging has been configured by {ctx.author.mention}\n\nAll future guild join/leave events will appear in this channel.",
                    color=EMBED_COLOR_NORMAL
                )
                test_embed.add_field(
                    name="Setup Details",
                    value=f"**Configured by:** {ctx.author} (`{ctx.author.id}`)\n**From channel:** {ctx.channel.mention}\n**Server:** {ctx.guild.name}",
                    inline=False
                )
                test_embed.add_field(
                    name="Events That Will Be Logged",
                    value="• Bot joins new servers\n• Bot leaves/gets kicked from servers",
                    inline=False
                )
                test_embed.set_footer(text="This is a test message to confirm guild logging is working")
                await channel.send(embed=test_embed)
                logger.info(f"Sent test message to guild logging channel {channel}")
            except Exception as e:
                logger.warning(f"Could not send test message to guild logging channel: {e}")
                
            logger.info(f"Global guild logging set to {channel} by {ctx.author}")
            
        except Exception as e:
            embed = discord.Embed(
                title="Error Setting Guild Logging",
                description=f"Failed to configure guild logging: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            logger.error(f"Error setting global guild logging: {e}")
    
    @guildlogs.command(name="status", hidden=True)
    async def guildlogs_status(self, ctx):
        """Check global guild logging status"""
        embed = discord.Embed(
            title="Global Guild Logging Status",
            color=EMBED_COLOR_NORMAL
        )
        
        global_channel_id = os.getenv('LOG_GUILD_EVENTS')
        if global_channel_id:
            try:
                channel = self.bot.get_channel(int(global_channel_id))
                if channel:
                    embed.add_field(name="**Status**", value="Enabled", inline=True)
                    embed.add_field(name="**Channel**", value=channel.mention, inline=True)
                    embed.add_field(name="**Server**", value=channel.guild.name, inline=True)
                else:
                    embed.add_field(name="**Status**", value="Channel Not Found", inline=False)
                    embed.add_field(name="**Channel ID**", value=global_channel_id, inline=False)
            except (ValueError, TypeError):
                embed.add_field(name="**Status**", value="Invalid Channel ID", inline=False)
        else:
            embed.add_field(name="**Status**", value="Disabled", inline=False)
        
        embed.set_footer(text=f"Checked by {ctx.author.display_name}")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="devhelp", description="Show developer commands help", hidden=True)
    async def devhelp(self, ctx):
        """Show help for developer-only commands"""
        # Developer check is handled automatically by cog_check method
        
        embed = discord.Embed(
            title="Developer Commands Help",
            description="Complete list of developer-only bot commands. All commands require bot developer permissions.",
            color=EMBED_COLOR_NORMAL
        )
        
        # Command categories
        embed.add_field(
            name="Bot Management",
            value=(
                "`s.reload` - Reload a specific cog\n"
                "`s.reloadall` - Reload all cogs\n"
                "`s.eval` - Evaluate Python code\n"
                "`s.guilds` - List all guilds the bot is in\n"
                "`s.leaveguild` - Make bot leave a specific server\n"
                "`s.settings` - View all configured bot settings"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Bot Status",
            value=(
                "`s.setstatus` - Set bot status (online/idle/dnd/invisible)\n"
                "`s.setactivity` - Set bot activity (playing/watching/listening/competing/streaming)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Global Logging System", 
            value=(
                "`s.cmdlogs set` - Set global command logging channel\n"
                "`s.dmlogs set` - Set global DM logging channel\n"
                "`s.guildlogs set` - Set global guild join/leave logging channel\n"
                "`s.cmdlogs status` - Check command logging status\n"
                "`s.dmlogs status` - Check DM logging status\n"
                "`s.guildlogs status` - Check guild logging status\n"
                "**Note:** All logs go to your bot server globally"
            ),
            inline=False
        )
        
        embed.add_field(
            name="System Management",
            value=(
                "`s.cooldown` - Set global command cooldown (supports 1s, 5m, 2h, 1d)\n"
                "`s.maintenance` - Toggle maintenance mode (complete silence for others)\n"
                "`s.shutdown` - Safely shut down the bot\n"
                "`s.clearslash` - Remove all slash commands from Discord"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Server Stats & Monitoring",
            value=(
                "`s.serverstats start` - Start server stats monitoring\n"
                "`s.serverstats stop` - Stop server stats monitoring\n"
                "`s.serverstats show` - Show current server stats\n"
                "`s.serverstats list` - List all monitored servers\n"
                "`s.ratelimit status` - Check rate limit status\n"
                "`s.ratelimit setchannel` - Set rate limit alert channel\n"
                "`s.ratelimit threshold` - Set rate limit threshold\n"
                "`s.ratelimit reset` - Reset rate limit warnings"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Data Management",
            value=(
                "`s.listdata user` - List saved embeds, tickets, reminders for user\n"
                "`s.listdata guild` - List auto responders, sticky messages, settings for guild\n"
                "`s.listdata all` - Overview of all data: embeds, tickets, transcripts, user data\n"
                "`s.deletedata user` - Delete user's saved embeds, tickets, reminders\n"
                "`s.deletedata guild` - Delete guild's auto responders, sticky messages, settings\n"
                "`s.resetdata` - **DANGER** Reset all: embeds, tickets, auto responders, user data\n"
                "**Owner Only - Manages: saved embeds, sticky messages, ticket settings, transcripts, user data, auto responders**"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Communications",
            value=(
                "`s.changelog` - Send changelog updates to all server owners\n"
                "**Owner Only - Use for bot changelog updates and version releases**"
            ),
            inline=False
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Developer: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        await ctx.reply(embed=embed, mention_author=False)
        logger.info(f"Developer help accessed by {ctx.author}")

    @commands.command(name="changelog", description="Send changelog update to all server owners", hidden=True)
    @commands.is_owner()
    async def send_changelog(self, ctx, *, message: str):
        """Send changelog update to all server owners"""
        if len(message) > 1900:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Message Too Long",
                description="Message must be under 1900 characters to ensure delivery.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Count unique owners for confirmation
        unique_owner_ids = set()
        for guild in self.bot.guilds:
            if guild.owner:
                unique_owner_ids.add(guild.owner.id)
        
        # Confirmation step
        confirm_embed = discord.Embed(
            title=f"{SPROUTS_WARNING} Changelog Confirmation",
            description=f"You are about to send this changelog to **{len(unique_owner_ids)}** unique server owners:",
            color=EMBED_COLOR_WARNING
        )
        confirm_embed.add_field(
            name="Message Preview:",
            value=f"```{message}```",
            inline=False
        )
        confirm_embed.add_field(
            name="Recipients:",
            value=f"{len(unique_owner_ids)} unique owners across {len(self.bot.guilds)} servers",
            inline=True
        )
        confirm_embed.set_footer(text="React to confirm or cancel")
        
        confirm_msg = await ctx.reply(embed=confirm_embed, mention_author=False)
        await confirm_msg.add_reaction(SPROUTS_CHECK)
        await confirm_msg.add_reaction(SPROUTS_ERROR)
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in [SPROUTS_CHECK, SPROUTS_ERROR] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Changelog Cancelled",
                description="Confirmation timed out. No messages were sent.",
                color=EMBED_COLOR_ERROR
            )
            await confirm_msg.edit(embed=embed)
            return
        
        if str(reaction.emoji) == SPROUTS_ERROR:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Changelog Cancelled",
                description="Operation cancelled by user. No messages were sent.",
                color=EMBED_COLOR_ERROR
            )
            await confirm_msg.edit(embed=embed)
            return
        
        # Start mass DM process
        processing_embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Sending Changelog...",
            description="Processing... This may take a while.",
            color=EMBED_COLOR_NORMAL
        )
        await confirm_msg.edit(embed=processing_embed)
        
        successful = 0
        failed = 0
        failed_owners = []
        
        # Create the DM message
        dm_embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Sprouts Changelog Update",
            description=message,
            color=EMBED_COLOR_NORMAL
        )
        dm_embed.add_field(
            name="Changelog Notice",
            value="This is an official changelog update from the Sprouts development team.",
            inline=False
        )
        dm_embed.set_footer(
            text="Sprouts Bot • Official Team Communication",
            icon_url=self.bot.user.display_avatar.url
        )
        dm_embed.timestamp = discord.utils.utcnow()
        
        # Collect unique owners and their servers
        unique_owners = {}  # {owner_id: {owner: User, guilds: [Guild1, Guild2, ...]}}
        
        for guild in self.bot.guilds:
            if guild.owner:
                owner_id = guild.owner.id
                if owner_id not in unique_owners:
                    unique_owners[owner_id] = {
                        'owner': guild.owner,
                        'guilds': []
                    }
                unique_owners[owner_id]['guilds'].append(guild)
            else:
                failed += 1
                failed_owners.append(f"{guild.name} (No owner found)")
        
        # Send one message per unique owner
        for owner_id, owner_data in unique_owners.items():
            owner = owner_data['owner']
            owned_guilds = owner_data['guilds']
            
            try:
                await owner.send(embed=dm_embed)
                successful += 1
                server_names = ", ".join([guild.name for guild in owned_guilds])
                logger.info(f"Changelog sent to {owner} (Owner of {len(owned_guilds)} servers: {server_names})")
                
                # Rate limiting - wait a bit between sends
                await asyncio.sleep(1)
                
            except discord.Forbidden:
                failed += 1
                server_names = ", ".join([guild.name for guild in owned_guilds])
                failed_owners.append(f"{owner.display_name} ({len(owned_guilds)} servers: {server_names}) - DMs disabled")
                logger.warning(f"Failed to send changelog to {owner} (Owner of {len(owned_guilds)} servers) - DMs disabled")
            except discord.HTTPException as e:
                failed += 1
                server_names = ", ".join([guild.name for guild in owned_guilds])
                failed_owners.append(f"{owner.display_name} ({len(owned_guilds)} servers: {server_names}) - Error: {str(e)}")
                logger.error(f"Failed to send changelog to {owner} (Owner of {len(owned_guilds)} servers) - Error: {e}")
            except Exception as e:
                failed += 1
                server_names = ", ".join([guild.name for guild in owned_guilds])
                failed_owners.append(f"{owner.display_name} ({len(owned_guilds)} servers) - Unexpected error")
                logger.error(f"Unexpected error sending changelog to {owner} (Owner of {len(owned_guilds)} servers): {e}")
        
        # Results embed
        results_embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Changelog Complete",
            color=EMBED_COLOR_NORMAL if successful > 0 else EMBED_COLOR_ERROR
        )
        
        results_embed.add_field(
            name=f"{SPROUTS_CHECK} Successful",
            value=f"{successful} messages sent",
            inline=True
        )
        results_embed.add_field(
            name=f"{SPROUTS_ERROR} Failed", 
            value=f"{failed} messages failed",
            inline=True
        )
        results_embed.add_field(
            name=f"{SPROUTS_WARNING} Success Rate",
            value=f"{(successful/(successful+failed)*100):.1f}%" if (successful+failed) > 0 else "0%",
            inline=True
        )
        
        if failed_owners and len(failed_owners) <= 10:
            failed_text = "\n".join(failed_owners[:10])
            if len(failed_owners) > 10:
                failed_text += f"\n... and {len(failed_owners) - 10} more"
            results_embed.add_field(
                name="Failed Recipients",
                value=f"```{failed_text}```",
                inline=False
            )
        elif failed_owners:
            results_embed.add_field(
                name="Failed Recipients",
                value=f"Too many to display ({len(failed_owners)} failed)",
                inline=False
            )
        
        results_embed.set_footer(text=f"Changelog executed by {ctx.author.display_name}")
        results_embed.timestamp = discord.utils.utcnow()
        
        await confirm_msg.edit(embed=results_embed)
        logger.info(f"Changelog completed: {successful} successful, {failed} failed - Executed by {ctx.author}")

    @commands.command(name="resetdata", description="Complete bot data reset (DANGER)", hidden=True)
    @commands.is_owner()
    async def reset_data(self, ctx, confirmation: str = None):
        """Clear ALL bot data and cache (Owner Only)"""
        if confirmation != "CONFIRM_RESET":
            embed = discord.Embed(
                title="Complete Bot Data Reset",
                description=(
                    "**This will permanently delete all:**\n\n"
                    "All reminder data\n"
                    "All sticky message configurations\n"
                    "All auto-responder data\n"
                    "All embed templates\n"
                    "All ticket system data\n"
                    "All guild settings and prefixes\n"
                    "All logging configurations\n"
                    "Server stats configurations\n"
                    "Global cooldown settings\n"
                    "Bot memory cache\n\n"
                    "**This action cannot be undone.**\n\n"
                    "To confirm, use:\n`s.resetdata CONFIRM_RESET`"
                ),
                color=EMBED_COLOR_ERROR
            )
            embed.set_footer(text="This command is restricted to bot owner only")
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        try:
            # Send initial warning
            embed = discord.Embed(
                title="Bot Data Reset in Progress",
                description="**Clearing all bot data and cache...**\n\n*This will take a few moments...*",
                color=EMBED_COLOR_ERROR
            )
            warning_msg = await ctx.reply(embed=embed, mention_author=False)
            
            # Wait 3 seconds for dramatic effect and safety
            await asyncio.sleep(3)
            
            deleted_files = []
            cleared_caches = []
            
            # Define all data files to delete
            data_files = [
                "src/data/reminders.json",
                "src/data/reminder_counter.json", 
                "src/data/stickies.json",
                "src/data/autoresponders.json",
                "src/data/embeds.json",
                "src/data/tickets.json",
                "src/data/guild_settings.json",
                "src/data/command_logs.json",
                "src/data/dm_logs.json", 
                "src/data/guild_logs.json",
                "config/global_cooldown.json"
            ]
            
            # Delete all data files
            for file_path in data_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_files.append(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")
            
            # Clear in-memory caches for all cogs
            for cog_name, cog in self.bot.cogs.items():
                try:
                    # Clear reminders cache
                    if hasattr(cog, 'reminders'):
                        cog.reminders.clear()
                        cleared_caches.append(f"{cog_name}.reminders")
                    
                    # Clear sticky messages cache
                    if hasattr(cog, 'stickies'):
                        cog.stickies.clear()
                        cleared_caches.append(f"{cog_name}.stickies")
                    
                    # Clear auto-responders cache
                    if hasattr(cog, 'autoresponders'):
                        cog.autoresponders.clear()
                        cleared_caches.append(f"{cog_name}.autoresponders")
                    
                    # Clear embed templates cache
                    if hasattr(cog, 'embeds'):
                        cog.embeds.clear()
                        cleared_caches.append(f"{cog_name}.embeds")
                    
                    # Clear tickets cache
                    if hasattr(cog, 'tickets'):
                        cog.tickets.clear()
                        cleared_caches.append(f"{cog_name}.tickets")
                    
                    # Clear guild settings cache
                    if hasattr(cog, 'guild_settings'):
                        cog.guild_settings.clear()
                        cleared_caches.append(f"{cog_name}.guild_settings")
                    
                    # Clear message counts
                    if hasattr(cog, 'message_counts'):
                        cog.message_counts.clear()
                        cleared_caches.append(f"{cog_name}.message_counts")
                    
                    # Reset global cooldown
                    if hasattr(cog, 'global_cooldown'):
                        cog.global_cooldown.remove_cooldown()
                        cleared_caches.append(f"{cog_name}.global_cooldown")
                        
                except Exception as e:
                    logger.error(f"Failed to clear cache for {cog_name}: {e}")
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Update with completion status
            embed = discord.Embed(
                title="Bot Data Reset Completed",
                description=(
                    "**Complete data reset successful!**\n\n"
                    f"**Files Deleted:** {len(deleted_files)}\n"
                    f"**Caches Cleared:** {len(cleared_caches)}\n\n"
                    "**Deleted Files:**\n"
                    f"```\n{chr(10).join(deleted_files) if deleted_files else 'None'}```\n\n"
                    "**Cleared Caches:**\n"
                    f"```\n{chr(10).join(cleared_caches) if cleared_caches else 'None'}```\n\n"
                    "**Bot restart recommended for complete reset**"
                ),
                color=EMBED_COLOR_SUCCESS
            )
            embed.set_footer(text=f"Data reset executed by {ctx.author.display_name}")
            embed.timestamp = discord.utils.utcnow()
            
            await warning_msg.edit(embed=embed)
            
            logger.critical(f"COMPLETE DATA RESET executed by {ctx.author} - ALL DATA DELETED")
            
        except Exception as e:
            logger.error(f"Error during data reset: {e}")
            embed = discord.Embed(
                title="Data Reset Failed",
                description=f"Failed to complete data reset: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="listdata", description="List data files for users or guilds", hidden=True)
    @commands.is_owner()
    async def list_data_files(self, ctx, data_type: str = None, *, identifier: str = None):
        """
        List data files for specific users or guilds
        
        Usage:
        - listdata user <user_id> - List all data files for a specific user
        - listdata guild <guild_id> - List all data files for a specific guild
        - listdata all - List all data directories and file counts
        """
        try:
            if not data_type:
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} List Data Files",
                    description="List data files for users or guilds.",
                    color=EMBED_COLOR_NORMAL
                )
                embed.add_field(
                    name="Usage Examples:",
                    value="```\nlistdata user 123456789 - List all files for user\n"
                          "listdata guild 987654321 - List all files for guild\n"
                          "listdata all - List all data directories```",
                    inline=False
                )
                embed.set_footer(text="Data inspection tool")
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            base_paths = ["src/data", "config"]
            
            if data_type.lower() == "all":
                # List all data directories and file counts
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} All Data Overview",
                    description="Overview of all data files and directories:",
                    color=EMBED_COLOR_NORMAL
                )
                
                total_files = 0
                for base_path in base_paths:
                    if os.path.exists(base_path):
                        files_info = []
                        dir_count = 0
                        file_count = 0
                        
                        for root, dirs, files in os.walk(base_path):
                            dir_count += len(dirs)
                            file_count += len(files)
                            total_files += len(files)
                            
                            if files:
                                rel_path = os.path.relpath(root, base_path)
                                if rel_path == ".":
                                    rel_path = "root"
                                files_info.append(f"**{rel_path}**: {len(files)} files")
                        
                        if files_info:
                            embed.add_field(
                                name=f"{base_path.title()} Directory ({file_count} files, {dir_count} dirs)",
                                value="\n".join(files_info[:10]) + ("\n..." if len(files_info) > 10 else ""),
                                inline=False
                            )
                
                embed.add_field(
                    name="Summary",
                    value=f"**Total Files:** {total_files}\n**Data Locations:** {', '.join(base_paths)}",
                    inline=False
                )
                
            elif data_type.lower() == "user":
                if not identifier:
                    await ctx.reply("Please provide a user ID.", mention_author=False)
                    return
                
                user_files = []
                
                # Check various data files for user data
                data_files = [
                    "src/data/reminders.json",
                    "src/data/tickets.json",
                    "src/data/embed_builder.json"
                ]
                
                for file_path in data_files:
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                                if identifier in data:
                                    user_files.append(f"✅ {os.path.basename(file_path)} - Has data")
                                else:
                                    user_files.append(f"❌ {os.path.basename(file_path)} - No data")
                        except:
                            user_files.append(f"⚠️ {os.path.basename(file_path)} - Error reading")
                    else:
                        user_files.append(f"❌ {os.path.basename(file_path)} - File not found")
                
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} User Data Files",
                    description=f"Data files for User ID: `{identifier}`",
                    color=EMBED_COLOR_NORMAL
                )
                
                if user_files:
                    embed.add_field(
                        name="Data Files Status",
                        value="\n".join(user_files),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Result",
                        value="No data files found for this user.",
                        inline=False
                    )
                    
            elif data_type.lower() == "guild":
                if not identifier:
                    await ctx.reply("Please provide a guild ID.", mention_author=False)
                    return
                
                guild_files = []
                guild_path = f"config/guild_{identifier}"
                
                # Check guild-specific directory
                if os.path.exists(guild_path):
                    for root, dirs, files in os.walk(guild_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, guild_path)
                            file_size = os.path.getsize(file_path)
                            guild_files.append(f"📄 {rel_path} ({file_size} bytes)")
                
                # Check other data files for guild data
                data_files = [
                    "src/data/autoresponders.json",
                    "src/data/sticky_messages.json"
                ]
                
                for file_path in data_files:
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                                if identifier in data:
                                    guild_files.append(f"✅ {os.path.basename(file_path)} - Has data")
                                else:
                                    guild_files.append(f"❌ {os.path.basename(file_path)} - No data")
                        except:
                            guild_files.append(f"⚠️ {os.path.basename(file_path)} - Error reading")
                
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Guild Data Files",
                    description=f"Data files for Guild ID: `{identifier}`",
                    color=EMBED_COLOR_NORMAL
                )
                
                if guild_files:
                    embed.add_field(
                        name="Data Files",
                        value="\n".join(guild_files[:15]) + ("\n..." if len(guild_files) > 15 else ""),
                        inline=False
                    )
                    embed.add_field(
                        name="Summary",
                        value=f"**Total Files:** {len([f for f in guild_files if f.startswith('📄')])}\n"
                              f"**Guild Directory:** `{guild_path}`",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Result",
                        value="No data files found for this guild.",
                        inline=False
                    )
            else:
                await ctx.reply("Invalid data type. Use: `user`, `guild`, or `all`", mention_author=False)
                return
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error in listdata command: {e}")
            await ctx.reply("An error occurred while listing data files.", mention_author=False)

    @commands.command(name="deletedata", description="Safely delete specific user data", hidden=True)
    @commands.is_owner()
    async def delete_user_data(self, ctx, data_type: str = None, *, identifier: str = None):
        """
        Safely delete specific user data without bulk deletion risks
        
        Usage:
        - deletedata list - Show available data types
        - deletedata user <user_id> - Delete all data for a specific user
        - deletedata guild <guild_id> - Delete all data for a specific guild
        - deletedata tickets <user_id> - Delete tickets for a specific user
        - deletedata reminders <user_id> - Delete reminders for a specific user
        - deletedata autoresponder <guild_id> <trigger> - Delete specific autoresponder
        """
        try:
            if not data_type:
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} Delete User Data",
                    description="Please specify a data type and identifier.",
                    color=EMBED_COLOR_WARNING
                )
                embed.add_field(
                    name="Usage Examples:",
                    value="```\ndeletedata list - Show available data types\n"
                          "deletedata user 123456789 - Delete all data for user\n"
                          "deletedata guild 987654321 - Delete all data for guild\n"
                          "deletedata tickets 123456789 - Delete user tickets\n"
                          "deletedata reminders 123456789 - Delete user reminders```",
                    inline=False
                )
                embed.set_footer(text="Safe deletion - no bulk operations")
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            if data_type.lower() == "list":
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Available Data Types",
                    description="Safe data deletion options:",
                    color=EMBED_COLOR_NORMAL
                )
                embed.add_field(
                    name="Data Types:",
                    value="```\nuser <user_id> - All data for specific user\n"
                          "guild <guild_id> - All data for specific guild\n"
                          "tickets <user_id> - User's ticket data\n"
                          "reminders <user_id> - User's reminders\n"
                          "autoresponder <guild_id> <trigger> - Specific autoresponder```",
                    inline=False
                )
                embed.add_field(
                    name="Safety Features:",
                    value="• No bulk deletion\n• Specific targeting only\n• Confirmation required\n• Detailed logging",
                    inline=False
                )
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            if not identifier:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Missing Identifier",
                    description=f"Please specify an identifier for data type: {data_type}",
                    color=EMBED_COLOR_ERROR
                )
                embed.timestamp = discord.utils.utcnow()
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            # Confirmation embed
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Confirm Data Deletion",
                description=f"**Data Type:** {data_type}\n**Identifier:** {identifier}\n\n"
                           "**⚠️ This action cannot be undone!**\n\n"
                           "React with ✅ to confirm or ❌ to cancel.",
                color=EMBED_COLOR_WARNING
            )
            embed.set_footer(text="You have 30 seconds to confirm")
            embed.timestamp = discord.utils.utcnow()
            
            confirm_msg = await ctx.reply(embed=embed, mention_author=False)
            await confirm_msg.add_reaction("✅")
            await confirm_msg.add_reaction("❌")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Operation Cancelled",
                    description="Data deletion cancelled due to timeout.",
                    color=EMBED_COLOR_ERROR
                )
                embed.timestamp = discord.utils.utcnow()
                await confirm_msg.edit(embed=embed)
                return
            
            if str(reaction.emoji) == SPROUTS_ERROR:
                embed = discord.Embed(
                    title="Operation Cancelled",
                    description="Data deletion cancelled by user.",
                    color=EMBED_COLOR_ERROR
                )
                embed.timestamp = discord.utils.utcnow()
                await confirm_msg.edit(embed=embed)
                return
            
            # Process deletion based on data type
            deleted_items = []
            
            if data_type.lower() == "user":
                user_id = identifier
                
                # Delete user reminders
                reminders_file = Path("config/reminders.json")
                if reminders_file.exists():
                    try:
                        with open(reminders_file, 'r') as f:
                            reminders = json.load(f)
                        
                        original_count = len(reminders.get(user_id, {}))
                        if user_id in reminders:
                            del reminders[user_id]
                            deleted_items.append(f"Reminders: {original_count} items")
                        
                        with open(reminders_file, 'w') as f:
                            json.dump(reminders, f, indent=2)
                    except Exception as e:
                        logger.error(f"Error deleting user reminders: {e}")
                
                # Delete user tickets
                for guild_folder in Path("config").glob("guild_*"):
                    tickets_file = guild_folder / "tickets.json"
                    if tickets_file.exists():
                        try:
                            with open(tickets_file, 'r') as f:
                                tickets = json.load(f)
                            
                            user_tickets = [t for t in tickets if tickets[t].get('creator_id') == user_id]
                            for ticket_id in user_tickets:
                                del tickets[ticket_id]
                            
                            if user_tickets:
                                deleted_items.append(f"Tickets: {len(user_tickets)} items from {guild_folder.name}")
                                with open(tickets_file, 'w') as f:
                                    json.dump(tickets, f, indent=2)
                        except Exception as e:
                            logger.error(f"Error deleting user tickets from {guild_folder}: {e}")
            
            elif data_type.lower() == "guild":
                guild_id = identifier
                guild_folder = Path(f"config/guild_{guild_id}")
                
                if guild_folder.exists():
                    try:
                        import shutil
                        shutil.rmtree(guild_folder)
                        deleted_items.append(f"Guild folder: {guild_folder.name}")
                    except Exception as e:
                        logger.error(f"Error deleting guild folder: {e}")
            
            elif data_type.lower() == "tickets":
                user_id = identifier
                ticket_count = 0
                
                for guild_folder in Path("config").glob("guild_*"):
                    tickets_file = guild_folder / "tickets.json"
                    if tickets_file.exists():
                        try:
                            with open(tickets_file, 'r') as f:
                                tickets = json.load(f)
                            
                            user_tickets = [t for t in tickets if tickets[t].get('creator_id') == user_id]
                            for ticket_id in user_tickets:
                                del tickets[ticket_id]
                                ticket_count += 1
                            
                            if user_tickets:
                                with open(tickets_file, 'w') as f:
                                    json.dump(tickets, f, indent=2)
                        except Exception as e:
                            logger.error(f"Error deleting user tickets from {guild_folder}: {e}")
                
                if ticket_count > 0:
                    deleted_items.append(f"Tickets: {ticket_count} items")
            
            elif data_type.lower() == "reminders":
                user_id = identifier
                reminders_file = Path("config/reminders.json")
                
                if reminders_file.exists():
                    try:
                        with open(reminders_file, 'r') as f:
                            reminders = json.load(f)
                        
                        original_count = len(reminders.get(user_id, {}))
                        if user_id in reminders:
                            del reminders[user_id]
                            deleted_items.append(f"Reminders: {original_count} items")
                        
                        with open(reminders_file, 'w') as f:
                            json.dump(reminders, f, indent=2)
                    except Exception as e:
                        logger.error(f"Error deleting user reminders: {e}")
            
            # Success embed
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Data Deletion Complete",
                description=f"Successfully deleted data for: **{identifier}**",
                color=EMBED_COLOR_NORMAL
            )
            
            if deleted_items:
                embed.add_field(
                    name="Deleted Items:",
                    value="\n".join(f"• {item}" for item in deleted_items),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Result:",
                    value="No data found for the specified identifier.",
                    inline=False
                )
            
            embed.add_field(
                name="Safety Log:",
                value=f"Operation: {data_type} deletion\nTarget: {identifier}\nExecuted by: {ctx.author} ({ctx.author.id})",
                inline=False
            )
            embed.timestamp = discord.utils.utcnow()
            await confirm_msg.edit(embed=embed)
            
            # Log the deletion
            logger.warning(f"TARGETED DATA DELETION: {data_type} for {identifier} by {ctx.author} ({ctx.author.id})")
            
        except Exception as e:
            logger.error(f"Error during targeted data deletion: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Deletion Failed",
                description=f"Failed to delete data: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="clearslash", description="Clear all slash commands", hidden=True)
    @commands.is_owner()
    async def clear_slash_commands(self, ctx):
        """Clear all slash commands from Discord"""
        embed = discord.Embed(
            title="Clearing Slash Commands",
            description="Removing all slash commands from Discord...",
            color=EMBED_COLOR_NORMAL
        )
        msg = await ctx.reply(embed=embed, mention_author=False)
        
        try:
            # Clear global slash commands
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync()
            
            # Clear guild-specific slash commands for all guilds
            for guild in self.bot.guilds:
                self.bot.tree.clear_commands(guild=guild)
                await self.bot.tree.sync(guild=guild)
            
            embed = discord.Embed(
                title="Slash Commands Cleared",
                description="All slash commands have been removed from Discord. Changes may take up to 1 hour to fully propagate.",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Cleared From:",
                value=f"• Global commands\n• {len(self.bot.guilds)} guild-specific commands",
                inline=False
            )
            await msg.edit(embed=embed)
            logger.info(f"Slash commands cleared by {ctx.author}")
            
        except Exception as e:
            embed = discord.Embed(
                title="Error Clearing Slash Commands",
                description=f"Failed to clear slash commands: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await msg.edit(embed=embed)
            logger.error(f"Error clearing slash commands: {e}")

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(DevOnly(bot))
    logger.info("Developer-only commands setup completed")

async def setup_devonly(bot):
    """Alternative setup function name for compatibility"""
    await setup(bot)
