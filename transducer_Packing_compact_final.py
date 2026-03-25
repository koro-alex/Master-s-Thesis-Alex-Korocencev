import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ============================================================
# USER PARAMETERS
# ============================================================
R = 56.0            # sphere radius in mm
small_diameter = 16.0  # circle diameter in mm
small_r = small_diameter / 2.0

# radius of the circles at the north and south pole
radius_large_P = 17.25 - 2.25 - 1 + 1  # mm, only used for the two pole circles

# per-row rotation angles (in degrees), counted from the poles
# index 1 = first row away from poles, index 2 = second row, etc.
row_angle_deg_1 = 22.50
row_angle_deg_2 = 12.85714286
row_angle_deg_3 = 10.0
row_angle_deg_4 = 9.0
row_angle_deg_5 = 0.0


# ============================================================
# BASIC GEOMETRY
# ============================================================
alpha = small_r / R          # approximate geodesic radius (radians)
d_min_geodesic = 2 * alpha   # min center distance on sphere (radians)
d_min_chord = small_diameter # min center distance in 3D space (mm)


# ============================================================
# SPHERE COORDINATE HELPERS
# ============================================================
def sph_colat_to_cart(theta, phi, R):
    """
    theta: colatitude [0..pi], 0 at north pole
    phi:   longitude [0..2pi)
    """
    x = R * np.sin(theta) * np.cos(phi)
    y = R * np.sin(theta) * np.sin(phi)
    z = R * np.cos(theta)
    return np.array([x, y, z])


# ============================================================
# SYMMETRIC RING PACKING FROM POLES
# ============================================================
def generate_centers_ring_symmetric(R, small_r, radius_large_P):
    alpha_s = small_r / R
    alpha_p = radius_large_P / R

    # meridional spacing between small-circle ring centers ≈ 2 * alpha_s
    theta_step = 2 * alpha_s

    centers = []

    # poles (these two will use radius_large_P when drawing)
    centers.append(np.array([0.0, 0.0,  R]))
    centers.append(np.array([0.0, 0.0, -R]))

    # list of colatitudes (north hemisphere) for small-circle ring centers
    thetas = []

    # first ring: tangent between one large pole circle and one small circle
    # distance between centers ≈ alpha_p + alpha_s
    theta = alpha_p + alpha_s

    # ensure small circles do not cross the equator:
    # theta + alpha_s <= pi/2  ->  theta <= pi/2 - alpha_s
    theta_max = np.pi / 2.0 - alpha_s
    while theta <= theta_max + 1e-9:
        thetas.append(theta)
        theta += theta_step

    row_angles_deg = [
        row_angle_deg_1,
        row_angle_deg_2,
        row_angle_deg_3,
        row_angle_deg_4,
        row_angle_deg_5,
    ]

    for ring_index, theta in enumerate(thetas, start=1):
        # ring circumference and max number of small circles
        # C = 2*pi*R*sin(theta)
        # spacing along ring >= 2*small_r  ->  n <= C / (2*small_r)
        n_in_ring = int(np.floor(np.pi * np.sin(theta) / alpha_s))
        if n_in_ring < 1:
            continue

        if ring_index <= len(row_angles_deg):
            phi_offset = np.deg2rad(row_angles_deg[ring_index - 1])
        else:
            phi_offset = 0.0

        for k in range(n_in_ring):
            phi = 2.0 * np.pi * k / n_in_ring + phi_offset

            # north hemisphere ring
            p_north = sph_colat_to_cart(theta, phi, R)
            centers.append(p_north)

            # exact mirror in south hemisphere
            p_south = np.array([p_north[0], p_north[1], -p_north[2]])
            centers.append(p_south)

    return np.array(centers)


# ============================================================
# GENERATE CENTERS
# ============================================================
centers = generate_centers_ring_symmetric(R, small_r, radius_large_P)

print("Circles placed:", len(centers))

