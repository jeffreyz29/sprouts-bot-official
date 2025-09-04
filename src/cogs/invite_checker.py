"""
Invite Checker Cog for Sprouts Discord Bot
Scans channels for Discord invites and validates them automatically
"""

import discord
from discord.ext import commands
import asyncio
import re
import aiohttp
import time
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional, Tuple

# Import bot configuration and emojis
from src.emojis import SPROUTS_CHECK, SPROUTS_WARNING, SPROUTS_ERROR

# Define color constants
EMBED_COLOR_NORMAL = 0x2ecc71
EMBED_COLOR_ERROR = 0xe74c3c

class InviteChecker(commands.Cog):
    """Advanced invite validation system for Discord servers"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "config/invite_checker.json"
        self.invite_pattern = re.compile(r'(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discordapp\.com/invite)/([a-zA-Z0-9\-]{2,32})')
        self.scan_status = {}  # Track active scans
        self.load_config()
    
    def load_config(self):
        """Load invite checker configuration"""
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
                    "enabled": False,
                    "scan_categories": [],
                    "ignore_channels": [],
                    "auto_delete": False,
                    "invite_check_channel": None,
                    "allowed_servers": []
                }
        self.save_config()
    
    def save_config(self):
        """Save invite checker configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    async def validate_invite(self, invite_code: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate a Discord invite and return server information
        
        Args:
            invite_code: The invite code to validate
            
        Returns:
            Tuple of (is_valid, server_info)
        """
        try:
            # Try to get invite info using Discord API
            invite = await self.bot.fetch_invite(invite_code)
            
            if invite and invite.guild:
                return True, {
                    "guild_name": invite.guild.name,
                    "guild_id": invite.guild.id,
                    "member_count": getattr(invite, 'approximate_member_count', 0),
                    "presence_count": getattr(invite, 'approximate_presence_count', 0),
                    "channel_name": invite.channel.name if invite.channel else "Unknown",
                    "channel_type": str(invite.channel.type) if invite.channel else "Unknown",
                    "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
                    "max_uses": invite.max_uses,
                    "uses": invite.uses,
                    "temporary": invite.temporary
                }
            else:
                return False, None
                
        except discord.NotFound:
            return False, None
        except discord.HTTPException:
            return False, None
        except Exception as e:
            print(f"Error validating invite {invite_code}: {e}")
            return False, None
    
    def extract_invites(self, message_content: str) -> List[str]:
        """Extract all Discord invites from message content"""
        matches = self.invite_pattern.findall(message_content)
        return list(set(matches))  # Remove duplicates
    
    @commands.command(name="category")
    @commands.has_permissions(administrator=True)
    async def category_command(self, ctx, action: str = None, category_id: int = None):
        """
        Manage categories for invite checking
        
        Usage:
        - s.category add [categoryID] - Add category to scan list
        - s.category remove [categoryID] - Remove category from scan list
        - s.category list - List configured categories
        """
        guild_id = str(ctx.guild.id)
        guild_config = self.config.get(guild_id, {})
        
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
            
            # Check if category exists
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
        """
        Set the invite check channel where scan results will be posted
        
        Usage: s.checkchannel #channel
        """
        guild_id = str(ctx.guild.id)
        
        if not channel:
            # Show current check channel
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
        
        # Set new check channel
        self.config[guild_id]["invite_check_channel"] = channel.id
        self.save_config()
        
        await ctx.reply(f"{SPROUTS_CHECK} Set invite check channel to {channel.mention}.", mention_author=False)
    
    @commands.command(name="ignore")
    @commands.has_permissions(administrator=True)
    async def ignore_command(self, ctx, action: str = None, channel: discord.TextChannel = None):
        """
        Manage channel blacklist for invite checking
        
        Usage:
        - s.ignore add #channel - Add channel to blacklist
        - s.ignore remove #channel - Remove channel from blacklist  
        - s.ignore list - List blacklisted channels
        """
        guild_id = str(ctx.guild.id)
        guild_config = self.config.get(guild_id, {})
        
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
    
    @commands.command(name="check")
    @commands.has_permissions(administrator=True)
    async def manual_scan(self, ctx, limit: int = 10):
        """
        Start a manual invite scan (can only be run in the designated invite check channel)
        
        Args:
            limit: Number of recent messages to scan per channel (default: 10, max: 100)
        """
        guild_id = str(ctx.guild.id)
        guild_config = self.config.get(guild_id, {})
        
        # Check if this is the designated invite check channel
        check_channel_id = guild_config.get("invite_check_channel")
        if not check_channel_id or ctx.channel.id != check_channel_id:
            if check_channel_id:
                check_channel = ctx.guild.get_channel(check_channel_id)
                if check_channel:
                    await ctx.reply(f"{SPROUTS_WARNING} Invite checks can only be run in {check_channel.mention}.", mention_author=False)
                else:
                    await ctx.reply(f"{SPROUTS_WARNING} No valid invite check channel configured. Use `{ctx.prefix}checkchannel` to set one.", mention_author=False)
            else:
                await ctx.reply(f"{SPROUTS_WARNING} No invite check channel configured. Use `{ctx.prefix}checkchannel` to set one.", mention_author=False)
            return
        
        # Check if scan is already running
        if guild_id in self.scan_status:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Scan in Progress",
                description="An invite check is currently in process. Please wait a few minutes as the scanner searches your categories.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Validate limit
        if limit < 1 or limit > 100:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Invalid Limit",
                description="Scan limit must be between 1 and 100 messages per channel.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        scan_categories = guild_config.get("scan_categories", [])
        
        if not scan_categories:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} No Categories Configured",
                description=f"No categories are set up for scanning. Use `{ctx.prefix}category add [categoryID]` to configure categories.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Start scan
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Starting Invite Scan",
            description=f"An invite check is currently in process. Please wait a few minutes as the scanner searches your categories.",
            color=EMBED_COLOR_NORMAL
        )
        scan_message = await ctx.reply(embed=embed, mention_author=False)
        
        # Get all channels from categories (excluding ignored channels)
        all_channels = []
        ignore_channels = guild_config.get("ignore_channels", [])
        
        for category_id in scan_categories:
            category = ctx.guild.get_channel(category_id)
            if category and isinstance(category, discord.CategoryChannel):
                for channel in category.channels:
                    if (isinstance(channel, discord.TextChannel) and 
                        channel.id not in ignore_channels and
                        channel.permissions_for(ctx.guild.me).read_message_history):
                        all_channels.append(channel.id)
        
        if not all_channels:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} No Valid Channels",
                description="No accessible text channels found in the configured categories.",
                color=EMBED_COLOR_ERROR
            )
            await scan_message.edit(embed=embed)
            return
        
        # Perform the scan
        results = await self.perform_scan(ctx.guild, all_channels, limit, scan_message)
        
        # Generate final report
        await self.generate_scan_report(ctx, results, scan_message)
        
        # Clean up scan status
        if guild_id in self.scan_status:
            del self.scan_status[guild_id]
        
        await self.mark_task_complete("4")
    
    async def mark_task_complete(self, task_id: str):
        """Helper to mark tasks as complete"""
        # This would integrate with the task system if available
        pass
    
    async def mark_task_in_progress(self, task_id: str):
        """Helper to mark tasks as in progress"""
        # This would integrate with the task system if available
        pass
    
    async def perform_scan(self, guild: discord.Guild, channel_ids: List[int], limit: int, status_message: discord.Message) -> Dict:
        """
        Perform the actual invite scan
        
        Args:
            guild: Discord guild to scan
            channel_ids: List of channel IDs to scan
            limit: Message limit per channel
            status_message: Message to update with progress
            
        Returns:
            Dictionary with scan results
        """
        guild_id = str(guild.id)
        self.scan_status[guild_id] = {
            "start_time": time.time(),
            "channels_total": len(channel_ids),
            "channels_scanned": 0,
            "invites_found": 0,
            "invites_valid": 0
        }
        
        results = {
            "channels_scanned": 0,
            "total_messages": 0,
            "invites_found": 0,
            "invites_valid": 0,
            "invites_invalid": 0,
            "channel_details": [],
            "valid_invites": [],
            "invalid_invites": []
        }
        
        # Process each channel
        for i, channel_id in enumerate(channel_ids):
            try:
                channel = guild.get_channel(channel_id)
                if not channel or not isinstance(channel, discord.TextChannel):
                    continue
                
                # Check permissions
                if not channel.permissions_for(guild.me).read_message_history:
                    continue
                
                channel_results = {
                    "channel_name": channel.name,
                    "channel_id": channel_id,
                    "messages_scanned": 0,
                    "invites_found": 0,
                    "invites_valid": 0,
                    "invites_invalid": 0
                }
                
                # Update progress
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Scanning in Progress",
                    description=f"Currently scanning: **#{channel.name}**\n"
                               f"Progress: {i}/{len(channel_ids)} channels",
                    color=EMBED_COLOR_NORMAL
                )
                await status_message.edit(embed=embed)
                
                # Scan messages in channel
                async for message in channel.history(limit=limit):
                    channel_results["messages_scanned"] += 1
                    results["total_messages"] += 1
                    
                    # Extract invites from message
                    invites = self.extract_invites(message.content)
                    
                    for invite_code in invites:
                        channel_results["invites_found"] += 1
                        results["invites_found"] += 1
                        
                        # Validate invite
                        is_valid, invite_info = await self.validate_invite(invite_code)
                        
                        invite_data = {
                            "code": invite_code,
                            "message_id": message.id,
                            "author": str(message.author),
                            "channel": channel.name,
                            "timestamp": message.created_at.isoformat(),
                            "info": invite_info
                        }
                        
                        if is_valid:
                            channel_results["invites_valid"] += 1
                            results["invites_valid"] += 1
                            results["valid_invites"].append(invite_data)
                        else:
                            channel_results["invites_invalid"] += 1
                            results["invites_invalid"] += 1
                            results["invalid_invites"].append(invite_data)
                        
                        # Small delay to avoid rate limits
                        await asyncio.sleep(0.1)
                
                results["channel_details"].append(channel_results)
                results["channels_scanned"] += 1
                
                # Update scan status
                self.scan_status[guild_id]["channels_scanned"] = i + 1
                self.scan_status[guild_id]["invites_found"] = results["invites_found"]
                self.scan_status[guild_id]["invites_valid"] = results["invites_valid"]
                
            except Exception as e:
                print(f"Error scanning channel {channel_id}: {e}")
                continue
        
        return results
    
    async def generate_scan_report(self, ctx: commands.Context, results: Dict, status_message: discord.Message):
        """Generate and send the final scan report"""
        
        # Calculate statistics
        total_invites = results["invites_found"]
        valid_invites = results["invites_valid"]
        invalid_invites = results["invites_invalid"]
        
        if total_invites > 0:
            valid_percentage = (valid_invites / total_invites) * 100
            invalid_percentage = (invalid_invites / total_invites) * 100
        else:
            valid_percentage = 0
            invalid_percentage = 0
        
        # Create summary embed
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Invite Check Complete!",
            color=EMBED_COLOR_NORMAL
        )
        
        embed.add_field(
            name="Scan Summary",
            value=f"**Channels checked:** {results['channels_scanned']}\n"
                  f"**Messages scanned:** {results['total_messages']:,}\n"
                  f"**Invites found:** {total_invites}",
            inline=True
        )
        
        embed.add_field(
            name="Invite Statistics",
            value=f"**Valid invites:** {valid_invites} ({valid_percentage:.1f}% {SPROUTS_CHECK})\n"
                  f"**Invalid invites:** {invalid_invites} ({invalid_percentage:.1f}% {SPROUTS_ERROR})",
            inline=True
        )
        
        # Add detailed channel breakdown
        if results["channel_details"]:
            channel_summary = []
            for i, channel in enumerate(results["channel_details"][:10]):  # Show max 10 channels
                status_emoji = SPROUTS_CHECK if channel["invites_invalid"] == 0 else SPROUTS_WARNING
                channel_summary.append(
                    f"{status_emoji} **{channel['channel_name']}** - "
                    f"Found: {channel['invites_found']}, "
                    f"Valid: {channel['invites_valid']}, "
                    f"Invalid: {channel['invites_invalid']}"
                )
            
            if len(results["channel_details"]) > 10:
                channel_summary.append(f"... and {len(results['channel_details']) - 10} more channels")
            
            embed.add_field(
                name="Channel Breakdown",
                value="\n".join(channel_summary) if channel_summary else "No channels scanned",
                inline=False
            )
        
        embed.set_footer(text=f"Scan completed • Requested by {ctx.author.display_name}", 
                        icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        await status_message.edit(embed=embed)
        
        # Send detailed invalid invites if any found
        if invalid_invites > 0 and invalid_invites <= 25:  # Discord embed limit
            invalid_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Invites Found",
                description=f"Found {invalid_invites} invalid invite(s):",
                color=EMBED_COLOR_ERROR
            )
            
            for i, invite in enumerate(results["invalid_invites"][:25]):
                invalid_embed.add_field(
                    name=f"#{invite['channel']}",
                    value=f"**Code:** `{invite['code']}`\n"
                          f"**Author:** {invite['author']}\n"
                          f"**Date:** <t:{int(datetime.fromisoformat(invite['timestamp'].replace('Z', '+00:00')).timestamp())}:R>",
                    inline=True
                )
            
            await ctx.send(embed=invalid_embed)
    
    @invite_check.command(name="channels")
    @commands.has_permissions(administrator=True)
    async def manage_channels(self, ctx, action: str = None, *, channel: discord.TextChannel = None):
        """
        Manage channels for invite scanning
        
        Usage:
        - invitecheck channels list - Show configured channels
        - invitecheck channels add #channel - Add channel to scan list
        - invitecheck channels remove #channel - Remove channel from scan list
        - invitecheck channels clear - Clear all scan channels
        """
        guild_id = str(ctx.guild.id)
        guild_config = self.config.get(guild_id, {})
        
        if not action:
            # Show help
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Channel Management",
                description="Manage channels for invite scanning",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="Available Actions",
                value=f"`{ctx.prefix}invitecheck channels list` - Show configured channels\n"
                      f"`{ctx.prefix}invitecheck channels add #channel` - Add channel\n"
                      f"`{ctx.prefix}invitecheck channels remove #channel` - Remove channel\n"
                      f"`{ctx.prefix}invitecheck channels clear` - Clear all channels",
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        if action.lower() == "list":
            scan_channels = guild_config.get("scan_channels", [])
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Configured Scan Channels",
                color=EMBED_COLOR_NORMAL
            )
            
            if scan_channels:
                channel_list = []
                for channel_id in scan_channels:
                    channel_obj = ctx.guild.get_channel(channel_id)
                    if channel_obj:
                        channel_list.append(f"#{channel_obj.name}")
                    else:
                        channel_list.append(f"Unknown Channel (ID: {channel_id})")
                
                embed.add_field(
                    name=f"Channels ({len(scan_channels)})",
                    value="\n".join(channel_list),
                    inline=False
                )
            else:
                embed.description = "No channels configured for scanning."
            
            await ctx.reply(embed=embed, mention_author=False)
        
        elif action.lower() == "add":
            if not channel:
                await ctx.reply(f"{SPROUTS_WARNING} Please specify a channel to add.", mention_author=False)
                return
            
            scan_channels = guild_config.get("scan_channels", [])
            
            if channel.id in scan_channels:
                await ctx.reply(f"{SPROUTS_WARNING} Channel #{channel.name} is already in the scan list.", mention_author=False)
                return
            
            scan_channels.append(channel.id)
            self.config[guild_id]["scan_channels"] = scan_channels
            self.save_config()
            
            await ctx.reply(f"{SPROUTS_CHECK} Added #{channel.name} to scan channels.", mention_author=False)
        
        elif action.lower() == "remove":
            if not channel:
                await ctx.reply(f"{SPROUTS_WARNING} Please specify a channel to remove.", mention_author=False)
                return
            
            scan_channels = guild_config.get("scan_channels", [])
            
            if channel.id not in scan_channels:
                await ctx.reply(f"{SPROUTS_WARNING} Channel #{channel.name} is not in the scan list.", mention_author=False)
                return
            
            scan_channels.remove(channel.id)
            self.config[guild_id]["scan_channels"] = scan_channels
            self.save_config()
            
            await ctx.reply(f"{SPROUTS_CHECK} Removed #{channel.name} from scan channels.", mention_author=False)
        
        elif action.lower() == "clear":
            self.config[guild_id]["scan_channels"] = []
            self.save_config()
            
            await ctx.reply(f"{SPROUTS_CHECK} Cleared all scan channels.", mention_author=False)
        
        else:
            await ctx.reply(f"{SPROUTS_WARNING} Invalid action. Use `list`, `add`, `remove`, or `clear`.", mention_author=False)
    
    @invite_check.command(name="config")
    @commands.has_permissions(administrator=True) 
    async def configure(self, ctx, setting: str = None, *, value: str = None):
        """
        Configure invite checker settings
        
        Settings:
        - enabled (true/false) - Enable/disable invite checking
        - autodelete (true/false) - Auto-delete invalid invites
        - logchannel (#channel) - Set log channel for reports
        """
        guild_id = str(ctx.guild.id)
        
        if not setting:
            # Show current config
            guild_config = self.config.get(guild_id, {})
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Invite Checker Configuration",
                color=EMBED_COLOR_NORMAL
            )
            
            log_channel = None
            if guild_config.get("log_channel"):
                log_channel = ctx.guild.get_channel(guild_config["log_channel"])
            
            embed.add_field(
                name="Current Settings",
                value=f"**Enabled:** {'Yes' if guild_config.get('enabled', False) else 'No'}\n"
                      f"**Auto Delete:** {'Yes' if guild_config.get('auto_delete', False) else 'No'}\n"
                      f"**Log Channel:** {f'#{log_channel.name}' if log_channel else 'Not set'}\n"
                      f"**Scan Channels:** {len(guild_config.get('scan_channels', []))}",
                inline=False
            )
            
            embed.add_field(
                name="Available Settings",
                value=f"`{ctx.prefix}invitecheck config enabled true/false`\n"
                      f"`{ctx.prefix}invitecheck config autodelete true/false`\n"
                      f"`{ctx.prefix}invitecheck config logchannel #channel`",
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        setting = setting.lower()
        
        if setting == "enabled":
            if value and value.lower() in ["true", "false"]:
                enabled = value.lower() == "true"
                self.config[guild_id]["enabled"] = enabled
                self.save_config()
                
                status = "enabled" if enabled else "disabled"
                await ctx.reply(f"{SPROUTS_CHECK} Invite checker {status}.", mention_author=False)
            else:
                await ctx.reply(f"{SPROUTS_WARNING} Please specify `true` or `false`.", mention_author=False)
        
        elif setting == "autodelete":
            if value and value.lower() in ["true", "false"]:
                auto_delete = value.lower() == "true"
                self.config[guild_id]["auto_delete"] = auto_delete
                self.save_config()
                
                status = "enabled" if auto_delete else "disabled"
                await ctx.reply(f"{SPROUTS_CHECK} Auto-delete {status}.", mention_author=False)
            else:
                await ctx.reply(f"{SPROUTS_WARNING} Please specify `true` or `false`.", mention_author=False)
        
        elif setting == "logchannel":
            if value:
                # Try to parse channel mention
                channel_id = value.strip('<#>')
                try:
                    channel_id = int(channel_id)
                    channel = ctx.guild.get_channel(channel_id)
                    
                    if channel and isinstance(channel, discord.TextChannel):
                        self.config[guild_id]["log_channel"] = channel_id
                        self.save_config()
                        await ctx.reply(f"{SPROUTS_CHECK} Log channel set to #{channel.name}.", mention_author=False)
                    else:
                        await ctx.reply(f"{SPROUTS_WARNING} Invalid channel specified.", mention_author=False)
                except ValueError:
                    await ctx.reply(f"{SPROUTS_WARNING} Invalid channel format.", mention_author=False)
            else:
                await ctx.reply(f"{SPROUTS_WARNING} Please specify a channel.", mention_author=False)
        
        else:
            await ctx.reply(f"{SPROUTS_WARNING} Unknown setting. Use `enabled`, `autodelete`, or `logchannel`.", mention_author=False)

async def setup(bot):
    """Setup function for the invite checker cog"""
    await bot.add_cog(InviteChecker(bot))
    print("Invite checker cog loaded successfully")