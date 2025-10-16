"""
MCP Server for NYTimes Books API.

This server exposes tools that allow Claude to search for book reviews and
access NYTimes Best Sellers lists.
"""

import logging
import json
import os
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

from .nyt_api import NYTimesBookAPI

# Load environment variables from .env file
load_dotenv()

# Set up logging to help with debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create our MCP server instance
# The server handles all the protocol communication with Claude Desktop
server = Server("nytimes-books-mcp-server")

# Create our NYTimes API client
# This will be initialized when the server starts
nyt_api = None


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    Define the tools that Claude can use.
    
    This function tells Claude what tools are available and how to use them.
    Claude reads these descriptions to decide when and how to call each tool.
    
    Returns:
        A list of Tool objects defining available tools
    """
    return [
        Tool(
            name="search_book_reviews",
            description=(
                "Search for NYTimes book reviews. You can search by author name, "
                "book title, ISBN, or a general query. Returns review summaries, "
                "publication dates, and links to full reviews. Great for finding "
                "critical reception of books or discovering reviewed books by "
                "specific authors."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "General search query. If provided without other "
                            "parameters, searches in book titles."
                        )
                    },
                    "author": {
                        "type": "string",
                        "description": "Search by author name (e.g., 'Toni Morrison')"
                    },
                    "title": {
                        "type": "string",
                        "description": "Search by book title (e.g., 'Beloved')"
                    },
                    "isbn": {
                        "type": "string",
                        "description": "Search by ISBN (10 or 13 digit)"
                    }
                },
                # At least one search parameter must be provided
                "anyOf": [
                    {"required": ["query"]},
                    {"required": ["author"]},
                    {"required": ["title"]},
                    {"required": ["isbn"]}
                ]
            }
        ),
        Tool(
            name="get_best_sellers_lists",
            description=(
                "Get all available NYTimes Best Sellers list names. "
                "The NYTimes publishes multiple best sellers lists including "
                "Fiction, Non-Fiction, Children's books, Graphic Books, and more. "
                "Use this to discover what lists are available before requesting "
                "a specific list's books."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_best_sellers",
            description=(
                "Get books from a specific NYTimes Best Sellers list. "
                "Returns the current or historical best sellers with rankings, "
                "descriptions, and purchase links. Each book includes its rank, "
                "weeks on the list, and movement from the previous week."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "list_name": {
                        "type": "string",
                        "description": (
                            "The encoded name of the best sellers list "
                            "(e.g., 'combined-print-and-e-book-fiction', "
                            "'hardcover-nonfiction'). Use get_best_sellers_lists "
                            "to see all available options."
                        ),
                        "default": "combined-print-and-e-book-fiction"
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "Optional: The date of the list in YYYY-MM-DD format. "
                            "If not provided, returns the most recent list."
                        )
                    }
                },
                "required": ["list_name"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Handle tool execution requests from Claude.
    
    When Claude decides it needs to use one of our tools, this function gets called.
    We execute the requested tool and return the results.
    
    Args:
        name: The name of the tool Claude wants to use
        arguments: The arguments Claude is passing to the tool
        
    Returns:
        A list of TextContent objects containing the results
        
    Raises:
        ValueError: If an unknown tool is requested
    """
    global nyt_api
    
    # Initialize the API client if it hasn't been created yet
    if nyt_api is None:
        try:
            nyt_api = NYTimesBookAPI()
            logger.info("NYTimes API client initialized successfully")
        except ValueError as e:
            error_msg = (
                f"Failed to initialize NYTimes API client: {str(e)}\n\n"
                "Please ensure NYTIMES_API_KEY is set in your .env file or "
                "environment variables."
            )
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]
    
    # Handle each tool based on its name
    if name == "search_book_reviews":
        # Extract search parameters
        query = arguments.get("query")
        author = arguments.get("author")
        title = arguments.get("title")
        isbn = arguments.get("isbn")
        
        logger.info(
            f"Searching book reviews - query: {query}, author: {author}, "
            f"title: {title}, isbn: {isbn}"
        )
        
        try:
            results = nyt_api.search_reviews(
                query=query,
                author=author,
                title=title,
                isbn=isbn
            )
            
            # Format results as JSON for Claude
            results_text = json.dumps(results, indent=2)
            
            return [
                TextContent(
                    type="text",
                    text=results_text
                )
            ]
            
        except ValueError as e:
            # Handle validation errors (e.g., no search parameters provided)
            return [
                TextContent(
                    type="text",
                    text=f"Invalid search parameters: {str(e)}"
                )
            ]
        except Exception as e:
            logger.error(f"Error searching book reviews: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error searching book reviews: {str(e)}"
                )
            ]
    
    elif name == "get_best_sellers_lists":
        logger.info("Fetching best sellers list names")
        
        try:
            results = nyt_api.get_best_sellers_lists()
            results_text = json.dumps(results, indent=2)
            
            return [
                TextContent(
                    type="text",
                    text=results_text
                )
            ]
            
        except Exception as e:
            logger.error(f"Error fetching best sellers lists: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error fetching best sellers lists: {str(e)}"
                )
            ]
    
    elif name == "get_best_sellers":
        # Extract parameters with defaults
        list_name = arguments.get("list_name", "combined-print-and-e-book-fiction")
        date = arguments.get("date")
        
        logger.info(f"Fetching best sellers - list: {list_name}, date: {date}")
        
        try:
            results = nyt_api.get_best_sellers(
                list_name=list_name,
                date=date
            )
            
            results_text = json.dumps(results, indent=2)
            
            return [
                TextContent(
                    type="text",
                    text=results_text
                )
            ]
            
        except Exception as e:
            logger.error(f"Error fetching best sellers: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error fetching best sellers: {str(e)}"
                )
            ]
    
    else:
        # This should never happen if we've configured everything correctly
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """
    Main entry point for the MCP server.
    
    This function starts the server and keeps it running, listening for
    requests from Claude Desktop over stdio.
    """
    logger.info("Starting NYTimes Books MCP Server")
    
    # Verify API key is available before starting
    api_key = os.getenv("NYTIMES_API_KEY")
    if not api_key:
        logger.error(
            "NYTIMES_API_KEY not found in environment variables. "
            "Please set it in your .env file or environment."
        )
        return
    
    logger.info("API key found, starting server...")
    
    # Run the server using stdio transport
    # This means Claude Desktop will communicate with us via standard input/output
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


# This is the entry point when the script is run directly
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())