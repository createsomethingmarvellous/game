"""
Verification script for forward monotonic loop closure with zero overlap.
"""
from blender_client import send_code

code = r'''
import math
from mathutils import Vector

anchors = [
    # --- Sector 1: Start/Finish Straight (Heading True North: (0, 1, 0)) ---
    # Anchor 0 is the Start/Finish line. Track moves strictly forward in +Y.
    (0.0, 0.0, 0.0, 0.0),            # Start / Finish Line & Gantry
    (0.0, 70.0, 1.5, 0.0),
    (0.0, 140.0, 3.5, 0.0),
    (0.0, 210.0, 5.5, 0.0),
    (0.0, 270.0, 7.0, 0.0),          # Braking zone for Turn 1

    # --- Turn 1: Symmetrical 90-degree Right Turn (Radius 55m) ---
    (16.0, 308.0, 8.5, 0.04),
    (55.0, 325.0, 10.0, 0.06),       # T1 Apex
    (94.0, 325.0, 11.5, 0.04),

    # --- Turn 2: Sweeping Uphill Left Arc ---
    (145.0, 340.0, 13.0, -0.04),
    (185.0, 385.0, 14.5, -0.06),
    (210.0, 450.0, 16.0, -0.05),
    (215.0, 525.0, 17.5, -0.03),

    # --- Turn 3: Summit Hairpin (Radius 45m, Wide separation) ---
    (230.0, 585.0, 18.5, 0.05),
    (265.0, 615.0, 19.0, 0.08),      # T3 Apex Summit
    (300.0, 585.0, 18.5, 0.06),

    # --- Back Straight (1.05 km heading South-East) ---
    (345.0, 480.0, 16.5, 0.0),
    (400.0, 340.0, 14.0, 0.0),
    (455.0, 200.0, 11.5, 0.0),
    (510.0, 60.0, 9.0, 0.0),
    (565.0, -80.0, 6.5, 0.0),
    (620.0, -220.0, 4.0, 0.0),
    (675.0, -360.0, 1.5, 0.0),
    (705.0, -435.0, 0.5, 0.0),       # Heavy braking for Turn 4

    # --- Turn 4: Right Hairpin (Radius 50m) ---
    (700.0, -485.0, 0.0, 0.06),
    (665.0, -515.0, 0.0, 0.08),      # T4 Apex
    (620.0, -505.0, 0.0, 0.05),

    # --- Straight Chute to Turn 5 (Deep in south plain, Y <= -300m) ---
    (530.0, -460.0, 0.0, 0.0),
    (420.0, -410.0, 0.0, 0.0),
    (310.0, -365.0, 0.0, 0.0),
    (200.0, -325.0, 0.0, 0.0),
    (100.0, -305.0, 0.0, 0.0),

    # --- Turn 5 & 6: Smooth Cyber Tunnel (Wide R=70m, gentle 3% slope) ---
    (40.0, -305.0, -1.0, -0.04),     # Tunnel Entrance
    (-25.0, -325.0, -2.5, -0.06),    # T5 Apex
    (-75.0, -355.0, -3.5, -0.05),
    (-110.0, -400.0, -3.5, 0.05),    # T6 Apex
    (-110.0, -455.0, -2.0, 0.04),

    # --- Turn 7, 8, 9: S-Section exiting tunnel ---
    (-95.0, -505.0, -0.5, -0.03),    # Tunnel Exit
    (-90.0, -550.0, 0.0, 0.0),
    (-105.0, -590.0, 0.0, 0.05),     # T8 Apex
    (-135.0, -620.0, 0.0, 0.06),     # T9 Apex
    (-175.0, -625.0, 0.0, 0.04),

    # --- Turn 10 & 11: The Iconic Parabolica (Wide Banked Carousel R=75m) ---
    (-225.0, -650.0, 0.0, 0.07),
    (-285.0, -630.0, 0.0, 0.09),     # South apex (banked 5.5 deg)
    (-320.0, -570.0, 0.0, 0.09),     # Mid carousel
    (-305.0, -500.0, 0.0, 0.08),     # Exit apex
    (-265.0, -440.0, 0.0, 0.05),

    # --- Turn 12, 13, 14: Ascending S-curves climbing north ---
    (-225.0, -395.0, 0.0, -0.04),
    (-200.0, -335.0, 0.0, 0.04),
    (-200.0, -250.0, 0.0, -0.03),
    (-200.0, -150.0, 0.0, 0.0),

    # --- Turn 15: Symmetrical 90-degree Left Turn (Radius 45m) ---
    (-190.0, -60.0, 0.0, -0.05),
    (-160.0, -20.0, 0.0, -0.07),     # T15 Apex
    (-115.0, -30.0, 0.0, -0.05),

    # --- Chute down to Turn 16 (Keeps X <= -80m, 80m gap from Main Straight) ---
    (-85.0, -50.0, 0.0, 0.0),
    (-85.0, -90.0, 0.0, 0.0),
    (-80.0, -140.0, 0.0, 0.0),

    # --- Turn 16: Wide Hairpin Arc (R=40m, center at X=-40, Y=-190) ---
    (-70.0, -170.0, 0.0, 0.06),
    (-40.0, -190.0, 0.0, 0.08),      # T16 Apex
    (-10.0, -170.0, 0.0, 0.06),

    # --- Sleek Monotonic Connection into Main Straight (heading True North: (0, 1, 0)) ---
    (0.0, -140.0, 0.0, 0.0),         # Joins X=0 heading North!
    (0.0, -70.0, 0.0, 0.0),          # Continuing North into Start/Finish Anchor 0!
]

def catmull_rom_eval(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        (2.0 * p1) +
        (-p0 + p2) * t +
        (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 +
        (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
    )

num_a = len(anchors)
raw_pts = []
for i in range(num_a):
    p0 = Vector(anchors[(i - 1) % num_a][:3])
    p1 = Vector(anchors[i][:3])
    p2 = Vector(anchors[(i + 1) % num_a][:3])
    p3 = Vector(anchors[(i + 2) % num_a][:3])
    for s in range(24):
        raw_pts.append(catmull_rom_eval(p0, p1, p2, p3, s / 24.0))

cum_d = [0.0]
for i in range(len(raw_pts)):
    cum_d.append(cum_d[-1] + (raw_pts[(i+1)%len(raw_pts)] - raw_pts[i]).length)

total_len = cum_d[-1]
num_rings = int(total_len / 3.5)
uniform_pts = []
raw_idx = 0
for r in range(num_rings):
    target = r * 3.5
    while raw_idx < len(raw_pts) and cum_d[raw_idx + 1] < target:
        raw_idx += 1
    t = (target - cum_d[raw_idx]) / (cum_d[raw_idx + 1] - cum_d[raw_idx]) if (cum_d[raw_idx + 1] > cum_d[raw_idx]) else 0.0
    uniform_pts.append(raw_pts[raw_idx % len(raw_pts)].lerp(raw_pts[(raw_idx + 1) % len(raw_pts)], t))

# Check clearance
min_d = float('inf')
min_pair = None
overlaps = []
total = len(uniform_pts)

for i in range(total):
    p_i = uniform_pts[i]
    for j in range(i + 35, total):
        if (total - (j - i)) < 35:
            continue
        p_j = uniform_pts[j]
        d = (p_i - p_j).length
        if d < min_d:
            min_d = d
            min_pair = (i, j)
        if d < 28.0:
            overlaps.append((i, j, d))

print(f"Total track length: {total_len:.1f}m, Uniform rings: {total}")
print(f"Minimum non-adjacent clearance: {min_d:.2f}m between ring {min_pair[0]} and {min_pair[1]}")
print(f"Ring {min_pair[0]}: {uniform_pts[min_pair[0]]}")
print(f"Ring {min_pair[1]}: {uniform_pts[min_pair[1]]}")
print(f"Overlapping rings (< 28m): {len(overlaps)}")

# Check loop closure tangent continuity
p_first = uniform_pts[0]
p_last = uniform_pts[-1]
p_before_last = uniform_pts[-2]
p_second = uniform_pts[1]
tan_end = (p_first - p_last).normalized()
tan_start = (p_second - p_first).normalized()
print("Tangent at loop seam:", tan_end, "vs start tangent:", tan_start)
print("Seam tangent dot product (1.0 = perfectly seamless):", tan_end.dot(tan_start))
'''

res = send_code(code)
print(res["output"])
