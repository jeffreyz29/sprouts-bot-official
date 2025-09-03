"""
Variable Processing System for Sprouts Bot
Handles dynamic variable replacement in messages and embeds
"""

import discord
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class VariableProcessor:
    """Process variables in text content"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def process_variables(self, text: str, guild: Optional[discord.Guild] = None, 
                              user: Optional[discord.User] = None, 
                              channel: Optional[discord.TextChannel] = None,
                              member: Optional[discord.Member] = None,
                              ticket_data: Optional[dict] = None) -> str:
        """Process all variables in the given text"""
        if not text:
            return text
            
        try:
            # Process different variable types
            text = await self._process_user_variables(text, user, member)
            text = await self._process_server_variables(text, guild)
            text = await self._process_channel_variables(text, channel)
            text = await self._process_time_variables(text)
            text = await self._process_ticket_variables(text, ticket_data)
            text = await self._process_special_variables(text)
            
            return text
        except Exception as e:
            logger.error(f"Error processing variables: {e}")
            return text
    
    async def _process_user_variables(self, text: str, user: Optional[discord.User], 
                                    member: Optional[discord.Member]) -> str:
        """Parse user-related variables"""
        if not user and not member:
            return text
            
        target_user = member or user
        
        variables = {
            # User variables
            '$(user.name)': target_user.name if target_user else '',
            '$(user.nick)': member.nick if member and member.nick else '',
            '$(user.mention)': target_user.mention if target_user else '',
            '$(user.id)': str(target_user.id) if target_user else '',
            '$(user.tag)': str(target_user) if target_user else '',
            '$(user.displayname)': target_user.display_name if target_user else '',
            '$(user.avatar)': target_user.display_avatar.url if target_user else '',
            '$(user.joined)': member.joined_at.strftime('%B %d, %Y') if member and member.joined_at else '',
            '$(user.created)': target_user.created_at.strftime('%B %d, %Y') if target_user else '',
            '$(user.bot)': 'true' if target_user and target_user.bot else 'false',
            '$(user.roles)': ', '.join([role.name for role in member.roles[1:]]) if member else '',  # Skip @everyone
            '$(user.leave)': 'true',  # For leave events
            
            # Member aliases
            '$(member)': target_user.mention if target_user else '',
            '$(member.name)': target_user.name if target_user else '',
            '$(member.mention)': target_user.mention if target_user else '',
            '$(member.displayname)': target_user.display_name if target_user else '',
            '$(member.id)': str(target_user.id) if target_user else '',
            '$(member.avatar)': target_user.display_avatar.url if target_user else '',
            '$(member.tag)': str(target_user) if target_user else '',
        }
        
        for var, value in variables.items():
            text = text.replace(var, str(value))
            
        return text
    
    async def _process_server_variables(self, text: str, guild: Optional[discord.Guild]) -> str:
        """Parse server-related variables"""
        if not guild:
            return text
            
        variables = {
            # Server variables
            '$(server.name)': guild.name,
            '$(server.id)': str(guild.id),
            '$(server.members)': str(guild.member_count),
            '$(server.owner)': guild.owner.display_name if guild.owner else '',
            '$(server.ownermention)': guild.owner.mention if guild.owner else '',
            '$(server.icon)': guild.icon.url if guild.icon else '',
            '$(server.created)': guild.created_at.strftime('%B %d, %Y'),
            '$(server.boosts)': str(guild.premium_subscription_count or 0),
            '$(server.channels)': str(len(guild.channels)),
            '$(server.roles)': str(len(guild.roles)),
            '$(server.region)': str(guild.preferred_locale) if guild.preferred_locale else 'Unknown',
            
            # Guild aliases
            '$(guild.name)': guild.name,
            '$(guild.icon)': guild.icon.url if guild.icon else '',
            '$(guild.members)': str(guild.member_count),
            '$(guild.members.ordinal)': self._get_ordinal_number(guild.member_count or 0),
            '$(guild.age)': str((datetime.now() - guild.created_at.replace(tzinfo=None)).days),
        }
        
        for var, value in variables.items():
            text = text.replace(var, str(value))
            
        return text
    
    async def _process_channel_variables(self, text: str, channel: Optional[discord.TextChannel]) -> str:
        """Parse channel-related variables"""
        if not channel:
            return text
            
        variables = {
            '$(channel.name)': channel.name,
            '$(channel.id)': str(channel.id),
            '$(channel.mention)': channel.mention,
            '$(channel.category)': channel.category.name if channel.category else '',
            '$(channel.topic)': channel.topic or '',
            '$(channel.position)': str(channel.position),
        }
        
        for var, value in variables.items():
            text = text.replace(var, str(value))
            
        return text
    
    async def _process_time_variables(self, text: str) -> str:
        """Parse time-related variables"""
        now = datetime.now()
        
        variables = {
            '$(time)': now.strftime('%I:%M %p'),
            '$(date)': now.strftime('%B %d, %Y'),
            '$(datetime)': now.strftime('%B %d, %Y at %I:%M %p'),
            '$(timestamp)': str(int(now.timestamp())),
            '$(year)': str(now.year),
            '$(month)': now.strftime('%B'),
            '$(day)': str(now.day),
            '$(weekday)': now.strftime('%A'),
            '$(hour)': str(now.hour),
            '$(minute)': str(now.minute),
        }
        
        for var, value in variables.items():
            text = text.replace(var, str(value))
            
        return text
    
    async def _process_ticket_variables(self, text: str, ticket_data: Optional[dict]) -> str:
        """Parse ticket-related variables"""
        if not ticket_data:
            return text
            
        variables = {
            '$(ticket.id)': str(ticket_data.get('id', '')),
            '$(ticket.category)': str(ticket_data.get('category', '')),
            '$(ticket.created)': str(ticket_data.get('created', '')),
            '$(ticket.status)': str(ticket_data.get('status', 'Open')),
            '$(ticket.creator)': str(ticket_data.get('creator', '')),
            '$(ticket.staff)': str(ticket_data.get('staff', 'None')),
        }
        
        for var, value in variables.items():
            text = text.replace(var, str(value))
            
        return text
    
    async def _process_special_variables(self, text: str) -> str:
        """Process special variables like random, math, conditionals"""
        import random
        import re
        
        # Process random ranges
        random_pattern = r'\$\(random:(\d+)-(\d+)\)'
        for match in re.finditer(random_pattern, text):
            min_val = int(match.group(1))
            max_val = int(match.group(2))
            random_num = random.randint(min_val, max_val)
            text = text.replace(match.group(0), str(random_num))
        
        # Process random choices
        choice_pattern = r'\$\((?:random|choose):([^)]+)\)'
        for match in re.finditer(choice_pattern, text):
            choices = match.group(1).split('|')
            chosen = random.choice(choices)
            text = text.replace(match.group(0), chosen)
        
        # Process basic math
        math_pattern = r'\$\(math:([^)]+)\)'
        for match in re.finditer(math_pattern, text):
            try:
                # Simple eval for basic math (be careful with this in production)
                expr = match.group(1)
                # Only allow basic math operations
                if all(c in '0123456789+-*/.() ' for c in expr):
                    result = eval(expr)
                    text = text.replace(match.group(0), str(result))
            except:
                pass  # Keep original if math fails
        
        # Process basic conditionals
        if_pattern = r'\$\(if:([^?]+)\?([^:]*):([^)]*)\)'
        for match in re.finditer(if_pattern, text):
            condition = match.group(1)
            true_val = match.group(2)
            false_val = match.group(3)
            
            # Simple condition checking
            if 'user.bot' in condition:
                # This would need actual user context
                result = false_val  # Default to false
            else:
                result = false_val
            
            text = text.replace(match.group(0), result)
        
        return text
    
    def _get_ordinal_number(self, num: int) -> str:
        """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
        if 10 <= num % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
        return f"{num}{suffix}"

