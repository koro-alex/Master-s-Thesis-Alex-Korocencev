import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.colors import LinearSegmentedColormap, Normalize

# ============================================================
# USER PARAMETERS
# ============================================================
R_min = 30.0            # mm
R_max = 100.0           # mm
R_step = 0.05           # mm

small_diameter = 16.0   # transducer diameter in mm
small_r = small_diameter / 2.0

# radius of the circles at the north and south pole
radius_large_P = 17.25 - 2.25 - 1 + 1   # mm

# full north south clearance threshold across the equatorial gap
H_minimum = 15.0       # mm

# sinusoidal strip parameters
lambda_bg = 8.583       # mm
phi_bg = -2.405         # rad

# highlighted vertical line
x_highlight = 56.0      # mm

# manual row colors, in order of appearance
row_colors = [
    "crimson",
    "mediumvioletred",
    "darkviolet",
    "mediumblue",
    "lightseagreen",
    "forestgreen",
    "yellowgreen",
    "gold",
    "orange",
]

# font sizes
title_fontsize = 16
label_fontsize = 13
tick_fontsize = 11
colorbar_title_fontsize = 9.0
colorbar_tick_fontsize = 9

# grid and highlight styling
major_grid_lw = 1.4
minor_grid_lw = 0.7
thick_y_grid_lw = 1.4
highlight_lw = 2.0

# grid opacity
major_grid_alpha = 0.50
minor_grid_alpha = 0.38
y_grid_alpha = 0.36
thick_y_grid_alpha = 0.60

# kept unchanged from the original model
row_angle_deg_1 = 22.50
row_angle_deg_2 = 12.85714286
row_angle_deg_3 = 10.0
row_angle_deg_4 = 9.0
row_angle_deg_5 = 0.0


# ============================================================
# ROW COUNT FUNCTION WITH H_minimum CRITERION
# ============================================================
def transducers_per_row(R, small_r, radius_large_P, H_minimum=0.0):
    """
    Returns:
        row_counts: number of 16 mm transducers in each non pole row
                    for one hemisphere only
        row_gaps:   corresponding full north south gap H for each active row

    H is the full straight line distance between
    the lowest point of the relevant northern transducer
    and the highest point of the mirrored southern transducer.
    """
    alpha_s = small_r / R
    alpha_p = radius_large_P / R

    theta_step = 2.0 * alpha_s
    theta = alpha_p + alpha_s
    theta_max = np.pi / 2.0 - alpha_s

    row_counts = []
    row_gaps = []

    while theta <= theta_max + 1e-12:
        H = 2.0 * R * np.cos(theta + alpha_s)

        if H < H_minimum - 1e-12:
            break

        n_in_ring = int(np.floor(np.pi * np.sin(theta) / alpha_s))
        if n_in_ring >= 1:
            row_counts.append(n_in_ring)
            row_gaps.append(H)

        theta += theta_step

    return row_counts, row_gaps


# ============================================================
# SWEEP SPHERE RADIUS
# ============================================================
radii = np.arange(R_min, R_max + 0.5 * R_step, R_step)

all_counts = []
all_gaps = []
coverage_percent = []

for R in radii:
    counts, gaps = transducers_per_row(R, small_r, radius_large_P, H_minimum)
    all_counts.append(counts)
    all_gaps.append(gaps)

    total_small_circles = 2 * sum(counts)   # north + south hemispheres
    covered_area = total_small_circles * np.pi * small_r**2
    sphere_area = 4.0 * np.pi * R**2
    coverage_percent.append(100.0 * covered_area / sphere_area)

coverage_percent = np.array(coverage_percent)

max_rows = max(len(c) for c in all_counts) if all_counts else 0
row_data = np.full((max_rows, len(radii)), np.nan)

for i, counts in enumerate(all_counts):
    row_data[:len(counts), i] = counts


# ============================================================
# FIGURE WITH TOP STRIP + MAIN PLOT + BOTTOM STRIP
# ============================================================
fig = plt.figure(figsize=(11, 7.4))
gs = fig.add_gridspec(
    nrows=3,
    ncols=1,
    height_ratios=[1.2, 22, 1.2],
    hspace=0.0
)

ax_top = fig.add_subplot(gs[0])
ax = fig.add_subplot(gs[1], sharex=ax_top)
ax_strip = fig.add_subplot(gs[2], sharex=ax_top)


# ============================================================
# TOP COVERAGE STRIP
# ============================================================
nx_top = 3000
x_top = np.linspace(R_min, R_max, nx_top)
coverage_interp = np.interp(x_top, radii, coverage_percent)

