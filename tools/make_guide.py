"""家具の位置を指示するための座標ガイド図 (平面図) を作る。

    python3 tools/make_guide.py        # -> renders/guide_plan.png

寸法は scripts/room_spec.py から読むので、部屋を変えたら自動で追従する。
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from layout import FURNITURE, corners, footprint, rotation_deg
from room_spec import *

FONT_PATH = "/usr/share/fonts/opentype/ipaexfont-gothic/ipaexg.ttf"
S = 170                       # 1m あたりの画素数
L, R, T, B = 240, 250, 230, 230
RW, RH = round(ROOM_W * S), round(ROOM_D * S)
WT = round(WALL_T * S)
W, H = L + RW + R, T + RH + B

C_FLOOR, C_GRID_MINOR, C_GRID, C_GRID_1M = (246, 236, 215), (238, 227, 203), (214, 199, 170), (186, 166, 130)
C_WALL, C_TEXT, C_SUB = (72, 72, 78), (40, 40, 44), (110, 110, 118)
C_WINDOW, C_DOOR, C_CLOSET, C_ACCENT = (150, 200, 238), (222, 184, 120), (236, 229, 205), (200, 70, 60)


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def P(x, y):
    """部屋の座標 (X=西壁から, Y=南壁から, m) -> 画像の画素。北が上。"""
    return (L + x * S, T + (ROOM_D - y) * S)


def ticks(length, step=0.5):
    """0.5m ごとの目盛り。端が半端なら、端の数値を優先して手前の目盛りを間引く。"""
    vals = [i * step for i in range(int(length / step + 1e-9) + 1)]
    if abs(vals[-1] - length) > 1e-9:
        if length - vals[-1] < step / 2:
            vals.pop()
        vals.append(length)
    return vals


def text_block(d, xy, lines, size=17, color=C_TEXT, h="l", gap=4):
    """複数行テキスト。xy は左端 (h='l') / 中央 (h='m') / 右端 (h='r') の最初の行の中心。"""
    f = font(size)
    x, y = xy
    for line in lines:
        d.text((x, y), line, font=f, fill=color, anchor=f"{h}m")
        y += size + gap


def dashed_rect(d, box, color, dash=8, width=2):
    x0, y0, x1, y1 = box
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        n = max(1, int(math.hypot(bx - ax, by - ay) // dash))
        for i in range(0, n, 2):
            d.line([(ax + (bx - ax) * i / n, ay + (by - ay) * i / n),
                    (ax + (bx - ax) * min(i + 1, n) / n, ay + (by - ay) * min(i + 1, n) / n)],
                   fill=color, width=width)


def arrow(d, a, b, color=C_TEXT, width=3):
    d.line([a, b], fill=color, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-0.45, 0.45):
        d.line([b, (b[0] - 14 * math.cos(ang + s), b[1] - 14 * math.sin(ang + s))], fill=color, width=width)


def main():
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)

    # 床とグリッド (0.25m 薄線 / 0.5m 線 / 1m 太線)
    d.rectangle([P(0, ROOM_D), P(ROOM_W, 0)], fill=C_FLOOR)
    for i in range(0, int(ROOM_W / 0.25) + 1):
        x = i * 0.25
        col, w = (C_GRID_1M, 2) if i % 4 == 0 else (C_GRID, 1) if i % 2 == 0 else (C_GRID_MINOR, 1)
        d.line([P(x, 0), P(x, ROOM_D)], fill=col, width=w)
    for j in range(0, int(ROOM_D / 0.25) + 1):
        y = j * 0.25
        col, w = (C_GRID_1M, 2) if j % 4 == 0 else (C_GRID, 1) if j % 2 == 0 else (C_GRID_MINOR, 1)
        d.line([P(0, y), P(ROOM_W, y)], fill=col, width=w)

    # ドアの開閉範囲 (蝶番は北端。室内側へ開く)
    door = WEST_DOOR
    dw = door["y1"] - door["y0"]
    hx, hy = P(0, door["y1"])
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.pieslice([hx - dw * S, hy - dw * S, hx + dw * S, hy + dw * S], 0, 90,
                fill=(*C_ACCENT, 60), outline=(*C_ACCENT, 200), width=2)
    img = Image.alpha_composite(img, overlay)
    d = ImageDraw.Draw(img)
    text_block(d, (P(0.10, 1.00)[0], P(0, 1.0)[1] + 6), ["ドアの開閉範囲", "(家具NG)"], 15, C_ACCENT)

    # 壁 (開口部は色を変えて隙間にする)
    def wall(x0, x1, y0, y1, color=C_WALL):
        a, b = P(x0, y1), P(x1, y0)
        d.rectangle([a, b], fill=color)

    t = WALL_T
    wall(-t, ROOM_W + t, ROOM_D, ROOM_D + t)                  # 北
    wall(-t, ROOM_W + t, -t, 0)                               # 南
    e, wn, cl, dr = EAST_WINDOW, None, WEST_CLOSET, WEST_DOOR
    wall(ROOM_W, ROOM_W + t, 0, e["y0"])                      # 東 (窓の南)
    wall(ROOM_W, ROOM_W + t, e["y1"], ROOM_D)                 # 東 (窓の北)
    wall(ROOM_W, ROOM_W + t, e["y0"], e["y1"], C_WINDOW)      # 掃き出し窓
    wall(-t, 0, 0, dr["y0"])                                  # 西
    wall(-t, 0, dr["y1"], cl["y0"])
    wall(-t, 0, cl["y1"], ROOM_D)
    wall(-t, 0, dr["y0"], dr["y1"], C_DOOR)                   # ドア
    wall(-t, 0, cl["y0"], cl["y1"], C_CLOSET)                 # 収納折れ戸
    for k in range(1, 4):                                     # 折れ戸の4枚の継ぎ目
        y = cl["y0"] + (cl["y1"] - cl["y0"]) * k / 4
        d.line([P(-t, y), P(0, y)], fill=C_WALL, width=1)
    d.line([P(ROOM_W, (e["y0"] + e["y1"]) / 2), P(ROOM_W + t, (e["y0"] + e["y1"]) / 2)], fill=C_WALL, width=2)

    # エアコン (東壁)
    a = AIRCON
    ay0, ay1 = a["y_center"] - a["width"] / 2, a["y_center"] + a["width"] / 2
    d.rectangle([P(ROOM_W - a["depth"], ay1), P(ROOM_W, ay0)], fill=(252, 252, 250), outline=(120, 120, 126), width=2)

    # 出窓: 天板 (壁の開口から前面まで) + 左右の側面のガラス枠 + 前面のガラス
    b = NORTH_BAY
    yf = ROOM_D + b["depth"]
    d.rectangle([P(b["x0"], yf), P(b["x1"], ROOM_D)], fill=(240, 236, 224))
    for xa, xb in ((b["x0"] - 0.05, b["x0"]), (b["x1"], b["x1"] + 0.05)):
        d.rectangle([P(xa, yf), P(xb, ROOM_D + t)], fill=C_WINDOW, outline=C_WALL)
    d.rectangle([P(b["x0"], yf), P(b["x1"], yf - 0.04)], fill=C_WINDOW, outline=C_WALL)

    # 配置済みの家具の足元 (矢印 = 正面の向き)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for fur in FURNITURE.values():
        od.polygon([P(*c) for c in corners(fur)], fill=(*fur["color"], 150), outline=(*fur["color"], 255), width=2)
    img = Image.alpha_composite(img, overlay)
    d = ImageDraw.Draw(img)
    used = []   # 足元に書いた文字の矩形 (机の上の物どうしで重ならないように、重なったら下へずらす)
    for fur in FURNITURE.values():
        x0, y0, x1, y1 = footprint(fur)
        (ax, ay), (bx, by) = P(x0, y1), P(x1, y0)
        cx, cy = (ax + bx) / 2, (ay + by) / 2
        ang = math.radians(rotation_deg(fur))
        fx, fy = math.sin(ang), math.cos(ang)   # 正面の向き (画像上。下=南)。回転 0 = 南向き
        n = max(14, min(bx - ax, by - ay) * 0.45)
        arrow(d, (cx, cy), (cx + fx * n, cy + fy * n), color=(30, 30, 34), width=2)
        ink = (30, 30, 34) if sum(fur["color"]) > 600 else (255, 255, 255)   # 白っぽい家具には黒い文字
        on_desk = fur.get("z0", 0) > 0.3    # 机や出窓の天板の上の物は小さい文字
        size = 11 if on_desk else 13
        tw = font(size).getlength(fur["label"])
        if tw + 4 <= bx - ax and by - ay >= (14 if on_desk else 26):
            ty = cy - 12
            while any(abs(ty - uy) < size + 1 and abs(cx - ux) < (tw + uw) / 2 for ux, uy, uw in used):
                ty += size + 2
            used.append((cx, ty, tw))
            d.text((cx, ty), fur["label"], font=font(size), fill=ink, anchor="mm")
        elif on_desk:   # 机の上の小さな物 (マウスなど) は、足元のすぐ北 (上) に書く
            ty = ay - size / 2 - 2
            while any(abs(ty - uy) < size + 1 and abs(cx - ux) < (tw + uw) / 2 for ux, uy, uw in used):
                ty -= size + 2
            used.append((cx, ty, tw))
            d.text((cx, ty), fur["label"], font=font(size), fill=(30, 30, 34), anchor="mm")
        else:   # 細い家具は足元に文字が入らないので、右の余白に書く
            text_block(d, (L + RW + WT + 30, cy + 70), [fur["label"]], 16, fur["color"])

    # --- 目盛りと名前 ---
    for x in ticks(ROOM_W):
        d.text((P(x, 0)[0], T + RH + WT + 22), f"{x:g}", font=font(18), fill=C_TEXT, anchor="mm")
    for y in ticks(ROOM_D):
        d.text((L - WT - 14, P(0, y)[1]), f"{y:g}", font=font(18), fill=C_TEXT, anchor="rm")

    d.text((L, 36), f"洋室 10.0帖   {ROOM_W:g}m × {ROOM_D:g}m   天井高 {ROOM_H:g}m", font=font(30), fill=C_TEXT, anchor="lm")
    d.text((L, 74), "座標ガイド (上から見た図 / 単位 m)", font=font(18), fill=C_SUB, anchor="lm")

    d.text((P(ROOM_W * 0.68, 0)[0], T - WT - 28), f"▲ 北壁   Y = {ROOM_D:g}", font=font(20), fill=C_TEXT, anchor="mm")
    d.text((L + RW // 2, T + RH + WT + 60), "X [m]   西壁からの距離  →  東へ増える", font=font(18), fill=C_TEXT, anchor="mm")
    d.text((L + RW // 2, T + RH + WT + 92), "▼ 南壁   Y = 0   (開口なし)", font=font(20), fill=C_TEXT, anchor="mm")
    text_block(d, (L + RW + WT + 30, T + 4), ["東壁  X = %g" % ROOM_W, "(バルコニー側)"], 20, C_TEXT)
    text_block(d, (12, T - 6), ["西壁  X = 0", "(キッチン・玄関側)"], 18, C_TEXT)
    d.text((12, 110), "↑ Y [m]   南壁からの距離 (北へ増える)", font=font(15), fill=C_SUB, anchor="lm")

    # 開口部の注記 (西=左の余白 / 東=右の余白 / 北)
    text_block(d, (12, P(0, 3.45)[1] + 30), ["収納 (折れ戸4枚)", f"Y {cl['y0']:.2f}〜{cl['y1']:.2f}", "高さ 0〜%.1fm" % cl["z1"]], 15, (130, 100, 40))
    text_block(d, (12, P(0, 1.20)[1] + 0), ["ドア (室内側へ開く)", f"Y {dr['y0']:.2f}〜{dr['y1']:.2f}", "蝶番は北側"], 15, (130, 100, 40))
    xr = L + RW + WT + 30
    text_block(d, (xr, P(0, 1.6)[1] - 38), ["掃き出し窓", "(引き違い2枚)", f"Y {e['y0']:.2f}〜{e['y1']:.2f}", "高さ 0〜%.1fm" % e["z1"]], 16, (40, 100, 160))
    text_block(d, (xr, P(0, a["y_center"])[1] - 24), ["エアコン", f"Y {ay0:.2f}〜{ay1:.2f}", f"高さ {a['z0']:.2f}〜{a['z0'] + a['height']:.2f}m"], 16, C_SUB)
    d.text((P(b["x0"], 0)[0], P(0, yf)[1] - 22), f"出窓 (腰高窓)  X {b['x0']:.2f}〜{b['x1']:.2f}   出幅 {b['depth']:.2f}   天板の高さ {b['sill_z']:.2f}m", font=font(16), fill=C_SUB, anchor="lm")

    # 軸の凡例 (右下)
    ox, oy = L + RW + 90, T + RH + 100
    arrow(d, (ox, oy), (ox + 70, oy))
    arrow(d, (ox, oy), (ox, oy - 70))
    d.ellipse([ox - 8, oy - 8, ox + 8, oy + 8], outline=C_TEXT, width=3)
    d.ellipse([ox - 2, oy - 2, ox + 2, oy + 2], fill=C_TEXT)
    d.text((ox + 78, oy), "+X 東", font=font(17), fill=C_TEXT, anchor="lm")
    d.text((ox, oy - 82), "+Y 北", font=font(17), fill=C_TEXT, anchor="mm")
    d.text((ox + 14, oy + 22), "+Z 上 (手前へ)", font=font(15), fill=C_SUB, anchor="lm")

    d.text((12, H - 54), "色付きの四角 = 置いた家具の足元 (矢印 = 正面の向き)。位置・向き・大きさは scripts/layout.py", font=font(15), fill=C_SUB, anchor="lm")
    d.text((12, H - 28), "座標 (X, Y) = (西壁からの距離, 南壁からの距離)  Z = 床からの高さ。 東西南北は間取り図の向き (上=北) に合わせた呼び方で、実際の方位とは無関係。",
           font=font(15), fill=C_SUB, anchor="lm")

    out = os.path.join(ROOT, "renders", "guide_plan.png")
    img.convert("RGB").save(out)
    print("WROTE:", out, img.size)


if __name__ == "__main__":
    main()
