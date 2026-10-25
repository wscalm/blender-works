"""Poly Haven (CC0) の元画像から、色を物件写真・家具の色に合わせたテクスチャを作る (python3 tools/make_textures.py)。

glTF の baseColorFactor は 1 を超えられない (画像を明るくできない) ので、明るくしたい物・色味を大きく変えたい物は画像の側で色を合わせる。
  gain: 元の色むら (木目の濃淡・色の違い) を残したまま、RGB ごとの倍率で平均の色を target に合わせる (木・壁紙)
  gray: 元の明るさの模様だけを使い、色は target にする (布。元の色がまったく違うとき)
contrast は模様の濃さの倍率 (1 = 元のまま)。計算は全てリニア RGB で行う。
"""
import math
import os

import numpy as np
from PIL import Image

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "textures")

# (作る画像, 元の画像, 方式, 平均の色 sRGB, contrast)
DERIVED = [
    # フローリング: 物件写真 (unilife.co.jp/view/10170) の床の色。ツヤのある明るいはちみつ色
    ("floor_honey_2k.jpg", "laminate_floor_03_diff_2k.jpg", "gain", (176, 122, 62), 1.0),
    # ドア・収納の折れ戸・枠・巾木: 写真のドアの色 (収納と巾木は build_room.py で暗くする)
    ("oak_honey_1k.jpg", "oak_veneer_01_diff_1k.jpg", "gain", (204, 162, 108), 1.0),
    # 木目を薄くした版 (平均の色は元と同じ。濃淡を 25% に)。ドア・収納・枠 / テレビ台の L字棚 / ベッドのヘッドボード。
    # 「テーブルとフローリング以外の木目はあまり見えないように。少し気味が悪い」(ユーザー指定)
    ("oak_honey_soft_1k.jpg", "oak_veneer_01_diff_1k.jpg", "gain", (204, 162, 108), 0.25),
    ("oak_soft_1k.jpg", "oak_veneer_01_diff_1k.jpg", "gain", (161, 126, 87), 0.25),
    ("walnut_soft_1k.jpg", "walnut_veneer_diff_1k.jpg", "gain", (138, 105, 81), 0.25),
    ("oak_light_soft_1k.jpg", "oak_veneer_01_diff_1k.jpg", "gain", (230, 199, 149), 0.25),
    # 明るいナチュラルな木 (スツール)
    ("oak_light_1k.jpg", "oak_veneer_01_diff_1k.jpg", "gain", (230, 199, 149), 1.0),
    # 壁と天井: 白いエンボスのビニールクロス。凹凸の陰影を少し強める
    ("wall_vinyl_1k.jpg", "white_stucco_diff_1k.jpg", "gain", (243, 242, 239), 1.6),
    # ソファーの布 (クッションの色。本体は furniture_sofa.py で少し暗くする)
    ("sofa_fabric_1k.jpg", "poly_wool_herringbone_diff_1k.jpg", "gray", (134, 146, 162), 1.0),
]

# 部屋の距離 (1〜3m) から見る布。元の見本 (約 27cm 角) の織り目は細かすぎて離れると無地に見えるので、
# 見本を tiles x tiles 枚並べ、数 cm〜十数 cm のむら (mottle) と、横糸の太い所の筋 (slub、横向き) を足す。色は target (sRGB の平均)。
# 画像の上下・左右の端はつながる (繰り返して貼れる)。画像1枚の実寸 = 見本の実寸 x tiles (材質の texture_size に使う)
FABRICS = [
    # (作る画像, 元の画像, 平均の色, tiles, 織り目の濃さ, むらの強さ, むらの大きさ (画像の幅に対する割合), 筋の強さ, seed)
    ("curtain_fabric_1k.jpg", "terlenka_diff_1k.jpg", (125, 111, 99), 2, 2.0, 0.07, 0.08, 0.06, 1),   # カーテン (無地のグレージュ寄りの茶)
    ("blanket_fleece_1k.jpg", "polar_fleece_diff_1k.jpg", (48, 48, 51), 2, 1.6, 0.08, 0.06, 0.0, 2),   # 毛布 (黒のフリース。ユーザー指定)
    # 白っぽい綿と帆布。材質の側で色を掛けて使う (common.FABRIC / fabric_material)
    ("cotton_light_1k.jpg", "cotton_jersey_diff_1k.jpg", (242, 240, 235), 2, 1.3, 0.05, 0.10, 0.02, 3),
    ("canvas_light_1k.jpg", "rough_linen_diff_1k.jpg", (238, 234, 224), 2, 1.4, 0.05, 0.08, 0.05, 4),
]


