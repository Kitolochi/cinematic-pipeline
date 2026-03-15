"""Install the Blender MCP addon and start the server."""
import bpy
import os
import sys

addon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender_mcp_addon.py")

# Install addon
bpy.ops.preferences.addon_install(filepath=addon_path)

# Enable addon
bpy.ops.preferences.addon_enable(module="blender_mcp_addon")

# Save preferences so it persists
bpy.ops.wm.save_userpref()

print(f"\nBlender MCP addon installed from: {addon_path}")
print("Addon enabled and preferences saved.")
print("\nTo start the MCP server:")
print("  1. Open Blender normally (not --background)")
print("  2. Press N to open sidebar")
print("  3. Find 'BlenderMCP' tab")
print("  4. Click 'Start MCP Server'")
