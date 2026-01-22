import os
import json
import uvicorn
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
app = FastMCP()
NODE_API_URL = "http://localhost:3001/api/movies"
AUTH0_TOKEN_URL = f"https://{os.getenv('AUTH0_DOMAIN')}/oauth/token"
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

# A simple in-memory cache for the Auth0 token
auth0_token_cache = {"token": None, "expires_at": 0}

# --- Helper Function to get M2M Token from Auth0 ---
def get_auth0_token():
    """
    Fetches a new M2M access token from Auth0 if the cached one is expired.
    """
    # For simplicity, we'll just get a new token each time.
    # In a production app, you would cache this until it expires.
    payload = {
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "audience": AUTH0_AUDIENCE,
        "grant_type": "client_credentials",
    }
    headers = {"content-type": "application/json"}

    try:
        response = requests.post(AUTH0_TOKEN_URL, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Auth0 token: {e}")
        raise ToolError("Could not authenticate with backend service.")

# --- Tool Implementation (before decoration) ---
def _search_movies_impl(query: str):
    """
    Searches the movie wishlist for a specific movie title.
    """
    print(f"MCP Tool: Received search query for '{query}'")
    
    try:
        # 1. Get a valid M2M token for our Node.js API
        access_token = get_auth0_token()
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # 2. Call the Node.js API to get the full list of movies
        response = requests.get(NODE_API_URL, headers=headers)
        response.raise_for_status()
        
        all_movies = response.json()
        
        # 3. Search for the movie in the list (case-insensitive)
        found_movies = [
            movie for movie in all_movies 
            if query.lower() in movie['title'].lower()
        ]

        # 4. Formulate a response for the LLM
        if not found_movies:
            return f"The movie '{query}' was not found in the wishlist."
        
        results = []
        for movie in found_movies:
            status = "has been watched" if movie['watched'] else "has NOT been watched"
            results.append(f"'{movie['title']}' is on the list and {status}.")
            
        return " ".join(results)

    except ToolError as e:
        # Re-raise known tool errors
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise ToolError("An internal error occurred while searching for movies.")

# --- Tool Definition ---
@app.tool()
def search_movies(query: str):
    """
    Searches the movie wishlist for a specific movie title.
    """
    return _search_movies_impl(query)


# --- Create ASGI app with JSON-RPC middleware ---
fastmcp_asgi = app.http_app()

# Create wrapper that adds JSON-RPC handling
async def json_rpc_asgi_app(scope, receive, send):
    if scope["type"] == "http" and scope["method"] == "POST" and scope["path"] == "/":
        # Collect the body
        body_parts = []
        while True:
            message = await receive()
            if message["type"] == "http.request":
                body_parts.append(message.get("body", b""))
                if not message.get("more_body", False):
                    break
        
        body = b"".join(body_parts)
        
        try:
            jsonrpc_req = json.loads(body)
            
            # Check if this is a JSON-RPC request
            if jsonrpc_req.get("jsonrpc") == "2.0" and jsonrpc_req.get("method") == "tools/call":
                tool_name = jsonrpc_req.get("params", {}).get("name")
                arguments = jsonrpc_req.get("params", {}).get("arguments", {})
                request_id = jsonrpc_req.get("id")
                
                try:
                    # Call the tool implementation
                    if tool_name == "search_movies":
                        result = _search_movies_impl(arguments.get("query", ""))
                    else:
                        result = {"error": f"Unknown tool: {tool_name}"}
                    
                    # Return JSON-RPC response
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    }
                    response_body = json.dumps(response).encode()
                    
                    await send({
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [[b"content-type", b"application/json"]],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": response_body,
                    })
                    return
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        }
                    }
                    response_body = json.dumps(response).encode()
                    
                    await send({
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [[b"content-type", b"application/json"]],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": response_body,
                    })
                    return
        except json.JSONDecodeError:
            pass
    
    # Fall back to the FastMCP ASGI app
    await fastmcp_asgi(scope, receive, send)

# --- Main execution block ---
if __name__ == "__main__":
    uvicorn.run(json_rpc_asgi_app, host="0.0.0.0", port=8000)
