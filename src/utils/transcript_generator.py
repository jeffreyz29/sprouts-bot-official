"""
Advanced Transcript System for Discord Tickets
Generates HTML log viewer URLs instead of plain text files
"""

import discord
import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging
import aiohttp
import base64

logger = logging.getLogger(__name__)

class TranscriptGenerator:
    """Generate beautiful HTML transcripts for ticket conversations"""
    
    def __init__(self, bot=None):
        self.bot = bot
        self.transcript_dir = "src/data/transcripts"
        self.base_url = "http://localhost:5000"  # Local web server URL
        
    async def generate_transcript(
        self, 
        channel: discord.TextChannel, 
        ticket_id: int,
        creator: discord.Member = None,
        staff: discord.Member = None,
        reason: str = None,
        close_reason: str = None
    ) -> str:
        """Generate transcript and return log viewer URL"""
        
        try:
            # Create transcript directory if it doesn't exist
            os.makedirs(self.transcript_dir, exist_ok=True)
            
            # Collect all messages from the ticket channel
            messages = await self._collect_messages(channel)
            
            # Generate HTML transcript
            html_content = await self._generate_html_transcript(
                messages, ticket_id, creator, staff, reason, close_reason
            )
            
            # Save HTML file
            filename = f"ticket_{ticket_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.transcript_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate proper web viewer URL
            log_url = f"{self.base_url}/transcripts/{filename}"
            
            logger.info(f"Generated transcript for ticket {ticket_id}: {filename}")
            return log_url, filepath
            
        except Exception as e:
            logger.error(f"Error generating transcript for ticket {ticket_id}: {e}")
            return None, None
    
    async def _collect_messages(self, channel: discord.TextChannel) -> List[Dict]:
        """Collect all messages from the ticket channel"""
        messages = []
        
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                # Skip bot system messages that aren't important
                if message.author.bot and message.content.startswith(("Ticket created", "User added", "User removed")):
                    continue
                    
                message_data = {
                    'id': message.id,
                    'author': {
                        'name': message.author.display_name,
                        'username': str(message.author),
                        'avatar': message.author.display_avatar.url,
                        'id': message.author.id,
                        'bot': message.author.bot,
                        'color': self._get_user_color(message.author)
                    },
                    'content': message.content or '',
                    'timestamp': message.created_at.isoformat(),
                    'edited': message.edited_at.isoformat() if message.edited_at else None,
                    'attachments': [
                        {
                            'url': att.url,
                            'filename': att.filename,
                            'size': att.size
                        } for att in message.attachments
                    ],
                    'embeds': [
                        {
                            'title': embed.title,
                            'description': embed.description,
                            'color': embed.color.value if embed.color else None,
                            'fields': [
                                {
                                    'name': field.name,
                                    'value': field.value,
                                    'inline': field.inline
                                } for field in embed.fields
                            ] if embed.fields else []
                        } for embed in message.embeds
                    ],
                    'reactions': [
                        {
                            'emoji': str(reaction.emoji),
                            'count': reaction.count
                        } for reaction in message.reactions
                    ]
                }
                messages.append(message_data)
                
        except Exception as e:
            logger.error(f"Error collecting messages: {e}")
            
        return messages
    
    def _get_user_color(self, user: discord.Member) -> str:
        """Get user's role color or default"""
        if hasattr(user, 'color') and user.color.value != 0:
            return f"#{user.color.value:06x}"
        return "#7289da"  # Discord blurple default
    
    async def _generate_html_transcript(
        self,
        messages: List[Dict],
        ticket_id: int,
        creator: discord.Member = None,
        staff: discord.Member = None,
        reason: str = None,
        close_reason: str = None
    ) -> str:
        """Generate beautiful HTML transcript"""
        
        # Ticket metadata
        metadata = {
            'ticket_id': ticket_id,
            'creator': {
                'name': creator.display_name if creator else 'Unknown',
                'username': str(creator) if creator else 'Unknown',
                'avatar': creator.display_avatar.url if creator else '',
                'id': creator.id if creator else 0
            },
            'staff': {
                'name': staff.display_name if staff else 'Unassigned',
                'username': str(staff) if staff else 'Unassigned',
                'avatar': staff.display_avatar.url if staff else '',
                'id': staff.id if staff else 0
            },
            'reason': reason or 'No reason provided',
            'close_reason': close_reason or 'No close reason provided',
            'created_at': datetime.now().isoformat(),
            'message_count': len(messages)
        }
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticket #{ticket_id} Transcript</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #36393f;
            color: #dcddde;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: #2f3136;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 20px;
            border-left: 4px solid #7289da;
        }}
        
        .ticket-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .info-card {{
            background: #40444b;
            padding: 16px;
            border-radius: 6px;
        }}
        
        .info-card h3 {{
            color: #7289da;
            font-size: 14px;
            text-transform: uppercase;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        
        .user-info {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .avatar {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #7289da;
        }}
        
        .messages {{
            background: #2f3136;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .message {{
            padding: 12px 20px;
            border-bottom: 1px solid #3a3e44;
            display: flex;
            gap: 12px;
        }}
        
        .message:hover {{
            background: #32353b;
        }}
        
        .message-avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            flex-shrink: 0;
            background: #7289da;
        }}
        
        .message-content {{
            flex: 1;
            min-width: 0;
        }}
        
        .message-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }}
        
        .message-author {{
            font-weight: 500;
            color: #ffffff;
        }}
        
        .message-timestamp {{
            font-size: 12px;
            color: #72767d;
        }}
        
        .bot-badge {{
            background: #5865f2;
            color: white;
            font-size: 10px;
            padding: 1px 4px;
            border-radius: 3px;
            text-transform: uppercase;
            font-weight: 500;
        }}
        
        .message-text {{
            color: #dcddde;
            word-wrap: break-word;
            white-space: pre-wrap;
        }}
        
        .attachment {{
            background: #40444b;
            border-radius: 4px;
            padding: 8px;
            margin-top: 8px;
            display: inline-block;
        }}
        
        .embed {{
            border-left: 4px solid #7289da;
            background: #2f3136;
            padding: 12px;
            margin-top: 8px;
            border-radius: 0 4px 4px 0;
        }}
        
        .embed-title {{
            color: #ffffff;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .embed-description {{
            color: #dcddde;
            margin-bottom: 8px;
        }}
        
        .embed-field {{
            margin-bottom: 8px;
        }}
        
        .embed-field-name {{
            color: #ffffff;
            font-weight: 600;
            font-size: 14px;
        }}
        
        .embed-field-value {{
            color: #dcddde;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #72767d;
            font-size: 14px;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .message {{
                padding: 8px 12px;
            }}
            
            .ticket-info {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Ticket #{metadata['ticket_id']} Transcript</h1>
            <p>Complete conversation log from this support ticket</p>
            
            <div class="ticket-info">
                <div class="info-card">
                    <h3>Opened By</h3>
                    <div class="user-info">
                        <img src="{metadata['creator']['avatar']}" alt="Avatar" class="avatar" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSI+PHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiBmaWxsPSIjNzI4OWRhIi8+PC9zdmc+'">
                        <div>
                            <div style="font-weight: 600;">{metadata['creator']['name']}</div>
                            <div style="font-size: 12px; color: #72767d;">{metadata['creator']['username']}</div>
                        </div>
                    </div>
                </div>
                
                <div class="info-card">
                    <h3>Assigned Staff</h3>
                    <div class="user-info">
                        <img src="{metadata['staff']['avatar']}" alt="Avatar" class="avatar" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSI+PHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiBmaWxsPSIjNzI4OWRhIi8+PC9zdmc+'">
                        <div>
                            <div style="font-weight: 600;">{metadata['staff']['name']}</div>
                            <div style="font-size: 12px; color: #72767d;">{metadata['staff']['username']}</div>
                        </div>
                    </div>
                </div>
                
                <div class="info-card">
                    <h3>Reason</h3>
                    <p>{metadata['reason']}</p>
                </div>
                
                <div class="info-card">
                    <h3>Close Reason</h3>
                    <p>{metadata['close_reason']}</p>
                </div>
                
                <div class="info-card">
                    <h3>Statistics</h3>
                    <p><strong>{metadata['message_count']}</strong> messages</p>
                    <p><strong>{datetime.now().strftime('%B %d, %Y')}</strong></p>
                </div>
            </div>
        </div>
        
        <div class="messages">
"""
        
        # Add messages
        for msg in messages:
            timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
            formatted_time = timestamp.strftime('%m/%d/%Y %I:%M %p')
            
            html_template += f"""
            <div class="message">
                <img src="{msg['author']['avatar']}" alt="Avatar" class="message-avatar" 
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSI+PHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjNzI4OWRhIi8+PC9zdmc+'">
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author" style="color: {msg['author']['color']}">{msg['author']['name']}</span>
                        {f'<span class="bot-badge">BOT</span>' if msg['author']['bot'] else ''}
                        <span class="message-timestamp">{formatted_time}</span>
                    </div>
                    <div class="message-text">{self._escape_html(msg['content'])}</div>
            """
            
            # Add attachments
            for attachment in msg['attachments']:
                html_template += f"""
                    <div class="attachment">
                        📎 <a href="{attachment['url']}" target="_blank">{attachment['filename']}</a>
                        <span style="color: #72767d;">({self._format_file_size(attachment['size'])})</span>
                    </div>
                """
            
            # Add embeds
            for embed in msg['embeds']:
                embed_color = f"#{embed['color']:06x}" if embed['color'] else "#7289da"
                html_template += f"""
                    <div class="embed" style="border-left-color: {embed_color}">
                        {f'<div class="embed-title">{self._escape_html(embed["title"])}</div>' if embed['title'] else ''}
                        {f'<div class="embed-description">{self._escape_html(embed["description"])}</div>' if embed['description'] else ''}
                """
                
                for field in embed['fields']:
                    html_template += f"""
                        <div class="embed-field">
                            <div class="embed-field-name">{self._escape_html(field['name'])}</div>
                            <div class="embed-field-value">{self._escape_html(field['value'])}</div>
                        </div>
                    """
                
                html_template += "</div>"
            
            html_template += """
                </div>
            </div>
            """
        
        # Close HTML
        html_template += f"""
        </div>
        
        <div class="footer">
            <p>Generated by Sprouts Bot • {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>Ticket #{ticket_id} • {len(messages)} messages archived</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_template
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

# Global transcript generator instance
transcript_generator = TranscriptGenerator()