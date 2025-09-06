"""
Discord-Tickets GitHub Official Transcript System
Implements the official discord-tickets bot transcript system using chat_exporter
"""

import discord
import asyncio
import os
import io
from datetime import datetime
from typing import Optional, Union
import logging
import chat_exporter  # Official discord-tickets transcript library

logger = logging.getLogger(__name__)

class DiscordTicketsTranscriptSystem:
    """Official Discord-Tickets transcript system implementation"""
    
    def __init__(self, bot=None):
        self.bot = bot
        self.transcript_dir = "src/data/transcripts"
        
        # Production domain configuration
        production_domain = os.getenv('PRODUCTION_DOMAIN', 'sproutsbot.app')
        
        if 'ondigitalocean.app' in os.getenv('DOMAIN', '') or production_domain != 'sproutsbot.app':
            self.base_url = f"https://{production_domain}"
        elif os.getenv('REPLIT_DEV_DOMAIN'):
            # Use https for Replit dev domain
            self.base_url = f"https://{os.getenv('REPLIT_DEV_DOMAIN')}"
        else:
            self.base_url = "http://localhost:5000"
        
        logger.info(f"Discord-Tickets transcript system initialized with URL: {self.base_url}")
    
    async def generate_transcript(
        self,
        channel: discord.TextChannel,
        ticket_id: Union[int, str],
        creator: Optional[discord.Member] = None,
        staff: Optional[discord.Member] = None,
        reason: Optional[str] = None,
        close_reason: Optional[str] = None
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Create transcript using the official discord-tickets method
        Returns: (transcript_url, file_path)
        """
        try:
            # Ensure transcript directory exists
            os.makedirs(self.transcript_dir, exist_ok=True)
            
            logger.info(f"Creating transcript for ticket {ticket_id} using discord-tickets system")
            
            # Generate transcript using official discord-tickets method
            transcript = await chat_exporter.export(
                channel,
                limit=None,  # Export all messages
                tz_info="UTC",
                military_time=False,  # 12-hour format
                bot=self.bot,
                fancy_times=True  # Show "Today", "Yesterday" format
            )
            
            if transcript is None:
                logger.error(f"Failed to generate transcript for ticket {ticket_id}")
                return None, None
            
            # Save transcript to file
            filename = f"ticket_{ticket_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            file_path = os.path.join(self.transcript_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            # Generate clean URL using ticket ID
            transcript_url = f"{self.base_url}/ticket/transcripts/view={ticket_id}"
            
            logger.info(f"Discord-tickets transcript created: {filename}")
            return transcript_url, file_path
            
        except Exception as e:
            logger.error(f"Error creating transcript for ticket {ticket_id}: {e}")
            return None, None
    
    async def export_as_file(
        self,
        channel: discord.TextChannel,
        ticket_id: Union[int, str]
    ) -> Optional[discord.File]:
        """Export transcript as Discord file attachment (official discord-tickets style)"""
        try:
            transcript = await chat_exporter.export(
                channel,
                limit=None,
                tz_info="UTC", 
                military_time=False,
                bot=self.bot,
                fancy_times=True
            )
            
            if transcript is None:
                return None
            
            # Create file object for Discord
            transcript_file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"ticket-{ticket_id}-transcript.html"
            )
            
            return transcript_file
            
        except Exception as e:
            logger.error(f"Error exporting transcript as file: {e}")
            return None
    
    async def quick_export(self, channel: discord.TextChannel) -> Optional[discord.Message]:
        """Quick export function (discord-tickets style) - exports and sends to same channel"""
        try:
            transcript_file = await self.export_as_file(channel, channel.id)
            
            if transcript_file is None:
                return None
            
            embed = discord.Embed(
                title="📜 Channel Transcript",
                description=f"Transcript for {channel.mention}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            
            message = await channel.send(embed=embed, file=transcript_file)
            return message
            
        except Exception as e:
            logger.error(f"Error in quick export: {e}")
            return None

# Global instance using official discord-tickets pattern
transcript_generator = DiscordTicketsTranscriptSystem()