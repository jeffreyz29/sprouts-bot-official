"""
TicketsBot-Compatible Tag Commands  
Implements the 4 tag commands from TicketsBot specification
"""

import discord
from discord.ext import commands
import json
import os
from src.config import SPROUTS_CHECK, SPROUTS_ERROR, SPROUTS_WARNING, EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR, EMBED_COLOR_HIERARCHY

import logging
logger = logging.getLogger(__name__)

class TicketTags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tags_file = 'src/data/ticket_tags.json'
        self.tags_data = self.load_tags()
    
    def load_tags(self):
        """Load tags from file"""
        if os.path.exists(self.tags_file):
            with open(self.tags_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_tags(self):
        """Save tags to file"""
        os.makedirs(os.path.dirname(self.tags_file), exist_ok=True)
        with open(self.tags_file, 'w') as f:
            json.dump(self.tags_data, f, indent=4)
    
    def get_guild_tags(self, guild_id):
        """Get tags for a specific guild"""
        if str(guild_id) not in self.tags_data:
            self.tags_data[str(guild_id)] = {}
            self.save_tags()
        return self.tags_data[str(guild_id)]
    
    async def is_staff(self, member, guild):
        """Check if user is staff (needed for tag management)"""
        # Get ticket settings cog for staff checking
        ticket_settings = self.bot.get_cog('TicketSettings')
        if ticket_settings:
            return await ticket_settings.is_support(member, guild)
        
        # Fallback to admin permissions
        return member.guild_permissions.administrator
    
    # TAG COMMANDS (4 commands)
    
    @commands.group(name="managetags", invoke_without_command=True)
    async def manage_tags(self, ctx):
        """Manage tags command group"""
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can manage tags.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Tag Management",
            description="Available tag management commands:",
            color=EMBED_COLOR_HIERARCHY
        )
        
        embed.add_field(
            name="Commands",
            value="`s.managetags add <tag_id> <content>` - Add a new tag\n"
                  "`s.managetags delete <tag_id>` - Delete a tag\n"
                  "`s.managetags list` - List all existing tags",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @manage_tags.command(name="add")
    async def add_tag(self, ctx, tag_id: str = None, *, content: str = None):
        """Adds a new tag"""
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can manage tags.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        if not tag_id or not content:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Missing Parameters",
                description="Usage: `s.managetags add <tag_id> <content>`\n\n"
                           "Example: `s.managetags add welcome Welcome to our support! Please describe your issue.`",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=15)
            return
        
        # Clean tag ID (remove special characters, make lowercase)
        tag_id = tag_id.lower().replace(" ", "_")
        
        guild_tags = self.get_guild_tags(ctx.guild.id)
        
        if tag_id in guild_tags:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Tag Exists",
                description=f"Tag `{tag_id}` already exists. Delete it first or use a different ID.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Add tag
        guild_tags[tag_id] = {
            'content': content,
            'author': ctx.author.id,
            'created_at': ctx.message.created_at.isoformat(),
            'uses': 0
        }
        
        self.save_tags()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Tag Added",
            description=f"Tag `{tag_id}` has been created successfully!",
            color=EMBED_COLOR_NORMAL
        )
        
        embed.add_field(
            name="Content Preview",
            value=content[:100] + ("..." if len(content) > 100 else ""),
            inline=False
        )
        
        embed.add_field(
            name="Usage",
            value=f"`s.tag {tag_id}` - Send this tag",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @manage_tags.command(name="delete")
    async def delete_tag(self, ctx, tag_id: str = None):
        """Deletes a tag"""
        if not await self.is_staff(ctx.author, ctx.guild):
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Access Denied",
                description="Only staff can manage tags.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        if not tag_id:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Missing Tag ID",
                description="Usage: `s.managetags delete <tag_id>`\n\n"
                           "Use `s.managetags list` to see available tags.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        tag_id = tag_id.lower()
        guild_tags = self.get_guild_tags(ctx.guild.id)
        
        if tag_id not in guild_tags:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Tag Not Found",
                description=f"Tag `{tag_id}` does not exist.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Delete tag
        deleted_tag = guild_tags.pop(tag_id)
        self.save_tags()
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Tag Deleted",
            description=f"Tag `{tag_id}` has been deleted successfully.",
            color=EMBED_COLOR_NORMAL
        )
        
        embed.add_field(
            name="Deleted Content",
            value=deleted_tag['content'][:100] + ("..." if len(deleted_tag['content']) > 100 else ""),
            inline=False
        )
        
        embed.add_field(
            name="Statistics",
            value=f"Used {deleted_tag.get('uses', 0)} times",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @manage_tags.command(name="list")
    async def list_tags(self, ctx):
        """Lists all existing tags"""
        guild_tags = self.get_guild_tags(ctx.guild.id)
        
        if not guild_tags:
            embed = discord.Embed(
                title=f"{SPROUTS_WARNING} No Tags",
                description="No tags have been created for this server yet.\n\n"
                           "Use `s.managetags add <tag_id> <content>` to create your first tag!",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Server Tags ({len(guild_tags)})",
            color=EMBED_COLOR_NORMAL
        )
        
        # Sort tags by usage
        sorted_tags = sorted(guild_tags.items(), key=lambda x: x[1].get('uses', 0), reverse=True)
        
        tag_list = []
        for tag_id, tag_data in sorted_tags[:20]:  # Limit to 20 tags
            uses = tag_data.get('uses', 0)
            content_preview = tag_data['content'][:50] + ("..." if len(tag_data['content']) > 50 else "")
            tag_list.append(f"`{tag_id}` - {content_preview} ({uses} uses)")
        
        embed.add_field(
            name="Available Tags",
            value="\n".join(tag_list) if tag_list else "No tags found",
            inline=False
        )
        
        if len(guild_tags) > 20:
            embed.add_field(
                name="Notice",
                value=f"Showing top 20 tags. Total: {len(guild_tags)} tags",
                inline=False
            )
        
        embed.add_field(
            name="Usage",
            value="`s.tag <tag_id>` - Send a tag\n`s.managetags add/delete` - Manage tags",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="tag")
    async def send_tag(self, ctx, tag_id: str = None):
        """Sends a message snippet"""
        if not tag_id:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Missing Tag ID",
                description="Usage: `s.tag <tag_id>`\n\n"
                           "Use `s.managetags list` to see available tags.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        tag_id = tag_id.lower()
        guild_tags = self.get_guild_tags(ctx.guild.id)
        
        if tag_id not in guild_tags:
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Tag Not Found",
                description=f"Tag `{tag_id}` does not exist.\n\n"
                           "Use `s.managetags list` to see available tags.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Get tag data
        tag_data = guild_tags[tag_id]
        content = tag_data['content']
        
        # Update usage count
        guild_tags[tag_id]['uses'] = guild_tags[tag_id].get('uses', 0) + 1
        self.save_tags()
        
        # Process variables in content (basic ones)
        content = content.replace("{user}", ctx.author.mention)
        content = content.replace("{server}", ctx.guild.name)
        content = content.replace("{channel}", ctx.channel.mention)
        
        # Delete the command message
        try:
            await ctx.message.delete()
        except:
            pass
        
        # Send tag content as embed for better formatting
        embed = discord.Embed(
            description=content,
            color=EMBED_COLOR_NORMAL
        )
        
        embed.set_footer(
            text=f"Tag: {tag_id} | Sent by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TicketTags(bot))