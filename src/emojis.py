"""
Custom Emoji Configuration for Sprouts Discord Bot
Centralized storage for all custom animated emojis used throughout the bot
"""

# Custom Animated Emojis - The only 4 emojis used in the entire bot
SPROUTS_CHECK = "<a:sprouts_check_dns:1411790001565466725>"
SPROUTS_ERROR = "<a:sprouts_error_dns:1411790004652605500>"
SPROUTS_WARNING = "<a:sprouts_warning_dns:1412200379206336522>"
SPROUTS_INFORMATION = "<a:sprouts_information_dns:1413464347078033478>"

# Emoji dictionary for easy access
EMOJIS = {
    "check": SPROUTS_CHECK,
    "error": SPROUTS_ERROR,  
    "warning": SPROUTS_WARNING,
    "information": SPROUTS_INFORMATION,
    "info": SPROUTS_INFORMATION,
    "success": SPROUTS_CHECK,
    "fail": SPROUTS_ERROR,
    "warn": SPROUTS_WARNING
}

def get_emoji(emoji_type: str) -> str:
    """
    Get emoji by type name
    
    Args:
        emoji_type: Type of emoji ('check', 'error', 'warning', 'information', 'info', 'success', 'fail', 'warn')
    
    Returns:
        Custom emoji string or empty string if not found
    """
    return EMOJIS.get(emoji_type.lower(), "")