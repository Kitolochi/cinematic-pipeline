"""Start Blender with MCP server auto-started.

Usage:
    "C:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --python scripts/start_blender_mcp.py

This opens Blender normally (with UI) and auto-starts the MCP socket server
so Claude Code can connect immediately.
"""
import bpy
import time


def auto_start_mcp():
    """Start the MCP server after Blender finishes loading."""
    try:
        # Direct server start — bypasses operator context requirements
        if not hasattr(bpy.types, "blendermcp_server") or not bpy.types.blendermcp_server:
            from blender_mcp_addon import BlenderMCPServer
            port = bpy.context.scene.blendermcp_port
            bpy.types.blendermcp_server = BlenderMCPServer(port=port)
        bpy.types.blendermcp_server.start()
        bpy.context.scene.blendermcp_server_running = True
        print(f"\n[Cinematic Pipeline] MCP server started on port {bpy.context.scene.blendermcp_port}!")
        print("[Cinematic Pipeline] Claude Code can now connect to Blender.")
    except Exception as e:
        print(f"\n[Cinematic Pipeline] Could not auto-start MCP: {e}")
        print("[Cinematic Pipeline] Open sidebar (N) → BlenderMCP tab → click 'Connect to Claude'")
    return None  # Don't repeat the timer


# Delay start by 2 seconds to let Blender finish initialization
bpy.app.timers.register(auto_start_mcp, first_interval=2.0)
print("\n[Cinematic Pipeline] Will auto-start MCP server in 2 seconds...")
