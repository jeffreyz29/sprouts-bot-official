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
                    "scan_channels": [],
                    "ignore_channels": [],
                    "auto_delete": False,
                    "log_channel": None,
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
    
    @commands.group(name="invitecheck", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def invite_check(self, ctx):
        """Main invite checker command group"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Invite Checker",
                description="Advanced Discord invite validation system",
                color=EMBED_COLOR_NORMAL
            )
            
            guild_config = self.config.get(str(ctx.guild.id), {})
            status = "Enabled" if guild_config.get("enabled", False) else "Disabled"
            
            embed.add_field(
                name="Current Status",
                value=f"**Status:** {status}\n"
                      f"**Scan Channels:** {len(guild_config.get('scan_channels', []))}\n"
                      f"**Auto Delete:** {'Yes' if guild_config.get('auto_delete', False) else 'No'}",
                inline=True
            )
            
            embed.add_field(
                name="Available Commands",
                value=f"`{ctx.prefix}invitecheck scan` - Start manual scan\n"
                      f"`{ctx.prefix}invitecheck config` - Configure settings\n"
                      f"`{ctx.prefix}invitecheck channels` - Manage scan channels\n"
                      f"`{ctx.prefix}invitecheck status` - View detailed status",
                inline=False
            )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
    
    @invite_check.command(name="scan")
    @commands.has_permissions(administrator=True)
    async def manual_scan(self, ctx, limit: int = 50):
        """
        Start a manual invite scan
        
        Args:
            limit: Number of recent messages to scan per channel (default: 50, max: 1000)
        """
        guild_id = str(ctx.guild.id)
        
        # Check if scan is already running
        if guild_id in self.scan_status:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Scan in Progress",
                description="An invite scan is already running. Please wait for it to complete.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Validate limit
        if limit < 1 or limit > 1000:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Invalid Limit",
                description="Scan limit must be between 1 and 1000 messages per channel.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        guild_config = self.config.get(guild_id, {})
        scan_channels = guild_config.get("scan_channels", [])
        
        if not scan_channels:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} No Channels Configured",
                description=f"No channels are set up for scanning. Use `{ctx.prefix}invitecheck channels add` to configure channels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Start scan
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Starting Invite Scan",
            description=f"An invite check is currently in process. Please wait a few minutes as the scanner searches your channels.",
            color=EMBED_COLOR_NORMAL
        )
        scan_message = await ctx.reply(embed=embed, mention_author=False)
        
        # Mark task as complete and start next one
        await self.mark_task_complete("1")
        await self.mark_task_in_progress("2")
        
        # Perform the scan
        results = await self.perform_scan(ctx.guild, scan_channels, limit, scan_message)
        
        # Mark scanning task complete and start reporting
        await self.mark_task_complete("2")
        await self.mark_task_in_progress("4")
        
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