"""
Cluster Management Commands for SPROUTS Bot
Integrates with existing rate limit and shard monitoring
"""

import discord
from discord.ext import commands
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from emojis import SPROUTS_CHECK, SPROUTS_ERROR, SPROUTS_WARNING, SPROUTS_INFORMATION
from systems.cluster_manager import ClusterManager

logger = logging.getLogger(__name__)

class ClusterCog(commands.Cog, name="cluster"):
    """Cluster management and multi-instance coordination"""
    
    def __init__(self, bot):
        self.bot = bot
        # Initialize cluster manager with auto-detection
        cluster_id = int(getattr(bot, 'cluster_id', 0))
        total_clusters = int(getattr(bot, 'total_clusters', 1))
        self.cluster_manager = ClusterManager(bot, cluster_id, total_clusters)
        
    @commands.group(name="cluster", invoke_without_command=True)
    @commands.is_owner()
    async def cluster(self, ctx):
        """Cluster management and distribution information"""
        if ctx.invoked_subcommand is None:
            await self.cluster_info(ctx)
        
    @cluster.command(name="info", aliases=["status"])
    @commands.is_owner()
    async def cluster_info(self, ctx):
        """Show cluster management and distribution information"""
        try:
            stats = self.cluster_manager.get_cluster_stats()
            
            embed = discord.Embed(
                title=f"{SPROUTS_INFORMATION} SPROUTS Cluster Dashboard",
                description="Multi-instance deployment and shard distribution management",
                color=0x00D9FF
            )
            
            cluster_info = stats.get('cluster_info', {})
            performance = stats.get('performance', {})
            recommendations = stats.get('recommendations', {})
            
            # Cluster identification
            embed.add_field(
                name=f"{SPROUTS_CHECK} Cluster Information",
                value=(
                    f"**Cluster ID:** {cluster_info.get('cluster_id', 'N/A')}\n"
                    f"**Instance:** `{cluster_info.get('instance_id', 'Unknown')}`\n"
                    f"**Environment:** {cluster_info.get('environment', 'Unknown').title()}\n"
                    f"**Status:** {cluster_info.get('status', 'Unknown').title()}"
                ),
                inline=True
            )
            
            # Shard distribution
            shard_range = cluster_info.get('shard_range', (0, 0))
            embed.add_field(
                name=f"{SPROUTS_WARNING} Shard Distribution",
                value=(
                    f"**Assigned Range:** {shard_range[0]}-{shard_range[1]}\n"
                    f"**Total Shards:** {cluster_info.get('total_shards', 1)}\n"
                    f"**Guilds/Shard:** {performance.get('guilds_per_shard', 0):.1f}\n"
                    f"**Efficiency:** {recommendations.get('current_efficiency', 0):.1f}%"
                ),
                inline=True
            )
            
            # Performance metrics
            embed.add_field(
                name=f"{SPROUTS_INFORMATION} Performance",
                value=(
                    f"**Guilds:** {cluster_info.get('guilds', 0):,}\n"
                    f"**Users:** {cluster_info.get('users', 0):,}\n"
                    f"**Users/Guild:** {performance.get('users_per_guild', 0):.1f}\n"
                    f"**Growth Rate:** {performance.get('guilds_per_hour', 0):.1f}/hr"
                ),
                inline=True
            )
            
            # Recommendations
            embed.add_field(
                name="Optimization Recommendations",
                value=(
                    f"**Optimal Shards:** {recommendations.get('optimal_shards', 'N/A')}\n"
                    f"**Recommended Clusters:** {recommendations.get('recommended_clusters', 'N/A')}\n"
                    f"**Current Load:** {f'{SPROUTS_CHECK} Optimal' if recommendations.get('current_efficiency', 0) >= 80 else f'{SPROUTS_WARNING} Moderate' if recommendations.get('current_efficiency', 0) >= 60 else f'{SPROUTS_ERROR} High'}"
                ),
                inline=False
            )
            
            # Uptime and health
            embed.add_field(
                name="Health Status",
                value=(
                    f"**Uptime:** {stats.get('uptime_human', 'Unknown')}\n"
                    f"**Started:** {datetime.fromtimestamp(cluster_info.get('start_time', time.time())).strftime('%m/%d %H:%M')}\n"
                    f"**Version:** {cluster_info.get('version', 'Unknown')}"
                ),
                inline=True
            )
            
            # Available commands
            embed.add_field(
                name="Available Commands",
                value=(
                    f"`{ctx.prefix}cluster info` - This information\n"
                    f"`{ctx.prefix}cluster shards` - Shard health summary\n"
                    f"`{ctx.prefix}cluster export` - Export cluster metrics\n"
                    f"`{ctx.prefix}cluster optimize` - Optimization suggestions"
                ),
                inline=True
            )
            
            embed.set_footer(text=f"Instance: {cluster_info.get('instance_id', 'Unknown')}")
            embed.timestamp = datetime.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description=f"Failed to retrieve cluster information: {str(e)}",
                color=0xff0000
            )
            await ctx.reply(embed=embed, mention_author=False)
            
    @cluster.command(name="shards", aliases=["sh"])
    @commands.is_owner()
    async def cluster_shards(self, ctx):
        """Show shard health for this cluster only"""
        try:
            stats = self.cluster_manager.get_cluster_stats()
            shard_health = stats.get('shard_health', {})
            cluster_info = stats.get('cluster_info', {})
            
            embed = discord.Embed(
                title=f"{SPROUTS_INFORMATION} Cluster Shard Health",
                description=f"Shards managed by Cluster {cluster_info.get('cluster_id', 'N/A')}",
                color=0x00D9FF
            )
            
            if not shard_health:
                embed.add_field(
                    name="No Shard Data",
                    value="No shard health information available for this cluster.",
                    inline=False
                )
            else:
                # Overall health
                connected_shards = sum(1 for s in shard_health.values() if s['connected'])
                total_shards = len(shard_health)
                avg_latency = sum(s['latency_ms'] for s in shard_health.values()) / max(1, total_shards)
                
                health_percentage = (connected_shards / max(1, total_shards)) * 100
                health_emoji = SPROUTS_CHECK if health_percentage >= 90 else SPROUTS_WARNING if health_percentage >= 70 else SPROUTS_ERROR
                
                embed.add_field(
                    name=f"{health_emoji} Cluster Health Summary",
                    value=(
                        f"**Connected:** {connected_shards}/{total_shards} ({health_percentage:.1f}%)\n"
                        f"**Avg Latency:** {avg_latency:.1f}ms\n"
                        f"**Total Guilds:** {sum(s['guilds'] for s in shard_health.values())}"
                    ),
                    inline=False
                )
                
                # Individual shard details
                shard_details = []
                for shard_id, shard_data in sorted(shard_health.items()):
                    latency = shard_data['latency_ms']
                    guilds = shard_data['guilds']
                    connected = shard_data['connected']
                    
                    status_emoji = SPROUTS_CHECK if connected and latency < 500 else SPROUTS_WARNING if connected else SPROUTS_ERROR
                    shard_details.append(
                        f"{status_emoji} **Shard {shard_id}** - {latency:.0f}ms | {guilds} guilds"
                    )
                    
                # Split into multiple fields if needed
                chunk_size = 8
                for i in range(0, len(shard_details), chunk_size):
                    chunk = shard_details[i:i + chunk_size]
                    field_name = f"Shards ({i//chunk_size + 1})" if len(shard_details) > chunk_size else "Shard Details"
                    embed.add_field(
                        name=field_name,
                        value="\n".join(chunk),
                        inline=True
                    )
                    
            embed.set_footer(text=f"Use '{ctx.prefix}shards' for complete bot shard information")
            embed.timestamp = datetime.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error getting cluster shard info: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description=f"Failed to retrieve shard information: {str(e)}",
                color=0xff0000
            )
            await ctx.reply(embed=embed, mention_author=False)
            
    @cluster.command(name="optimize", aliases=["recommendations", "rec"])
    @commands.is_owner()
    async def cluster_optimize(self, ctx):
        """Show optimization recommendations for scaling"""
        try:
            stats = self.cluster_manager.get_cluster_stats()
            cluster_info = stats.get('cluster_info', {})
            recommendations = stats.get('recommendations', {})
            performance = stats.get('performance', {})
            
            embed = discord.Embed(
                title=f"{SPROUTS_INFORMATION} Cluster Optimization Analysis",
                description="Scaling recommendations based on current performance",
                color=0x00D9FF
            )
            
            current_guilds = cluster_info.get('guilds', 0)
            current_shards = cluster_info.get('total_shards', 1)
            optimal_shards = recommendations.get('optimal_shards', current_shards)
            recommended_clusters = recommendations.get('recommended_clusters', 1)
            efficiency = recommendations.get('current_efficiency', 0)
            
            # Current status
            embed.add_field(
                name=f"Current Configuration",
                value=(
                    f"**Guilds:** {current_guilds:,}\n"
                    f"**Shards:** {current_shards}\n"
                    f"**Clusters:** {self.cluster_manager.total_clusters}\n"
                    f"**Efficiency:** {efficiency:.1f}%"
                ),
                inline=True
            )
            
            # Recommendations
            embed.add_field(
                name="Optimization Recommendations",
                value=(
                    f"**Optimal Shards:** {optimal_shards}\n"
                    f"**Recommended Clusters:** {recommended_clusters}\n"
                    f"**Target Guilds/Shard:** ~1000\n"
                    f"**Target Guilds/Cluster:** ~5000"
                ),
                inline=True
            )
            
            # Performance analysis
            guilds_per_shard = performance.get('guilds_per_shard', 0)
            if guilds_per_shard > 2000:
                priority = f"{SPROUTS_ERROR} **HIGH PRIORITY**"
                action = "Consider adding more shards immediately"
            elif guilds_per_shard > 1500:
                priority = f"{SPROUTS_WARNING} **MEDIUM PRIORITY**"
                action = "Plan for additional shards soon"
            elif guilds_per_shard < 500:
                priority = f"{SPROUTS_INFORMATION} **LOW PRIORITY**"
                action = "Current configuration is efficient"
            else:
                priority = f"{SPROUTS_CHECK} **OPTIMAL**"
                action = "No immediate changes needed"
                
            embed.add_field(
                name=f"Load Analysis",
                value=(
                    f"{priority}\n"
                    f"**Guilds/Shard:** {guilds_per_shard:.1f}\n"
                    f"**Action:** {action}"
                ),
                inline=False
            )
            
            # Scaling guidance
            if current_guilds > 10000:
                scaling_advice = (
                    f"{SPROUTS_INFORMATION} **Large Scale Deployment**\n"
                    "• Use multiple clusters for redundancy\n"
                    "• Monitor shard distribution carefully\n"
                    "• Consider geographic distribution\n"
                    "• Implement health monitoring"
                )
            elif current_guilds > 2000:
                scaling_advice = (
                    f"{SPROUTS_INFORMATION} **Medium Scale Deployment**\n"
                    "• Single cluster should suffice\n"
                    "• Monitor growth trends\n"
                    "• Plan for future scaling\n"
                    "• Optimize shard count"
                )
            else:
                scaling_advice = (
                    f"{SPROUTS_INFORMATION} **Small Scale Deployment**\n"
                    "• Single shard configuration optimal\n"
                    "• Focus on feature development\n"
                    "• Monitor for growth\n"
                    "• Simple deployment preferred"
                )
                
            embed.add_field(
                name="Scaling Guidance",
                value=scaling_advice,
                inline=False
            )
            
            embed.set_footer(text="Recommendations based on Discord best practices")
            embed.timestamp = datetime.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Error",
                description=f"Failed to generate recommendations: {str(e)}",
                color=0xff0000
            )
            await ctx.reply(embed=embed, mention_author=False)
            
    @cluster.command(name="export", aliases=["dump"])
    @commands.is_owner()
    async def export_cluster_metrics(self, ctx):
        """Export comprehensive cluster metrics"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cluster_metrics_{timestamp}.json"
            
            # Export cluster metrics
            self.cluster_manager.export_cluster_metrics(filename)
            
            embed = discord.Embed(
                title=f"{SPROUTS_CHECK} Cluster Metrics Exported",
                description=f"Comprehensive cluster data exported to `{filename}`",
                color=0x00ff00
            )
            
            embed.add_field(
                name="Exported Data",
                value=(
                    f"{SPROUTS_INFORMATION} Cluster configuration and status\n"
                    f"{SPROUTS_CHECK} Performance metrics and statistics\n"
                    f"{SPROUTS_WARNING} Shard health and distribution\n"
                    f"{SPROUTS_INFORMATION} Optimization recommendations\n"
                    f"{SPROUTS_CHECK} Uptime and historical data"
                ),
                inline=False
            )
            
            embed.set_footer(text="File saved to bot directory")
            embed.timestamp = datetime.utcnow()
            
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error exporting cluster metrics: {e}")
            embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Export Failed",
                description=f"Failed to export cluster metrics: {str(e)}",
                color=0xff0000
            )
            await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    """Setup function for the cluster cog"""
    await bot.add_cog(ClusterCog(bot))
    logger.info("Cluster management system initialized")