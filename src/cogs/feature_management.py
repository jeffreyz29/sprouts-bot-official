"""
Feature Flag Management Commands for SPROUTS Bot
Developer commands to control feature releases
"""

import discord
from discord.ext import commands
import logging
from src.emojis import SPROUTS_CHECK, SPROUTS_ERROR, SPROUTS_WARNING, SPROUTS_INFORMATION
from config import EMBED_COLOR_NORMAL, EMBED_COLOR_ERROR, EMBED_COLOR_WARNING, EMBED_COLOR_HIERARCHY
from src.feature_flags import feature_manager

logger = logging.getLogger(__name__)

class FeaturesView(discord.ui.View):
    """Pagination view for features command"""
    
    def __init__(self, pages, author):
        super().__init__(timeout=300)
        self.pages = pages
        self.author = author
        self.current_page = 0
        self.message = None
        
        # Update button states
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page"""
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        if interaction.user != self.author:
            await interaction.response.send_message("Only the command user can use these buttons.", ephemeral=True)
            return
            
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        if interaction.user != self.author:
            await interaction.response.send_message("Only the command user can use these buttons.", ephemeral=True)
            return
            
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the interface"""
        if interaction.user != self.author:
            await interaction.response.send_message("Only the command user can use these buttons.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title=f"{SPROUTS_CHECK} Features Interface Closed",
            description="Feature management interface has been closed.",
            color=EMBED_COLOR_NORMAL
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def on_timeout(self):
        """Handle timeout"""
        if self.message:
            try:
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} Features Interface Timed Out",
                    description="Feature management interface has timed out.",
                    color=EMBED_COLOR_WARNING
                )
                await self.message.edit(embed=embed, view=None)
            except:
                pass