class VariableParser:
    """Variable parser for showing available variables"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def get_available_variables(self):
        """Return dictionary of all available variables with descriptions"""
        return {
            # User Variables
            '$(user.name)': 'User\'s username',
            '$(user.nick)': 'User\'s server nickname',
            '$(user.mention)': 'Mentions the user',
            '$(user.id)': 'User\'s Discord ID',
            '$(user.tag)': 'Full username with discriminator',
            '$(user.displayname)': 'Display name shown in server',
            '$(user.avatar)': 'User\'s avatar image URL',
            '$(user.joined)': 'Date user joined the server',
            '$(user.created)': 'Date user account was created',
            '$(user.bot)': 'Whether user is a bot (true/false)',
            '$(user.roles)': 'List of user\'s roles',
            '$(user.leave)': 'Leave-related variable (for leave events)',
            
            # Member aliases (for welcome system)
            '$(member)': 'Mentions the member (same as user)',
            '$(member.name)': 'Member\'s username',
            '$(member.mention)': 'Mentions the member',
            '$(member.displayname)': 'Member\'s display name',
            '$(member.id)': 'Member\'s Discord ID',
            '$(member.avatar)': 'Member\'s avatar URL',
            '$(member.tag)': 'Member\'s full tag',
            
            # Server Variables
            '$(server.name)': 'Server name',
            '$(server.id)': 'Server\'s Discord ID',
            '$(server.members)': 'Total member count',
            '$(server.owner)': 'Server owner\'s name',
            '$(server.ownermention)': 'Mentions server owner',
            '$(server.icon)': 'Server icon image URL',
            '$(server.created)': 'Date server was created',
            '$(server.boosts)': 'Number of server boosts',
            '$(server.channels)': 'Total channel count',
            '$(server.roles)': 'Total role count',
            '$(server.region)': 'Server\'s voice region',
            
            # Guild aliases (alternative server names)
            '$(guild.name)': 'Current server\'s name',
            '$(guild.icon)': 'Current server\'s icon',
            '$(guild.members)': 'Current server\'s members count (ex. 123)',
            '$(guild.members.ordinal)': 'Current server\'s members count in ordinal (ex. 123rd)',
            '$(guild.age)': 'Current server\'s age in days',
            
            # Channel Variables
            '$(channel.name)': 'Current channel name',
            '$(channel.id)': 'Channel\'s Discord ID',
            '$(channel.mention)': 'Mentions the current channel',
            '$(channel.category)': 'Channel\'s category name',
            '$(channel.topic)': 'Channel\'s topic description',
            '$(channel.position)': 'Channel\'s position in list',
            
            # Time & Date Variables
            '$(time)': 'Current time (12-hour format)',
            '$(date)': 'Current date (long format)',
            '$(datetime)': 'Current date and time combined',
            '$(timestamp)': 'Unix timestamp',
            '$(year)': 'Current year',
            '$(month)': 'Current month name',
            '$(day)': 'Current day of month',
            '$(weekday)': 'Current day of week',
            '$(hour)': 'Current hour',
            '$(minute)': 'Current minute',
            
            # Special Variables
            '$(random:1-100)': 'Random number between range',
            '$(random:word1|word2)': 'Random choice from options',
            '$(choose:a|b|c)': 'Randomly selects from list',
            '$(math:5+5)': 'Performs basic math calculations',
            '$(math:user.id/1000)': 'Math with other variables',
            '$(if:user.bot?Bot:Human)': 'Conditional text output',
            
            # Ticket Variables
            '$(ticket.id)': 'Ticket\'s unique ID number',
            '$(ticket.category)': 'Ticket category name',
            '$(ticket.created)': 'Date ticket was created',
            '$(ticket.status)': 'Current ticket status',
            '$(ticket.creator)': 'User who created ticket',
            '$(ticket.staff)': 'Staff member assigned to ticket',
        }