# 敷きパッド (ベッドカバー): タオル地 (terry_cloth の色の模様と、ループの間の陰 = AO を合わせる) に、キルティングの縫い目を薄く入れる。
# 縫い目はひし形 (一辺 約 10cm)。縫い目の所は少しへこんで暗く、縫い糸の点線が見え、間は少しふくらんで明るい。白っぽい色で作り、材質の側で色を掛ける。
# 画像1枚 = 見本 (36.7cm 角) を 2x2 = 0.734m (common.FABRIC の texture_size)。縫い目のひし形はその中に repeat 回繰り返す (端はつながる)
TOWEL = dict(dst="towel_quilt_1k.jpg", src="terry_cloth_diff_1k.jpg", ao="terry_cloth_ao_1k.jpg", target=(240, 240, 237),
             tiles=2, size=0.734, repeat=5, seed=7)
LUMA = np.array([0.2126, 0.7152, 0.0722])


def to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def derive(dst, src, mode, target, contrast):
    img = to_linear(np.asarray(Image.open(os.path.join(TEX, src)).convert("RGB"), dtype=np.float64) / 255)
    goal = to_linear(np.array(target, dtype=np.float64) / 255)
    if mode == "gain":
        mean = img.reshape(-1, 3).mean(axis=0)
        out = (mean + (img - mean) * contrast) * (goal / mean)
    else:
        lum = img @ np.array([0.2126, 0.7152, 0.0722])
        ratio = 1 + (lum / lum.mean() - 1) * contrast
        out = ratio[..., None] * goal
    rgb = np.round(to_srgb(out) * 255).astype(np.uint8)
    Image.fromarray(rgb).save(os.path.join(TEX, dst), quality=90)
    print(f"{dst}: mean sRGB {tuple(int(v) for v in rgb.reshape(-1, 3).mean(axis=0))} (target {target})")


def periodic_noise(n, size, rng):
    """端がつながる、なめらかなむら (平均 0・標準偏差 1)。size = むらの大きさ (画素)"""
    k = np.fft.fftfreq(n)
    k2 = k[:, None] ** 2 + k[None, :] ** 2
    f = np.fft.fft2(rng.standard_normal((n, n))) * np.exp(-2 * (np.pi * size) ** 2 * k2)
    out = np.real(np.fft.ifft2(f))
    return (out - out.mean()) / out.std()


def slubs(n, rng, count):
    """横糸の太い所: 横に細長い筋 (明るい物と暗い物)。端はつながる"""
    out = np.zeros((n, n))
    for _ in range(count):
        y, x0 = rng.integers(0, n, 2)
        length = int(rng.uniform(0.02, 0.15) * n)
        xs = np.arange(x0, x0 + length) % n
        w = np.sin(np.linspace(0, np.pi, length))   # 両端は細く
        out[y % n, xs] += rng.choice((-1, 1)) * rng.uniform(0.5, 1.0) * w
    k = np.fft.fftfreq(n)   # 少しぼかす (縦に 1〜2 画素の太さ)
    blur = np.exp(-2 * (np.pi * 0.8) ** 2 * k[:, None] ** 2 - 2 * (np.pi * 1.5) ** 2 * k[None, :] ** 2)
    return np.real(np.fft.ifft2(np.fft.fft2(out) * blur)) / 0.35


