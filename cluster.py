#!/usr/bin/env python3
"""
Cluster Manager for Discord Bot Sharding
Supports multi-process clustering for large-scale deployments
"""

import os
import asyncio
import logging
from bot import DiscordBot
from config import DISCORD_BOT_TOKEN

logger = logging.getLogger(__name__)

class ClusterManager:
    """Manages bot clustering and shard distribution"""
    
    def __init__(self):
        # Environment variables for clustering
        self.is_clustered = os.getenv("IS_CLUSTERED", "false").lower() == "true"
        self.cluster_id = int(os.getenv("CLUSTER_ID", 0))
        self.total_shards = int(os.getenv("TOTAL_SHARDS", 1))
        self.shards_per_cluster = int(os.getenv("SHARDS_PER_CLUSTER", 1))
        
        # Calculate shard IDs for this cluster
        if self.is_clustered:
            start_shard = self.cluster_id * self.shards_per_cluster
            end_shard = min(start_shard + self.shards_per_cluster, self.total_shards)
            self.shard_ids = list(range(start_shard, end_shard))
        else:
            self.shard_ids = None
    
    def create_bot(self):
        """Create bot instance with appropriate sharding configuration"""
        if self.is_clustered:
            logger.info(f"Starting cluster {self.cluster_id} with shards {self.shard_ids}")
            return DiscordBot(
                cluster_id=self.cluster_id,
                shard_ids=self.shard_ids,
                shard_count=self.total_shards
            )
        else:
            # AutoShardedBot will determine shard count automatically
            logger.info("Starting with automatic sharding")
            return DiscordBot()
    
    async def run(self):
        """Run the bot cluster"""
        bot = self.create_bot()
        
        try:
            cluster_info = f" (Cluster {self.cluster_id})" if self.is_clustered else ""
            logger.info(f"Starting Discord bot{cluster_info}...")
            await bot.start(DISCORD_BOT_TOKEN)
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            await bot.close()

def main():
    """Main entry point for cluster"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    cluster_manager = ClusterManager()
    
    try:
        asyncio.run(cluster_manager.run())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()