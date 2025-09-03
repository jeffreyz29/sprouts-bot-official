"""
Discord Bot Web Viewer
Simple Flask web interface to monitor bot status, logs, and statistics
"""

from flask import Flask, render_template, jsonify
import json
import os
import datetime
import psutil
from threading import Thread
import time
import logging

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotStats:
    """Class to track and provide bot statistics"""
    
    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.command_count = 0
        self.dm_count = 0
        self.guild_count = 0
        self.last_update = datetime.datetime.now()
        self.bot_user = None
        
        # Cached features data
        self.features_data = {
            'server_monitors': 0,
            'auto_responders': 0,
            'active_reminders': 0,
            'sticky_messages': 0,
            'total_tickets': 0,
            'configured_guilds': 0
        }
        
        # Cached environment data
        self.environment_data = {
            'default_prefix': '',
            'bot_status': '',
            'bot_activity': ''
        }
    
    def update_stats(self):
        """Update bot statistics including features and environment data"""
        try:
            # Update features data from files
            self.update_features_data()
            
            # Update environment data
            self.update_environment_data()
            
            self.last_update = datetime.datetime.now()
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
    
    def update_guild_count(self, count):
        """Update guild count"""
        self.guild_count = count
        self.last_update = datetime.datetime.now()
    
    def update_features_data(self):
        """Update cached features data"""
        try:
            # Load server stats monitoring
            server_stats_data = {}
            if os.path.exists('data/server_stats.json'):
                with open('data/server_stats.json', 'r') as f:
                    server_stats_data = json.load(f)
            
            # Load auto responders
            auto_responders = {}
            if os.path.exists('data/autoresponders.json'):
                with open('data/autoresponders.json', 'r') as f:
                    auto_responders = json.load(f)
            
            # Load reminders
            reminders_data = {}
            if os.path.exists('data/reminders.json'):
                with open('data/reminders.json', 'r') as f:
                    reminders_data = json.load(f)
            
            # Load sticky messages
            sticky_messages = {}
            if os.path.exists('data/sticky_messages.json'):
                with open('data/sticky_messages.json', 'r') as f:
                    sticky_messages = json.load(f)
            
            # Load ticket data
            ticket_data = {}
            if os.path.exists('tickets_data.json'):
                with open('tickets_data.json', 'r') as f:
                    ticket_data = json.load(f)
            
            # Load guild settings
            guild_settings = {}
            if os.path.exists('guild_settings.json'):
                with open('guild_settings.json', 'r') as f:
                    guild_settings = json.load(f)
            
            # Update cached features data
            self.features_data = {
                'server_monitors': len(server_stats_data),
                'auto_responders': sum(len(responders) for responders in auto_responders.values()),
                'active_reminders': sum(len(reminders) for reminders in reminders_data.values()),
                'sticky_messages': sum(len(messages) for messages in sticky_messages.values()),
                'total_tickets': len(ticket_data.get('tickets', {})),
                'configured_guilds': len(guild_settings)
            }
        except Exception as e:
            logger.error(f"Error updating features data: {e}")
    
    def update_environment_data(self):
        """Update cached environment data"""
        try:
            import os
            self.environment_data = {
                'default_prefix': os.getenv('DEFAULT_PREFIX', 's.'),
                'bot_status': os.getenv('BOT_STATUS', 'Unknown'),
                'bot_activity': os.getenv('BOT_ACTIVITY_NAME', 'Unknown')
            }
        except Exception as e:
            logger.error(f"Error updating environment data: {e}")
    
    def get_uptime(self):
        """Get bot uptime"""
        delta = datetime.datetime.now() - self.start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"
    
    def get_system_stats(self):
        """Get comprehensive system resource usage"""
        try:
            # CPU Information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count_physical = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            # Memory Information
            memory = psutil.virtual_memory()
            try:
                swap = psutil.swap_memory()
            except (FileNotFoundError, OSError):
                # Handle systems without /proc/vmstat (like containerized environments)
                swap = type('SwapMemory', (), {'total': 0, 'used': 0, 'percent': 0})()
            
            # Disk Information
            disk = psutil.disk_usage('/')
            
            # Network Information
            try:
                net_io = psutil.net_io_counters()
            except (FileNotFoundError, OSError):
                # Handle systems without /proc/net/dev
                net_io = type('NetworkIO', (), {'bytes_sent': 0, 'bytes_recv': 0, 'packets_sent': 0, 'packets_recv': 0})()
            
            # Process Information
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'cores_physical': cpu_count_physical,
                    'cores_logical': cpu_count_logical,
                    'frequency_current': cpu_freq.current if cpu_freq else 0,
                    'frequency_max': cpu_freq.max if cpu_freq else 0,
                },
                'memory': {
                    'percent': memory.percent,
                    'used': memory.used,
                    'available': memory.available,
                    'total': memory.total,
                    'cached': memory.cached if hasattr(memory, 'cached') else 0,
                    'buffers': memory.buffers if hasattr(memory, 'buffers') else 0,
                },
                'swap': {
                    'percent': swap.percent if swap.total > 0 else 0,
                    'used': swap.used,
                    'total': swap.total,
                },
                'disk': {
                    'percent': (disk.used / disk.total) * 100,
                    'used': disk.used,
                    'free': disk.free,
                    'total': disk.total,
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                },
                'process': {
                    'cpu_percent': process_cpu,
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'memory_percent': process.memory_percent(),
                    'pid': process.pid,
                    'num_threads': process.num_threads(),
                }
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {
                'cpu': {'percent': 0, 'cores_physical': 0, 'cores_logical': 0, 'frequency_current': 0, 'frequency_max': 0},
                'memory': {'percent': 0, 'used': 0, 'available': 0, 'total': 0, 'cached': 0, 'buffers': 0},
                'swap': {'percent': 0, 'used': 0, 'total': 0},
                'disk': {'percent': 0, 'used': 0, 'free': 0, 'total': 0},
                'network': {'bytes_sent': 0, 'bytes_recv': 0, 'packets_sent': 0, 'packets_recv': 0},
                'process': {'cpu_percent': 0, 'memory_rss': 0, 'memory_vms': 0, 'memory_percent': 0, 'pid': 0, 'num_threads': 0}
            }

