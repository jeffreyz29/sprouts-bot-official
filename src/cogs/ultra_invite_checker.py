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
        """Fast invite validation like Hana bot"""
        try:
            # Use the exact same approach as Hana
            invite = await self.bot.fetch_invite(invite_code)
            if invite and invite.guild:
                return True, {
                    "guild_name": invite.guild.name,
                    "member_count": getattr(invite, 'approximate_member_count', 0),
                    "guild_id": invite.guild.id
                }
            return False, None
        except discord.NotFound:
            # Invalid/expired invite
            return False, None
        except discord.HTTPException:
            # Rate limited - treat as invalid for now
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

    @commands.command(name="cleanup")
    @commands.has_permissions(administrator=True)
    async def cleanup_ping_messages(self, ctx, limit: int = 50):
        """Clean up unwanted ping messages from the bot"""
        guild_id = str(ctx.guild.id)
        guild_config = self.ensure_guild_config(guild_id)
        
        scan_categories = guild_config.get("scan_categories", [])
        if not scan_categories:
            await ctx.reply("No categories configured to clean.", mention_author=False)
            return
        
        deleted_count = 0
        status_msg = await ctx.reply("🧹 Cleaning up unwanted ping messages...", mention_author=False)
        
        # Get all channels from categories
        all_channels = []
        for category_id in scan_categories:
            category = ctx.guild.get_channel(category_id)
            if category and isinstance(category, discord.CategoryChannel):
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        all_channels.append(channel)
        
        # Look for and delete the specific ping messages
        for channel in all_channels:
            try:
                async for message in channel.history(limit=limit):
                    if (message.author == self.bot.user and 
                        "Your invite" in message.content and 
                        "is invalid/expired" in message.content):
                        
                        await message.delete()
                        deleted_count += 1
            except:
                continue  # Skip channels we can't access
        
        await status_msg.edit(content=f"✅ Cleanup complete! Deleted {deleted_count} unwanted ping messages.")
        
        if deleted_count == 0:
            await status_msg.edit(content="✅ No unwanted ping messages found to delete.")

    @commands.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def view_settings(self, ctx):
        """View current ultra invite checker settings"""
        guild_id = str(ctx.guild.id)
        guild_config = self.ensure_guild_config(guild_id)
        
        # Simple text response instead of complex embed
        check_channel_id = guild_config.get("invite_check_channel")
        scan_categories = guild_config.get("scan_categories", [])
        ignore_channels = guild_config.get("ignore_channels", [])
        
        response = "**Ultra Invite Checker Settings:**\n\n"
        
        if check_channel_id:
            check_channel = ctx.guild.get_channel(check_channel_id)
            response += f"✅ Check Channel: {check_channel.mention if check_channel else 'Invalid'}\n"
        else:
            response += "❌ Check Channel: Not configured\n"
        
        response += f"📂 Scan Categories: {len(scan_categories)} configured\n"
        response += f"🚫 Ignored Channels: {len(ignore_channels)}\n\n"
        
        if check_channel_id and scan_categories:
            response += "🎯 **Status: Ready for ultracheck!**"
        else:
            missing = []
            if not check_channel_id:
                missing.append("check channel")
            if not scan_categories:
                missing.append("categories")
            response += f"⚠️ **Missing:** {', '.join(missing)}"
        
        await ctx.reply(response, mention_author=False)

    @commands.command(name="ultracheck")
    @commands.has_permissions(administrator=True)
    async def ultra_fast_check(self, ctx, limit: int = 20):
        """
        Ultra-fast invite checker with instant results and channel listings
        """
        guild_id = str(ctx.guild.id)
        guild_config = self.ensure_guild_config(guild_id)
        
        # Check setup without status messages - just start immediately
        check_channel_id = guild_config.get("invite_check_channel")
        if not check_channel_id:
            await ctx.reply("❌ Setup Required: Use `s.checkchannel #channel` first.", mention_author=False)
            return
        
        scan_categories = guild_config.get("scan_categories", [])
        if not scan_categories:
            await ctx.reply("❌ No Categories: Use `s.category add [ID]` to add them.", mention_author=False)
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
            await ctx.reply("❌ No accessible text channels found in the configured categories.", mention_author=False)
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
                                "message_link": f"https://discord.com/channels/{ctx.guild.id}/{channel.id}/{message.id}",
                                "channel": channel
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
        
        # SEND INDIVIDUAL CATEGORY EMBEDS (Hana-style with Sprouts touches)
        # Group results by category first
        category_results = {}
        for result in results:
            channel = result["channel"]
            if channel.category:
                category_name = channel.category.name
                if category_name not in category_results:
                    category_results[category_name] = []
                category_results[category_name].append(result)
        
        # Send embed for each category with channels
        for category_name, cat_results in category_results.items():
            category_lines = []
            
            for result in cat_results:
                channel = result["channel"]
                valid_count = result["valid_count"]
                invalid_count = result["invalid_count"]
                total_in_channel = valid_count + invalid_count
                
                if total_in_channel > 0:
                    if valid_count == total_in_channel:
                        # All good
                        emoji = "🟢"
                        status = "good"
                        # Get user count from first valid invite
                        user_count = 0
                        if result["valid_invites"]:
                            user_count = result["valid_invites"][0].get("member_count", 0)
                        category_lines.append(f"{emoji} {channel.mention} : {valid_count}/{total_in_channel} {status} `{user_count:,} Users`")
                    else:
                        # Some bad - ping authors of invalid invites
                        emoji = "🔴"
                        status = "bad"
                        category_lines.append(f"{emoji} {channel.mention} : {valid_count}/{total_in_channel} {status} `0 Users`")
                        
                        # Send ping messages for invalid invites in that channel
                        for invalid_invite in result["invalid_invites"]:
                            if invalid_invite.get("author"):
                                try:
                                    await channel.send(f"<@{invalid_invite['author'].id}> Your invite `{invalid_invite['code']}` is invalid/expired.")
                                except:
                                    pass  # Skip if we can't send message
                else:
                    # No invites found
                    category_lines.append(f"🔴 {channel.mention} : 0 found `0 Users`")
            
            # Only show categories with results
            if category_lines:
                embed = discord.Embed(
                    title=f"🌱 The {category_name} category",
                    description="\n".join(category_lines),
                    color=0x98FB98  # Light Sprouts green
                )
                embed.set_footer(text=f"🌱 Checked {limit} recent messages • {time.strftime('%b %d, %Y')}")
                await ctx.send(embed=embed)
        
        # FINAL SUMMARY EMBED (Hana-style with Sprouts touches)
        await asyncio.sleep(0.5)
        
        # Success completion message
        final_embed = discord.Embed(
            description="🌱 Invite check complete!",
            color=0x98FB98
        )
        await ctx.send(embed=final_embed)
        
        # Detailed stats like Hana
        if total_invites > 0:
            good_percent = (total_valid/total_invites) * 100
            bad_percent = (total_invalid/total_invites) * 100
            
            total_embed = discord.Embed(
                title="🌱 Sprouts check results",
                color=0x90EE90
            )
            
            total_embed.add_field(
                name="Check counts",
                value=f"📊 {total_channels} channels, {total_invites} invites",
                inline=True
            )
            
            total_embed.add_field(
                name="Stats",
                value=f"✅ {total_valid}/{total_invites} good ({good_percent:.1f}%)\n❌ {total_invalid}/{total_invites} bad ({bad_percent:.1f}%)",
                inline=True
            )
            
            total_embed.set_footer(text="🌱 Sprouts keeps your server healthy!")
            await ctx.send(embed=total_embed)

async def setup(bot):
    """Setup function for the ultra invite checker cog"""
    await bot.add_cog(UltraInviteChecker(bot))
    print("Ultra invite checker cog loaded successfully")