cov_min = coverage_percent.min()
cov_max = coverage_percent.max()

if cov_max - cov_min > 1e-12:
    coverage_norm = (coverage_interp - cov_min) / (cov_max - cov_min)
else:
    coverage_norm = np.zeros_like(coverage_interp)

coverage_bg = np.tile(coverage_norm, (2, 1))

coverage_cmap = LinearSegmentedColormap.from_list(
    "coverage_cmap",
    ["red", "yellow", "green"]
)

ax_top.imshow(
    coverage_bg,
    extent=[R_min, R_max, 0, 1],
    origin="lower",
    aspect="auto",
    cmap=coverage_cmap,
    alpha=0.95,
    zorder=0
)

ax_top.set_ylim(0, 1)
ax_top.set_yticks([])
ax_top.xaxis.set_major_locator(MultipleLocator(5))
ax_top.xaxis.set_minor_locator(MultipleLocator(1))
ax_top.grid(which="major", axis="x", linewidth=major_grid_lw, alpha=major_grid_alpha)
ax_top.grid(which="minor", axis="x", linewidth=minor_grid_lw, alpha=minor_grid_alpha)
ax_top.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)

ax_top.spines["left"].set_visible(False)
ax_top.spines["right"].set_visible(False)
ax_top.spines["bottom"].set_visible(False)


# ============================================================
# MAIN PLOT
# ============================================================
for row_idx in range(max_rows):
    y = row_data[row_idx]
    valid = ~np.isnan(y)

    x_valid = radii[valid]
    y_valid = y[valid]

    color = row_colors[row_idx % len(row_colors)]

    ax.step(
        x_valid,
        y_valid,
        where="post",
        linewidth=3.2,
        color=color,
        label=f"Row {row_idx + 1}",
        zorder=3
    )

    change_mask = np.r_[True, np.diff(y_valid) != 0]
    ax.plot(
        x_valid[change_mask],
        y_valid[change_mask],
        "o",
        markersize=5.0,
        color=color,
        zorder=4
    )

polar_diameter = 2.0 * radius_large_P

ax.set_ylabel(
    "Transducers per row (counting from pole to equator)",
    fontsize=label_fontsize
)
ax.set_title(
    f"Transducer Row Population versus Sphere Radius, "
    f"Polar Diameter = {polar_diameter:.0f} mm",
    pad=34,
    fontsize=title_fontsize
)

ax.set_xlim(R_min, R_max)
ax.set_ylim(6, 40)
ax.set_yticks(np.arange(6, 41, 2))

ax.xaxis.set_major_locator(MultipleLocator(5))
ax.xaxis.set_minor_locator(MultipleLocator(1))

ax.tick_params(axis="x", which="both", labelbottom=False, labelsize=tick_fontsize)
ax.tick_params(axis="y", which="both", labelsize=tick_fontsize)

ax.grid(which="major", axis="x", linewidth=major_grid_lw, alpha=major_grid_alpha)
ax.grid(which="minor", axis="x", linewidth=minor_grid_lw, alpha=minor_grid_alpha)
ax.grid(which="major", axis="y", linewidth=minor_grid_lw, alpha=y_grid_alpha)

for y in np.arange(8, 41, 4):
    ax.axhline(y, color="gray", linewidth=thick_y_grid_lw, alpha=thick_y_grid_alpha, zorder=1)

# row legend
row_legend = ax.legend(
    ncol=2,
    loc="upper left",
    frameon=True,
    fontsize=9
)
ax.add_artist(row_legend)

# coverage legend
coverage_norm_bar = Normalize(vmin=cov_min, vmax=cov_max)
sm_coverage = plt.cm.ScalarMappable(norm=coverage_norm_bar, cmap=coverage_cmap)
sm_coverage.set_array([])

cax_cov = ax.inset_axes([0.035, 0.39, 0.035, 0.36], zorder=6)
cax_cov.set_facecolor("white")

cbar_cov = fig.colorbar(sm_coverage, cax=cax_cov, orientation="vertical")
ticks_cov = np.linspace(cov_min, cov_max, 5)
cbar_cov.set_ticks(ticks_cov)
cbar_cov.set_ticklabels([f"{t:.1f}" for t in ticks_cov])
cbar_cov.ax.tick_params(labelsize=colorbar_tick_fontsize, pad=2, length=3)
cbar_cov.ax.set_title(
    "Transducer\ncoverage\n[%]",
    fontsize=colorbar_title_fontsize,
    pad=6,
    color="black"
)

