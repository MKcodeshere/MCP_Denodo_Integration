Here's a comprehensive GitHub README.md for the AskDenodo.py MCP server:

```markdown
# AskDenodo MCP Server

A Model Context Protocol (MCP) server that connects Claude and other AI assistants to your enterprise data through the Denodo data virtualization platform.

## Overview

AskDenodo is a single MCP server that eliminates the need to build separate MCP servers for each of your data sources. By leveraging Denodo's data virtualization capabilities, it provides a unified interface to query all your enterprise data using natural language.


## Features

- **Natural Language Querying**: Ask questions about your data in plain English
- **Single Access Point**: Query data across multiple sources through one interface
- **Metadata Integration**: Retrieve and understand your data model
- **Security Compliance**: Respects Denodo's access control rules
- **Easy Configuration**: Simple setup with Claude for Desktop

## Prerequisites

- Python 3.10+
- Denodo Platform 9.0.5+
- Denodo AI SDK running
- Claude for Desktop (or other MCP-compatible host)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/askdenodo.git
   cd askdenodo
   ```

2. Install dependencies:
   ```bash
   pip install fastmcp httpx
   ```

3. Configure the Denodo AI SDK URL in `askDenodo.py` if needed (default is `http://localhost:8008`)

## Usage

1. Make sure the Denodo Platform and Denodo AI SDK are running.

2. Run the AskDenodo MCP server:
   ```bash
   python askDenodo.py
   ```

3. Configure Claude for Desktop:
   - Open your Claude Desktop configuration file:
     - Windows: `%AppData%\Claude\claude_desktop_config.json`
     - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Add the following configuration:
     ```json
      {
       "mcpServers": {
           "askDenodo": {
               "command": "C:\\Users\\MuthuKumaranKuppuswa\\AppData\\Roaming\\Python\\Python312\\Scripts\\uv",
               "args": [
                   "--directory",
                   "C:\\MCP_DEMO\\Denodo",
                   "run",
                   "ask_denodo.py"
               ]
           }
       }
      }
     ```

4. Restart Claude for Desktop and look for the hammer icon to access the tools.

## Available Tools

### answer_question

Ask a natural language question to be answered using your Denodo data.

**Parameters:**
- `question` (required): The natural language question to ask
- `username` (optional): Denodo username for authentication
- `password` (optional): Denodo password for authentication
- `plot` (optional): Whether to generate a plot with the answer (default: false)
- `mode` (optional): One of "default", "data", or "metadata" (default: "default")
- `use_views` (optional): Specific views to use for the query (e.g. "bank.loans, bank.customers")
- `custom_instructions` (optional): Additional instructions for the LLM

### get_metadata

Retrieve metadata from specified Denodo databases and optionally store it in a vector database.

**Parameters:**
- `database_names` (required): Comma-separated list of databases
- `insert` (optional): Store metadata in vector store (default: false)
- `overwrite` (optional): Overwrite existing vector store data (default: false)
- `username` (optional): Denodo username for authentication
- `password` (optional): Denodo password for authentication

## Example Code

