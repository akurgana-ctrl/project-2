"""כח התערבות — 4s cinematic 3D logo outro (1920x1080 @ 30fps).

Usage: python3 render.py <frames_dir>
Renders PNG frames; encode/mux with build.sh.
"""
import math
import os
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS, DUR = 1920, 1080, 30, 4.0
N = int(FPS * DUR)
CX, CY = W / 2, H / 2 + 10
FOCAL = 1600.0
LOGO_H = 640.0          # on-screen height of the logo at rest (px)
DEPTH = 70.0            # extrusion depth in the same units
LAYERS = 16
T_IN0, T_IMPACT = 0.30, 1.60
HERE = os.path.dirname(os.path.abspath(__file__))

rng = np.random.default_rng(7)


# ---------------------------------------------------------------- helpers
def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def smooth(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ease_out_expo(t):
    t = min(max(t, 0.0), 1.0)
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def ease_out_back(t, s=1.25):
    t = min(max(t, 0.0), 1.0) - 1
    return t * t * ((s + 1) * t + s) + 1


# ---------------------------------------------------------------- logo texture
def load_logo():
    im = Image.open(os.path.join(HERE, "logo.png")).convert("RGBA")
    a = np.asarray(im).astype(np.float32) / 255
    ys, xs = np.where(a[..., 3] > 0.02)
    pad = 6
    a = a[ys.min() - pad:ys.max() + pad + 1, xs.min() - pad:xs.max() + pad + 1]
    scale = 4
    h, w = a.shape[:2]
    prem = a.copy()
    prem[..., :3] *= prem[..., 3:4]
    big = []
    for c in range(4):
        ch = Image.fromarray(prem[..., c]).resize((w * scale, h * scale), Image.LANCZOS)
        big.append(np.asarray(ch))
    big = np.clip(np.stack(big, -1), 0, 1)
    al = big[..., 3]
    rgb = big[..., :3] / np.maximum(al[..., None], 1e-4)
    # crisp edges: steepen alpha around 0.5 (SDF-like upscale)
    al2 = np.clip((al - 0.5) * 2.2 + 0.5, 0, 1)
    al2 = al2 * al2 * (3 - 2 * al2)
    return np.clip(rgb, 0, 1).astype(np.float32), al2.astype(np.float32)


LOGO_RGB, LOGO_A = load_logo()
TH, TW = LOGO_A.shape
LOGO_W = LOGO_H * TW / TH
UU, VV = np.meshgrid(np.linspace(0, 1, TW, dtype=np.float32),
                     np.linspace(0, 1, TH, dtype=np.float32))
GOLDISH = clamp01((LOGO_RGB[..., 0] - LOGO_RGB[..., 2]) * 2.5)  # 1 on gold areas
TOPLIGHT = (1.10 - 0.22 * VV)[..., None]


def front_texture(t):
    rgb = LOGO_RGB * TOPLIGHT
    # metallic sheen sweep after the impact
    p = smooth(T_IMPACT + 0.05, T_IMPACT + 1.05, t) * 2.0 - 0.5
    if -0.4 < p < 1.6:
        band = np.exp(-(((UU * 0.75 + VV * 0.55) - p) / 0.07) ** 2)
        warm = np.stack([1.0, 0.93, 0.75]).astype(np.float32)
        tint = warm * GOLDISH[..., None] + np.array([0.75, 0.82, 1.0], np.float32) * (1 - GOLDISH[..., None])
        rgb = rgb + band[..., None] * tint * 0.85
    return np.clip(rgb, 0, 1.3)


def side_texture(k):
    """Darkened logo silhouette for extrusion layer k (0..1 from front to back)."""
    f = 0.42 - 0.26 * k
    rgb = LOGO_RGB * f * (0.85 + 0.3 * GOLDISH[..., None])
    return rgb


SIDE_TEX = [side_texture(i / (LAYERS - 1)) for i in range(LAYERS)]


# ---------------------------------------------------------------- 3D projection
def rot_matrix(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


def project(R, trans, z_local):
    pts = np.array([[-LOGO_W / 2, -LOGO_H / 2, z_local], [LOGO_W / 2, -LOGO_H / 2, z_local],
                    [LOGO_W / 2, LOGO_H / 2, z_local], [-LOGO_W / 2, LOGO_H / 2, z_local]])
    P = pts @ R.T + trans
    return np.stack([CX + FOCAL * P[:, 0] / P[:, 2], CY + FOCAL * P[:, 1] / P[:, 2]], 1)


def homography(dst):
    src = np.array([[0, 0], [TW, 0], [TW, TH], [0, TH]], float)
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A), np.array(b))


