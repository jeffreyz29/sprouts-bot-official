"""
Advanced Rate Limit Monitoring and Management System
Enterprise-grade rate limit handling with clustering support
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import discord
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)

@dataclass
class RateLimitEvent:
    """Rate limit event data structure"""
    timestamp: float
    endpoint: str
    retry_after: float
    scope: str  # global, guild, channel, user
    guild_id: Optional[int] = None
    channel_id: Optional[int] = None
    user_id: Optional[int] = None
    shard_id: Optional[int] = None

@dataclass
class ShardMetrics:
    """Shard performance metrics"""
    shard_id: int
    latency: float
    guilds: int
    rate_limits: int
    last_heartbeat: float
    status: str  # connected, disconnected, reconnecting
    events_processed: int

class RateLimitMonitor:
    """Advanced rate limit monitoring and alerting system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.rate_limit_events: List[RateLimitEvent] = []
        self.shard_metrics: Dict[int, ShardMetrics] = {}
        self.alert_channel_id = None
        self.cluster_id = 0  # For multi-cluster deployments
        self.max_events = 1000  # Keep last 1000 events
        self.alert_threshold = 5  # Alert after 5 rate limits in 5 minutes
        
        # Start monitoring tasks
        self.cleanup_old_events.start()
        self.monitor_shards.start()
        self.rate_limit_alerts.start()
        
    def setup_alert_channel(self, channel_id: int):
        """Set the channel for rate limit alerts"""
        self.alert_channel_id = channel_id
        logger.info(f"Rate limit alerts will be sent to channel {channel_id}")
        
    async def on_rate_limited(self, rate_limit_data: Dict[str, Any]):
        """Handle rate limit events from Discord"""
        try:
            event = RateLimitEvent(
                timestamp=time.time(),
                endpoint=rate_limit_data.get('endpoint', 'unknown'),
                retry_after=rate_limit_data.get('retry_after', 0),
                scope=rate_limit_data.get('scope', 'unknown'),
                guild_id=rate_limit_data.get('guild_id'),
                channel_id=rate_limit_data.get('channel_id'), 
                user_id=rate_limit_data.get('user_id'),
                shard_id=rate_limit_data.get('shard_id', 0)
            )
            
            self.rate_limit_events.append(event)
            
            # Log the rate limit
            logger.warning(
                f"Rate limited on {event.endpoint} "
                f"(retry after {event.retry_after}s, scope: {event.scope})"
            )
            
            # Update shard metrics
            if event.shard_id is not None:
                self.update_shard_rate_limit(event.shard_id)
                
        except Exception as e:
            logger.error(f"Error handling rate limit event: {e}")
            
    def update_shard_rate_limit(self, shard_id: int):
        """Update rate limit count for a shard"""
        if shard_id not in self.shard_metrics:
            self.shard_metrics[shard_id] = ShardMetrics(
                shard_id=shard_id,
                latency=0.0,
                guilds=0,
                rate_limits=0,
                last_heartbeat=time.time(),
                status='unknown',
                events_processed=0
            )
        
        self.shard_metrics[shard_id].rate_limits += 1
        
    @tasks.loop(minutes=5)
    async def cleanup_old_events(self):
        """Clean up old rate limit events"""
        try:
            cutoff_time = time.time() - (24 * 3600)  # 24 hours ago
            self.rate_limit_events = [
                event for event in self.rate_limit_events 
                if event.timestamp > cutoff_time
            ]
            
            # Keep only the most recent events if we have too many
            if len(self.rate_limit_events) > self.max_events:
                self.rate_limit_events = self.rate_limit_events[-self.max_events:]
                
        except Exception as e:
            logger.error(f"Error cleaning up rate limit events: {e}")
            
    @tasks.loop(minutes=1)
    async def monitor_shards(self):
        """Monitor shard health and update metrics"""
        try:
            if not hasattr(self.bot, 'shards'):
                return
                
            for shard_id, shard in self.bot.shards.items():
                # Update shard metrics
                if shard_id not in self.shard_metrics:
                    self.shard_metrics[shard_id] = ShardMetrics(
                        shard_id=shard_id,
                        latency=0.0,
                        guilds=0,
                        rate_limits=0,
                        last_heartbeat=time.time(),
                        status='unknown',
                        events_processed=0
                    )
                
                metrics = self.shard_metrics[shard_id]
                metrics.latency = shard.latency * 1000  # Convert to ms
                metrics.guilds = len([g for g in self.bot.guilds if g.shard_id == shard_id])
                metrics.last_heartbeat = time.time()
                
                # Determine shard status
                if shard.is_closed():
                    metrics.status = 'disconnected'
                elif shard.latency > 0.5:  # High latency
                    metrics.status = 'degraded'
                else:
                    metrics.status = 'connected'
                    
        except Exception as e:
            logger.error(f"Error monitoring shards: {e}")
            
    @tasks.loop(minutes=5)
    async def rate_limit_alerts(self):
        """Check for rate limit patterns and send alerts"""
        try:
            if not self.alert_channel_id:
                return
                
            # Check recent rate limits
            recent_cutoff = time.time() - 300  # 5 minutes ago
            recent_events = [
                event for event in self.rate_limit_events
                if event.timestamp > recent_cutoff
            ]
            
            if len(recent_events) >= self.alert_threshold:
                await self.send_rate_limit_alert(recent_events)
                
        except Exception as e:
            logger.error(f"Error checking rate limit alerts: {e}")
            
    async def send_rate_limit_alert(self, events: List[RateLimitEvent]):
        """Send rate limit alert to designated channel"""
        try:
            channel = self.bot.get_channel(self.alert_channel_id)
            if not channel:
                return
                
            # Group events by endpoint
            endpoint_counts = {}
            for event in events:
                endpoint_counts[event.endpoint] = endpoint_counts.get(event.endpoint, 0) + 1
                
            # Create alert embed
            embed = discord.Embed(
                title="🚨 Rate Limit Alert",
                description=f"Detected {len(events)} rate limits in the last 5 minutes",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            
            # Add endpoint breakdown
            endpoint_list = []
            for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True):
                endpoint_list.append(f"• `{endpoint}`: {count} hits")
                
            if endpoint_list:
                embed.add_field(
                    name="Affected Endpoints",
                    value="\n".join(endpoint_list[:10]),  # Show top 10
                    inline=False
                )
                
            # Add shard information if available
            shard_issues = []
            for shard_id, metrics in self.shard_metrics.items():
                if metrics.rate_limits > 0:
                    shard_issues.append(f"Shard {shard_id}: {metrics.rate_limits} limits")
                    
            if shard_issues:
                embed.add_field(
                    name="Shard Impact",
                    value="\n".join(shard_issues[:5]),
                    inline=False
                )
                
            embed.add_field(
                name="Cluster Info",
                value=f"Cluster ID: {self.cluster_id}\nBot: {self.bot.user.name}",
                inline=True
            )
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error sending rate limit alert: {e}")
            
    def get_rate_limit_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get rate limit statistics for the specified time period"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            recent_events = [
                event for event in self.rate_limit_events
                if event.timestamp > cutoff_time
            ]
            
            # Calculate statistics
            total_events = len(recent_events)
            endpoint_counts = {}
            scope_counts = {}
            
            for event in recent_events:
                endpoint_counts[event.endpoint] = endpoint_counts.get(event.endpoint, 0) + 1
                scope_counts[event.scope] = scope_counts.get(event.scope, 0) + 1
                
            return {
                'total_rate_limits': total_events,
                'time_period_hours': hours,
                'endpoints': dict(sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)),
                'scopes': dict(sorted(scope_counts.items(), key=lambda x: x[1], reverse=True)),
                'shard_metrics': {
                    shard_id: asdict(metrics) 
                    for shard_id, metrics in self.shard_metrics.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {}
            
    def get_shard_status(self) -> Dict[str, Any]:
        """Get current shard status and health metrics"""
        try:
            current_time = time.time()
            shard_status = {}
            
            for shard_id, metrics in self.shard_metrics.items():
                time_since_heartbeat = current_time - metrics.last_heartbeat
                
                shard_status[f"shard_{shard_id}"] = {
                    'id': shard_id,
                    'status': metrics.status,
                    'latency_ms': round(metrics.latency, 2),
                    'guilds': metrics.guilds,
                    'rate_limits': metrics.rate_limits,
                    'events_processed': metrics.events_processed,
                    'heartbeat_age_seconds': round(time_since_heartbeat, 2),
                    'healthy': time_since_heartbeat < 120 and metrics.latency < 1000  # 2 min timeout, 1s latency
                }
                
            return {
                'cluster_id': self.cluster_id,
                'total_shards': len(shard_status),
                'healthy_shards': sum(1 for s in shard_status.values() if s['healthy']),
                'shards': shard_status
            }
            
        except Exception as e:
            logger.error(f"Error getting shard status: {e}")
            return {}

    async def export_metrics(self, filepath: str):
        """Export rate limit and shard metrics to JSON file"""
        try:
            data = {
                'export_timestamp': time.time(),
                'cluster_id': self.cluster_id,
                'rate_limit_events': [asdict(event) for event in self.rate_limit_events],
                'shard_metrics': {str(k): asdict(v) for k, v in self.shard_metrics.items()},
                'statistics': self.get_rate_limit_stats(24)
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")