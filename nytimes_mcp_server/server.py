"""
MCP Server for NYTimes Books API.

This server exposes tools that allow Claude to access NYTimes Best Sellers lists.
"""

import logging
import json
import os
from typing import Any
from mcp.server import Server # Core MCP server functionality
from mcp.server.stdio import stdio_server # stdio transport for communication
from mcp.types import Tool, TextContent # MCP types (data structures) for defining tools and responses
from dotenv import load_dotenv # Load environment variables (API key) from .env file

from .nyt_api import NYTimesBookAPI # Client for interacting with NYTimes Books API (. just means from the same package)

# Load environment variables from .env file
load_dotenv()

# Set up logging to help with debugging
logging.basicConfig(level=logging.INFO) # Show INFO level logs
logger = logging.getLogger(__name__) # Logger for this module


# Create the MCP server instance with unique name
# The server handles all the protocol communication with Claude Desktop
server = Server("nytimes-books-mcp-server")

# Create the NYTimes API client but don't initialize it yet
# This will be initialized when the server starts so we can handle errors gracefully (lazy initialization)
nyt_api = None


@server.list_tools() # Decorator to define available tools for Claude (when Claude asks what tools are available server calls this)
async def list_tools() -> list[Tool]: # MCP SDK handles async functions for us and this one returns a list of Tool objects
    """
    Define the tools that Claude can use.
    
    This function tells Claude what tools are available and how to use them.
    Claude reads these descriptions to decide when and how to call each tool.
    
    Returns:
        A list of Tool objects defining available tools
    """
    return [
        Tool(
            name="get_best_sellers",
            description=( # This description tells Claude when to use this tool!
                "Get books from a specific NYTimes Best Sellers list. "
                "Returns the current or historical best sellers with rankings, "
                "descriptions, and purchase links. Each book includes its rank, "
                "weeks on the list, and movement from the previous week. "
                "Use this when someone asks about current best sellers or "
                "specific best seller lists like fiction, non-fiction, etc."
            ),
            inputSchema={ # JSON schema defining the input parameters for this tool
                "type": "object", # The input is an object (dictionary)
                "properties": { # Define the parameters
                    "list_name": {
                        "type": "string",
                        "description": (
                            "The encoded name of the best sellers list. "
                            "Common options include:\n"
                            "- 'combined-print-and-e-book-fiction' (default)\n"
                            "- 'combined-print-and-e-book-nonfiction'\n"
                            "- 'hardcover-fiction'\n"
                            "- 'hardcover-nonfiction'\n"
                            "- 'trade-fiction-paperback'\n"
                            "Use get_best_sellers_overview to see all available lists."
                        ),
                        "default": "combined-print-and-e-book-fiction"
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "Optional: The date of the list in YYYY-MM-DD format. "
                            "If not provided, returns the most recent list. "
                            "Lists are typically published weekly."
                        )
                    }
                },
                "required": [] # No required parameters, both are optional
            }
        ),
        Tool(
            name="get_best_sellers_overview",
            description=( # When to use this tool vs the other one!
                "Get an overview of ALL NYTimes Best Sellers lists. "
                "Returns the top 5 books from each list (Fiction, Non-Fiction, "
                "Children's, Graphic Books, etc.). This is perfect for getting "
                "a comprehensive view of what's popular across all categories. "
                "Use this when someone asks 'what are the best sellers' without "
                "specifying a particular list, or when they want to see multiple lists."
            ),
            inputSchema={
                "type": "object",
                "properties": {}, # No input parameters for this tool
                "required": []
            }
        )
    ]


@server.call_tool() # Registers this function to handle tool execution requests
async def call_tool(name: str, arguments: Any) -> list[TextContent]: # name = which tool, arguments = parameters being passed
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
    global nyt_api # allows us to modify the module level variable
    
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
    if name == "get_best_sellers":
        # Extract parameters with defaults
        list_name = arguments.get("list_name", "combined-print-and-e-book-fiction") # use .get with defaults
        date = arguments.get("date")
        
        logger.info(f"Fetching best sellers - list: {list_name}, date: {date}") # Log the request
        
        try: # wrap the API call in error handling
            results = nyt_api.get_best_sellers( # call the NYTimes API client method
                list_name=list_name,
                date=date
            )
            
            results_text = json.dumps(results, indent=2) # Convert results to pretty JSON string
            
            return [ # wrap result in MCP's expected format
                TextContent(
                    type="text",
                    text=results_text
                )
            ]
            
        except Exception as e: # return the error if anything goes wrong
            logger.error(f"Error fetching best sellers: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error fetching best sellers: {str(e)}"
                )
            ]
    
    elif name == "get_best_sellers_overview":
        logger.info("Fetching best sellers overview") # log what we're doing
        
        try:
            results = nyt_api.get_best_sellers_overview() # call the API method
            results_text = json.dumps(results, indent=2) # Convert to pretty JSON string
            
            return [ # wrap result in MCP's expected format
                TextContent(
                    type="text",
                    text=results_text
                )
            ]
            
        except Exception as e: # handle errors
            logger.error(f"Error fetching best sellers overview: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error fetching best sellers overview: {str(e)}"
                )
            ]
    
    else:
        # Unknown tool handler - if Claude requests a tool we don't know throw an error (this shouldn't happen if configured correctly)
        raise ValueError(f"Unknown tool: {name}")


async def main(): # main entry point to start the server
    """
    Main entry point for the MCP server.
    
    This function starts the server and keeps it running, listening for
    requests from Claude Desktop over stdio.
    """
    logger.info("Starting NYTimes Books MCP Server") # Log server start
    
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
    async with stdio_server() as (read_stream, write_stream): # async context manager to handle stdio streams
        await server.run( # starts server and keeps it running
            read_stream, # Read stream from stdio
            write_stream, # Write stream to stdio
            server.create_initialization_options()
        )


# This is the entry point when the script is run directly
if __name__ == "__main__": # only runs if this file is executed directly
    import asyncio # Python's async library
    asyncio.run(main()) # Run the main async function to start the server