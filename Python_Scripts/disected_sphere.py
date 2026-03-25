import numpy as np
import matplotlib.pyplot as plt

R = 1.0          # sphere radius
L = 2.4 * R      # side length of each square plane

fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, projection="3d")

# ---------- square cutting planes through the origin ----------
s = np.linspace(-L / 2, L / 2, 2)
U, V = np.meshgrid(s, s)

# yz plane: x = 0
X = np.zeros_like(U)
Y = U
Z = V
ax.plot_surface(X, Y, Z, color="lightgray", alpha=0.28, edgecolor="k", linewidth=0.6)

# xz plane: y = 0
X = U
Y = np.zeros_like(U)
Z = V
ax.plot_surface(X, Y, Z, color="silver", alpha=0.28, edgecolor="k", linewidth=0.6)

# xy plane: z = 0
X = U
Y = V
Z = np.zeros_like(U)
ax.plot_surface(X, Y, Z, color="gainsboro", alpha=0.28, edgecolor="k", linewidth=0.6)

# ---------- sphere split into 8 octants ----------
theta_ranges = [(0, np.pi / 2), (np.pi / 2, np.pi)]
phi_ranges = [
    (0, np.pi / 2),
    (np.pi / 2, np.pi),
    (np.pi, 3 * np.pi / 2),
    (3 * np.pi / 2, 2 * np.pi),
]

colors = [
    "blue", "cyan", "blue", "cyan",
    "cyan", "blue", "cyan", "blue"
]

k = 0
for th0, th1 in theta_ranges:
    for ph0, ph1 in phi_ranges:
        theta = np.linspace(th0, th1, 80)
        phi = np.linspace(ph0, ph1, 80)
        theta, phi = np.meshgrid(theta, phi)

        x = R * np.sin(theta) * np.cos(phi)
        y = R * np.sin(theta) * np.sin(phi)
        z = R * np.cos(theta)

        ax.plot_surface(
            x, y, z,
            color=colors[k],
            alpha=0.82,
            edgecolor="none"
        )
        k += 1

# ---------- appearance ----------
lim = L / 2
ax.set_xlim(-lim, lim)
ax.set_ylim(-lim, lim)
ax.set_zlim(-lim, lim)
ax.set_box_aspect([1, 1, 1])
ax.set_axis_off()

plt.tight_layout()
plt.show()
