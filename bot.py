"""
Discord Bot Class - Separated from main.py
Contains the main DiscordBot class and configuration
"""

import asyncio
import logging
import discord
from discord.ext import commands
from config import BOT_CONFIG, EMBED_COLOR_ERROR, BOT_OWNER_ID
from src.emojis import SPROUTS_ERROR
from web_viewer import bot_stats

logger = logging.getLogger(__name__)

class DiscordBot(commands.AutoShardedBot):
    """Main Discord Bot Class with Sharding Support"""
    
    async def get_prefix(self, message):
        """Get custom prefix for each guild - supports both custom prefix and bot mentions"""
        # Always allow bot mentions as prefix
        base_prefixes = [BOT_CONFIG['prefix']]  # Default: s.
        
        # Add custom guild prefix if in a guild
        if message.guild:
            try:
                # Import guild_settings here to avoid circular imports
                from src.cogs.guild_settings import guild_settings
                guild_prefix = guild_settings.get_prefix(message.guild.id)
                if guild_prefix and guild_prefix != BOT_CONFIG['prefix']:
                    base_prefixes.append(guild_prefix)
            except:
                pass  # Use default if guild settings fail
        
        # Return prefixes + bot mentions
        return commands.when_mentioned_or(*base_prefixes)(self, message)
    
    def __init__(self, cluster_id=None, shard_ids=None, shard_count=None, total_clusters=None):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        # Store cluster info for multi-instance deployment
        self.cluster_id = cluster_id or 0
        self.total_clusters = total_clusters or 1
        
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            owner_id=BOT_OWNER_ID,
            shard_ids=shard_ids,
            shard_count=shard_count
        )
        
        # Track bot start time for uptime calculation
        self.start_time = discord.utils.utcnow()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Bot is starting up...")
        
        # Initialize data manager and create startup backup
        from src.data_manager import data_manager
        await data_manager.auto_backup_on_startup()
        
        # Initialize Replit persistence system for deployment protection
        from src.database.replit_persistence import replit_persistence
        await replit_persistence.initialize_persistence_system()
        
        # Verify data integrity and create defaults if needed
        integrity = data_manager.verify_data_integrity()
        missing_files = [name for name, valid in integrity.items() if not valid]
        if missing_files:
            logger.warning(f"Missing/corrupted data files: {missing_files}")
            data_manager.create_empty_defaults()
            logger.info("Created default configuration files")
        
        # Setup all cogs - removed custom replies and welcome system
        from src.cogs.uncategorized import setup_uncategorized
        from src.cogs.events import setup_events
        from src.cogs.ticket import setup_ticket_system
        from src.cogs.utilities import setup_utilities
        from src.cogs.help import setup_help
        from src.cogs.logger import setup_logger
        from src.cogs.embed_builder import setup as setup_embed_builder
        from src.cogs.dev_only import setup_devonly
        from src.cogs.autoresponders import setup as setup_autoresponders
        from src.cogs.reminders import setup_reminders
        from src.cogs.sticky_messages import setup_stickymessages
        from src.cogs.server_stats import setup_server_stats
        from src.cogs.dm_logging import setup_dm_logging
        from src.cogs.cmd_logging import setup_cmd_logging
        from src.cogs.feature_management import setup as setup_feature_management
        from src.cogs.persistence_commands import setup as setup_persistence_commands
        from src.cogs.cluster import setup as setup_cluster
        
        await setup_uncategorized(self)
        await setup_events(self)
        await setup_ticket_system(self)
        await setup_utilities(self)
        await setup_help(self)
        await setup_logger(self)
        await setup_embed_builder(self)
        await setup_devonly(self)
        await setup_autoresponders(self)
        await setup_reminders(self)
        await setup_stickymessages(self)
        await setup_server_stats(self)
        await setup_dm_logging(self)
        await setup_cmd_logging(self)
        await setup_feature_management(self)
        await setup_persistence_commands(self)
        await setup_cluster(self)
        
        # Add persistent views for ticket buttons after ticket system is loaded
        try:
            from src.cogs.ticket import TicketButtons, StaffPanel, TicketPanelView
            self.add_view(TicketButtons())
            self.add_view(StaffPanel())
            
            # Add persistent views for all existing ticket panels
            ticket_cog = self.get_cog('TicketSystem')
            if ticket_cog and hasattr(ticket_cog, 'panels_data'):
                for panel_id in ticket_cog.panels_data.keys():
                    self.add_view(TicketPanelView(panel_id))
        except Exception as e:
            logger.warning(f"Ticket views not available: {e}")
        
    async def global_check(self, ctx):
        """Global check that runs before every command"""
        logger.info(f"GLOBAL CHECK: Command '{ctx.command.name if ctx.command else 'unknown'}' from user {ctx.author} (ID: {ctx.author.id})")
        
        # Check feature flags for command availability
        if ctx.command:
            from src.feature_flags import feature_manager
            
            # Always allow developer commands for bot owner
            if ctx.author.id != self.owner_id:
                if not feature_manager.is_command_enabled(ctx.command.name):
                    # Silently ignore disabled commands
                    return False
        
        # Check maintenance mode first - only allow bot owner during maintenance
        devonly_cog = self.get_cog('DevOnly')
        if devonly_cog and devonly_cog.maintenance_mode:
            if ctx.author.id != BOT_OWNER_ID:
                # Log maintenance mode block for debugging
                logger.info(f"MAINTENANCE: Blocked command '{ctx.command.name if ctx.command else 'unknown'}' from user {ctx.author} (ID: {ctx.author.id})")
                # Silently ignore commands from non-owners during maintenance
                return False
            else:
                logger.info(f"MAINTENANCE: Allowed command '{ctx.command.name if ctx.command else 'unknown'}' from owner {ctx.author}")
        
        # Skip cooldown check for developer commands
        if ctx.command and ctx.command.name in ["devhelp", "cooldown", "maintenance"]:
            return True
        
        # Check global cooldown
        try:
            from src.cogs.dev_only import global_cooldown
            remaining_time = global_cooldown.check_cooldown(ctx.author.id)
        except:
            remaining_time = 0
        
        if remaining_time > 0:
            # User is on cooldown - using custom emoji
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Cooldown Active",
                description=f"You're on cooldown! Try again in **{remaining_time:.1f} seconds**.",
                color=EMBED_COLOR_ERROR
            )
            embed.set_footer(text=f"Global bot cooldown", icon_url=self.user.display_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return False
        
        # Update user's last command time
        try:
            from src.cogs.dev_only import global_cooldown
            global_cooldown.update_user_cooldown(ctx.author.id)
        except:
            pass
        return True
    
    async def on_message(self, message):
        """Process messages for commands with maintenance mode check"""
        if message.author.bot:
            return
        
        # Get command context
        ctx = await self.get_context(message)
        
        # Only process if it's actually a command
        if ctx.command:
            # Check maintenance mode BEFORE processing
            devonly_cog = self.get_cog('DevOnly')
            if devonly_cog and devonly_cog.maintenance_mode:
                if ctx.author.id != BOT_OWNER_ID:
                    logger.info(f"MAINTENANCE: Blocked '{ctx.command.name}' from {ctx.author}")
                    try:
                        await message.add_reaction(SPROUTS_ERROR)
                    except discord.HTTPException:
                        try:
                            pass
                        except discord.HTTPException:
                            pass
                    return
                else:
                    logger.info(f"MAINTENANCE: Allowed '{ctx.command.name}' from owner")
            
            # Process the command
            await self.process_commands(message)

    async def on_command_error(self, ctx, error):
        """Override Discord.py's default error handling completely"""
        # Let the events cog handle all errors
        pass
    
    async def on_ready(self):
        """Called when bot is ready and connected"""
        cluster_info = f" (Cluster {self.cluster_id})" if self.cluster_id is not None else ""
        shard_info = f" with {self.shard_count} shards" if self.shard_count else ""
        
        logger.info(f'{self.user} has connected to Discord{cluster_info}{shard_info}!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        if self.shard_count:
            logger.info(f'Shard IDs: {list(self.shards.keys()) if self.shards else "None"}')
        
        # Store bot user and guild count for web dashboard
        bot_stats.bot_user = self.user
        bot_stats.update_guild_count(len(self.guilds))
        
        # Start with clean presence
        logger.info("Bot started with clean presence - use setstatus/setactivity commands to customize")
    
    async def on_shard_ready(self, shard_id):
        """Called when a specific shard is ready"""
        guild_count = len([guild for guild in self.guilds if guild.shard_id == shard_id])
        cluster_info = f" [Cluster {self.cluster_id}]" if self.cluster_id is not None else ""
        logger.info(f'Shard {shard_id}{cluster_info} is ready! ({guild_count} guilds)')
    
    async def on_shard_connect(self, shard_id):
        """Called when a shard connects"""
        cluster_info = f" [Cluster {self.cluster_id}]" if self.cluster_id is not None else ""
        logger.info(f'Shard {shard_id}{cluster_info} connected')
    
    async def on_shard_disconnect(self, shard_id):
        """Called when a shard disconnects"""
        cluster_info = f" [Cluster {self.cluster_id}]" if self.cluster_id is not None else ""
        logger.warning(f'Shard {shard_id}{cluster_info} disconnected')
    
    async def on_shard_resumed(self, shard_id):
        """Called when a shard resumes"""
        cluster_info = f" [Cluster {self.cluster_id}]" if self.cluster_id is not None else ""
        logger.info(f'Shard {shard_id}{cluster_info} resumed')