def warp(rgb, alpha, coeffs):
    """Warp a texture onto the canvas. Returns premultiplied rgb, alpha (float)."""
    a8 = Image.fromarray((alpha * 255).astype(np.uint8), "L")
    p = np.clip(rgb * alpha[..., None], 0, 1.3) / 1.3
    p8 = Image.fromarray((p * 255).astype(np.uint8), "RGB")
    ao = np.asarray(a8.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BICUBIC), np.float32) / 255
    po = np.asarray(p8.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BICUBIC), np.float32) / 255 * 1.3
    return po, ao


def logo_pose(t):
    """rx, ry, rz, (tx, ty, tz), opacity"""
    e = (t - T_IN0) / (T_IMPACT - T_IN0)
    pz = ease_out_expo(e * 0.92)
    pr = ease_out_back(e, 1.1)
    if t < T_IMPACT:
        tz = 5200 * (1 - pz)
        ry = -100 * (1 - pr)
        rx = 18 * (1 - pr)
        rz = -10 * (1 - pr)
        ty = -60 * (1 - pz)
    else:
        h = t - T_IMPACT
        punch = -55 * math.exp(-h * 9) * math.cos(h * 26)       # impact recoil
        tz = punch - 70 * smooth(0, 2.4, h)                        # slow push-in
        ry = 4.5 * math.sin(h * 1.25) * smooth(0, 0.5, h)
        rx = -1.8 * math.sin(h * 0.9) * smooth(0, 0.5, h)
        rz = 0.0
        ty = 0.0
    op = smooth(T_IN0, T_IN0 + 0.25, t)
    return rx, ry, rz, (0.0, ty, FOCAL + tz), op


def render_logo(t):
    rx, ry, rz, trans, op = logo_pose(t)
    R = rot_matrix(rx, ry, rz)
    acc = np.zeros((H, W, 3), np.float32)
    acc_a = np.zeros((H, W), np.float32)
    if op <= 0:
        return acc, acc_a
    # extrusion: back to front
    for i in range(LAYERS - 1, -1, -1):
        z = DEPTH * (i + 1) / LAYERS
        c, a = warp(SIDE_TEX[i], LOGO_A, homography(project(R, trans, z)))
        acc = c + acc * (1 - a[..., None])
        acc_a = a + acc_a * (1 - a)
    c, a = warp(front_texture(t), LOGO_A, homography(project(R, trans, 0.0)))
    acc = c + acc * (1 - a[..., None])
    acc_a = a + acc_a * (1 - a)
    return acc * op, acc_a * op


# ---------------------------------------------------------------- background
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
RR = np.sqrt((XX - CX) ** 2 + (YY - CY) ** 2)
ANG = np.arctan2(YY - CY, XX - CX)

h2, w2 = H // 2, W // 2
YY2, XX2 = np.mgrid[0:h2, 0:w2].astype(np.float32)
RR2 = np.sqrt((XX2 - CX / 2) ** 2 + (YY2 - CY / 2) ** 2) * 2
ANG2 = np.arctan2(YY2 - CY / 2, XX2 - CX / 2)
RAY_K = rng.integers(3, 40, 14)
RAY_P = rng.uniform(0, 2 * np.pi, 14)
RAY_A = rng.uniform(0.3, 1.0, 14)

BASE = (np.array([0.012, 0.022, 0.06], np.float32)
        + np.array([0.06, 0.10, 0.22], np.float32) * np.exp(-(RR / 900) ** 2)[..., None])
VIGN = (1 - 0.55 * clamp01((RR / 1150) ** 2.2))[..., None]


