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
        bpy.ops.blendermcp.connect()
        print("\n[Cinematic Pipeline] MCP server started automatically!")
        print("[Cinematic Pipeline] Claude Code can now connect to Blender.")
    except Exception as e:
        print(f"\n[Cinematic Pipeline] Could not auto-start MCP: {e}")
        print("[Cinematic Pipeline] Open sidebar (N) → BlenderMCP tab → click 'Start MCP Server'")
    return None  # Don't repeat the timer


# Delay start by 2 seconds to let Blender finish initialization
bpy.app.timers.register(auto_start_mcp, first_interval=2.0)
print("\n[Cinematic Pipeline] Will auto-start MCP server in 2 seconds...")