# identify indices of the two pole circles to draw them with radius_large_P
pole_indices = []
for i, c in enumerate(centers):
    if np.allclose(c, [0.0, 0.0,  R], atol=1e-6) or np.allclose(c, [0.0, 0.0, -R], atol=1e-6):
        pole_indices.append(i)


# ============================================================
# EXTRA OUTPUT: RING ANGLES AND DISTANCES
# ============================================================
non_pole = []
for c in centers:
    if not (
        np.allclose(c, [0.0, 0.0,  R], atol=1e-6) or
        np.allclose(c, [0.0, 0.0, -R], atol=1e-6)
    ):
        non_pole.append(c)

non_pole = np.array(non_pole)

if non_pole.size > 0:
    z_vals = non_pole[:, 2]

    # colatitude theta from +z, then fold north/south onto same value
    theta = np.arccos(z_vals / R)                  # [0, pi]
    theta_row = np.minimum(theta, np.pi - theta)  # [0, pi/2]

    # group by theta using rounding (rows)
    theta_rounded = np.round(theta_row, 6)
    unique_rows = np.unique(theta_rounded)

    print("\nRing rows (excluding poles):")
    print("row  |  theta [deg]  |  distance center→row plane [mm]  |  distance center→vertical axis [mm]  |  circles in this row (both hemispheres)")
    for idx_row, val in enumerate(unique_rows, start=1):
        mask = (theta_rounded == val)
        theta_val = theta_row[mask][0]

        # distance from sphere center to the plane of this ring (|z|)
        dist_plane = R * np.cos(theta_val)

        # distance from circle center to vertical (z) axis (ring radius in xy-plane)
        dist_axis = R * np.sin(theta_val)

        n_circles_row = mask.sum()
        print(f"{idx_row:3d}  |  {np.degrees(theta_val):10.3f}  |  {dist_plane:29.3f}  |  {dist_axis:32.3f}  |  {n_circles_row:5d}")


# ============================================================
# DRAW FILLED CIRCLE ON SPHERE
# ============================================================
def draw_circle(center_vec, ax, R, circle_r, n_pts=120):
    # unit normal
    n = center_vec / np.linalg.norm(center_vec)
    theta = circle_r / R  # geodesic radius

    # local tangent basis
    tmp = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(tmp, n)) > 0.9:
        tmp = np.array([0.0, 1.0, 0.0])

    t1 = np.cross(n, tmp)
    t1 /= np.linalg.norm(t1)
    t2 = np.cross(n, t1)

    ang = np.linspace(0.0, 2.0 * np.pi, n_pts)
    pts = []
    for a in ang:
        v = np.cos(theta) * n + np.sin(theta) * (np.cos(a) * t1 + np.sin(a) * t2)
        pts.append(R * v)

    pts = np.array(pts)

    poly = Poly3DCollection([pts])
    poly.set_facecolor("lightblue")
    poly.set_edgecolor("red")
    poly.set_linewidth(0.8)
    ax.add_collection3d(poly)


# ============================================================
# 3D PLOT
# ============================================================
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection="3d")
ax.set_box_aspect([1, 1, 1])

# sphere surface
u = np.linspace(0.0, 2.0 * np.pi, 60)
v = np.linspace(0.0, np.pi, 30)
xs = R * np.outer(np.cos(u), np.sin(v))
ys = R * np.outer(np.sin(u), np.sin(v))
zs = R * np.outer(np.ones_like(u), np.cos(v))
ax.plot_surface(xs, ys, zs, color="lightgray", alpha=0.2, linewidth=0)

# circles
for i, c in enumerate(centers):
    if i in pole_indices:
        circle_r = radius_large_P
    else:
        circle_r = small_r
    draw_circle(c, ax, R, circle_r)

ax.set_xlabel("X (mm)")
ax.set_ylabel("Y (mm)")
ax.set_zlabel("Z (mm)")
plt.title(f"Ring (symmetric) packing, R = {R} mm, {len(centers)} circles")
plt.show()