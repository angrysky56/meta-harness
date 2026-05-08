
import sys
import os

# Add hermes-agent to sys.path
hermes_path = os.path.expanduser("~/.hermes/hermes-agent")
if hermes_path not in sys.path:
    sys.path.insert(0, hermes_path)

try:
    from tools.mcp_tool import discover_mcp_tools
    from tools.registry import registry
    
    print("Discovering MCP tools...")
    mcp_tools = discover_mcp_tools()
    print(f"Discovered {len(mcp_tools)} tools: {mcp_tools}")
    
    # Check if a specific tool from a configured server is there
    # For example, 'mcp-advanced-reasoning-advanced_reasoning'
    all_registered = list(registry._tools.keys())
    print(f"Total registered tools in registry: {len(all_registered)}")
    
    for tool in all_registered:
        if tool.startswith("mcp-"):
            print(f"Found MCP tool: {tool}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
