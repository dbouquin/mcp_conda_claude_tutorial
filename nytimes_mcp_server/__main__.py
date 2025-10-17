"""
Entry point for running the server as a module.

This allows the server to be run with: python -m nytimes_mcp_server
"""

from .server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())