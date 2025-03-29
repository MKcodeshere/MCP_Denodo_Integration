from typing import Any, Optional, List
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
username=""
password=""

async def make_denodo_request(endpoint: str, method: str = "GET", params: Optional[dict] = None, json_data: Optional[dict] = None, auth: Optional[tuple] = None) -> dict[str, Any] | None:
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
async def answer_question(question: str, username=username, password=password, plot: bool = False, 
                         mode: str = "default", use_views: str = "", custom_instructions: str = "") -> str:
    """
    Ask a natural language question to be answered using Denodo data.
    
    Args:
        question: The natural language question to be answered
        username: Denodo username for authentication (optional)
        password: Denodo password for authentication (optional)
        plot: Whether to generate a plot with the answer (default: False)
        mode: One of "default", "data", or "metadata" (default: "default")
        use_views: Specific views to use for the query, comma-separated (e.g. "bank.loans, bank.customers")
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
async def answer_data_question(question: str, username=username, password=password, 
                              plot: bool = False, use_views: str = "") -> str:
    """
    Ask a question specifically for querying data (forces data mode).
    
    Args:
        question: The natural language question to be answered
        username: Denodo username for authentication (optional)
        password: Denodo password for authentication (optional)
        plot: Whether to generate a plot with the answer (default: False)
        use_views: Specific views to use for the query, comma-separated (e.g. "bank.loans, bank.customers")
    """
    auth = (username, password) if username and password else None
    
    json_data = {
        "question": question,
        "plot": plot,
        "markdown_response": True,
        "verbose": True
    }
    
    if use_views:
        json_data["use_views"] = use_views
    
    result = await make_denodo_request("answerDataQuestion", method="POST", json_data=json_data, auth=auth)
    
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
async def answer_metadata_question(question: str,username=username, password=password) -> str:
    """
    Ask a question specifically about metadata (forces metadata mode).
    
    Args:
        question: The natural language question to be answered
        username: Denodo username for authentication (optional)
        password: Denodo password for authentication (optional)
    """
    auth = (username, password) if username and password else None
    
    json_data = {
        "question": question,
        "markdown_response": True,
        "verbose": True
    }
    
    result = await make_denodo_request("answerMetadataQuestion", method="POST", json_data=json_data, auth=auth)
    
    if not result or "error" in result:
        return f"Error: {result.get('error', 'Unknown error occurred')}" if result else "Failed to get a response"
    
    # Format the response
    answer = result.get("answer", "No answer provided")
    
    return f"Answer: {answer}"

@mcp.tool()
async def similarity_search(query: str, n_results: int = 5, username=username, password=password) -> str:
    """
    Perform similarity search on previously stored metadata.
    
    Args:
        query: Search query
        n_results: Number of results to return (default: 5)
        username: Denodo username for authentication (optional)
        password: Denodo password for authentication (optional)
    """
    auth = (username, password) if username and password else None
    
    params = {
        "query": query,
        "n_results": n_results,
        "scores": True
    }
    
    result = await make_denodo_request("similaritySearch", method="GET", params=params, auth=auth)
    
    if not result or "error" in result:
        return f"Error: {result.get('error', 'Unknown error occurred')}" if result else "Failed to get a response"
    
    # Format the results
    if not result or "results" not in result:
        return "No results found or unable to perform similarity search."
    
    formatted_results = []
    for i, item in enumerate(result["results"], 1):
        table_name = item.get("table_name", "Unknown")
        score = item.get("score", 0)
        description = item.get("description", "No description available")
        
        formatted_results.append(f"{i}. Table: {table_name}\n   Score: {score:.4f}\n   Description: {description}")
    
    return "Search Results:\n\n" + "\n\n".join(formatted_results)

@mcp.tool()
async def get_metadata(database_names: str, insert: bool = True, 
                      overwrite: bool = True, username=username, password=password) -> str:
    """
    Retrieve metadata from specified VDP databases and optionally store it in a vector database.
    
    Args:
        database_names: Pass the databasename whenever user ask for it
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
