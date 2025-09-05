"""
Persistence Management Commands for SPROUTS Bot
Developer commands to manage data persistence and deployment protection
"""

import discord
from discord.ext import commands
import logging
from src.emojis import SPROUTS_CHECK, SPROUTS_ERROR, SPROUTS_WARNING, SPROUTS_INFORMATION
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR, EMBED_COLOR_SUCCESS, EMBED_COLOR_WARNING

logger = logging.getLogger(__name__)

class PersistenceCommands(commands.Cog):
    """Commands for managing data persistence across deployments"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def is_dev(self, user_id: int) -> bool:
        """Check if user is a developer"""
        return user_id in [764874247646085151]  # Bot owner ID
    
    @commands.command(name="persiststatus", help="Check persistence system status")
    async def persistence_status(self, ctx):
        """Check the status of the data persistence system"""
        if not self.is_dev(ctx.author.id):
            return
        
        try:
            from src.database.replit_persistence import replit_persistence
            status = await replit_persistence.get_persistence_status()
            
            if "error" in status:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Persistence System Error",
                    description=f"Error getting status: {status['error']}",
                    color=EMBED_COLOR_ERROR
                )
            else:
                # Determine overall health
                health_color = EMBED_COLOR_NORMAL
                health_icon = SPROUTS_CHECK
                if status["system_health"] == "needs_attention":
                    health_color = EMBED_COLOR_WARNING
                    health_icon = SPROUTS_WARNING
                
                embed = discord.Embed(
                    title=f"{health_icon} Data Persistence Status",
                    description=f"System Health: **{status['system_health'].title()}**",
                    color=health_color
                )
                
                # File system status
                embed.add_field(
                    name="File System Status",
                    value=f"{SPROUTS_CHECK} **{status['files_present']}/{status['total_files']}** files present\n"
                          f"{SPROUTS_ERROR} **{len(status['files_missing'])}** files missing",
                    inline=True
                )
                
                # Database status
                embed.add_field(
                    name="Database Persistence",
                    value=f"{SPROUTS_INFORMATION} **{status['database_backups']}** data backups\n"
                          f"{SPROUTS_INFORMATION} **{status['snapshots_available']}** snapshots available",
                    inline=True
                )
                
                # Latest deployment info
                if status['latest_deployment']:
                    latest = status['latest_deployment']
                    embed.add_field(
                        name="Latest Deployment",
                        value=f"**ID:** {latest['deployment_id']}\n"
                              f"**Time:** <t:{int(latest['deployment_time'].timestamp())}:R>\n"
                              f"**Status:** {'✅ Success' if latest['restoration_successful'] else '❌ Failed'}",
                        inline=False
                    )
                
                # Missing files warning
                if status['files_missing']:
                    missing_list = "\n".join([f"• `{f}`" for f in status['files_missing'][:5]])
                    if len(status['files_missing']) > 5:
                        missing_list += f"\n• ...and {len(status['files_missing']) - 5} more"
                    
                    embed.add_field(
                        name=f"{SPROUTS_WARNING} Missing Files",
                        value=missing_list,
                        inline=False
                    )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error getting persistence status: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Status Check Failed",
                description="An error occurred while checking persistence status.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=error_embed, mention_author=False)
    
    @commands.command(name="forcebackup", help="Force immediate backup to database")
    async def force_backup(self, ctx):
        """Force an immediate backup of all data to the database"""
        if not self.is_dev(ctx.author.id):
            return
        
        try:
            from src.database.replit_persistence import replit_persistence
            
            # Show initial status
            initial_embed = discord.Embed(
                title=f"{SPROUTS_INFORMATION} Creating Force Backup",
                description="Backing up all critical data to database...",
                color=EMBED_COLOR_NORMAL
            )
            message = await ctx.reply(embed=initial_embed, mention_author=False)
            
            # Perform backup
            result = await replit_persistence.backup_all_data_to_database()
            
            if result.get("success"):
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Force Backup Completed",
                    description="All critical data has been safely backed up to the database.",
                    color=EMBED_COLOR_SUCCESS
                )
                
                embed.add_field(
                    name="Backup Results",
                    value=f"{SPROUTS_CHECK} **{result['files_backed_up']}** files backed up\n"
                          f"{SPROUTS_INFORMATION} Snapshot ID: **{result['snapshot_id']}**",
                    inline=False
                )
                
                logger.info(f"Force backup completed by {ctx.author}: {result['files_backed_up']} files")
            else:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Force Backup Failed",
                    description=f"Backup failed: {result.get('error', 'Unknown error')}",
                    color=EMBED_COLOR_ERROR
                )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await message.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in force backup: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Backup Error",
                description=f"An error occurred during backup: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=error_embed, mention_author=False)
    
    @commands.command(name="forcerestore", help="Force restore data from database")
    async def force_restore(self, ctx):
        """Force restore all data from the database"""
        if not self.is_dev(ctx.author.id):
            return
        
        try:
            # Confirmation check
            confirm_embed = discord.Embed(
                title=f"{SPROUTS_WARNING} Force Restore Confirmation",
                description="⚠️ **WARNING:** This will overwrite all current data files with database backups.\n\n"
                           "Type `CONFIRM RESTORE` to proceed or wait 30 seconds to cancel.",
                color=EMBED_COLOR_WARNING
            )
            message = await ctx.reply(embed=confirm_embed, mention_author=False)
            
            # Wait for confirmation
            def check(m):
                return (m.author == ctx.author and 
                       m.channel == ctx.channel and 
                       m.content.upper() == "CONFIRM RESTORE")
            
            try:
                await self.bot.wait_for('message', check=check, timeout=30.0)
            except:
                timeout_embed = discord.Embed(
                    title=f"{SPROUTS_INFORMATION} Restore Cancelled",
                    description="Force restore operation timed out and was cancelled.",
                    color=EMBED_COLOR_NORMAL
                )
                await message.edit(embed=timeout_embed)
                return
            
            # Perform restore
            from src.database.replit_persistence import replit_persistence
            
            progress_embed = discord.Embed(
                title=f"{SPROUTS_INFORMATION} Restoring Data",
                description="Restoring all critical data from database...",
                color=EMBED_COLOR_NORMAL
            )
            await message.edit(embed=progress_embed)
            
            result = await replit_persistence.restore_all_data_from_database()
            
            if result.get("success"):
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Restore Completed",
                    description="All critical data has been successfully restored from the database.",
                    color=EMBED_COLOR_SUCCESS
                )
                
                embed.add_field(
                    name="Restore Results",
                    value=f"{SPROUTS_CHECK} **{result['files_restored']}** files restored\n"
                          f"{SPROUTS_WARNING} Bot restart recommended for full effect",
                    inline=False
                )
                
                logger.info(f"Force restore completed by {ctx.author}: {result['files_restored']} files")
            else:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Restore Failed",
                    description=f"Restore failed: {result.get('error', 'Unknown error')}",
                    color=EMBED_COLOR_ERROR
                )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await message.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in force restore: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Restore Error",
                description=f"An error occurred during restore: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=error_embed, mention_author=False)

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(PersistenceCommands(bot))
    logger.info("Persistence management commands setup completed")