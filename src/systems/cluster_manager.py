"""
Advanced Cluster Management System for SPROUTS Bot
Handles multi-instance deployment and coordination
"""

import asyncio
import logging
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import discord
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)

@dataclass
class ClusterInfo:
    """Information about a bot cluster instance"""
    cluster_id: int
    instance_id: str
    start_time: float
    shard_range: tuple  # (min_shard, max_shard)
    total_shards: int
    guilds: int
    users: int
    status: str  # starting, running, stopping, error
    last_heartbeat: float
    version: str
    environment: str  # production, staging, development

@dataclass
class ShardDistribution:
    """Shard distribution across clusters"""
    total_shards: int
    clusters: Dict[int, tuple]  # cluster_id: (min_shard, max_shard)
    recommended_guilds_per_shard: int = 1000

class ClusterManager:
    """Manages bot clustering and shard distribution"""
    
    def __init__(self, bot, cluster_id: int = 0, total_clusters: int = 1):
        self.bot = bot
        self.cluster_id = cluster_id
        self.total_clusters = total_clusters
        self.instance_id = f"sprouts-{cluster_id}-{int(time.time())}"
        self.start_time = time.time()
        self.cluster_info = {}
        self.shard_distribution = None
        
        # Calculate shard range for this cluster
        self.shard_range = self.calculate_shard_range()
        
        # Environment detection
        self.environment = self.detect_environment()
        
        # Start cluster management tasks
        self.heartbeat_task.start()
        self.cluster_monitor.start()
        
    def detect_environment(self) -> str:
        """Detect the deployment environment"""
        if os.getenv('REPL_ID'):
            return 'replit'
        elif os.getenv('DYNO'):
            return 'heroku'
        elif os.getenv('DO_APP_NAME'):
            return 'digitalocean'
        elif os.getenv('NODE_ENV') == 'production':
            return 'production'
        else:
            return 'development'
            
    def calculate_shard_range(self) -> tuple:
        """Calculate the shard range for this cluster"""
        if self.total_clusters <= 1:
            return (0, self.bot.shard_count - 1 if self.bot.shard_count else 0)
            
        shards_per_cluster = max(1, (self.bot.shard_count or 1) // self.total_clusters)
        min_shard = self.cluster_id * shards_per_cluster
        max_shard = min(min_shard + shards_per_cluster - 1, (self.bot.shard_count or 1) - 1)
        
        return (min_shard, max_shard)
        
    def get_cluster_info(self) -> ClusterInfo:
        """Get current cluster information"""
        try:
            return ClusterInfo(
                cluster_id=self.cluster_id,
                instance_id=self.instance_id,
                start_time=self.start_time,
                shard_range=self.shard_range,
                total_shards=self.bot.shard_count or 1,
                guilds=len(self.bot.guilds),
                users=len(self.bot.users),
                status='running' if self.bot.is_ready() else 'starting',
                last_heartbeat=time.time(),
                version=getattr(self.bot, 'version', '1.0.0'),
                environment=self.environment
            )
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return ClusterInfo(
                cluster_id=self.cluster_id,
                instance_id=self.instance_id,
                start_time=self.start_time,
                shard_range=self.shard_range,
                total_shards=1,
                guilds=0,
                users=0,
                status='error',
                last_heartbeat=time.time(),
                version='unknown',
                environment=self.environment
            )
            
    @tasks.loop(minutes=1)
    async def heartbeat_task(self):
        """Send heartbeat to indicate cluster is alive"""
        try:
            info = self.get_cluster_info()
            self.cluster_info[self.cluster_id] = info
            
            # Log cluster status
            logger.info(
                f"Cluster {self.cluster_id} heartbeat - "
                f"Shards: {self.shard_range[0]}-{self.shard_range[1]}, "
                f"Guilds: {info.guilds}, Users: {info.users}, "
                f"Status: {info.status}"
            )
            
        except Exception as e:
            logger.error(f"Error in cluster heartbeat: {e}")
            
    @tasks.loop(minutes=5)
    async def cluster_monitor(self):
        """Monitor cluster health and performance"""
        try:
            # Check for cluster issues
            info = self.get_cluster_info()
            
            # Monitor guild distribution
            if info.guilds > 0:
                guilds_per_shard = info.guilds / max(1, (self.shard_range[1] - self.shard_range[0] + 1))
                
                if guilds_per_shard > 2000:  # Warning threshold
                    logger.warning(
                        f"Cluster {self.cluster_id} has high guild density: "
                        f"{guilds_per_shard:.1f} guilds per shard"
                    )
                    
            # Monitor memory usage if available
            try:
                import psutil
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 85:
                    logger.warning(f"Cluster {self.cluster_id} high memory usage: {memory_percent}%")
            except ImportError:
                pass
                
        except Exception as e:
            logger.error(f"Error in cluster monitoring: {e}")
            
    def calculate_optimal_shards(self, guild_count: int) -> int:
        """Calculate optimal number of shards based on guild count"""
        # Discord recommendation: ~1000 guilds per shard
        # Add buffer for growth
        base_shards = max(1, guild_count // 1000)
        
        # Add 25% buffer for growth
        optimal_shards = max(1, int(base_shards * 1.25))
        
        # Ensure it's a power of 2 for even distribution
        import math
        return 2 ** math.ceil(math.log2(optimal_shards))
        
    def recommend_cluster_count(self, guild_count: int, target_guilds_per_cluster: int = 5000) -> int:
        """Recommend number of clusters based on guild count"""
        if guild_count <= target_guilds_per_cluster:
            return 1
            
        return max(1, guild_count // target_guilds_per_cluster)
        
    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get comprehensive cluster statistics"""
        try:
            info = self.get_cluster_info()
            uptime_seconds = time.time() - self.start_time
            
            # Calculate rates
            guilds_per_hour = (info.guilds / max(1, uptime_seconds)) * 3600 if uptime_seconds > 0 else 0
            
            # Shard health
            shard_health = {}
            if hasattr(self.bot, 'shards'):
                for shard_id, shard in self.bot.shards.items():
                    if self.shard_range[0] <= shard_id <= self.shard_range[1]:
                        shard_health[shard_id] = {
                            'latency_ms': round(shard.latency * 1000, 2),
                            'connected': not shard.is_closed(),
                            'guilds': len([g for g in self.bot.guilds if g.shard_id == shard_id])
                        }
                        
            return {
                'cluster_info': asdict(info),
                'uptime_seconds': round(uptime_seconds, 2),
                'uptime_human': self.format_uptime(uptime_seconds),
                'performance': {
                    'guilds_per_hour': round(guilds_per_hour, 2),
                    'guilds_per_shard': round(info.guilds / max(1, len(shard_health)), 2),
                    'users_per_guild': round(info.users / max(1, info.guilds), 2)
                },
                'shard_health': shard_health,
                'recommendations': {
                    'optimal_shards': self.calculate_optimal_shards(info.guilds),
                    'recommended_clusters': self.recommend_cluster_count(info.guilds),
                    'current_efficiency': min(100, (1000 / max(1, info.guilds / max(1, len(shard_health)))) * 100)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cluster stats: {e}")
            return {}
            
    def format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        try:
            uptime = timedelta(seconds=int(seconds))
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except Exception:
            return "unknown"
            
    async def graceful_shutdown(self):
        """Perform graceful shutdown of the cluster"""
        try:
            logger.info(f"Starting graceful shutdown of cluster {self.cluster_id}")
            
            # Update status
            if self.cluster_id in self.cluster_info:
                self.cluster_info[self.cluster_id].status = 'stopping'
                
            # Stop background tasks
            self.heartbeat_task.cancel()
            self.cluster_monitor.cancel()
            
            # Close bot connection
            if not self.bot.is_closed():
                await self.bot.close()
                
            logger.info(f"Cluster {self.cluster_id} shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
            
    def export_cluster_metrics(self, filepath: str):
        """Export cluster metrics to file"""
        try:
            data = {
                'export_timestamp': time.time(),
                'cluster_stats': self.get_cluster_stats(),
                'all_clusters': {str(k): asdict(v) for k, v in self.cluster_info.items()},
                'shard_distribution': {
                    'total_shards': self.bot.shard_count or 1,
                    'this_cluster_range': self.shard_range,
                    'total_clusters': self.total_clusters
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Cluster metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting cluster metrics: {e}")