def rays(t, strength):
    s = np.zeros_like(ANG2)
    for k, p, a in zip(RAY_K, RAY_P, RAY_A):
        s += a * (0.5 + 0.5 * np.sin(k * ANG2 + p + t * 0.12 * (1 if k % 2 else -1)))
    s = (s / RAY_A.sum()) ** 4
    fall = np.exp(-RR2 / 650) * clamp01(RR2 / 120)
    img = (s * fall * strength)[..., None] * np.array([1.0, 0.82, 0.45], np.float32)
    return np.asarray(Image.fromarray(np.clip(img * 255 / 2, 0, 255).astype(np.uint8))
                      .resize((W, H), Image.BILINEAR), np.float32) / 255 * 2


# dust / bokeh
ND = 260
DUST = np.stack([rng.uniform(-1600, 1600, ND), rng.uniform(-900, 900, ND),
                 rng.uniform(300, 3200, ND)], 1)
DUST_V = rng.normal(0, 1, (ND, 3)) * [12, 10, 0] + [0, -14, -220]
DUST_C = rng.uniform(0, 1, ND)


def dust_layer(t):
    img = Image.new("RGB", (w2, h2))
    d = ImageDraw.Draw(img)
    P = DUST + DUST_V * t
    P[:, 2] = (P[:, 2] - 300) % 2900 + 300
    order = np.argsort(-P[:, 2])
    for i in order:
        x, y, z = P[i]
        sx, sy = (CX + FOCAL * x / z) / 2, (CY + FOCAL * y / z) / 2
        r = max(0.6, 1600 / z * 1.4 + (abs(z - 1600) / 1600) * 2.2)
        br = (0.25 + 0.75 * (1 - z / 3200)) * (0.35 if r > 3 else 1.0)
        col = (np.array([1.0, 0.78, 0.35]) if DUST_C[i] > 0.35 else np.array([0.6, 0.75, 1.0])) * br * 170
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=tuple(int(c) for c in col))
    img = img.filter(ImageFilter.GaussianBlur(1.2)).resize((W, H), Image.BILINEAR)
    return np.asarray(img, np.float32) / 255


# sparks fired at impact
NS = 220
SP_ANG = rng.uniform(0, 2 * np.pi, NS)
SP_SPD = rng.gamma(2.2, 420, NS) + 150
SP_LIFE = rng.uniform(0.35, 1.2, NS)
SP_R0 = rng.uniform(80, 330, NS)
SP_HOT = rng.uniform(0, 1, NS)


def sparks_layer(h):
    img = Image.new("RGB", (W, H))
    if h < 0 or h > 1.3:
        return np.zeros((H, W, 3), np.float32)
    d = ImageDraw.Draw(img)
    drag = 3.2
    for i in range(NS):
        if h > SP_LIFE[i]:
            continue
        dist = SP_R0[i] + SP_SPD[i] * (1 - math.exp(-drag * h)) / drag
        vel = SP_SPD[i] * math.exp(-drag * h)
        ca, sa = math.cos(SP_ANG[i]), math.sin(SP_ANG[i]) * 0.72
        x, y = CX + ca * dist, CY + sa * dist + 160 * h * h
        tail = vel * 0.045 + 3
        x2, y2 = x - ca * tail, y - sa * tail
        life = 1 - h / SP_LIFE[i]
        hot = SP_HOT[i]
        col = (255, int(200 + 55 * hot), int(90 + 150 * hot))
        col = tuple(int(c * life) for c in col)
        d.line([x2, y2, x, y], fill=col, width=2 if hot > 0.6 else 1)
    return np.asarray(img, np.float32) / 255


def shock_ring(h):
    if h < 0 or h > 0.8:
        return 0.0
    r = 150 + 1400 * ease_out_expo(h / 0.8)
    w = 18 + 60 * h
    ring = np.exp(-((RR - r) / w) ** 2) * (1 - h / 0.8) ** 1.5 * 0.45
    return ring[..., None] * np.array([1.0, 0.86, 0.55], np.float32)


