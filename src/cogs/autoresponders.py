"""
Auto Responders System
Simple autoresponder system with trigger: and reply: syntax
"""

import discord
from discord.ext import commands
import json
import os
import logging
from datetime import datetime
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR
from src.emojis import SPROUTS_ERROR, SPROUTS_CHECK, SPROUTS_WARNING

logger = logging.getLogger(__name__)

class AutoResponders(commands.Cog):
    """Auto responders system with basic trigger and reply functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.responders_file = "src/data/autoresponders.json"
        self.autoresponders = self.load_autoresponders()
    
    def load_autoresponders(self) -> dict:
        """Load auto responders from file"""
        try:
            os.makedirs("src/data", exist_ok=True)
            if os.path.exists(self.responders_file):
                with open(self.responders_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading auto responders: {e}")
            return {}
    
    def save_autoresponders(self):
        """Save auto responders to file"""
        try:
            os.makedirs("src/data", exist_ok=True)
            with open(self.responders_file, 'w') as f:
                json.dump(self.autoresponders, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving auto responders: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for auto responder triggers - DO NOT PROCESS COMMANDS"""
        if not message.guild or message.author.bot:
            return
        
        # Check if this is a command - if so, don't trigger autoresponders
        ctx = await self.bot.get_context(message)
        if ctx.command:
            return  # Don't respond to commands
        
        guild_id = str(message.guild.id)
        if guild_id not in self.autoresponders:
            return
        
        guild_responders = self.autoresponders[guild_id]
        
        for trigger, responder_data in guild_responders.items():
            if not responder_data.get('enabled', True):
                continue
            
            # Check if message matches trigger (case-insensitive contains)
            if trigger.lower() in message.content.lower():
                response = responder_data['response']
                await message.channel.send(response)
                break  # Only trigger the first matching responder
    
    @commands.group(name="autoresponder", aliases=["ar"], invoke_without_command=True, help="Auto responder management commands")
    @commands.has_permissions(administrator=True)
    async def autoresponder(self, ctx):
        """Auto responder management commands

        Simple autoresponder system with trigger and reply functionality.
        Use subcommands to add, edit, remove, list, or toggle auto responders.

        Usage: `s.autoresponder <subcommand>`
        Base command that shows available subcommands and examples

        Available subcommands:
        - add: Create new auto responder
        - editreply: Modify existing response
        - remove: Delete auto responder
        - list: Show all responders
        - toggle: Enable/disable responder
        """
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title=" Simple Auto Responder System",
                description="Basic autoresponder system with trigger and reply functionality",
                color=EMBED_COLOR_NORMAL
            )
            
            embed.add_field(
                name="Commands",
                value=f"`{ctx.prefix}autoresponder add trigger:<trigger> reply:<response>` - Add responder\n"
                      f"`{ctx.prefix}autoresponder editreply trigger:<trigger> reply:<new response>` - Edit responder\n"
                      f"`{ctx.prefix}autoresponder remove <trigger>` - Remove responder\n"
                      f"`{ctx.prefix}autoresponder list` - List all responders\n"
                      f"`{ctx.prefix}autoresponder toggle <trigger>` - Enable/disable responder",
                inline=False
            )
            
            embed.add_field(
                name="Example",
                value=f"`{ctx.prefix}autoresponder add trigger:hello reply:Hello there! Welcome to our server!`",
                inline=False
            )
            
            await ctx.send(embed=embed)
    
    @autoresponder.command(name="add", help="Add simple auto responder")
    @commands.has_permissions(administrator=True)
    async def autoresponder_add(self, ctx, *, args):
        """Add simple auto responder

        Usage: `s.autoresponder add trigger:<trigger> reply:<response>`
        Creates auto responder that replies when trigger word/phrase is detected

        Examples:
        - `s.autoresponder add trigger:hello reply:Hello there! Welcome!`
        - `s.autoresponder add trigger:rules reply:Please check #rules channel`
        - `s.autoresponder add trigger:support reply:Create a ticket for assistance`

        Format: trigger:<text> reply:<response>
        Simple trigger and reply system without complex functions

        Common Errors:
        - Missing format: Must use trigger:<text> reply:<text> format
        - Empty values: Both trigger and reply must have content
        - Administrator only: Requires Administrator permission
        """
        try:
            # Parse trigger: and reply: format
            if 'trigger:' not in args or 'reply:' not in args:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Invalid Format",
                    description=f"**Correct format:** `{ctx.prefix}autoresponder add trigger:<trigger> reply:<response>`\n\n"
                               f"**Example:** `{ctx.prefix}autoresponder add trigger:hello reply:Hello there! Welcome!`",
                    color=EMBED_COLOR_ERROR
                )
                embed.add_field(
                    name="What you provided:",
                    value=f"`{args}`",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            # Extract trigger and reply
            trigger_start = args.find('trigger:') + 8
            reply_start = args.find('reply:') + 6
            
            if reply_start < trigger_start:
                # reply: comes before trigger:
                trigger = args[trigger_start:].strip()
                reply = args[reply_start:args.find('trigger:')].strip()
            else:
                # trigger: comes before reply:
                trigger = args[trigger_start:args.find('reply:')].strip()
                reply = args[reply_start:].strip()
            
            if not trigger or not reply:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Missing Information",
                    description=f"**Both trigger and reply are required!**\n\n"
                               f"**Correct format:** `{ctx.prefix}autoresponder add trigger:<trigger> reply:<response>`\n\n"
                               f"**Example:** `{ctx.prefix}autoresponder add trigger:hello reply:Welcome to our server!`",
                    color=EMBED_COLOR_ERROR
                )
                embed.add_field(
                    name="What you provided:",
                    value=f"`{args}`",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            guild_id = str(ctx.guild.id)
            if guild_id not in self.autoresponders:
                self.autoresponders[guild_id] = {}
            
            # Check if trigger already exists
            if trigger in self.autoresponders[guild_id]:
                current_response = self.autoresponders[guild_id][trigger]['response']
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Auto Responder Already Exists",
                    description=f"**An auto responder for trigger `{trigger}` already exists!**\n\n"
                               f"**Available options:**\n"
                               f"`{ctx.prefix}autoresponder editreply trigger:{trigger} reply:<new response>` - Edit existing responder\n"
                               f"`{ctx.prefix}autoresponder remove {trigger}` - Remove existing responder\n"
                               f"`{ctx.prefix}autoresponder toggle {trigger}` - Enable/disable responder",
                    color=EMBED_COLOR_ERROR
                )
                embed.add_field(
                    name="Current response:",
                    value=f"`{current_response[:100]}{'...' if len(current_response) > 100 else ''}`",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            # Add the responder
            self.autoresponders[guild_id][trigger] = {
                'response': reply,
                'enabled': True,
                'created_by': str(ctx.author.id),
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.save_autoresponders()
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Auto Responder Added",
                description=f"Successfully added auto responder for trigger: `{trigger}`",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(name="Trigger", value=trigger, inline=True)
            embed.add_field(name="Response", value=reply[:100] + "..." if len(reply) > 100 else reply, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error adding auto responder: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description="Failed to add auto responder. Please check your syntax.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
    
    @autoresponder.command(name="editreply", help="Edit responder reply")
    @commands.has_permissions(administrator=True)
    async def autoresponder_editreply(self, ctx, *, args):
        """Edit responder reply

        Usage: `s.autoresponder editreply trigger:<trigger> reply:<new_response>`
        Changes the response message for existing trigger

        Examples:
        - `s.autoresponder editreply trigger:hello reply:Hi! Welcome to our server!`
        - `s.autoresponder editreply trigger:rules reply:Check out our updated rules`

        Common Errors:
        - Trigger not found: Auto responder with that trigger doesn't exist
        - Missing format: Must use trigger:<text> reply:<text> format
        - Administrator only: Requires Administrator permission
        """
        try:
            # Parse trigger: and reply: format
            if 'trigger:' not in args or 'reply:' not in args:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Invalid Format",
                    description=f"**Correct format:** `{ctx.prefix}autoresponder editreply trigger:<trigger> reply:<new response>`\n\n"
                               f"**Example:** `{ctx.prefix}autoresponder editreply trigger:hello reply:Hi there! Updated message!`",
                    color=EMBED_COLOR_ERROR
                )
                embed.add_field(
                    name="What you provided:",
                    value=f"`{args}`",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            # Extract trigger and reply
            trigger_start = args.find('trigger:') + 8
            reply_start = args.find('reply:') + 6
            
            if reply_start < trigger_start:
                # reply: comes before trigger:
                trigger = args[trigger_start:].strip()
                reply = args[reply_start:args.find('trigger:')].strip()
            else:
                # trigger: comes before reply:
                trigger = args[trigger_start:args.find('reply:')].strip()
                reply = args[reply_start:].strip()
            
            guild_id = str(ctx.guild.id)
            if guild_id not in self.autoresponders or trigger not in self.autoresponders[guild_id]:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Auto Responder Not Found",
                    description=f"**No auto responder found for trigger:** `{trigger}`\n\n"
                               f"**Available commands:**\n"
                               f"`{ctx.prefix}autoresponder list` - View all auto responders\n"
                               f"`{ctx.prefix}autoresponder add trigger:<trigger> reply:<response>` - Create new responder",
                    color=EMBED_COLOR_ERROR
                )
                embed.add_field(
                    name="What you searched for:",
                    value=f"`{trigger}`",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            # Update the response
            old_response = self.autoresponders[guild_id][trigger]['response']
            self.autoresponders[guild_id][trigger]['response'] = reply
            self.autoresponders[guild_id][trigger]['modified_at'] = datetime.utcnow().isoformat()
            self.autoresponders[guild_id][trigger]['modified_by'] = str(ctx.author.id)
            
            self.save_autoresponders()
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Auto Responder Updated",
                description=f"Successfully updated auto responder for trigger: `{trigger}`",
                color=EMBED_COLOR_NORMAL
            )
            embed.add_field(name="Old Response", value=old_response[:100] + "..." if len(old_response) > 100 else old_response, inline=False)
            embed.add_field(name="New Response", value=reply[:100] + "..." if len(reply) > 100 else reply, inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error editing auto responder: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description="Failed to edit auto responder. Please check your syntax.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
    
    @autoresponder.command(name="remove", aliases=["delete"], help="Remove auto responder permanently by trigger word")
    @commands.has_permissions(administrator=True)
    async def autoresponder_remove(self, ctx, *, trigger):
        """Remove an auto responder
        
        Usage: `{ctx.prefix}autoresponder remove <trigger>`
        Permanently deletes auto responder (cannot be undone)
        
        Examples:
        - `{ctx.prefix}autoresponder remove hello` - Delete 'hello' trigger
        - `{ctx.prefix}autoresponder remove rules` - Remove 'rules' auto responder
        - `{ctx.prefix}autoresponder remove old_command` - Clean up unused triggers
        
        Common Errors:
        - Trigger not found: Use autoresponder list to see available triggers
        - Case sensitive: Trigger must match exactly
        - Cannot undo: Deletion is permanent
        """
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.autoresponders or trigger not in self.autoresponders[guild_id]:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Auto Responder Not Found",
                description=f"**No auto responder found for trigger:** `{trigger}`\n\n"
                           f"**Available commands:**\n"
                           f"`{ctx.prefix}autoresponder list` - View all auto responders\n"
                           f"`{ctx.prefix}autoresponder add trigger:<trigger> reply:<response>` - Create new responder",
                color=EMBED_COLOR_ERROR
            )
            embed.add_field(
                name="What you searched for:",
                value=f"`{trigger}`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Remove the responder
        removed_responder = self.autoresponders[guild_id].pop(trigger)
        self.save_autoresponders()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Auto Responder Removed",
            description=f"Successfully removed auto responder for trigger: `{trigger}`",
            color=EMBED_COLOR_NORMAL
        )
        embed.add_field(name="Response", value=removed_responder['response'][:100] + "..." if len(removed_responder['response']) > 100 else removed_responder['response'], inline=False)
        
        await ctx.send(embed=embed)
    
    @autoresponder.command(name="list", help="Display all auto responders with triggers and status")
    @commands.has_permissions(administrator=True)
    async def autoresponder_list(self, ctx):
        """List all auto responders
        
        Usage: `{ctx.prefix}autoresponder list`
        Shows all configured auto responders with triggers, responses, and status
        
        Examples:
        - `{ctx.prefix}autoresponder list` - View all server auto responders
        - Shows enabled/disabled status for each
        - Displays first 50 characters of each response
        
        Features:
        - Shows up to 10 responders per page
        - Indicates enabled/disabled status
        - Truncates long responses for readability
        - Perfect for managing large collections
        """
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.autoresponders or not self.autoresponders[guild_id]:
            embed = discord.Embed(
                title=" Auto Responders",
                description="No auto responders configured for this server.",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.send(embed=embed)
            return
        
        responders = self.autoresponders[guild_id]
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Auto Responders",
            description=f"Found {len(responders)} auto responder(s)",
            color=EMBED_COLOR_NORMAL
        )
        
        for trigger, data in list(responders.items())[:10]:  # Show first 10
            status = f"{SPROUTS_CHECK} Enabled" if data.get('enabled', True) else f"{SPROUTS_ERROR} Disabled"
            response = data['response'][:50] + "..." if len(data['response']) > 50 else data['response']
            embed.add_field(
                name=f"{trigger} ({status})",
                value=response,
                inline=False
            )
        
        if len(responders) > 10:
            embed.set_footer(text=f"Showing 10 of {len(responders)} auto responders")
        
        await ctx.send(embed=embed)
    
    @autoresponder.command(name="toggle", help="Enable or disable an existing auto responder by providing its trigger word")
    @commands.has_permissions(administrator=True)
    async def autoresponder_toggle(self, ctx, *, trigger):
        """Toggle an auto responder on/off without deleting it
        
        Usage: `{ctx.prefix}autoresponder toggle <trigger>`
        
        How to use:
        1. First, check existing responders with 'autoresponder list'
        2. Find the trigger word of the responder you want to toggle
        3. Use 'autoresponder toggle <trigger>' to enable/disable it
        4. The responder will switch between enabled and disabled states
        
        Examples:
        - `{ctx.prefix}autoresponder toggle hello` - Enable/disable the 'hello' responder
        - `{ctx.prefix}autoresponder toggle maintenance` - Toggle maintenance message on/off
        - `{ctx.prefix}autoresponder toggle rules` - Temporarily disable rules reminder
        
        What this does:
        - Disables the responder: It will stop responding to messages but keep all settings
        - Enables the responder: It will start responding to messages again
        - Preserves all data: No need to recreate the responder later
        - Better than delete/add: Quick way to temporarily turn off responders
        
        Note: You must use the exact trigger word that was used when creating the responder
        """
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.autoresponders or trigger not in self.autoresponders[guild_id]:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Auto Responder Not Found",
                description=f"**No auto responder found for trigger:** `{trigger}`\n\n"
                           f"**Available commands:**\n"
                           f"`{ctx.prefix}autoresponder list` - View all auto responders\n"
                           f"`{ctx.prefix}autoresponder add trigger:<trigger> reply:<response>` - Create new responder",
                color=EMBED_COLOR_ERROR
            )
            embed.add_field(
                name="What you searched for:",
                value=f"`{trigger}`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Toggle the responder
        current_status = self.autoresponders[guild_id][trigger].get('enabled', True)
        new_status = not current_status
        self.autoresponders[guild_id][trigger]['enabled'] = new_status
        self.save_autoresponders()
        
        status_text = "enabled" if new_status else "disabled"
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Auto Responder Toggled",
            description=f"Auto responder for trigger `{trigger}` has been **{status_text}**",
            color=EMBED_COLOR_NORMAL
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(AutoResponders(bot))
    logger.info("Auto responders setup completed")
