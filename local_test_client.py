import os
import json
import requests
from dotenv import load_dotenv

# Load credentials from your existing .env file
load_dotenv()

# --- Configuration (Read from .env) ---
AUTH0_TOKEN_URL = f"https://{os.getenv('AUTH0_DOMAIN')}/oauth/token"
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

# Your locally running MCP server
MCP_SERVER_URL = "http://localhost:8000"

def get_mcp_access_token():
    """
    Step 1: Authenticate with Auth0 to get a token for our MCP server.
    """
    print("--> Step 1: Requesting M2M Access Token from Auth0...")
    payload = {
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "audience": AUTH0_AUDIENCE,
        "grant_type": "client_credentials",
    }
    try:
        response = requests.post(AUTH0_TOKEN_URL, json=payload)
        response.raise_for_status()
        print("...Success! Received Access Token.")
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"!!! FAILED to get Auth0 token: {e}")
        if e.response is not None:
            print("Response Body:", e.response.text)
        return None


def test_search_movies_tool(movie_title: str, token: str):
    """
    Step 2: Call the MCP server using JSON-RPC 2.0 protocol.
    """
    print(f"\n--> Step 2: Calling MCP tool 'search_movies' for '{movie_title}'...")
    
    # JSON-RPC 2.0 request for calling a tool
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_movies",
            "arguments": {
                "query": movie_title
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(MCP_SERVER_URL, json=jsonrpc_request, headers=headers)
        response.raise_for_status()
        print("...Success! Tool executed.")
        result = response.json()
        print("✅ Response from tool:", json.dumps(result, indent=2))
    except requests.exceptions.RequestException as e:
        print(f"!!! FAILED to call tool: {e}")
        if e.response is not None:
            print("Status Code:", e.response.status_code)
            print("Response Body:", e.response.text)


# --- Main Test Execution (No changes needed here) ---
if __name__ == "__main__":
    print("--- Starting Local MCP Server Test ---")
    
    access_token = get_mcp_access_token()
    
    if access_token:
        test_search_movies_tool("The Matrix", access_token)
        test_search_movies_tool("Inception", access_token)
        test_search_movies_tool("A Non-Existent Movie", access_token)
    
    print("\n--- Test Complete ---")