# resonance legend
blue_phase_cmap = LinearSegmentedColormap.from_list(
    "blue_phase_cmap",
    [
        (0.00, "cyan"),
        (0.25, "blue"),
        (0.50, "darkblue"),
        (0.75, "blue"),
        (1.00, "cyan"),
    ]
)

res_norm_bar = Normalize(vmin=0, vmax=360)
sm_res = plt.cm.ScalarMappable(norm=res_norm_bar, cmap=blue_phase_cmap)
sm_res.set_array([])

cax_res = ax.inset_axes([0.1375, 0.39, 0.035, 0.36], zorder=6)
cax_res.set_facecolor("white")

cbar_res = fig.colorbar(sm_res, cax=cax_res, orientation="vertical")
cbar_res.set_ticks([0, 90, 180, 270, 360])
cbar_res.set_ticklabels(["0", "90", "180", "270", "360"])
cbar_res.ax.tick_params(labelsize=colorbar_tick_fontsize, pad=2, length=3)
cbar_res.ax.set_title(
    "Transducer\nresonance\n[degrees]",
    fontsize=colorbar_title_fontsize,
    pad=6,
    color="black"
)


# ============================================================
# BOTTOM RESONANCE COLOR STRIP
# ============================================================
blue_cmap = LinearSegmentedColormap.from_list(
    "blue_sine",
    ["cyan", "blue", "darkblue"]
)

nx = 3000
x_bg = np.linspace(R_min, R_max, nx)

sin_vals = np.sin((2*2.0 * np.pi * x_bg / lambda_bg) + phi_bg)
sin_norm = (sin_vals + 1.0) / 2.0

bg = np.tile(sin_norm, (2, 1))

ax_strip.imshow(
    bg,
    extent=[R_min, R_max, 0, 1],
    origin="lower",
    aspect="auto",
    cmap=blue_cmap,
    alpha=0.95,
    zorder=0
)

ax_strip.set_ylim(0, 1)
ax_strip.set_yticks([])
ax_strip.set_xlabel("Sphere radius R (mm)", fontsize=label_fontsize)

ax_strip.xaxis.set_major_locator(MultipleLocator(5))
ax_strip.xaxis.set_minor_locator(MultipleLocator(1))

ax_strip.tick_params(axis="x", which="both", labelsize=tick_fontsize)
ax_strip.grid(which="major", axis="x", linewidth=major_grid_lw, alpha=major_grid_alpha)
ax_strip.grid(which="minor", axis="x", linewidth=minor_grid_lw, alpha=minor_grid_alpha)

ax_strip.spines["left"].set_visible(False)
ax_strip.spines["right"].set_visible(False)
ax_strip.spines["top"].set_visible(False)


# ============================================================
# HIGHLIGHTED VERTICAL LINE AT x = 56 mm
# ============================================================
ax_top.axvline(x_highlight, color="dimgray", linewidth=highlight_lw, zorder=5)
ax.axvline(x_highlight, color="dimgray", linewidth=highlight_lw, zorder=5)
ax_strip.axvline(x_highlight, color="dimgray", linewidth=highlight_lw, zorder=5)

fig.subplots_adjust(top=0.93, bottom=0.09, left=0.08, right=0.98)
plt.show()


# ============================================================
# OPTIONAL TEXT OUTPUT
# ============================================================
print(f"At R = {R_min:.2f} mm: {all_counts[0]}")
print(f"At R = {R_max:.2f} mm: {all_counts[-1]}")

print("\nFirst appearance of each row:")
for row_idx in range(max_rows):
    valid = ~np.isnan(row_data[row_idx])
    first_i = np.argmax(valid)
    print(f"Row {row_idx + 1}: first appears at R = {radii[first_i]:.2f} mm")

print("\nGap H for the last active row at the endpoints:")
for R, counts, gaps in [
    (radii[0], all_counts[0], all_gaps[0]),
    (radii[-1], all_counts[-1], all_gaps[-1])
]:
    if len(gaps) > 0:
        print(f"R = {R:.2f} mm: last active row has H = {gaps[-1]:.3f} mm")
    else:
        print(f"R = {R:.2f} mm: no non pole rows satisfy H_minimum")

print("\nCoverage percentage range of 16 mm transducers only:")
print(f"Minimum achieved coverage: {coverage_percent.min():.3f} %")
print(f"Maximum achieved coverage: {coverage_percent.max():.3f} %")