def flare(h):
    if h < -0.02:
        return 0.0
    k = math.exp(-max(h, 0) * 5.5)
    streak = np.exp(-((YY - CY) / 7) ** 2) * np.exp(-(np.abs(XX - CX) / 700) ** 1.2)
    glow = np.exp(-(RR / 240) ** 2)
    img = (streak[..., None] * np.array([0.45, 0.7, 1.0], np.float32) * 1.3
           + glow[..., None] * np.array([1.0, 0.9, 0.7], np.float32) * 0.6)
    flash = 0.28 * math.exp(-max(h, 0) * 16)
    return img * k + flash


def bloom(img, thresh=0.75, k=0.55):
    small = np.clip((img - thresh) * 255, 0, 255).astype(np.uint8)
    pil = Image.fromarray(small).resize((W // 4, H // 4), Image.BILINEAR)
    b1 = np.asarray(pil.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR), np.float32)
    b2 = np.asarray(pil.filter(ImageFilter.GaussianBlur(22)).resize((W, H), Image.BILINEAR), np.float32)
    return img + (b1 * 0.6 + b2 * 0.6) / 255 * k


# ---------------------------------------------------------------- frame
def halo_strength(t):
    return 0.08 + 0.45 * smooth(0.2, T_IMPACT, t) + 0.35 * math.exp(-max(t - T_IMPACT, 0) * 3) * (t >= T_IMPACT)


def shake(t):
    h = t - T_IMPACT
    if h < 0:
        return 0, 0
    a = 9 * math.exp(-h * 10)
    return a * math.sin(h * 83), a * math.cos(h * 61)


def render_frame(fi):
    t = fi / FPS
    # motion blur during the fly-in: average sub-frames
    subs = [t + d / FPS for d in (-0.33, 0.0, 0.33)] if T_IN0 < t < T_IMPACT + 0.1 else [t]
    logo_c = np.zeros((H, W, 3), np.float32)
    logo_a = np.zeros((H, W), np.float32)
    for s in subs:
        c, a = render_logo(s)
        logo_c += c / len(subs)
        logo_a += a / len(subs)

    hs = halo_strength(t)
    halo = (np.exp(-(RR / 430) ** 2) * 0.85 + np.exp(-(RR / 900) ** 2) * 0.25) * hs
    img = BASE + halo[..., None] * np.array([0.62, 0.74, 1.0], np.float32)
    img = img + rays(t, 0.15 + 0.9 * smooth(0.0, T_IMPACT, t) - 0.25 * smooth(T_IMPACT, 3.5, t))
    img = img + dust_layer(t) * (0.5 + 0.5 * smooth(0, 0.6, t))
    # soft contact shadow / separation behind logo
    img = img * (1 - 0.25 * logo_a[..., None])
    img = logo_c + img * (1 - logo_a[..., None])

    h = t - T_IMPACT
    img = img + sparks_layer(h) * 1.4
    img = img + shock_ring(h)
    img = img + flare(h)
    img = bloom(img)
    img = img * VIGN

    # camera shake (integer shift is fine at this amplitude)
    dx, dy = shake(t)
    if dx or dy:
        img = np.roll(img, (int(round(dy)), int(round(dx))), (0, 1))

    fade = 1 - smooth(3.70, 4.0, t)
    fade *= smooth(0.0, 0.15, t) * 0.85 + 0.15
    img = img * fade
    img = img + np.random.default_rng(fi).normal(0, 0.012, (H, W, 1)).astype(np.float32)
    out = (np.clip(img, 0, 1) ** (1 / 1.0) * 255 + 0.5).astype(np.uint8)
    return out


def work(fi):
    out = render_frame(fi)
    Image.fromarray(out).save(os.path.join(OUT, f"f{fi:04d}.png"), compress_level=1)
    return fi


if __name__ == "__main__":
    OUT = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    only = [int(x) for x in sys.argv[2:]]
    frames = only or list(range(N))
    with Pool(4, initializer=globals().update, initargs=({"OUT": OUT},)) as p:
        for fi in p.imap_unordered(work, frames):
            print(fi, end=" ", flush=True)
    print()
