"""
Advanced Variable Processing System for Discord Bot
Supports comprehensive variable replacement with math, logic, and dynamic content
"""

import discord
import re
import random
import math
from datetime import datetime
from typing import Optional, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)

class VariableProcessor:
    """Advanced variable processor supporting complex variables and operations"""
    
    def __init__(self, bot=None):
        self.bot = bot
        
    async def process_variables(
        self, 
        text: str, 
        user: discord.Member = None, 
        guild: discord.Guild = None, 
        channel: discord.TextChannel = None,
        ticket_data: Dict[str, Any] = None
    ) -> str:
        """Process all variables in text with comprehensive support"""
        if not text:
            return text
            
        processed_text = text
        
        # Process in order of complexity
        processed_text = await self._process_math_variables(processed_text)
        processed_text = await self._process_logic_variables(processed_text, user, guild, channel, ticket_data)
        processed_text = await self._process_time_variables(processed_text)
        processed_text = await self._process_user_variables(processed_text, user)
        processed_text = await self._process_server_variables(processed_text, guild)
        processed_text = await self._process_channel_variables(processed_text, channel)
        processed_text = await self._process_ticket_variables(processed_text, ticket_data, user, guild)
        
        return processed_text
    
    async def _process_user_variables(self, text: str, user: discord.Member = None) -> str:
        """Process user-related variables"""
        if not user:
            return text
            
        variables = {
            r'\$\(user\.name\)': user.name,
            r'\$\(user\.mention\)': user.mention,
            r'\$\(user\.id\)': str(user.id),
            r'\$\(user\.nick\)': user.display_name if hasattr(user, 'display_name') else user.name,
            r'\$\(user\.tag\)': str(user),
            r'\$\(user\.avatar\)': user.display_avatar.url,
            r'\$\(user\.joined\)': user.joined_at.strftime('%B %d, %Y') if hasattr(user, 'joined_at') and user.joined_at else 'Unknown',
            r'\$\(user\.created\)': user.created_at.strftime('%B %d, %Y')
        }
        
        for pattern, replacement in variables.items():
            text = re.sub(pattern, str(replacement), text)
            
        return text
    
    async def _process_server_variables(self, text: str, guild: discord.Guild = None) -> str:
        """Process server-related variables"""
        if not guild:
            return text
            
        variables = {
            r'\$\(server\.name\)': guild.name,
            r'\$\(server\.membercount\)': str(guild.member_count),
            r'\$\(server\.owner\)': str(guild.owner) if guild.owner else 'Unknown',
            r'\$\(server\.id\)': str(guild.id),
            r'\$\(server\.icon\)': guild.icon.url if guild.icon else 'No icon',
            r'\$\(server\.created\)': guild.created_at.strftime('%B %d, %Y'),
            r'\$\(server\.boosts\)': str(guild.premium_subscription_count or 0),
            r'\$\(server\.channels\)': str(len(guild.channels))
        }
        
        for pattern, replacement in variables.items():
            text = re.sub(pattern, str(replacement), text)
            
        return text
    
    async def _process_channel_variables(self, text: str, channel: discord.TextChannel = None) -> str:
        """Process channel-related variables"""
        if not channel:
            return text
            
        variables = {
            r'\$\(channel\.name\)': channel.name,
            r'\$\(channel\.id\)': str(channel.id),
            r'\$\(channel\.mention\)': channel.mention,
            r'\$\(channel\.topic\)': channel.topic or 'No topic set',
            r'\$\(channel\.category\)': channel.category.name if channel.category else 'No category',
            r'\$\(channel\.position\)': str(channel.position),
            r'\$\(channel\.created\)': channel.created_at.strftime('%B %d, %Y'),
            r'\$\(channel\.nsfw\)': 'Yes' if channel.nsfw else 'No',
            r'\$\(channel\.slowmode\)': f"{channel.slowmode_delay} seconds" if channel.slowmode_delay else 'Disabled'
        }
        
        for pattern, replacement in variables.items():
            text = re.sub(pattern, str(replacement), text)
            
        return text
    
    async def _process_time_variables(self, text: str) -> str:
        """Process time-related variables"""
        now = datetime.now()
        
        variables = {
            r'\$\(time\)': now.strftime('%H:%M:%S'),
            r'\$\(date\)': now.strftime('%m/%d/%Y'),
            r'\$\(datetime\)': now.strftime('%m/%d/%Y %H:%M:%S'),
            r'\$\(year\)': str(now.year),
            r'\$\(month\)': now.strftime('%B'),
            r'\$\(day\)': str(now.day),
            r'\$\(weekday\)': now.strftime('%A'),
            r'\$\(timestamp\)': str(int(now.timestamp()))
        }
        
        for pattern, replacement in variables.items():
            text = re.sub(pattern, replacement, text)
            
        return text
    
    async def _process_math_variables(self, text: str) -> str:
        """Process math operations"""
        # Match $(math:expression) pattern
        math_pattern = r'\$\(math:([^)]+)\)'
        matches = re.finditer(math_pattern, text)
        
        for match in matches:
            expression = match.group(1)
            try:
                # Safe evaluation of basic math expressions
                allowed_chars = set('0123456789+-*/()., ')
                if all(c in allowed_chars for c in expression):
                    result = eval(expression)
                    text = text.replace(match.group(0), str(result))
                else:
                    text = text.replace(match.group(0), 'Invalid math expression')
            except Exception as e:
                text = text.replace(match.group(0), 'Math error')
                logger.warning(f"Math expression error: {e}")
                
        return text
    
    async def _process_logic_variables(
        self, 
        text: str, 
        user: discord.Member = None, 
        guild: discord.Guild = None, 
        channel: discord.TextChannel = None,
        ticket_data: Dict[str, Any] = None
    ) -> str:
        """Process logic operations and advanced functions"""
        
        # Process random numbers $(random:1-100)
        random_pattern = r'\$\(random:(\d+)-(\d+)\)'
        matches = re.finditer(random_pattern, text)
        for match in matches:
            min_val, max_val = int(match.group(1)), int(match.group(2))
            result = random.randint(min_val, max_val)
            text = text.replace(match.group(0), str(result))
        
        # Process random choice $(choose:a|b|c)
        choose_pattern = r'\$\(choose:([^)]+)\)'
        matches = re.finditer(choose_pattern, text)
        for match in matches:
            choices = match.group(1).split('|')
            result = random.choice(choices)
            text = text.replace(match.group(0), result)
        
        # Process string length $(len:text)
        len_pattern = r'\$\(len:([^)]+)\)'
        matches = re.finditer(len_pattern, text)
        for match in matches:
            string_content = match.group(1)
            result = len(string_content)
            text = text.replace(match.group(0), str(result))
        
        # Process uppercase $(upper:text)
        upper_pattern = r'\$\(upper:([^)]+)\)'
        matches = re.finditer(upper_pattern, text)
        for match in matches:
            string_content = match.group(1)
            result = string_content.upper()
            text = text.replace(match.group(0), result)
        
        # Process conditional logic $(if:condition?true:false)
        if_pattern = r'\$\(if:([^?]+)\?([^:]+):([^)]+)\)'
        matches = re.finditer(if_pattern, text)
        for match in matches:
            condition, true_val, false_val = match.group(1), match.group(2), match.group(3)
            
            # Evaluate simple conditions
            result = false_val  # default
            if condition == 'user.bot' and user:
                result = true_val if user.bot else false_val
            elif condition.startswith('user.') and user:
                # Handle user property checks
                prop = condition.split('.')[1]
                if hasattr(user, prop):
                    value = getattr(user, prop)
                    result = true_val if value else false_val
            
            text = text.replace(match.group(0), result)
        
        return text
    
    async def _process_ticket_variables(
        self, 
        text: str, 
        ticket_data: Dict[str, Any] = None,
        user: discord.Member = None,
        guild: discord.Guild = None
    ) -> str:
        """Process ticket-related variables"""
        if not ticket_data:
            return text
            
        # Get bot instance for user lookups
        bot = self.bot
        
        # Process basic ticket variables
        ticket_id = ticket_data.get('ticket_id', 'Unknown')
        creator_id = ticket_data.get('creator_id')
        creator = bot.get_user(creator_id) if bot and creator_id else None
        creator_name = creator.display_name if creator else 'Unknown'
        
        claimed_by_id = ticket_data.get('claimed_by')
        claimed_by = bot.get_user(claimed_by_id) if bot and claimed_by_id else None
        staff_name = claimed_by.display_name if claimed_by else 'Unassigned'
        
        variables = {
            r'\$\(ticket\.id\)': str(ticket_id),
            r'\$\(ticket\.creator\)': creator_name,
            r'\$\(ticket\.category\)': ticket_data.get('category', 'General'),
            r'\$\(ticket\.status\)': ticket_data.get('status', 'open'),
            r'\$\(ticket\.staff\)': staff_name,
            r'\$\(ticket\.claimed\)': 'Yes' if claimed_by_id else 'No',
            r'\$\(ticket\.tags\)': ', '.join(ticket_data.get('tags', [])) or 'None',
            r'\$\(ticket\.panel\)': ticket_data.get('panel_name', 'Direct'),
            r'\$\(ticket\.transcript\)': f"transcript_{ticket_id}.html"
        }
        
        for pattern, replacement in variables.items():
            text = re.sub(pattern, str(replacement), text)
            
        return text
    
    def get_all_variables_help(self) -> str:
        """Return comprehensive help text for all available variables"""
        help_text = """
**Available Variables for Embeds and Messages**

**User Variables**
`$(user.name)` - User's username
`$(user.mention)` - Mentions the user  
`$(user.id)` - User's Discord ID
`$(user.nick)` - User's server nickname
`$(user.tag)` - Full username with discriminator
`$(user.avatar)` - User's avatar image URL
`$(user.joined)` - Date user joined the server
`$(user.created)` - Date user account was created

**Server Variables**
`$(server.name)` - Server name
`$(server.membercount)` - Total member count
`$(server.owner)` - Server owner's name
`$(server.id)` - Server's Discord ID
`$(server.icon)` - Server icon image URL
`$(server.created)` - Date server was created
`$(server.boosts)` - Number of server boosts
`$(server.channels)` - Total channel count

**Channel Variables**
`$(channel.name)` - Current channel name
`$(channel.id)` - Channel's Discord ID
`$(channel.mention)` - Mentions the current channel
`$(channel.topic)` - Channel's topic description
`$(channel.category)` - Channel's category name
`$(channel.position)` - Channel's position in list
`$(channel.created)` - Date channel was created
`$(channel.nsfw)` - Whether channel is NSFW
`$(channel.slowmode)` - Channel slowmode delay

**Time Variables**
`$(time)` - Current time
`$(date)` - Current date
`$(datetime)` - Current date and time
`$(year)` - Current year
`$(month)` - Current month name
`$(day)` - Current day of month
`$(weekday)` - Current day of week
`$(timestamp)` - Unix timestamp

**Math & Logic Variables**
`$(math:5+5)` - Basic math operations
`$(random:1-100)` - Random number in range
`$(choose:a|b|c)` - Random choice from list
`$(if:user.bot?Bot:Human)` - Conditional logic
`$(len:text)` - String length calculator
`$(upper:text)` - Convert to uppercase

**Advanced Ticket Variables**
`$(ticket.id)` - Ticket's unique ID number
`$(ticket.creator)` - User who created ticket
`$(ticket.category)` - Ticket category name
`$(ticket.status)` - Current ticket status
`$(ticket.staff)` - Staff member assigned
`$(ticket.claimed)` - Is ticket claimed (Yes/No)
`$(ticket.tags)` - List of ticket tags
`$(ticket.panel)` - Panel used to create ticket
`$(ticket.transcript)` - Transcript download URL
        """
        return help_text.strip()

# Global variable processor instance
variable_processor = VariableProcessor()

# Initialize with bot when available
def init_variable_processor(bot):
    """Initialize the variable processor with bot instance"""
    variable_processor.bot = bot