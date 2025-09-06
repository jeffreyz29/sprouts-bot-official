"""
Staff Management Select Menu System
Modern interface for managing ticket admins and support staff
"""

import discord
from discord.ext import commands
import json
import os
from src.config import SPROUTS_CHECK, SPROUTS_ERROR, SPROUTS_WARNING, SPROUTS_INFORMATION, EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR, EMBED_COLOR_SUCCESS, EMBED_COLOR_WARNING, EMBED_COLOR_INFO

import logging
logger = logging.getLogger(__name__)

class StaffManagementView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the user who ran the command to use the menu"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot control someone else's staff menu!", ephemeral=True)
            return False
        return True
    
    @discord.ui.select(
        placeholder="Choose a staff management action...",
        options=[
            discord.SelectOption(
                label="Add Admin",
                description="Grant admin privileges to a user or role",
                emoji=f"{SPROUTS_CHECK}",
                value="add_admin"
            ),
            discord.SelectOption(
                label="Remove Admin", 
                description="Revoke admin privileges from a user or role",
                emoji=f"{SPROUTS_ERROR}",
                value="remove_admin"
            ),
            discord.SelectOption(
                label="Add Support",
                description="Add a user or role as support staff",
                emoji=f"{SPROUTS_INFORMATION}",
                value="add_support"
            ),
            discord.SelectOption(
                label="Remove Support",
                description="Remove support privileges from a user or role", 
                emoji=f"{SPROUTS_WARNING}",
                value="remove_support"
            ),
            discord.SelectOption(
                label="View All Staff",
                description="List all current admins and support staff",
                emoji=f"{SPROUTS_INFORMATION}",
                value="view_staff"
            ),
            discord.SelectOption(
                label="Manage Blacklist",
                description="Add/remove users from the blacklist",
                emoji=f"{SPROUTS_ERROR}",
                value="manage_blacklist"
            )
        ]
    )
    async def staff_action_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        action = select.values[0]
        
        if action == "add_admin":
            await self.add_admin_prompt(interaction)
        elif action == "remove_admin":
            await self.remove_admin_prompt(interaction)
        elif action == "add_support":
            await self.add_support_prompt(interaction)
        elif action == "remove_support":
            await self.remove_support_prompt(interaction)
        elif action == "view_staff":
            await self.view_staff(interaction)
        elif action == "manage_blacklist":
            await self.manage_blacklist_prompt(interaction)
    
    async def add_admin_prompt(self, interaction: discord.Interaction):
        """Prompt for adding admin"""
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Add Ticket Admin",
            description="Please mention the user or role you want to grant admin privileges to.\n\n"
                       "**Example:** `@JohnDoe` or `@Admin Role`\n"
                       "**Note:** Type `cancel` to cancel this action.",
            color=EMBED_COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel
        
        try:
            msg = await interaction.client.wait_for('message', check=check, timeout=60.0)
            
            if msg.content.lower() == "cancel":
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} Cancelled",
                    description="Admin addition cancelled.",
                    color=EMBED_COLOR_ERROR
                )
                await msg.reply(embed=embed, delete_after=10, mention_author=False)
                return
            
            # Find target
            target, target_type = await self.find_target(msg, interaction.guild)
            
            if not target:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Target Not Found",
                    description="Could not find that user or role. Please try again with a valid mention.",
                    color=EMBED_COLOR_ERROR
                )
                await msg.reply(embed=embed, delete_after=10, mention_author=False)
                return
            
            # Add to admins
            settings = self.cog.get_guild_settings(interaction.guild.id)
            if target.id not in settings['admins']:
                settings['admins'].append(target.id)
                self.cog.save_settings()
                action = "granted"
                color = EMBED_COLOR_SUCCESS
            else:
                action = "already has"
                color = EMBED_COLOR_ERROR
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Admin Updated",
                description=f"{target_type.title()} {target.mention} {action} ticket admin privileges.",
                color=color
            )
            await msg.reply(embed=embed, mention_author=False)
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Timeout",
                description="No response received. Admin addition cancelled.",
                color=EMBED_COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def remove_admin_prompt(self, interaction: discord.Interaction):
        """Prompt for removing admin"""
        embed = discord.Embed(
            title=f"{SPROUTS_ERROR} Remove Ticket Admin",
            description="Please mention the user or role you want to revoke admin privileges from.\n\n"
                       "**Example:** `@JohnDoe` or `@Admin Role`\n"
                       "**Note:** Type `cancel` to cancel this action.",
            color=EMBED_COLOR_ERROR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel
        
        try:
            msg = await interaction.client.wait_for('message', check=check, timeout=60.0)
            
            if msg.content.lower() == "cancel":
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} Cancelled",
                    description="Admin removal cancelled.",
                    color=EMBED_COLOR_ERROR
                )
                await msg.reply(embed=embed, delete_after=10, mention_author=False)
                return
            
            # Find target
            target, target_type = await self.find_target(msg, interaction.guild)
            
            if not target:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Target Not Found",
                    description="Could not find that user or role. Please try again with a valid mention.",
                    color=EMBED_COLOR_ERROR
                )
                await msg.reply(embed=embed, delete_after=10, mention_author=False)
                return
            
            # Remove from admins
            settings = self.cog.get_guild_settings(interaction.guild.id)
            if target.id in settings['admins']:
                settings['admins'].remove(target.id)
                self.cog.save_settings()
                action = "revoked from"
                color = EMBED_COLOR_SUCCESS
            else:
                action = "does not have"
                color = EMBED_COLOR_ERROR
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Admin Updated",
                description=f"{target_type.title()} {target.mention} {action} ticket admin privileges.",
                color=color
            )
            await msg.reply(embed=embed, mention_author=False)
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Timeout",
                description="No response received. Admin removal cancelled.",
                color=EMBED_COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def add_support_prompt(self, interaction: discord.Interaction):
        """Prompt for adding support"""
        embed = discord.Embed(
            title=f"{SPROUTS_INFORMATION} Add Support Staff",
            description="Please mention the user or role you want to add as support staff.\n\n"
                       "**Example:** `@JohnDoe` or `@Support Role`\n"
                       "**Note:** Type `cancel` to cancel this action.",
            color=EMBED_COLOR_INFO
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel
        
        try:
            msg = await interaction.client.wait_for('message', check=check, timeout=60.0)
            
            if msg.content.lower() == "cancel":
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} Cancelled",
                    description="Support addition cancelled.",
                    color=EMBED_COLOR_ERROR
                )
                await msg.reply(embed=embed, delete_after=10, mention_author=False)
                return
            
            # Find target
            target, target_type = await self.find_target(msg, interaction.guild)
            
            if not target:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Target Not Found",
                    description="Could not find that user or role. Please try again with a valid mention.",
                    color=EMBED_COLOR_ERROR
                )
                await msg.reply(embed=embed, delete_after=10, mention_author=False)
                return
            
            # Add to support
            settings = self.cog.get_guild_settings(interaction.guild.id)
            if target.id not in settings['support']:
                settings['support'].append(target.id)
                self.cog.save_settings()
                action = "added as"
                color = EMBED_COLOR_SUCCESS
            else:
                action = "already is"
                color = EMBED_COLOR_ERROR
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Support Updated",
                description=f"{target_type.title()} {target.mention} {action} support staff.",
                color=color
            )
            await msg.reply(embed=embed, mention_author=False)
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Timeout",
                description="No response received. Support addition cancelled.",
                color=EMBED_COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def remove_support_prompt(self, interaction: discord.Interaction):
        """Prompt for removing support"""
        embed = discord.Embed(
            title=f"{SPROUTS_WARNING} Remove Support Staff",
            description="Please mention the user or role you want to remove from support staff.\n\n"
                       "**Example:** `@JohnDoe` or `@Support Role`\n"
                       "**Note:** Type `cancel` to cancel this action.",
            color=EMBED_COLOR_WARNING
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel
        
        try:
            msg = await interaction.client.wait_for('message', check=check, timeout=60.0)
            
            if msg.content.lower() == "cancel":
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} Cancelled",
                    description="Support removal cancelled.",
                    color=EMBED_COLOR_ERROR
                )
                await msg.reply(embed=embed, delete_after=10, mention_author=False)
                return
            
            # Find target
            target, target_type = await self.find_target(msg, interaction.guild)
            
            if not target:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Target Not Found",
                    description="Could not find that user or role. Please try again with a valid mention.",
                    color=EMBED_COLOR_ERROR
                )
                await msg.reply(embed=embed, delete_after=10, mention_author=False)
                return
            
            # Remove from support
            settings = self.cog.get_guild_settings(interaction.guild.id)
            if target.id in settings['support']:
                settings['support'].remove(target.id)
                self.cog.save_settings()
                action = "removed from"
                color = EMBED_COLOR_SUCCESS
            else:
                action = "is not"
                color = EMBED_COLOR_ERROR
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Support Updated",
                description=f"{target_type.title()} {target.mention} {action} support staff.",
                color=color
            )
            await msg.reply(embed=embed, mention_author=False)
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Timeout",
                description="No response received. Support removal cancelled.",
                color=EMBED_COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def view_staff(self, interaction: discord.Interaction):
        """View all current staff"""
        settings = self.cog.get_guild_settings(interaction.guild.id)
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Staff Management Overview",
            color=EMBED_COLOR_NORMAL
        )
        
        # Get admins
        admin_list = []
        for admin_id in settings.get('admins', []):
            member = interaction.guild.get_member(admin_id) or interaction.guild.get_role(admin_id)
            if member:
                admin_list.append(f"• {member.mention}")
        
        # Get support
        support_list = []
        for support_id in settings.get('support', []):
            member = interaction.guild.get_member(support_id) or interaction.guild.get_role(support_id)
            if member:
                support_list.append(f"• {member.mention}")
        
        # Get blacklist
        blacklist_list = []
        for blacklist_id in settings.get('blacklist', []):
            member = interaction.guild.get_member(blacklist_id) or interaction.guild.get_role(blacklist_id)
            if member:
                blacklist_list.append(f"• {member.mention}")
        
        embed.add_field(
            name=f"{SPROUTS_CHECK} Ticket Admins ({len(admin_list)})",
            value="\n".join(admin_list) if admin_list else "No admins configured",
            inline=False
        )
        
        embed.add_field(
            name=f"{SPROUTS_INFORMATION} Support Staff ({len(support_list)})",
            value="\n".join(support_list) if support_list else "No support staff configured",
            inline=False
        )
        
        embed.add_field(
            name=f"{SPROUTS_ERROR} Blacklisted ({len(blacklist_list)})",
            value="\n".join(blacklist_list) if blacklist_list else "No blacklisted users/roles",
            inline=False
        )
        
        embed.set_footer(text="Use the select menu above to manage staff permissions")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def manage_blacklist_prompt(self, interaction: discord.Interaction):
        """Prompt for blacklist management"""
        embed = discord.Embed(
            title=f"{SPROUTS_ERROR} Manage Blacklist",
            description="Please mention the user or role you want to toggle on the blacklist.\n\n"
                       "**Example:** `@Spammer` or `@Banned Role`\n"
                       "**Note:** Type `cancel` to cancel this action.",
            color=EMBED_COLOR_ERROR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel
        
        try:
            msg = await interaction.client.wait_for('message', check=check, timeout=60.0)
            
            if msg.content.lower() == "cancel":
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} Cancelled",
                    description="Blacklist management cancelled.",
                    color=EMBED_COLOR_ERROR
                )
                await msg.reply(embed=embed, delete_after=10, mention_author=False)
                return
            
            # Find target
            target, target_type = await self.find_target(msg, interaction.guild)
            
            if not target:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Target Not Found",
                    description="Could not find that user or role. Please try again with a valid mention.",
                    color=EMBED_COLOR_ERROR
                )
                await msg.reply(embed=embed, delete_after=10, mention_author=False)
                return
            
            # Toggle blacklist
            settings = self.cog.get_guild_settings(interaction.guild.id)
            if target.id in settings['blacklist']:
                settings['blacklist'].remove(target.id)
                self.cog.save_settings()
                action = "removed from"
                color = EMBED_COLOR_SUCCESS
            else:
                settings['blacklist'].append(target.id)
                self.cog.save_settings()
                action = "added to"
                color = EMBED_COLOR_ERROR
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Blacklist Updated",
                description=f"{target_type.title()} {target.mention} {action} the blacklist.",
                color=color
            )
            await msg.reply(embed=embed, mention_author=False)
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Timeout",
                description="No response received. Blacklist management cancelled.",
                color=EMBED_COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def find_target(self, message, guild):
        """Find target user or role from message"""
        target = None
        target_type = "user"
        
        # Check for mentions first
        if message.mentions:
            target = message.mentions[0]
        elif message.role_mentions:
            target = message.role_mentions[0]
            target_type = "role"
        else:
            # Try to parse ID or name
            try:
                # Try as ID first
                target_id = int(message.content.strip('<@&>!'))
                target = guild.get_member(target_id) or guild.get_role(target_id)
                if target and isinstance(target, discord.Role):
                    target_type = "role"
            except ValueError:
                # Try as name
                target = discord.utils.find(lambda m: m.name.lower() == message.content.lower(), guild.members)
                if not target:
                    target = discord.utils.find(lambda r: r.name.lower() == message.content.lower(), guild.roles)
                    if target:
                        target_type = "role"
        
        return target, target_type

class StaffManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = 'src/data/staff_settings.json'
        self.settings_data = self.load_settings()
    
    def load_settings(self):
        """Load staff settings from file"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_settings(self):
        """Save staff settings to file"""
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings_data, f, indent=4)
    
    def get_guild_settings(self, guild_id):
        """Get settings for a specific guild"""
        guild_key = str(guild_id)
        if guild_key not in self.settings_data:
            self.settings_data[guild_key] = {
                'admins': [],
                'support': [],
                'blacklist': []
            }
            self.save_settings()
        return self.settings_data[guild_key]
    
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
    
    @commands.command(name="staff")
    async def staff_management(self, ctx):
        """Open the staff management interface"""
        if not await self.is_admin(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only administrators can access staff management.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Staff Management Panel",
            description="Use the select menu below to manage ticket admins, support staff, and blacklisted users.\n\n"
                       "**Features:**\n"
                       "• Add/remove ticket admins\n"
                       "• Add/remove support staff\n"
                       "• Manage blacklisted users/roles\n"
                       "• View all current staff",
            color=EMBED_COLOR_INFO
        )
        
        view = StaffManagementView(self, ctx.author.id)
        await ctx.send(embed=embed, view=view)

import asyncio

async def setup(bot):
    await bot.add_cog(StaffManager(bot))