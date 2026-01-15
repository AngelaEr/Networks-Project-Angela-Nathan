"""
Simple launcher script for the Chat Server.
Run this from the ChatApp directory.
"""

import sys
import os

# Add server directory to path
server_dir = os.path.join(os.path.dirname(__file__), 'server')
sys.path.insert(0, server_dir)

from server import main

if __name__ == "__main__":
    main()
