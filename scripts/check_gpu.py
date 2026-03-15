"""Check GPU availability for Cycles rendering."""
import bpy
import sys

print("=" * 50)
print("CINEMATIC PIPELINE — GPU CHECK")
print("=" * 50)

# Check Cycles availability
print(f"\nBlender: {bpy.app.version_string}")
print(f"Render engines available:")
for engine in ['CYCLES', 'BLENDER_EEVEE_NEXT']:
    print(f"  - {engine}")

# Check Cycles compute devices
prefs = bpy.context.preferences.addons.get('cycles')
if prefs:
    cp = prefs.preferences

    # Try each compute type
    for device_type in ['OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL']:
        try:
            cp.compute_device_type = device_type
            cp.get_devices()
            devices = cp.devices
            gpu_devices = [d for d in devices if d.type != 'CPU']
            if gpu_devices:
                print(f"\n{device_type} devices found:")
                for d in gpu_devices:
                    print(f"  - {d.name} (type: {d.type}, use: {d.use})")
                    d.use = True
        except Exception as e:
            pass

    # Also show CPU
    try:
        cp.compute_device_type = 'NONE'
        cp.get_devices()
        cpu_devices = [d for d in cp.devices if d.type == 'CPU']
        if cpu_devices:
            print(f"\nCPU fallback:")
            for d in cpu_devices:
                print(f"  - {d.name}")
    except:
        pass
else:
    print("\nWARNING: Cycles addon not found!")

print("\n" + "=" * 50)
print("GPU check complete.")
print("=" * 50)