def fabric(dst, src, target, tiles, contrast, mottle, mottle_size, slub, seed):
    img = to_linear(np.asarray(Image.open(os.path.join(TEX, src)).convert("RGB"), dtype=np.float64) / 255)
    lum = img @ np.array([0.2126, 0.7152, 0.0722])
    ratio = np.tile(1 + (lum / lum.mean() - 1) * contrast, (tiles, tiles))
    n = 1024
    ratio = np.asarray(Image.fromarray(ratio.astype(np.float32)).resize((n, n), Image.LANCZOS), dtype=np.float64)
    rng = np.random.default_rng(seed)
    ratio *= 1 + mottle * (0.7 * periodic_noise(n, mottle_size * n, rng) + 0.3 * periodic_noise(n, mottle_size * n / 4, rng))
    if slub:
        ratio *= 1 + slub * slubs(n, rng, 900)
    goal = to_linear(np.array(target, dtype=np.float64) / 255)
    out = np.clip(ratio, 0.2, 3.0)[..., None] * goal
    rgb = np.round(to_srgb(out) * 255).astype(np.uint8)
    Image.fromarray(rgb).save(os.path.join(TEX, dst), quality=88)
    print(f"{dst}: mean sRGB {tuple(int(v) for v in rgb.reshape(-1, 3).mean(axis=0))} (target {target})")


def towel_quilt(dst, src, ao, target, tiles, size, repeat, seed):
    n = 1024
    mm = size * 1000 / n                       # 1画素の実寸 (mm)

    def pattern(name):   # 見本を tiles x tiles に並べた明るさの比 (平均 1)
        a = to_linear(np.asarray(Image.open(os.path.join(TEX, name)).convert("RGB"), dtype=np.float64) / 255) @ LUMA
        a = np.tile(a / a.mean(), (tiles, tiles)).astype(np.float32)
        return np.asarray(Image.fromarray(a).resize((n, n), Image.LANCZOS), dtype=np.float64)
    ratio = 1 + 1.4 * (pattern(src) - 1) + 0.9 * (pattern(ao) - 1)
    rng = np.random.default_rng(seed)
    ratio *= 1 + 0.05 * periodic_noise(n, 0.05 * n, rng) + 0.03 * periodic_noise(n, 0.012 * n, rng)   # パイルの寝た向きのむら
    # キルティング: 斜め 45° の線を2方向に、画像の幅に repeat 本ずつ (線の間隔 = 画像の幅 / repeat / √2)
    x, y = np.meshgrid(np.arange(n) + 0.5, np.arange(n) + 0.5)
    period = n / repeat
    groove = np.zeros((n, n))
    thread = np.zeros((n, n))
    nearest = np.full((n, n), np.inf)
    dash = n / math.sqrt(2) / round(n / math.sqrt(2) / (6.5 / mm))   # 縫い糸の点線の繰り返し (約 6.5mm。画像の端でつながる長さに丸める)
    for s, t in ((x + y, x - y), (x - y, x + y)):
        d = np.abs((s / period + 0.5) % 1 - 0.5) * period / math.sqrt(2)   # 線からの距離 (画素)
        nearest = np.minimum(nearest, d)
        groove = np.maximum(groove, np.exp(-(d * mm / 5.0) ** 2))         # へこみ (幅 約 1cm)
        on = ((t / math.sqrt(2) / dash) % 1) < 0.6                          # 点線 (縫い目 4mm・すき間 2.5mm)
        thread = np.maximum(thread, on * np.clip(1.2 - d * mm / 0.9, 0, 1))
    puff = np.clip(nearest / (period / (2 * math.sqrt(2))), 0, 1)
    puff = puff * puff * (3 - 2 * puff)                                     # ひし形の真ん中ほどふくらむ
    ratio *= (1 - 0.11 * groove) * (1 - 0.12 * thread) * (0.98 + 0.05 * puff)
    goal = to_linear(np.array(target, dtype=np.float64) / 255)
    rgb = np.round(to_srgb(np.clip(ratio, 0.2, 3.0)[..., None] * goal) * 255).astype(np.uint8)
    Image.fromarray(rgb).save(os.path.join(TEX, dst), quality=88)
    print(f"{dst}: mean sRGB {tuple(int(v) for v in rgb.reshape(-1, 3).mean(axis=0))} (target {target})")


if __name__ == "__main__":
    for row in DERIVED:
        derive(*row)
    for row in FABRICS:
        fabric(*row)
    towel_quilt(**TOWEL)
