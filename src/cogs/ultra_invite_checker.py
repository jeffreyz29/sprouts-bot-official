"""
Ultra-Fast Invite Checker with Instant Results
Creates the exact format from your screenshot with author pings
"""

import discord
from discord.ext import commands
import asyncio
import time
import json
import os
from typing import List, Dict, Optional, Tuple
from src.emojis import SPROUTS_CHECK, SPROUTS_WARNING, SPROUTS_ERROR
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
import re

class UltraInviteChecker(commands.Cog):
    """Lightning-fast invite checker with instant channel listing"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "config/ultra_invite_checker.json"
        self.config = {}
        self.invite_pattern = re.compile(r'(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li|com)/(?:invite/)?|discordapp\.com/invite/)([a-zA-Z0-9\-]{2,32})')
        self.load_config()
    
    def load_config(self):
        """Load configuration"""
        if not os.path.exists("config"):
            os.makedirs("config")
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}
        
        # Ensure guild configs exist
        for guild_id in [str(guild.id) for guild in self.bot.guilds]:
            if guild_id not in self.config:
                self.config[guild_id] = {
                    "scan_categories": [],
                    "ignore_channels": [],
                    "invite_check_channel": None
                }
        self.save_config()
    
    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def ensure_guild_config(self, guild_id: str):
        """Ensure guild configuration exists"""
        if guild_id not in self.config:
            self.config[guild_id] = {
                "scan_categories": [],
                "ignore_channels": [],
                "invite_check_channel": None
            }
            self.save_config()
        return self.config[guild_id]
    
    async def validate_invite_instant(self, invite_code: str) -> Tuple[bool, Optional[Dict]]:
        """Fast invite validation with smart rate limiting"""
        try:
            # Add small delay to avoid rate limits
            await asyncio.sleep(0.1)
            invite = await self.bot.fetch_invite(invite_code)
            if invite and invite.guild:
                return True, {
                    "guild_name": invite.guild.name,
                    "member_count": getattr(invite, 'approximate_member_count', 0),
                    "guild_id": invite.guild.id
                }
            return False, None
        except discord.HTTPException:
            # Rate limited or invalid
            return False, None
        except:
            return False, None
    
    def extract_invites(self, message_content: str) -> List[str]:
        """Extract Discord invites from message content"""
        matches = self.invite_pattern.findall(message_content)
        return list(set(matches))
    
    # Configuration commands (same as original)
    @commands.command(name="category")
    @commands.has_permissions(administrator=True)
    async def category_command(self, ctx, action: str = None, category_id: int = None):
        """Manage categories for invite checking"""
        guild_id = str(ctx.guild.id)
        guild_config = self.ensure_guild_config(guild_id)
        
        if not action:
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Category Management",
                description="Manage categories for invite scanning",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Available Actions",
                value=f"`{ctx.prefix}category add [categoryID]` - Add category to scan\n"
                      f"`{ctx.prefix}category remove [categoryID]` - Remove category\n"
                      f"`{ctx.prefix}category list` - List configured categories",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        if action.lower() == "add":
            if not category_id:
                await ctx.reply(f"{SPROUTS_WARNING} Please specify a category ID to add.", mention_author=False)
                return
            
            category = ctx.guild.get_channel(category_id)
            if not category or not isinstance(category, discord.CategoryChannel):
                await ctx.reply(f"{SPROUTS_WARNING} Invalid category ID or category not found.", mention_author=False)
                return
            
            scan_categories = guild_config.get("scan_categories", [])
            if category_id in scan_categories:
                await ctx.reply(f"{SPROUTS_WARNING} Category **{category.name}** is already in the scan list.", mention_author=False)
                return
            
            scan_categories.append(category_id)
            self.config[guild_id]["scan_categories"] = scan_categories
            self.save_config()
            await ctx.reply(f"{SPROUTS_CHECK} Added category **{category.name}** to scan list.", mention_author=False)
        
        elif action.lower() == "remove":
            if not category_id:
                await ctx.reply(f"{SPROUTS_WARNING} Please specify a category ID to remove.", mention_author=False)
                return
            
            scan_categories = guild_config.get("scan_categories", [])
            if category_id not in scan_categories:
                await ctx.reply(f"{SPROUTS_WARNING} Category ID {category_id} is not in the scan list.", mention_author=False)
                return
            
            scan_categories.remove(category_id)
            self.config[guild_id]["scan_categories"] = scan_categories
            self.save_config()
            
            category = ctx.guild.get_channel(category_id)
            category_name = category.name if category else f"ID: {category_id}"
            await ctx.reply(f"{SPROUTS_CHECK} Removed category **{category_name}** from scan list.", mention_author=False)
        
        elif action.lower() == "list":
            scan_categories = guild_config.get("scan_categories", [])
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Configured Scan Categories",
                color=EMBED_COLOR_NORMAL
            )
            
            if scan_categories:
                category_list = []
                for category_id in scan_categories:
                    category = ctx.guild.get_channel(category_id)
                    if category:
                        channel_count = len(category.channels)
                        category_list.append(f"**{category.name}** - {channel_count} channels (ID: {category_id})")
                    else:
                        category_list.append(f"Unknown Category (ID: {category_id})")
                
                embed.add_field(
                    name=f"Categories ({len(scan_categories)})",
                    value="\n".join(category_list),
                    inline=False
                )
            else:
                embed.description = "No categories configured for scanning."
            
            await ctx.reply(embed=embed, mention_author=False)
        else:
            await ctx.reply(f"{SPROUTS_WARNING} Invalid action. Use `add`, `remove`, or `list`.", mention_author=False)

    @commands.command(name="ids")
    @commands.has_permissions(administrator=True)
    async def list_category_ids(self, ctx):
        """Display all available category IDs in the server"""
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Available Categories",
            description="All categories in this server with their IDs",
            color=EMBED_COLOR_NORMAL
        )
        
        categories = [category for category in ctx.guild.categories]
        
        if categories:
            category_info = []
            for category in categories[:25]:  # Discord embed limit
                channel_count = len(category.channels)
                category_info.append(f"**{category.name}** - {channel_count} channels\nID: `{category.id}`")
            
            embed.add_field(
                name=f"Categories ({len(categories)})",
                value="\n\n".join(category_info),
                inline=False
            )
            
            if len(categories) > 25:
                embed.set_footer(text=f"Showing first 25 categories. Total: {len(categories)}")
        else:
            embed.description = "No categories found in this server."
        
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="checkchannel")
    @commands.has_permissions(administrator=True)
    async def set_check_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the invite check channel where scan results will be posted"""
        guild_id = str(ctx.guild.id)
        
        if not channel:
            current_channel_id = self.config.get(guild_id, {}).get("invite_check_channel")
            if current_channel_id:
                current_channel = ctx.guild.get_channel(current_channel_id)
                if current_channel:
                    embed = discord.Embed(
                        title=f"{SPROUTS_CHECK} Current Check Channel",
                        description=f"Invite check results are posted to {current_channel.mention}",
                        color=EMBED_COLOR_NORMAL
                    )
                else:
                    embed = discord.Embed(
                        title=f"{SPROUTS_WARNING} Invalid Check Channel",
                        description="The configured check channel no longer exists. Please set a new one.",
                        color=EMBED_COLOR_ERROR
                    )
            else:
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} No Check Channel Set",
                    description=f"Use `{ctx.prefix}checkchannel #channel` to set the invite check channel.",
                    color=EMBED_COLOR_ERROR
                )
            
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        self.config[guild_id]["invite_check_channel"] = channel.id
        self.save_config()
        await ctx.reply(f"{SPROUTS_CHECK} Set invite check channel to {channel.mention}.", mention_author=False)

    @commands.command(name="ignore")
    @commands.has_permissions(administrator=True)
    async def ignore_command(self, ctx, action: str = None, channel: discord.TextChannel = None):
        """Manage channel blacklist for invite checking"""
        guild_id = str(ctx.guild.id)
        guild_config = self.ensure_guild_config(guild_id)
        
        if not action:
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Channel Blacklist",
                description="Manage channels to ignore during invite scanning",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(
                name="Available Actions",
                value=f"`{ctx.prefix}ignore add #channel` - Add channel to blacklist\n"
                      f"`{ctx.prefix}ignore remove #channel` - Remove from blacklist\n"
                      f"`{ctx.prefix}ignore list` - List blacklisted channels",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        if action.lower() == "add":
            if not channel:
                await ctx.reply(f"{SPROUTS_WARNING} Please specify a channel to blacklist.", mention_author=False)
                return
            
            ignore_channels = guild_config.get("ignore_channels", [])
            if channel.id in ignore_channels:
                await ctx.reply(f"{SPROUTS_WARNING} Channel {channel.mention} is already blacklisted.", mention_author=False)
                return
            
            ignore_channels.append(channel.id)
            self.config[guild_id]["ignore_channels"] = ignore_channels
            self.save_config()
            await ctx.reply(f"{SPROUTS_CHECK} Added {channel.mention} to blacklist.", mention_author=False)
        
        elif action.lower() == "remove":
            if not channel:
                await ctx.reply(f"{SPROUTS_WARNING} Please specify a channel to remove from blacklist.", mention_author=False)
                return
            
            ignore_channels = guild_config.get("ignore_channels", [])
            if channel.id not in ignore_channels:
                await ctx.reply(f"{SPROUTS_WARNING} Channel {channel.mention} is not blacklisted.", mention_author=False)
                return
            
            ignore_channels.remove(channel.id)
            self.config[guild_id]["ignore_channels"] = ignore_channels
            self.save_config()
            await ctx.reply(f"{SPROUTS_CHECK} Removed {channel.mention} from blacklist.", mention_author=False)
        
        elif action.lower() == "list":
            ignore_channels = guild_config.get("ignore_channels", [])
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Blacklisted Channels",
                color=EMBED_COLOR_NORMAL
            )
            
            if ignore_channels:
                channel_list = []
                for channel_id in ignore_channels:
                    channel_obj = ctx.guild.get_channel(channel_id)
                    if channel_obj:
                        channel_list.append(f"{channel_obj.mention}")
                    else:
                        channel_list.append(f"Unknown Channel (ID: {channel_id})")
                
                embed.add_field(
                    name=f"Ignored Channels ({len(ignore_channels)})",
                    value="\n".join(channel_list),
                    inline=False
                )
            else:
                embed.description = "No channels are blacklisted."
            
            await ctx.reply(embed=embed, mention_author=False)
        else:
            await ctx.reply(f"{SPROUTS_WARNING} Invalid action. Use `add`, `remove`, or `list`.", mention_author=False)

    @commands.command(name="test")
    async def test_command(self, ctx):
        """Test if the bot is responding"""
        await ctx.reply("Bot is working! Ultra invite checker is ready.", mention_author=False)

    @commands.command(name="ultracheck")
    @commands.has_permissions(administrator=True)
    async def ultra_fast_check(self, ctx, limit: int = 20):
        """
        Ultra-fast invite checker with instant results and channel listings
        """
        guild_id = str(ctx.guild.id)
        guild_config = self.ensure_guild_config(guild_id)
        
        # Check if check channel is configured 
        check_channel_id = guild_config.get("invite_check_channel")
        if not check_channel_id:
            embed = discord.Embed(
                title="Setup Required",
                description=f"Please set up the invite checker first:\n\n"
                           f"**1.** `{ctx.prefix}checkchannel #channel` - Set check channel\n"
                           f"**2.** `{ctx.prefix}ids` - View category IDs\n"
                           f"**3.** `{ctx.prefix}category add [ID]` - Add categories\n"
                           f"**4.** `{ctx.prefix}ultracheck` - Run scan",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        scan_categories = guild_config.get("scan_categories", [])
        if not scan_categories:
            embed = discord.Embed(
                title="No Categories",
                description=f"No categories configured for scanning.\n\n"
                           f"Use `{ctx.prefix}ids` to see available categories\n"
                           f"Use `{ctx.prefix}category add [ID]` to add categories",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        start_time = time.time()
        
        # Get all channels from categories
        all_channels = []
        ignore_channels = guild_config.get("ignore_channels", [])
        
        for category_id in scan_categories:
            category = ctx.guild.get_channel(category_id)
            if category and isinstance(category, discord.CategoryChannel):
                for channel in category.channels:
                    if (isinstance(channel, discord.TextChannel) and 
                        channel.id not in ignore_channels and
                        channel.permissions_for(ctx.guild.me).read_message_history):
                        all_channels.append(channel)
        
        if not all_channels:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} No Valid Channels",
                description="No accessible text channels found in the configured categories.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # INSTANT concurrent scanning of all channels
        async def scan_channel_instantly(channel):
            try:
                channel_invites = []
                
                # Only scan most recent messages for speed - limit to 5 for rate limiting
                message_count = 0
                async for message in channel.history(limit=5):
                    message_count += 1
                    if any(pattern in message.content.lower() for pattern in ['discord.gg/', 'discord.com/invite/', 'discordapp.com/invite/']):
                        invites = self.extract_invites(message.content)
                        
                        # Limit to first 2 invites per channel to avoid rate limits
                        for invite_code in invites[:2]:
                            is_valid, invite_info = await self.validate_invite_instant(invite_code)
                            
                            invite_entry = {
                                "code": invite_code,
                                "valid": is_valid,
                                "server_name": invite_info.get("guild_name", "Unknown") if invite_info else "Invalid",
                                "member_count": invite_info.get("member_count", 0) if invite_info else 0,
                                "author": message.author,
                                "message_link": f"https://discord.com/channels/{ctx.guild.id}/{channel.id}/{message.id}"
                            }
                            
                            channel_invites.append(invite_entry)
                            
                            # Stop if we found enough invites
                            if len(channel_invites) >= 2:
                                break
                    
                    if len(channel_invites) >= 2:
                        break
                
                valid_invites = [inv for inv in channel_invites if inv["valid"]]
                invalid_invites = [inv for inv in channel_invites if not inv["valid"]]
                
                return {
                    "channel": channel,
                    "invites": channel_invites,
                    "valid_invites": valid_invites,
                    "invalid_invites": invalid_invites,
                    "valid_count": len(valid_invites),
                    "invalid_count": len(invalid_invites)
                }
            except:
                return {"channel": channel, "invites": [], "valid_count": 0, "status": "error"}
        
        # Process channels in smaller batches to avoid rate limits
        batch_size = 3  # Smaller batches to avoid rate limits
        results = []
        
        for i in range(0, len(all_channels), batch_size):
            batch = all_channels[i:i+batch_size]
            tasks = [scan_channel_instantly(channel) for channel in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Small delay between batches
            if i + batch_size < len(all_channels):
                await asyncio.sleep(0.5)
        
        scan_time = time.time() - start_time
        
        # Process results
        channels_with_invites = [r for r in results if len(r["invites"]) > 0]
        total_channels = len(all_channels)
        total_valid = sum(r["valid_count"] for r in results)
        total_invalid = sum(r["invalid_count"] for r in results)
        total_invites = total_valid + total_invalid
        
        # EMBED 1: Clean Channel Listing
        embed1 = discord.Embed(
            title="Invite Check Results", 
            description=f"Checked {total_channels} recent messages: {scan_time:.1f}s",
            color=EMBED_COLOR_NORMAL
        )
        
        # Create clean channel listing
        channel_lines = []
        for result in channels_with_invites:
            channel = result["channel"]
            valid_count = result["valid_count"]
            invalid_count = result["invalid_count"]
            
            if valid_count > 0:
                # Get unique server names for valid invites
                valid_servers = list(set([inv["server_name"] for inv in result["valid_invites"]]))
                server_text = ", ".join(valid_servers[:2])
                if len(valid_servers) > 2:
                    server_text += f" +{len(valid_servers)-2} more"
                
                channel_lines.append(f"• {channel.mention} : {valid_count}/{valid_count + invalid_count} good {server_text}")
        
        if channel_lines:
            embed1.add_field(
                name="Check counts",
                value=f"Channels checked: {total_channels}\nInvites checked: {total_invites}",
                inline=True
            )
            
            embed1.add_field(
                name="Stats",
                value=f"• {total_valid}/{total_invites} good invites ({(total_valid/total_invites*100):.1f}%)\n• {total_invalid}/{total_invites} bad invites ({(total_invalid/total_invites*100):.1f}%)",
                inline=True
            )
            
            # Split channel listing into chunks
            chunk_size = 15
            for i in range(0, len(channel_lines), chunk_size):
                chunk = channel_lines[i:i+chunk_size]
                embed1.add_field(
                    name="",
                    value="\n".join(chunk),
                    inline=False
                )
        else:
            embed1.add_field(
                name="Results",
                value="No invites found in recent messages",
                inline=False
            )
        
        await ctx.send(embed=embed1)
        
        # EMBED 2: Invalid Invites with Author Pings
        channels_with_invalid = [r for r in results if r["invalid_count"] > 0]
        if channels_with_invalid:
            await asyncio.sleep(0.5)
            
            embed2 = discord.Embed(
                title="Issues Found",
                description=f"{total_invalid} invalid invites detected",
                color=EMBED_COLOR_ERROR
            )
            
            for result in channels_with_invalid[:5]:  # Top 5 problematic channels
                channel = result["channel"]
                invalid_list = []
                
                for invite in result["invalid_invites"][:3]:  # Top 3 invalid per channel
                    invalid_list.append(f"• {invite['author'].mention} `{invite['code']}`")
                
                if invalid_list:
                    embed2.add_field(
                        name=f"{channel.mention}",
                        value="\n".join(invalid_list) + (f"\n*...and {len(result['invalid_invites'])-3} more*" if len(result['invalid_invites']) > 3 else ""),
                        inline=False
                    )
            
            await ctx.send(embed=embed2)

async def setup(bot):
    """Setup function for the ultra invite checker cog"""
    await bot.add_cog(UltraInviteChecker(bot))
    print("Ultra invite checker cog loaded successfully")