"""
Check exact minimum distance between any two non-adjacent track sections.
"""
from blender_client import send_code

code = r'''
import sys
workspace_dir = r"d:\game"
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import track_geometry
import importlib
importlib.reload(track_geometry)

frames = track_geometry.generate_refined_track_curve()
total = len(frames)
print(f"Total track rings: {total}")

# Road width is 18m, with kerbs (2m) and barriers (1m), total half-width is 12m.
# Minimum safe centerline distance without ANY overlap is 24.0m.
# Safe margin: 35.0m.

min_dist = float('inf')
min_pair = None
overlaps = []

for i in range(total):
    p_i = frames[i]["pos"]
    for j in range(i + 30, total):
        # Skip loop wrap-around near loop closure
        if (total - (j - i)) < 30:
            continue
        p_j = frames[j]["pos"]
        d = (p_i - p_j).length
        if d < min_dist:
            min_dist = d
            min_pair = (i, j)
        if d < 25.0:
            overlaps.append((i, j, d))

print(f"Minimum non-adjacent distance: {min_dist:.2f}m between ring {min_pair[0]} and {min_pair[1]}")
if min_pair:
    print(f"Ring {min_pair[0]}: {frames[min_pair[0]]['pos']}")
    print(f"Ring {min_pair[1]}: {frames[min_pair[1]]['pos']}")
print(f"Total overlapping pairs (< 25m): {len(overlaps)}")
'''

res = send_code(code)
print(res["output"])