```python
from typing import Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("denodo_ai_sdk")

# Constants
API_BASE_URL = "http://localhost:8008"  # Default Denodo AI SDK URL
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

async def make_denodo_request(endpoint: str, method: str = "GET", params: Optional[dict] = None, 
                             json_data: Optional[dict] = None, auth: Optional[tuple] = None) -> dict[str, Any] | None:
    """Make a request to the Denodo AI SDK API with proper error handling."""
    url = f"{API_BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, params=params, headers=DEFAULT_HEADERS, auth=auth, timeout=120.0)
            elif method.upper() == "POST":
                response = await client.post(url, params=params, json=json_data, headers=DEFAULT_HEADERS, auth=auth, timeout=120.0)
            else:
                return None
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

@mcp.tool()
async def answer_question(question: str, username: str = "", password: str = "", plot: bool = False, 
                         mode: str = "default", use_views: str = "", custom_instructions: str = "") -> str:
    """
    Ask a natural language question to be answered using Denodo data.
    
    Args:
        question: The natural language question to be answered
        username: Denodo username for authentication (optional)
        password: Denodo password for authentication (optional)
        plot: Whether to generate a plot with the answer (default: False)
        mode: One of "default", "data", or "metadata" (default: "default")
        use_views: Specific views to use for the query (e.g. "bank.loans, bank.customers")
        custom_instructions: Additional instructions for the LLM
    """
    auth = (username, password) if username and password else None
    
    json_data = {
        "question": question,
        "plot": plot,
        "mode": mode,
        "markdown_response": True,
        "verbose": True
    }
    
    if use_views:
        json_data["use_views"] = use_views
    
    if custom_instructions:
        json_data["custom_instructions"] = custom_instructions
    
    result = await make_denodo_request("answerQuestion", method="POST", json_data=json_data, auth=auth)
    
    if not result or "error" in result:
        return f"Error: {result.get('error', 'Unknown error occurred')}" if result else "Failed to get a response"
    
    # Format the response
    answer = result.get("answer", "No answer provided")
    sql_query = result.get("sql_query", "")
    tables_used = result.get("tables_used", [])
    
    formatted_response = f"""
Answer: {answer}

SQL Query: {sql_query if sql_query else 'No SQL query generated'}

Tables Used: {', '.join(tables_used) if tables_used else 'None'}
"""
    
    return formatted_response

@mcp.tool()
async def get_metadata(database_names: str, insert: bool = False, 
                      overwrite: bool = False, username: str = "", password: str = "") -> str:
    """
    Retrieve metadata from specified VDP databases and optionally store it in a vector database.
    
    Args:
        database_names: Comma-separated list of databases
        insert: Store metadata in vector store (default: False)
        overwrite: Overwrite existing vector store data (default: False)
        username: Denodo username for authentication (optional)
        password: Denodo password for authentication (optional)
    """
    auth = (username, password) if username and password else None
    
    params = {
        "vdp_database_names": database_names,
        "insert": str(insert).lower(),
        "overwrite": str(overwrite).lower(),
        "examples_per_table": 3,
        "descriptions": "true",
        "associations": "true"
    }
    
    result = await make_denodo_request("getMetadata", method="GET", params=params, auth=auth)
    
    if not result or "error" in result:
        return f"Error: {result.get('error', 'Unknown error occurred')}" if result else "Failed to get metadata"
    
    # Parse the actual response structure
    tables_count = 0
    databases = []
    
    if "db_schema_json" in result:
        for db in result["db_schema_json"]:
            db_name = db.get("databaseName", "Unknown")
            databases.append(db_name)
            
            # Count tables in this database
            db_tables = db.get("databaseTables", [])
            tables_count += len(db_tables)
    
    databases_str = ", ".join(databases) if databases else database_names
    
    return f"Successfully retrieved metadata for {tables_count} tables from database(s): {databases_str}."

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
```

## Why AskDenodo?

Traditional approaches would require building a separate MCP server for each data source (PostgreSQL, Snowflake, MongoDB, etc.), leading to:

- **Architecture Complexity**: Multiple servers to build and maintain
- **Inconsistent Data Models**: Different naming conventions across sources
- **Query Confusion**: LLMs struggling to determine which source to query
- **Security Overhead**: Multiple authentication systems to manage

AskDenodo leverages Denodo to provide:
- **Simplified Architecture**: One MCP server instead of many
- **Unified Data Model**: Consistent naming across all sources
- **Intelligent Query Routing**: Denodo determines which sources to query
- **Centralized Security**: One point for access control

## Resources

- [Model Context Protocol Quickstart](https://modelcontextprotocol.io/quickstart/server)
- [Anthropic's MCP Announcement](https://www.anthropic.com/news/model-context-protocol)
- [Denodo AI SDK Documentation](https://community.denodo.com/docs/html/document/denodoconnects/latest/en/Denodo%20AI%20SDK%20-%20User%20Manual)

## License

MIT

## Author

Your Name

*Note: While I work for Denodo, the AskDenodo MCP integration described in this project is my own initiative, and you can expect to see an official integration from Denodo soon.*
```

This README provides a comprehensive guide for users to understand, install, and use your AskDenodo MCP server. It includes:

1. An overview of the project
2. Installation instructions
3. Usage details
4. Tool documentation
5. Complete example code
6. Comparison with traditional approaches
7. Resources for further learning
8. License and author information

You might want to add an architecture diagram to make the value proposition even clearer.
