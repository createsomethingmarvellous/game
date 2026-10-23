"""
Mathematical Verification Script for Zero-Overlap Buddh Circuit Geometry.
"""
from blender_client import send_code

test_code = r'''
import math
from mathutils import Vector

# Mathematically Engineered Anchors with wide turn radii and guaranteed >= 50m separation
anchors = [
    # --- Main Start/Finish Straight (Heading True North: 0, 1, 0) ---
    (0.0, -160.0, 0.0, 0.0),         # Turn 16 exit onto main straight
    (0.0, -80.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0),           # Start / Finish Line & Gantry
    (0.0, 100.0, 2.0, 0.0),
    (0.0, 200.0, 4.5, 0.0),
    (0.0, 280.0, 7.0, 0.0),         # Braking zone for Turn 1

    # --- Turn 1: 90-degree Right Turn (Radius 55m) ---
    (16.0, 318.0, 9.0, 0.04),
    (55.0, 335.0, 10.5, 0.06),       # T1 Apex
    (94.0, 335.0, 12.0, 0.04),

    # --- Turn 2: Sweeping Uphill Left Arc ---
    (145.0, 350.0, 13.5, -0.04),
    (185.0, 395.0, 15.0, -0.06),
    (210.0, 460.0, 16.5, -0.05),
    (215.0, 535.0, 18.0, -0.03),

    # --- Turn 3: Summit Hairpin (Radius 45m, Wide separation) ---
    (230.0, 595.0, 19.0, 0.05),
    (265.0, 625.0, 19.5, 0.08),      # T3 Apex Summit
    (300.0, 595.0, 19.0, 0.06),

    # --- Massive Back Straight (1.05 km heading South-East) ---
    (345.0, 490.0, 17.0, 0.0),
    (400.0, 350.0, 14.5, 0.0),
    (455.0, 210.0, 12.0, 0.0),
    (510.0, 70.0, 9.5, 0.0),
    (565.0, -70.0, 7.0, 0.0),
    (620.0, -210.0, 4.5, 0.0),
    (675.0, -350.0, 2.0, 0.0),
    (705.0, -425.0, 0.5, 0.0),       # Heavy braking for Turn 4

    # --- Turn 4: Right Hairpin (Radius 50m) ---
    (700.0, -475.0, 0.0, 0.06),
    (665.0, -505.0, 0.0, 0.08),      # T4 Apex
    (620.0, -495.0, 0.0, 0.05),

    # --- Straight Chute to Turn 5 (Y <= -340m, 200m south of T16!) ---
    (530.0, -480.0, 0.0, 0.0),
    (420.0, -440.0, 0.0, 0.0),
    (310.0, -400.0, 0.0, 0.0),
    (200.0, -360.0, 0.0, 0.0),
    (100.0, -340.0, 0.0, 0.0),

    # --- Turn 5 & 6: Smooth Cyber Tunnel (Y <= -340m, wide separation!) ---
    (40.0, -340.0, -1.0, -0.04),     # Tunnel Entrance
    (-25.0, -360.0, -2.5, -0.06),    # T5 Apex
    (-75.0, -390.0, -3.5, -0.05),
    (-110.0, -435.0, -3.5, 0.05),    # T6 Apex
    (-110.0, -490.0, -2.0, 0.04),

    # --- Turn 7, 8, 9: S-Section exiting tunnel ---
    (-95.0, -540.0, -0.5, -0.03),    # Tunnel Exit
    (-90.0, -585.0, 0.0, 0.0),
    (-105.0, -625.0, 0.0, 0.05),     # T8 Apex
    (-135.0, -655.0, 0.0, 0.06),     # T9 Apex
    (-175.0, -660.0, 0.0, 0.04),

    # --- Turn 10 & 11: The Iconic Parabolica (Wide Banked Carousel R=75m) ---
    (-225.0, -685.0, 0.0, 0.07),
    (-285.0, -665.0, 0.0, 0.09),     # South apex (banked 5.5 deg)
    (-320.0, -605.0, 0.0, 0.09),     # Mid carousel
    (-305.0, -535.0, 0.0, 0.08),     # Exit apex
    (-265.0, -475.0, 0.0, 0.05),

    # --- Turn 12, 13, 14: Ascending S-curves climbing north ---
    (-225.0, -430.0, 0.0, -0.04),
    (-200.0, -370.0, 0.0, 0.04),
    (-200.0, -280.0, 0.0, -0.03),
    (-200.0, -170.0, 0.0, 0.0),

    # --- Turn 15: Symmetrical 90-degree Left Turn (Radius 45m) ---
    (-190.0, -70.0, 0.0, -0.05),
    (-160.0, -30.0, 0.0, -0.07),     # T15 Apex
    (-115.0, -40.0, 0.0, -0.05),

    # --- Diagonal Chute down to Turn 16 (Keeps X <= -80m, 80m separation from Main Straight!) ---
    (-85.0, -60.0, 0.0, 0.0),
    (-85.0, -95.0, 0.0, 0.0),
    (-80.0, -125.0, 0.0, 0.0),

    # --- Turn 16: Wide Hairpin Arc (Radius R=40m, sweeps from X=-80 to X=0 cleanly!) ---
    (-70.0, -150.0, 0.0, 0.06),
    (-40.0, -165.0, 0.0, 0.08),      # T16 Apex (Radius 40m, center at X=-40, Y=-125)
    (-10.0, -150.0, 0.0, 0.06),
    (0.0, -125.0, 0.0, 0.0),         # Joins Main Straight X=0 heading North!
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

# Arc-length reparameterize
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
'''

res = send_code(test_code)
print(res["output"])
