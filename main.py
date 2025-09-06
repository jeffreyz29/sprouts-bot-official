#!/usr/bin/env python3
"""
Root level entry point for Digital Ocean App Platform
Redirects to the actual bot entry point in src/
"""

import sys
import os

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

# Change to src directory to ensure relative imports work
os.chdir(src_path)

# Import and run the bot
try:
    from bot_with_web import main
    
    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    sys.exit(1)