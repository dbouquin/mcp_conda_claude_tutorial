# NYTimes Books MCP Server

A Model Context Protocol (MCP) server that connects Claude Desktop to the New York Times Books API, enabling Claude to search and retrieve information about NYTimes Best Sellers lists.

This tutorial demonstrates how to build an MCP server using Python and conda, providing a practical introduction to extending Claude's capabilities with external data sources.

## About This Tutorial

This tutorial was created to demonstrate:
- Building MCP servers with Python
- Using conda for environment management
- Integrating external APIs with Claude Desktop

Perfect for developers who want to extend Claude's capabilities with custom data sources and tools!

## What is MCP?

Model Context Protocol (MCP) is an open standard that allows AI assistants like Claude to connect to external data sources and tools. Think of it as a bridge that lets Claude access information beyond its training data - in this case, real-time data from the NYTimes Books API.

When you ask Claude a question about NYTimes best sellers, Claude recognizes it needs external data, calls this MCP server, which then queries the NYTimes API and returns the results.

## Features

This MCP server provides two tools that Claude can use:

- **get_best_sellers**: Retrieve books from a specific NYTimes Best Sellers list (fiction, non-fiction, etc.)
- **get_best_sellers_overview**: Get an overview of all Best Sellers lists with the top 5 books from each

## Prerequisites

- [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed
- [Claude Desktop](https://claude.ai/download) installed
- A [NYTimes Developer API key](https://developer.nytimes.com/get-started) (free)

## Project Structure
```
nytimes-mcp-server/
├── nytimes_mcp_server/        # Main package directory
│   ├── __init__.py            # Package initialization
│   ├── __main__.py            # Entry point for running as module
│   ├── server.py              # MCP server implementation
│   └── nyt_api.py             # NYTimes API wrapper
├── .env                       # Your API key (never commit this!)
├── .env.example               # An example environment file just for this tutorial
├── .gitignore                 # Git ignore rules 
├── test_manual.py             # Test script for API connectivity
└── README.md                  # This file
```

## Installation

### Step 1: Get Your NYTimes API Key

1. Go to https://developer.nytimes.com/get-started
2. Sign up or log in
3. Create a new app in [your apps](https://developer.nytimes.com/my-apps)
4. Enable the "Books API"
5. Copy your API key

### Step 2: Clone This Repository
```bash
git clone https://github.com/yourusername/nytimes-mcp-server.git
cd nytimes-mcp-server
```

### Step 3: Create Conda Environment
```bash
# Create the environment with required dependencies
conda create -n mcp_tutorial python=3.13 -y

# Activate the environment
conda activate mcp_tutorial

# Install dependencies
conda install mcp httpx python-dotenv -y
```

### Step 4: Configure Your API Key

Create a `.env` file in the project root. You can copy the .env.example file and edit the contents or create your own:
```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
NYTIMES_API_KEY=your_actual_api_key_here
```

**Important:** Never commit your `.env` file to version control! Add `.env` to your `.gitignore` file.

### Step 5: Test Your Setup

Run the test script to verify everything works:
```bash
python test_manual.py
```

You should see output showing successful API calls to the NYTimes Books API.

## Connecting to Claude Desktop

### Step 1: Find Your Paths

Get your project's absolute path:
```bash
pwd
```

Get your conda Python path (with environment activated):
```bash
which python
```

### Step 2: Configure Claude Desktop

Edit the Claude Desktop configuration file. You can do this by navigating to Settings > Developer > Edit Config or run the following:

**macOS:** (TextEdit or your favorite text editor)
```bash
open -a TextEdit ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:** 
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:** 
```
~/.config/Claude/claude_desktop_config.json
```

Add your server configuration (replace paths with your actual paths from the steps above):
```json
{
  "mcpServers": {
    "nytimes-books": {
      "command": "/path/to/anaconda3/envs/mcp_tutorial/bin/python",
      "args": [
        "-m",
        "nytimes_mcp_server"
      ],
      "cwd": "/path/to/nytimes-mcp-server",
      "env": {
        "PYTHONPATH": "/path/to/nytimes-mcp-server"
      }
    }
  }
}
```

**Configuration explained:**
- `command`: Full path to your conda environment's Python interpreter
- `args`: Runs the package as a module
- `cwd`: Your project root directory (where `.env` is located)
- `env.PYTHONPATH`: Tells Python where to find your package

### Step 3: Restart Claude Desktop

1. Completely quit Claude Desktop (not just close the window)
2. Reopen Claude Desktop
3. Navigate to Settings > Developer to see if your local MCP server is running successfully

### Step 4: Try It Out!

Create a new chat and click the Search and Tools icon. Make sure `nytimes-books` tool is turned on, then ask Claude questions like:

- "What are the fiction best sellers this month?"
- "Show me an overview of all the NYTimes best seller lists"
- "What's currently #1 on the hardcover non-fiction list?"

Claude should now use your MCP server to fetch real-time data!

## Troubleshooting

### Server Won't Start

**Check the logs:**
```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log

# Windows
# Check %APPDATA%\Claude\logs\

# Linux
# Check ~/.config/Claude/logs/
```

**Common issues:**

1. **"No module named nytimes_mcp_server"**
   - Make sure `PYTHONPATH` is set in your config
   - Verify `cwd` and `PYTHONPATH` both point to your project root

2. **"API key not found"**
   - Check that `.env` exists in the directory specified by `cwd`
   - Verify the API key is correctly set in `.env`

3. **API returns 404 errors**
   - Verify your API key is valid at https://developer.nytimes.com/
   - Ensure you've enabled the Books API for your key

### Manual Testing

You can test the server directly:
```bash
cd /path/to/nytimes-mcp-server
conda activate mcp_tutorial
python -m nytimes_mcp_server
```

The server should start and display:
```
INFO:root:Starting NYTimes Books MCP Server
INFO:root:API key found, starting server...
```

Press Ctrl+C to stop it.

## How It Works

### Architecture
```
You ask Claude a question
         ↓
Claude Desktop recognizes it needs NYTimes data
         ↓
Claude calls your MCP server (via stdio)
         ↓
Your MCP server queries the NYTimes API
         ↓
Results flow back to Claude
         ↓
Claude presents the answer to you
```

### Key Components

1. **nyt_api.py**: Handles all interactions with the NYTimes Books API
   - Manages HTTP requests
   - Formats API responses
   - Handles errors gracefully

2. **server.py**: Implements the MCP server
   - Defines tools that Claude can use
   - Handles tool execution requests
   - Manages communication with Claude Desktop

3. **__main__.py**: Entry point for running the server
   - Sets up async event loop
   - Initializes stdio communication

## Development

### Running Tests
```bash
python test_manual.py
```

### Project Dependencies

- **mcp**: Official MCP SDK from Anthropic
- **httpx**: Modern HTTP client for API calls
- **python-dotenv**: Loads environment variables from .env files

## What's Next?

This tutorial covers the basics of building an MCP server but more could be added

### Potential Enhancements

1. **Caching**: Store API results temporarily to reduce API calls
2. **More endpoints**: The NYTimes Books API has additional endpoints (like reviews and history)
3. **Advanced search**: Implement filtering and sorting options
4. **Error recovery**: Add retry logic for transient failures
5. **Rate limiting**: Implement request throttling to respect API limits

### Learning More About MCP

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Anthropic's MCP Guide](https://docs.anthropic.com/en/docs/build-with-claude/mcp)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this code for learning and teaching purposes.

## Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses the [NYTimes Books API](https://developer.nytimes.com/docs/books-product/1/overview)
- Tutorial developed for the Anaconda community
