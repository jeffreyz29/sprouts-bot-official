"""
Custom Emoji Configuration for Sprouts Discord Bot
Centralized storage for all custom animated emojis used throughout the bot
"""

# Custom Animated Emojis - The only 3 emojis used in the entire bot
SPROUTS_CHECK = "✅"  # Using standard emoji as fallback until custom ones are available
SPROUTS_ERROR = "❌"  # Using standard emoji as fallback until custom ones are available
SPROUTS_WARNING = "⚠️"  # Using standard emoji as fallback until custom ones are available

# Emoji dictionary for easy access
EMOJIS = {
    "check": SPROUTS_CHECK,
    "error": SPROUTS_ERROR,  
    "warning": SPROUTS_WARNING,
    "success": SPROUTS_CHECK,
    "fail": SPROUTS_ERROR,
    "warn": SPROUTS_WARNING
}

def get_emoji(emoji_type: str) -> str:
    """
    Get emoji by type name
    
    Args:
        emoji_type: Type of emoji ('check', 'error', 'warning', 'success', 'fail', 'warn')
    
    Returns:
        Custom emoji string or empty string if not found
    """
    return EMOJIS.get(emoji_type.lower(), "")