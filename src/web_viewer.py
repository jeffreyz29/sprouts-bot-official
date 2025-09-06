"""
Web Statistics Module for SPROUTS Bot
Provides bot statistics and monitoring data
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BotStats:
    """Bot statistics tracking"""
    
    def __init__(self):
        self.stats = {
            "commands_used": 0,
            "guilds": 0,
            "users": 0,
            "uptime": "0 seconds"
        }
        self.bot_user = None
    
    def update_stats(self, bot):
        """Update bot statistics"""
        try:
            self.stats["guilds"] = len(bot.guilds)
            self.stats["users"] = sum(guild.member_count for guild in bot.guilds)
        except Exception as e:
            logger.error(f"Error updating bot stats: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current bot statistics"""
        return self.stats.copy()
    
    def increment_command_usage(self):
        """Increment command usage counter"""
        self.stats["commands_used"] += 1
    
    def update_guild_count(self, guild_count):
        """Update guild count"""
        self.stats["guilds"] = guild_count
    
    def update_member_count(self, member_count):
        """Update member count"""
        self.stats["users"] = member_count

# Global instance
bot_stats = BotStats()

def run_web_server():
    """Run the Flask web server for bot monitoring"""
    try:
        from flask import Flask, jsonify, render_template_string
        
        app = Flask(__name__)
        
        @app.route('/')
        def dashboard():
            """Main dashboard page"""
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>SPROUTS Bot Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
                    .stat-card { background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 5px; }
                    h1 { color: #2ecc71; text-align: center; }
                    .status { color: #27ae60; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🌱 SPROUTS Bot Dashboard</h1>
                    <div class="stat-card">
                        <h3>Bot Status: <span class="status">Online</span></h3>
                    </div>
                    <div class="stat-card">
                        <h3>Guilds: {{ stats.guilds }}</h3>
                    </div>
                    <div class="stat-card">
                        <h3>Users: {{ stats.users }}</h3>
                    </div>
                    <div class="stat-card">
                        <h3>Commands Used: {{ stats.commands_used }}</h3>
                    </div>
                    <div class="stat-card">
                        <h3>Uptime: {{ stats.uptime }}</h3>
                    </div>
                </div>
            </body>
            </html>
            """
            return render_template_string(html_template, stats=bot_stats.get_stats())
        
        @app.route('/api/stats')
        def api_stats():
            """API endpoint for bot statistics"""
            return jsonify(bot_stats.get_stats())
        
        @app.route('/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({"status": "healthy", "service": "sprouts-bot"})
        
        @app.route('/ticket/transcripts/view=<ticket_id>')
        def serve_transcript_by_id(ticket_id):
            """Serve HTML transcript files by ticket ID"""
            try:
                import os
                import glob
                from flask import send_file
                
                # Security: Only allow alphanumeric ticket IDs
                if not ticket_id.replace('_', '').replace('-', '').isalnum():
                    return "Invalid ticket ID", 404
                
                # Find the transcript file that matches this ticket ID
                transcript_dir = os.path.join(os.path.dirname(__file__), 'data', 'transcripts')
                pattern = f"ticket_{ticket_id}_*.html"
                matching_files = glob.glob(os.path.join(transcript_dir, pattern))
                
                if matching_files:
                    # Get the most recent transcript if multiple exist
                    latest_transcript = max(matching_files, key=os.path.getmtime)
                    return send_file(latest_transcript, mimetype='text/html')
                else:
                    return "Transcript not found", 404
                    
            except Exception as e:
                logger.error(f"Error serving transcript for ticket {ticket_id}: {e}")
                return "Error loading transcript", 500
        
        @app.route('/transcripts/<filename>')
        def serve_transcript_legacy(filename):
            """Legacy transcript route for backward compatibility"""
            try:
                import os
                from flask import send_file
                
                # Security: Only allow .html files and prevent directory traversal
                if not filename.endswith('.html') or '..' in filename or '/' in filename:
                    return "Invalid file", 404
                
                transcript_path = os.path.join('src/data/transcripts', filename)
                if os.path.exists(transcript_path):
                    return send_file(transcript_path, mimetype='text/html')
                else:
                    return "Transcript not found", 404
                    
            except Exception as e:
                logger.error(f"Error serving transcript {filename}: {e}")
                return "Error loading transcript", 500
        
        # Run the Flask server
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        raise