class FeatureManagement(commands.Cog):
    """Commands for managing feature flags and controlled releases"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def is_dev(self, user_id: int) -> bool:
        """Check if user is a developer"""
        return user_id in [764874247646085151]  # Bot owner ID
    
    @commands.command(name="features", help="View all feature flags and their status")
    async def view_features(self, ctx):
        """View all feature flags and their current status with pagination"""
        if not self.is_dev(ctx.author.id):
            return
        
        try:
            status = feature_manager.get_feature_status()
            
            # Create pages
            pages = []
            
            # Page 1 - Always Enabled Features
            page1 = discord.Embed(
                title=f"{SPROUTS_CHECK} SPROUTS Feature Management System",
                description="**ALWAYS ENABLED FEATURES**\nThese features are core to the bot and cannot be disabled.",
                color=EMBED_COLOR_NORMAL
            )
            
            utilities_commands = ', '.join(status.get("utilities", {}).get("commands", []))
            core_help_commands = ', '.join(status.get("core_help", {}).get("commands", []))
            embeds_commands = ', '.join(status.get("embeds", {}).get("commands", []))
            
            page1.add_field(
                name=f"{SPROUTS_CHECK} **utilities**",
                value=utilities_commands,
                inline=False
            )
            page1.add_field(
                name=f"{SPROUTS_CHECK} **core_help**",
                value=core_help_commands,
                inline=False
            )
            page1.add_field(
                name=f"{SPROUTS_CHECK} **embeds**",
                value=embeds_commands,
                inline=False
            )
            
            page1.set_footer(text=f"Page 1/2 • Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            pages.append(page1)
            
            # Page 2 - User Controllable Features
            page2 = discord.Embed(
                title=f"{SPROUTS_CHECK} SPROUTS Feature Management System",
                description="**USER CONTROLLABLE FEATURES**\nThese features can be enabled/disabled for gradual rollouts.",
                color=EMBED_COLOR_NORMAL
            )
            
            # Tickets
            tickets_enabled = status.get("tickets", {}).get("enabled", False)
            tickets_icon = SPROUTS_CHECK if tickets_enabled else SPROUTS_ERROR
            tickets_commands = ', '.join(status.get("tickets", {}).get("commands", []))
            page2.add_field(
                name=f"{tickets_icon} **tickets**",
                value=tickets_commands,
                inline=False
            )
            
            # Autoresponders
            autoresponders_enabled = status.get("autoresponders", {}).get("enabled", False)
            auto_icon = SPROUTS_CHECK if autoresponders_enabled else SPROUTS_ERROR
            auto_commands = ', '.join(status.get("autoresponders", {}).get("commands", []))
            page2.add_field(
                name=f"{auto_icon} **autoresponders**",
                value=auto_commands,
                inline=False
            )
            
            # Sticky
            sticky_enabled = status.get("sticky", {}).get("enabled", False)
            sticky_icon = SPROUTS_CHECK if sticky_enabled else SPROUTS_ERROR
            sticky_commands = ', '.join(status.get("sticky", {}).get("commands", []))
            page2.add_field(
                name=f"{sticky_icon} **sticky**",
                value=sticky_commands,
                inline=False
            )
            
            # Reminders
            reminders_enabled = status.get("reminders", {}).get("enabled", False)
            remind_icon = SPROUTS_CHECK if reminders_enabled else SPROUTS_ERROR
            remind_commands = ', '.join(status.get("reminders", {}).get("commands", []))
            page2.add_field(
                name=f"{remind_icon} **reminders**",
                value=remind_commands,
                inline=False
            )
            
            # System Status
            enabled_count = sum(1 for f in status.values() if f.get("enabled", False))
            total_count = len(status)
            disabled_count = total_count - enabled_count
            enabled_commands = feature_manager.get_enabled_commands()
            
            page2.add_field(
                name="System Status & Controls",
                value=(
                    f"{SPROUTS_CHECK} **{enabled_count}** features enabled\n"
                    f"{SPROUTS_ERROR} **{disabled_count}** features disabled\n"
                    f"{SPROUTS_INFORMATION} **{len(enabled_commands)}** commands available\n\n"
                    f"`s.enablefeature <name>` - Enable feature\n"
                    f"`s.disablefeature <name>` - Disable feature"
                ),
                inline=False
            )
            
            page2.set_footer(text=f"Page 2/2 • Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            pages.append(page2)
            
            # Create view and send
            view = FeaturesView(pages, ctx.author)
            message = await ctx.reply(embed=pages[0], view=view, mention_author=False)
            view.message = message
            
            logger.info(f"Feature status viewed by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error viewing feature status: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Feature Status Error",
                description="An error occurred while retrieving feature status.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=error_embed, mention_author=False)
    
    @commands.command(name="enablefeature", help="Enable a feature flag")
    async def enable_feature(self, ctx, feature_name: str):
        """Enable a specific feature"""
        if not self.is_dev(ctx.author.id):
            return
        
        try:
            if feature_name not in feature_manager.feature_definitions:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Invalid Feature",
                    description=f"Feature `{feature_name}` does not exist.",
                    color=EMBED_COLOR_ERROR
                )
            elif feature_manager.is_feature_enabled(feature_name):
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} Feature Already Enabled",
                    description=f"Feature `{feature_name}` is already enabled.",
                    color=EMBED_COLOR_WARNING
                )
            elif feature_manager.enable_feature(feature_name):
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Feature Enabled",
                    description=f"Successfully enabled feature: `{feature_name}`",
                    color=EMBED_COLOR_NORMAL
                )
                
                # Show what commands were enabled
                feature_info = feature_manager.feature_definitions.get(feature_name, {})
                commands = feature_info.get("commands", [])
                if commands:
                    embed.add_field(
                        name="Commands Now Available",
                        value="\n".join([f"• `{cmd}`" for cmd in commands]),
                        inline=False
                    )
                
                logger.info(f"Feature '{feature_name}' enabled by {ctx.author}")
            else:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Enable Failed",
                    description=f"Failed to enable feature `{feature_name}`. It may be always-enabled or have restrictions.",
                    color=EMBED_COLOR_ERROR
                )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error enabling feature: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Enable Feature Error",
                description="An error occurred while enabling the feature.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=error_embed, mention_author=False)
    
    @commands.command(name="disablefeature", help="Disable a feature flag")
    async def disable_feature(self, ctx, feature_name: str):
        """Disable a specific feature"""
        if not self.is_dev(ctx.author.id):
            return
        
        try:
            if feature_name not in feature_manager.feature_definitions:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Invalid Feature",
                    description=f"Feature `{feature_name}` does not exist.",
                    color=EMBED_COLOR_ERROR
                )
            elif not feature_manager.is_feature_enabled(feature_name):
                embed = discord.Embed(
                    title=f"{SPROUTS_WARNING} Feature Already Disabled",
                    description=f"Feature `{feature_name}` is already disabled.",
                    color=EMBED_COLOR_WARNING
                )
            elif feature_manager.feature_definitions[feature_name].get("always_enabled", False):
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Cannot Disable Feature",
                    description=f"Feature `{feature_name}` is marked as always-enabled and cannot be disabled.",
                    color=EMBED_COLOR_ERROR
                )
            elif feature_manager.disable_feature(feature_name):
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} Feature Disabled",
                    description=f"Successfully disabled feature: `{feature_name}`",
                    color=EMBED_COLOR_WARNING
                )
                
                # Show what commands were disabled
                feature_info = feature_manager.feature_definitions.get(feature_name, {})
                commands = feature_info.get("commands", [])
                if commands:
                    embed.add_field(
                        name="Commands Now Hidden",
                        value="\n".join([f"• `{cmd}`" for cmd in commands]),
                        inline=False
                    )
                
                logger.info(f"Feature '{feature_name}' disabled by {ctx.author}")
            else:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Disable Failed",
                    description=f"Failed to disable feature `{feature_name}` for unknown reasons.",
                    color=EMBED_COLOR_ERROR
                )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error disabling feature: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Disable Feature Error",
                description="An error occurred while disabling the feature.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=error_embed, mention_author=False)
    
    @commands.command(name="featureinfo", help="Get detailed information about a feature")
    async def feature_info(self, ctx, feature_name: str):
        """Get detailed information about a specific feature"""
        if not self.is_dev(ctx.author.id):
            return
        
        try:
            if feature_name not in feature_manager.feature_definitions:
                embed = discord.Embed(
                    title=f"{SPROUTS_ERROR} Invalid Feature",
                    description=f"Feature `{feature_name}` does not exist.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
            
            feature_info = feature_manager.feature_definitions[feature_name]
            is_enabled = feature_manager.is_feature_enabled(feature_name)
            
            status_icon = f"{SPROUTS_CHECK}" if is_enabled else f"{SPROUTS_ERROR}"
            embed = discord.Embed(
                title=f"{status_icon} Feature: {feature_name}",
                description=feature_info.get("description", "No description available"),
                color=EMBED_COLOR_NORMAL if is_enabled else EMBED_COLOR_ERROR
            )
            
            # Basic info
            embed.add_field(
                name="Status",
                value=f"**Enabled:** {'Yes' if is_enabled else 'No'}\n"
                      f"**Always Enabled:** {'Yes' if feature_info.get('always_enabled', False) else 'No'}\n"
                      f"**Dev Only:** {'Yes' if feature_info.get('dev_only', False) else 'No'}",
                inline=True
            )
            
            # Commands
            commands = feature_info.get("commands", [])
            if commands:
                embed.add_field(
                    name=f"Commands ({len(commands)})",
                    value="\n".join([f"• `{cmd}`" for cmd in commands]),
                    inline=False
                )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error getting feature info: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Feature Info Error",
                description="An error occurred while retrieving feature information.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=error_embed, mention_author=False)
    
    @commands.command(name="enableall", help="Enable all features (use with caution)")
    async def enable_all_features(self, ctx):
        """Enable all features at once"""
        if not self.is_dev(ctx.author.id):
            return
        
        try:
            enabled_count = 0
            already_enabled_count = 0
            for feature_name in feature_manager.feature_definitions.keys():
                if feature_manager.is_feature_enabled(feature_name):
                    already_enabled_count += 1
                elif feature_manager.enable_feature(feature_name):
                    enabled_count += 1
            
            if enabled_count > 0:
                embed = discord.Embed(
                    title=f"{SPROUTS_CHECK} All Features Enabled",
                    description=f"Successfully enabled **{enabled_count}** features.\n"
                               f"**{already_enabled_count}** features were already enabled.\n"
                               f"All bot commands are now available to users.",
                    color=EMBED_COLOR_NORMAL
                )
            else:
                embed = discord.Embed(
                    title=f"{SPROUTS_INFORMATION} All Features Already Enabled",
                    description=f"All **{already_enabled_count}** features were already enabled.\n"
                               f"No changes were made.",
                    color=EMBED_COLOR_NORMAL
                )
            
            embed.add_field(
                name="Total Commands Available",
                value=f"**{len(feature_manager.get_enabled_commands())}** commands",
                inline=False
            )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.reply(embed=embed, mention_author=False)
            
            logger.info(f"All features enabled by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error enabling all features: {e}")
            error_embed = discord.Embed(
                title=f"{SPROUTS_ERROR} Enable All Error",
                description="An error occurred while enabling all features.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.reply(embed=error_embed, mention_author=False)

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(FeatureManagement(bot))
    logger.info("Feature Management commands setup completed")