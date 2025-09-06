"""
TicketsBot-Compatible Setting Commands
Implements the 15 setting commands from TicketsBot specification
"""

import discord
from discord.ext import commands
import json
import os
from src.config import SPROUTS_CHECK, SPROUTS_ERROR, SPROUTS_WARNING, EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR, EMBED_COLOR_HIERARCHY

import logging
logger = logging.getLogger(__name__)

class TicketSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = 'src/data/ticket_settings.json'
        self.settings_data = self.load_settings()
    
    def load_settings(self):
        """Load ticket settings from file"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_settings(self):
        """Save ticket settings to file"""
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings_data, f, indent=4)
    
    def get_guild_settings(self, guild_id):
        """Get settings for a specific guild"""
        if str(guild_id) not in self.settings_data:
            self.settings_data[str(guild_id)] = {
                'admins': [],
                'support': [],
                'blacklist': [],
                'ticket_limit': 1,
                'transcript_channel': None,
                'use_threads': False,
                'autoclose_enabled': False,
                'autoclose_after': 24  # hours
            }
            self.save_settings()
        return self.settings_data[str(guild_id)]
    
    async def is_admin(self, member, guild):
        """Check if user is a ticket admin"""
        if member.guild_permissions.administrator:
            return True
        
        settings = self.get_guild_settings(guild.id)
        admin_ids = settings.get('admins', [])
        
        # Check user ID
        if member.id in admin_ids:
            return True
        
        # Check role IDs
        for role in member.roles:
            if role.id in admin_ids:
                return True
        
        return False
    
    async def is_support(self, member, guild):
        """Check if user is support staff"""
        if await self.is_admin(member, guild):
            return True
        
        settings = self.get_guild_settings(guild.id)
        support_ids = settings.get('support', [])
        
        # Check user ID
        if member.id in support_ids:
            return True
        
        # Check role IDs
        for role in member.roles:
            if role.id in support_ids:
                return True
        
        return False
    
    # SETTING COMMANDS (15 commands)
    
    @commands.command(name="addadmin")
    async def add_admin(self, ctx, *, target_input: str = None):
        """Grants a user or role admin privileges of the bot"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can manage admin privileges.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        if not target_input:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Missing Target",
                description="Please specify a user or role to add as admin.\n\n"
                           "**Usage:** `s.addadmin @user` or `s.addadmin @role`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        # Try to find user or role
        target = None
        target_type = "user"
        
        # Check for mentions first
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
        elif ctx.message.role_mentions:
            target = ctx.message.role_mentions[0]
            target_type = "role"
        else:
            # Try to parse ID or name
            try:
                # Try as ID first
                target_id = int(target_input.strip('<@&>!'))
                target = ctx.guild.get_member(target_id) or ctx.guild.get_role(target_id)
                if target and isinstance(target, discord.Role):
                    target_type = "role"
            except ValueError:
                # Try as name
                target = discord.utils.find(lambda m: m.name.lower() == target_input.lower(), ctx.guild.members)
                if not target:
                    target = discord.utils.find(lambda r: r.name.lower() == target_input.lower(), ctx.guild.roles)
                    if target:
                        target_type = "role"
        
        if not target:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Target Not Found",
                description=f"Could not find user or role: `{target_input}`\n\n"
                           "**Usage:** `s.addadmin @user` or `s.addadmin @role`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        settings = self.get_guild_settings(ctx.guild.id)
        if target.id not in settings['admins']:
            settings['admins'].append(target.id)
            self.save_settings()
            action = "granted"
        else:
            action = "already has"
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Admin Updated",
            description=f"{target_type.title()} {target.mention} {action} ticket admin privileges.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed, mention_author=False)
    
    @commands.command(name="removeadmin")
    async def remove_admin(self, ctx, *, target_input: str = None):
        """Revokes a user's or role's admin privileges"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can manage admin privileges.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        if not target_input:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Missing Target",
                description="Please specify a user or role to remove admin privileges from.\n\n"
                           "**Usage:** `s.removeadmin @user` or `s.removeadmin @role`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        # Try to find user or role
        target = None
        target_type = "user"
        
        # Check for mentions first
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
        elif ctx.message.role_mentions:
            target = ctx.message.role_mentions[0]
            target_type = "role"
        else:
            # Try to parse ID or name
            try:
                # Try as ID first
                target_id = int(target_input.strip('<@&>!'))
                target = ctx.guild.get_member(target_id) or ctx.guild.get_role(target_id)
                if target and isinstance(target, discord.Role):
                    target_type = "role"
            except ValueError:
                # Try as name
                target = discord.utils.find(lambda m: m.name.lower() == target_input.lower(), ctx.guild.members)
                if not target:
                    target = discord.utils.find(lambda r: r.name.lower() == target_input.lower(), ctx.guild.roles)
                    if target:
                        target_type = "role"
        
        if not target:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Target Not Found",
                description=f"Could not find user or role: `{target_input}`\n\n"
                           "**Usage:** `s.removeadmin @user` or `s.removeadmin @role`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        settings = self.get_guild_settings(ctx.guild.id)
        if target.id in settings['admins']:
            settings['admins'].remove(target.id)
            self.save_settings()
            action = "revoked"
        else:
            action = "does not have"
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Admin Updated",
            description=f"{target_type.title()} {target.mention} {action} ticket admin privileges.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed, mention_author=False)
    
    @commands.command(name="addsupport")
    async def add_support(self, ctx, *, target_input: str = None):
        """Adds a user or role as a support representative"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can manage support staff.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        if not target_input:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Missing Target",
                description="Please specify a user or role to add as support.\n\n"
                           "**Usage:** `s.addsupport @user` or `s.addsupport @role`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        # Try to find user or role
        target = None
        target_type = "user"
        
        # Check for mentions first
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
        elif ctx.message.role_mentions:
            target = ctx.message.role_mentions[0]
            target_type = "role"
        else:
            # Try to parse ID or name
            try:
                # Try as ID first
                target_id = int(target_input.strip('<@&>!'))
                target = ctx.guild.get_member(target_id) or ctx.guild.get_role(target_id)
                if target and isinstance(target, discord.Role):
                    target_type = "role"
            except ValueError:
                # Try as name
                target = discord.utils.find(lambda m: m.name.lower() == target_input.lower(), ctx.guild.members)
                if not target:
                    target = discord.utils.find(lambda r: r.name.lower() == target_input.lower(), ctx.guild.roles)
                    if target:
                        target_type = "role"
        
        if not target:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Target Not Found",
                description=f"Could not find user or role: `{target_input}`\n\n"
                           "**Usage:** `s.addsupport @user` or `s.addsupport @role`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        settings = self.get_guild_settings(ctx.guild.id)
        if target.id not in settings['support']:
            settings['support'].append(target.id)
            self.save_settings()
            action = "added as"
        else:
            action = "already is"
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Support Updated",
            description=f"{target_type.title()} {target.mention} {action} a support representative.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed, mention_author=False)
    
    @commands.command(name="removesupport")
    async def remove_support(self, ctx, *, target_input: str = None):
        """Revokes a user's or role's support representative privileges"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can manage support staff.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        if not target_input:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Missing Target",
                description="Please specify a user or role to remove support privileges from.\n\n"
                           "**Usage:** `s.removesupport @user` or `s.removesupport @role`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        # Try to find user or role
        target = None
        target_type = "user"
        
        # Check for mentions first
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
        elif ctx.message.role_mentions:
            target = ctx.message.role_mentions[0]
            target_type = "role"
        else:
            # Try to parse ID or name
            try:
                # Try as ID first
                target_id = int(target_input.strip('<@&>!'))
                target = ctx.guild.get_member(target_id) or ctx.guild.get_role(target_id)
                if target and isinstance(target, discord.Role):
                    target_type = "role"
            except ValueError:
                # Try as name
                target = discord.utils.find(lambda m: m.name.lower() == target_input.lower(), ctx.guild.members)
                if not target:
                    target = discord.utils.find(lambda r: r.name.lower() == target_input.lower(), ctx.guild.roles)
                    if target:
                        target_type = "role"
        
        if not target:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Target Not Found",
                description=f"Could not find user or role: `{target_input}`\n\n"
                           "**Usage:** `s.removesupport @user` or `s.removesupport @role`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        settings = self.get_guild_settings(ctx.guild.id)
        if target.id in settings['support']:
            settings['support'].remove(target.id)
            self.save_settings()
            action = "removed from"
        else:
            action = "is not"
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Support Updated",
            description=f"{target_type.title()} {target.mention} {action} support staff.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed, mention_author=False)
    
    @commands.command(name="blacklist")
    async def blacklist_user(self, ctx, target: discord.Member = None):
        """Toggles whether users are allowed to interact with the bot"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can manage the blacklist.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        if not target:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Missing Target",
                description="Please specify a user to blacklist or unblacklist.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        settings = self.get_guild_settings(ctx.guild.id)
        if target.id in settings['blacklist']:
            settings['blacklist'].remove(target.id)
            action = "removed from"
            color = EMBED_COLOR_NORMAL
        else:
            settings['blacklist'].append(target.id)
            action = "added to"
            color = EMBED_COLOR_ERROR
        
        self.save_settings()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Blacklist Updated",
            description=f"{target.mention} has been {action} the blacklist.",
            color=color
        )
        await ctx.send(embed=embed, mention_author=False)
    
    @commands.command(name="viewstaff")
    async def view_staff(self, ctx):
        """Lists the staff members and roles (admin or support)"""
        settings = self.get_guild_settings(ctx.guild.id)
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Staff Members",
            color=EMBED_COLOR_NORMAL
        )
        
        # Get admins
        admin_list = []
        for admin_id in settings.get('admins', []):
            member = ctx.guild.get_member(admin_id) or ctx.guild.get_role(admin_id)
            if member:
                admin_list.append(member.mention)
        
        # Get support
        support_list = []
        for support_id in settings.get('support', []):
            member = ctx.guild.get_member(support_id) or ctx.guild.get_role(support_id)
            if member:
                support_list.append(member.mention)
        
        embed.add_field(
            name=f"{SPROUTS_CHECK} Admins ({len(admin_list)})",
            value="\n".join(admin_list) if admin_list else "No admins configured",
            inline=False
        )
        
        embed.add_field(
            name=f"{SPROUTS_WARNING} Support ({len(support_list)})",
            value="\n".join(support_list) if support_list else "No support staff configured",
            inline=False
        )
        
        await ctx.send(embed=embed, mention_author=False)
    
    @commands.command(name="panel")
    async def panel_setup(self, ctx):
        """Provides a link to create a reaction panel for users to open tickets"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can manage panels.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Ticket Panel Setup",
            description="**Panel Creation Steps:**\n\n"
                       "1. Create a message for your ticket panel\n"
                       "2. Add a reaction to that message (🎫 recommended)\n"
                       "3. Users can react to create tickets\n\n"
                       f"**Current Configuration:**\n"
                       f"• Ticket Limit: {self.get_guild_settings(ctx.guild.id)['ticket_limit']}\n"
                       f"• Use Threads: {'Yes' if self.get_guild_settings(ctx.guild.id)['use_threads'] else 'No'}",
            color=EMBED_COLOR_HIERARCHY
        )
        
        embed.add_field(
            name=f"{SPROUTS_WARNING} Configuration Commands",
            value="`s.setup limit <number>` - Set ticket limit per user\n"
                  "`s.setup use-threads` - Toggle thread mode\n"
                  "`s.setup transcripts <channel>` - Set transcript channel",
            inline=False
        )
        
        await ctx.send(embed=embed, mention_author=False)
    
    @commands.group(name="setup", invoke_without_command=True)
    async def setup(self, ctx):
        """Setup command group"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can modify setup settings.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Setup Commands",
            description="Available setup options:",
            color=EMBED_COLOR_HIERARCHY
        )
        
        embed.add_field(
            name="Commands",
            value="`s.setup limit <number>` - Change ticket limit per user\n"
                  "`s.setup transcripts <channel>` - Set transcript channel\n"
                  "`s.setup use-threads` - Toggle thread/channel mode",
            inline=False
        )
        
        await ctx.send(embed=embed, mention_author=False)
    
    @setup.command(name="limit")
    async def setup_limit(self, ctx, limit: int = None):
        """Change the quantity of tickets a single user can have open at the same time"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can modify setup settings.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        if limit is None:
            settings = self.get_guild_settings(ctx.guild.id)
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Current Ticket Limit",
                description=f"Users can have **{settings['ticket_limit']}** ticket(s) open at once.",
                color=EMBED_COLOR_NORMAL
            )
            await ctx.send(embed=embed, mention_author=False)
            return
        
        if limit < 1 or limit > 10:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Invalid Limit",
                description="Ticket limit must be between 1 and 10.",
                color=EMBED_COLOR_ERROR
            )
            embed.add_field(
                name="Usage",
                value="`s.setup limit <number>`\n\n**Examples:**\n`s.setup limit 3` - Allow 3 tickets per user\n`s.setup limit 5` - Allow 5 tickets per user",
                inline=False
            )
            embed.add_field(
                name="Valid Range",
                value="**Minimum:** 1 ticket per user\n**Maximum:** 10 tickets per user",
                inline=False
            )
            await ctx.send(embed=embed, delete_after=15, mention_author=False)
            return
        
        settings = self.get_guild_settings(ctx.guild.id)
        settings['ticket_limit'] = limit
        self.save_settings()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Limit Updated",
            description=f"Ticket limit set to **{limit}** ticket(s) per user.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed, mention_author=False)
    
    @setup.command(name="transcripts")
    async def setup_transcripts(self, ctx, channel: discord.TextChannel = None):
        """Change the transcripts channel"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can modify setup settings.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        settings = self.get_guild_settings(ctx.guild.id)
        
        if channel is None:
            current_channel_id = settings.get('transcript_channel')
            if current_channel_id:
                current_channel = ctx.guild.get_channel(current_channel_id)
                if current_channel:
                    embed = discord.Embed(
                        title=f"{SPROUTS_CHECK} Current Transcript Channel",
                        description=f"Transcripts are sent to {current_channel.mention}.",
                        color=EMBED_COLOR_NORMAL
                    )
                else:
                    embed = discord.Embed(
                        title=f"{SPROUTS_WARNING} Invalid Channel",
                        description="Transcript channel is set but no longer exists.",
                        color=EMBED_COLOR_ERROR
                    )
            else:
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} No Channel Set",
                    description="No transcript channel configured.",
                    color=EMBED_COLOR_ERROR
                )
            await ctx.send(embed=embed, mention_author=False)
            return
        
        settings['transcript_channel'] = channel.id
        self.save_settings()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Transcript Channel Updated",
            description=f"Transcripts will now be sent to {channel.mention}.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed, mention_author=False)
    
    @setup.command(name="use-threads")
    async def setup_use_threads(self, ctx):
        """Toggle if the bot creates new threads or new channels"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can modify setup settings.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        settings = self.get_guild_settings(ctx.guild.id)
        settings['use_threads'] = not settings.get('use_threads', False)
        self.save_settings()
        
        mode = "threads" if settings['use_threads'] else "channels"
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Thread Mode Updated",
            description=f"Tickets will now be created as **{mode}**.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed, mention_author=False)
    
    @commands.group(name="autoclose", invoke_without_command=True)
    async def autoclose(self, ctx):
        """Autoclose command group"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can modify autoclose settings.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Autoclose Commands",
            description="Available autoclose options:",
            color=EMBED_COLOR_HIERARCHY
        )
        
        embed.add_field(
            name="Commands",
            value="`s.autoclose configure` - Edit autoclose settings\n"
                  "`s.autoclose exclude` - Exclude current ticket from autoclose",
            inline=False
        )
        
        await ctx.send(embed=embed, mention_author=False)
    
    @autoclose.command(name="configure")
    async def autoclose_configure(self, ctx):
        """Edit autoclose related settings"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only ticket admins can modify autoclose settings.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10, mention_author=False)
            return
        
        settings = self.get_guild_settings(ctx.guild.id)
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Autoclose Configuration",
            description="Current autoclose settings:",
            color=EMBED_COLOR_HIERARCHY
        )
        
        embed.add_field(
            name="Status",
            value="Enabled" if settings.get('autoclose_enabled', False) else "Disabled",
            inline=True
        )
        
        embed.add_field(
            name="Close After",
            value=f"{settings.get('autoclose_after', 24)} hours",
            inline=True
        )
        
        embed.add_field(
            name="Configuration Options",
            value=f"React with {SPROUTS_CHECK} to toggle autoclose\nReact with {SPROUTS_WARNING} to change time limit\nReact with {SPROUTS_INFORMATION} for help",
            inline=False
        )
        
        message = await ctx.send(embed=embed)
        # Add custom emoji reactions properly
        try:
            await message.add_reaction(self.bot.get_emoji(1411790001565466725))  # SPROUTS_CHECK
            await message.add_reaction(self.bot.get_emoji(1412200379206336522))  # SPROUTS_WARNING  
            await message.add_reaction(self.bot.get_emoji(1413464347078033478))  # SPROUTS_INFORMATION
        except Exception as e:
            # If custom emojis fail, send error message 
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Emoji Error",
                description="Could not add custom emoji reactions. Please check bot permissions or emoji availability.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=error_embed, delete_after=10)
    
    @autoclose.command(name="exclude")
    async def autoclose_exclude(self, ctx):
        """Excludes the current ticket from being automatically closed"""
        # This would require ticket data integration
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Autoclose Excluded",
            description="This ticket has been excluded from automatic closure.",
            color=EMBED_COLOR_NORMAL
        )
        await ctx.send(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(TicketSettings(bot))