# Initialize stats
bot_stats = BotStats()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint for comprehensive bot statistics"""
    try:
        # Load logging settings
        dm_settings = {}
        if os.path.exists('dm_settings.json'):
            with open('dm_settings.json', 'r') as f:
                dm_settings = json.load(f)
        
        # Load command logging settings
        cmd_settings = {}
        if os.path.exists('cmd_logging_settings.json'):
            with open('cmd_logging_settings.json', 'r') as f:
                cmd_settings = json.load(f)
        
        # Load global cooldown settings
        cooldown_settings = {}
        if os.path.exists('global_cooldown.json'):
            with open('global_cooldown.json', 'r') as f:
                cooldown_settings = json.load(f)
        
        # Features data is now cached and updated periodically
        # No need to load from files every API call
        
        # Get system stats
        system_stats = bot_stats.get_system_stats()
        
        # Format bytes function
        def format_bytes(bytes_value):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.2f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.2f} PB"
        
        # Try to get bot information if available
        bot_info = {}
        try:
            # This would need to be set by the main bot when it starts
            if hasattr(bot_stats, 'bot_user') and bot_stats.bot_user:
                bot_info = {
                    'name': bot_stats.bot_user.display_name,
                    'avatar_url': str(bot_stats.bot_user.display_avatar.url),
                    'id': bot_stats.bot_user.id
                }
        except:
            pass

        stats = {
            'uptime': bot_stats.get_uptime(),
            'last_update': bot_stats.last_update.strftime('%Y-%m-%d %H:%M:%S'),
            'bot_info': bot_info,
            'logging': {
                'dm_log_configured': bool(os.getenv('LOG_DMS_CHANNEL')),
                'cmd_log_configured': bool(os.getenv('LOG_COMMANDS_CHANNEL')),
                'guild_log_configured': False,  # Ticket logging handled within ticket system
                'total_guilds': bot_stats.guild_count,
                'cmd_settings': cmd_settings
            },
            'cooldown': {
                'enabled': cooldown_settings.get('cooldown_seconds', 0) > 0,
                'seconds': cooldown_settings.get('cooldown_seconds', 0)
            },
            'features': bot_stats.features_data,
            'system': system_stats,
            'system_formatted': {
                'cpu_percent': f"{system_stats['cpu']['percent']:.1f}%",
                'cpu_cores': f"{system_stats['cpu']['cores_physical']} physical / {system_stats['cpu']['cores_logical']} logical",
                'cpu_frequency': f"{system_stats['cpu']['frequency_current']:.0f} MHz" if system_stats['cpu']['frequency_current'] else 'N/A',
                'memory_usage': f"{system_stats['memory']['percent']:.1f}%",
                'memory_used': format_bytes(system_stats['memory']['used']),
                'memory_total': format_bytes(system_stats['memory']['total']),
                'memory_available': format_bytes(system_stats['memory']['available']),
                'swap_usage': f"{system_stats['swap']['percent']:.1f}%" if system_stats['swap']['total'] > 0 else 'No swap',
                'swap_used': format_bytes(system_stats['swap']['used']) if system_stats['swap']['total'] > 0 else 'N/A',
                'swap_total': format_bytes(system_stats['swap']['total']) if system_stats['swap']['total'] > 0 else 'N/A',
                'disk_usage': f"{system_stats['disk']['percent']:.1f}%",
                'disk_used': format_bytes(system_stats['disk']['used']),
                'disk_free': format_bytes(system_stats['disk']['free']),
                'disk_total': format_bytes(system_stats['disk']['total']),
                'network_sent': format_bytes(system_stats['network']['bytes_sent']),
                'network_recv': format_bytes(system_stats['network']['bytes_recv']),
                'process_cpu': f"{system_stats['process']['cpu_percent']:.1f}%",
                'process_memory': f"{system_stats['process']['memory_percent']:.1f}%",
                'process_rss': format_bytes(system_stats['process']['memory_rss']),
                'process_threads': system_stats['process']['num_threads']
            },
            'environment': bot_stats.environment_data
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """API endpoint for recent log entries - only show if logging is enabled"""
    try:
        # Check if any logging systems are enabled
        dm_settings = {}
        if os.path.exists('dm_settings.json'):
            with open('dm_settings.json', 'r') as f:
                dm_settings = json.load(f)
        
        cmd_settings = {}
        if os.path.exists('cmd_logging_settings.json'):
            with open('cmd_logging_settings.json', 'r') as f:
                cmd_settings = json.load(f)
        
        # Check if any logging is enabled
        dm_logging_enabled = dm_settings.get('enabled', False)
        cmd_logging_enabled = any(guild_data.get('enabled', False) for guild_data in cmd_settings.values())
        
        # Only show logs if logging is enabled in support server
        if not (dm_logging_enabled or cmd_logging_enabled):
            return jsonify({'logs': ['Logging is disabled - no logs to display'], 'logging_disabled': True})
        
        logs = []
        log_file = 'bot.log'
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Get last 100 lines
                recent_logs = lines[-100:] if len(lines) > 100 else lines
                logs = [line.strip() for line in recent_logs if line.strip()]
        
        return jsonify({'logs': logs, 'logging_disabled': False})
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500

def update_stats_periodically():
    """Background task to update stats periodically"""
    while True:
        try:
            bot_stats.update_stats()
            time.sleep(10)  # Update every 10 seconds for better responsiveness
        except Exception as e:
            logger.error(f"Error in stats update loop: {e}")
            time.sleep(30)

def run_web_server():
    """Run the Flask web server"""
    try:
        # Initialize stats on startup
        bot_stats.update_stats()
        
        # Start stats update thread
        stats_thread = Thread(target=update_stats_periodically, daemon=True)
        stats_thread.start()
        
        logger.info("Starting web viewer on port 5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f"Error running web server: {e}")

if __name__ == '__main__':
    run_web_server()