"""
Uncategorized Commands
Basic bot information and utility commands
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import time
from config import BOT_CONFIG, EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR, COMMAND_COOLDOWNS

logger = logging.getLogger(__name__)

class ShardsPaginationView(discord.ui.View):
    """Pagination view for shards server list"""
    
    def __init__(self, guilds, author, total_shards, current_shard, total_servers, total_users, bot):
        super().__init__(timeout=300)  # 5 minute timeout
        self.guilds = guilds
        self.author = author
        self.total_shards = total_shards
        self.current_shard = current_shard
        self.total_servers = total_servers
        self.total_users = total_users
        self.bot = bot
        self.current_page = 0
        self.per_page = 10
        self.max_pages = 1  # Single page for shard table
        self.message = None
        
        # Disable pagination buttons since we only have one page now
        self.next_page.disabled = True
        self.previous_page.disabled = True
        
    async def create_embed(self, page):
        """Create embed with shard statistics table"""
        # Build the shard table header
        description = "```\nShard - Latency - Servers - Members\n"
        description += "--------------------------------------\n"
        
        # For AutoShardedBot, get actual shard information
        if hasattr(self.guilds[0].me.bot, 'shards') and self.guilds[0].me.bot.shards:
            # Get shard statistics
            for shard_id, shard in self.guilds[0].me.bot.shards.items():
                # Count guilds and members for this shard
                shard_guilds = [g for g in self.guilds if g.shard_id == shard_id]
                guild_count = len(shard_guilds)
                member_count = sum(g.member_count for g in shard_guilds)
                
                # Get latency in milliseconds
                latency_ms = int(shard.latency * 1000)
                
                # Format the row
                description += f"{shard_id:4d} - {latency_ms:4d} ms - {guild_count:7,d} - {member_count:9,d}\n"
        else:
            # Single shard or no sharding
            latency_ms = int(self.guilds[0].me.bot.latency * 1000) if self.guilds else 0
            description += f"   0 - {latency_ms:4d} ms - {self.total_servers:7,d} - {self.total_users:9,d}\n"
        
        description += "```"
        
        embed = discord.Embed(
            title="Shard Information",
            description=description,
            color=0xc2ffe0
        )
        embed.set_thumbnail(url=self.guilds[0].me.display_avatar.url if self.guilds else None)
        
        # Add summary information
        embed.add_field(
            name="Summary",
            value=f"**Total Shards:** {self.total_shards}\n"
                  f"**Total Servers:** {self.total_servers:,}\n"
                  f"**Total Users:** {self.total_users:,}",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {self.author.display_name}", 
                        icon_url=self.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    async def interaction_check(self, interaction):
        """Only allow the command author to use buttons"""
        return interaction.user == self.author
    
    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.grey, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        self.current_page -= 1
        embed = await self.create_embed(self.current_page)
        
        # Update button states
        self.previous_page.disabled = (self.current_page == 0)
        self.next_page.disabled = (self.current_page == self.max_pages - 1)
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="▶ Next", style=discord.ButtonStyle.grey)
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
        pass

class Uncategorized(commands.Cog):
    """Uncategorized commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
    
    @commands.command(name="about", help="Show bot statistics, uptime, and system information")
    @commands.cooldown(1, COMMAND_COOLDOWNS.get('about', 5), commands.BucketType.user)
    async def about(self, ctx):
        """About command showing detailed bot information

        Usage: `{ctx.prefix}about`
        Shows bot uptime, server count, memory usage, framework info, and system specs

        Examples:
        - `{ctx.prefix}about` - View complete bot statistics and performance metrics

        Information shown:
        - Bot uptime since last restart
        - Server and user counts
        - Memory and system resource usage
        - Python and Discord.py versions
        - Operating system information
        """
        try:
            uptime_seconds = int(time.time() - self.start_time)
            uptime_hours = uptime_seconds // 3600
            uptime_minutes = (uptime_seconds % 3600) // 60
            uptime_seconds = uptime_seconds % 60
            
            embed = discord.Embed(
                title=f"About {self.bot.user.display_name}",
                description="Sprout is a versatile Discord bot built with Python and discord.py. Designed to enhance server management, it offers customizable commands, seamless ticket handling for APM portals, and tools that help your community stay organized and engaged.",
                color=EMBED_COLOR_NORMAL
            )
            
            # Get system info
            import psutil
            import platform
            
            # Memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            ram_usage_mb = memory_info.rss / 1024 / 1024
            
            # Create the grid layout as shown in image
            embed.add_field(name="Uptime", value=f"{uptime_hours:02d}:{uptime_minutes:02d}:{uptime_seconds:02d}", inline=True)
            embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
            embed.add_field(name="Users", value=str(len(self.bot.users)), inline=True)
            
            embed.add_field(name="Framework", value=f"discord.py {discord.__version__}", inline=True)
            embed.add_field(name="Python", value=f"{platform.python_version()}", inline=True)
            embed.add_field(name="OS", value=f"Linux {platform.release()}", inline=True)
            
            embed.add_field(name="RAM Usage", value=f"{ram_usage_mb:.2f} MB", inline=True)
            embed.add_field(name="Heap Usage", value=f"{(ram_usage_mb / 1024 * 100):.1f}%", inline=True)
            embed.add_field(name="Shard ID", value="0", inline=True)
            
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"About command used by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error in about command: {e}")
            await ctx.reply(
                "An error occurred while fetching bot information.",
                mention_author=False
            )
    
    @commands.command(name="invite", help="Get bot invite link and support server links")
    @commands.cooldown(1, COMMAND_COOLDOWNS.get('invite', 10), commands.BucketType.user)
    async def invite(self, ctx):
        """Invite command with bot invite link

        Usage: `{ctx.prefix}invite`
        Provides bot invite link with proper permissions and support server details

        Examples:
        - `{ctx.prefix}invite` - Add bot to your server with correct permissions setup

        Features:
        - Pre-configured permission set for full functionality
        - Support server access for help
        - Bot feature highlights and descriptions
        """
        try:
            # Generate invite URL with proper permissions
            permissions = discord.Permissions(
                read_messages=True,
                send_messages=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                add_reactions=True,
                use_external_emojis=True,
                manage_channels=True,
                manage_roles=True,
                manage_messages=True
            )
            
            invite_url = discord.utils.oauth_url(
                self.bot.user.id,
                permissions=permissions,
                scopes=['bot', 'applications.commands']
            )
            
            embed = discord.Embed(
                title="Invite Sprouts",
                description="Add Sprouts to your server for tickets, utilities, and more!",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="Bot Invite",
                value=f"[**Add to Your Server**]({invite_url})",
                inline=True
            )
            
            embed.add_field(
                name="Support Server",
                value="[**Get Help & Support**](https://discord.gg/45jND7kH9Q)",
                inline=True
            )
            
            embed.add_field(
                name="Key Features",
                value="• Complete ticket system\n"
                      "• Server utilities & info\n"
                      "• Custom embed builder",
                inline=False
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Invite command used by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error in invite command: {e}")
            await ctx.reply(
                "An error occurred while generating invite link.",
                mention_author=False
            )
    
    @commands.command(name="shards", help="Display bot shard information and latency")
    @commands.cooldown(1, COMMAND_COOLDOWNS.get('shards', 15), commands.BucketType.user)
    async def shards(self, ctx):
        """Shard information command with server list pagination

        Usage: `{ctx.prefix}shards`
        Shows current shard, total shards, and paginated server list with navigation

        Examples:
        - `{ctx.prefix}shards` - View bot's shard info and browse through all connected servers

        Information shown:
        - Current shard and total shard count
        - Server distribution across shards
        - Total users and servers
        - Interactive pagination for server browsing
        """
        try:
            # Calculate shard info
            if self.bot.shard_count and ctx.guild:
                current_shard = (ctx.guild.id >> 22) % self.bot.shard_count
                total_shards = self.bot.shard_count
            else:
                current_shard = 0
                total_shards = 1
            
            total_servers = len(self.bot.guilds)
            total_users = len(self.bot.users)
            
            # Create shard information view
            view = ShardsPaginationView(self.bot.guilds, ctx.author, total_shards, current_shard, total_servers, total_users, self.bot)
            embed = await view.create_embed(0)
            
            message = await ctx.reply(embed=embed, view=view, mention_author=False)
            view.message = message
            logger.info(f"Shards command used by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error in shards command: {e}")
            error_embed = discord.Embed(
                title="Error",
                description="An error occurred while fetching shard information.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=error_embed, mention_author=False)
    
    @commands.command(name="vote", help="Get voting links to support the bot")
    @commands.cooldown(1, COMMAND_COOLDOWNS.get('vote', 10), commands.BucketType.user)
    async def vote(self, ctx):
        """Vote command with voting links

        Usage: `{ctx.prefix}vote`
        Provides voting links for Top.gg and other bot lists to support development

        Examples:
        - `{ctx.prefix}vote` - Support the bot by voting every 12 hours on bot listing sites

        Features:
        - Direct links to voting platforms
        - Current bot statistics display
        - Information about voting benefits and frequency
        """
        try:
            embed = discord.Embed(
                title="Vote for sprouts beta",
                description="Thanks for wanting to support sprouts beta! Your votes help us grow and improve.",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="Top.gg",
                value="[**Vote Here**](https://top.gg/bot/980936828242788422)\n"
                      "*Vote every 12 hours*",
                inline=True
            )
            
            embed.add_field(
                name="Current Stats",
                value=f"**Servers:** {len(self.bot.guilds):,}\n"
                      f"**Users:** {len(self.bot.users):,}\n"
                      f"**Votes:** Coming Soon",
                inline=True
            )
            
            embed.add_field(
                name="Why Vote?",
                value="• Support bot development\n"
                      "• Help us reach more servers\n"
                      "• Future voting rewards",
                inline=True
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            logger.info(f"Vote command used by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error in vote command: {e}")
            await ctx.reply(
                "An error occurred while fetching vote links.",
                mention_author=False
            )

async def setup_uncategorized(bot):
    """Setup uncategorized commands for the bot"""
    await bot.add_cog(Uncategorized(bot))
    logger.info("Uncategorized commands setup completed")
