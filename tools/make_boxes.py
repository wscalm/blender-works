"""出窓の段ボール箱 2箱の印刷を描いて textures/ に保存する (python3 tools/make_boxes.py)。

ユーザー指定の実物の商品のケース。ネットの商品写真 (Amazon の商品ページ・メーカーのニュースリリース) から面ごとに採寸して描いた:
  box_water.jpg  い・ろ・は・す 天然水 ラベルレス 560ml×24本 (日本コカ・コーラ。2022年からの版)。
                 クラフト紙の地に、ミントの波で縁取ったクリームの帯・緑の星・黒い筆の字
  box_tea.jpg    伊藤園 ラベルレス お～いお茶 緑茶 460ml×30本 スマートボトル (2024年夏からの版)。
                 上の帯をクラフト紙のまま残した黄緑の地に、Smart Bottle BOX の帯・濃い緑の四角に抜いた「ラベルレス 30本入り」・筆の字のロゴ
箱の面 (正面 = 背面 / 側面 = 左右 / 上面 / 印刷の無い底) を1枚の画像に並べる。並びは scripts/layout.py の box_atlas()
(scripts/furniture_boxes.py も同じ物で貼る)。面の座標は mm で、左上が原点・下が +y。上面は画像の上が箱の奥。
印刷は色ごとの版 (Plate) を重ねて作る: 版に形を描き、字などを v=0 で描くと「抜き」(下の版や段ボールの地が見える)。
写真の網点 (星の薄い緑・ミントの帯) は、網点を平均した色で塗る。
字は Windows のフォント (無ければ IPAex など)。ロゴは似た書体の字を1字ずつ写真の位置に置いて似せた物 (写真の画像は使わない)。
バーコードは商品の JAN と、その頭に 0 を付けた ITF (ケースの写真と同じ) を正しく符号にした物
"""
import functools
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from make_prints import GOTHIC, MINCHO, SANS_BOLD, _apply_ink, _paper, save
from layout import BOX_IMAGE, BOX_PPM, FURNITURE, box_atlas

SS = 3   # 3倍の大きさで描いて縮める
WIN_FONTS = "/mnt/c/Windows/Fonts"
FONTS = {   # 書体の種類: (Windows のフォント, 無いときの代わり)
    "sans": ("NotoSansJP-VF.ttf", GOTHIC),        # 太いゴシック (weight で太さを変えられる)
    "brush": ("HGRSKP.TTF", MINCHO),              # HG正楷書体-PRO: い・ろ・は・す の筆の字
    "gyosho": ("HGRGY.TTC", MINCHO),              # HG行書体: お～いお茶 の筆の字
    "mincho": ("HGRME.TTC", MINCHO),              # HG明朝E: 伊藤園
    "round": ("ARLRDBD.TTF", SANS_BOLD),          # Arial Rounded MT Bold: Smart Bottle BOX・Eco&Happy
    "geo": ("GOTHICB.TTF", SANS_BOLD),            # Century Gothic Bold: NATURAL MINERAL WATER
    "hand": ("UDDigiKyokashoN-B.ttc", GOTHIC),    # UD デジタル教科書体: 手書き風の ラベルレス
    "mono": (None, "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),   # バーコードの数字
}


@functools.lru_cache(maxsize=None)
def _font(kind, px, weight=None):
    name, fallback = FONTS[kind]
    path = os.path.join(WIN_FONTS, name) if name else fallback
    if not os.path.exists(path):
        path = fallback
    f = ImageFont.truetype(path, px)
    if weight and path.endswith("-VF.ttf"):
        f.set_variation_by_axes([weight])
    return f


@functools.lru_cache(maxsize=None)
def _glyphs(text, kind="sans", weight=None, stroke=0.0, spacing=0.0, vertical=False, size=240):
    """字の形 (L のマスク。字の外接の箱で切り取る)。大きく描いて、置くときに縮める。
    stroke = 字を太らせる幅、spacing = 字の間に足す幅 (どちらも字の大きさに対する割合)。vertical = 縦書き"""
    f = _font(kind, size, weight)
    sw = round(stroke * size)
    long = int(size * (len(text) * (1.3 + spacing) + 2))
    m = Image.new("L", (size * 3, long) if vertical else (long, size * 3), 0)
    d = ImageDraw.Draw(m)
    if vertical:
        y = size
        for ch in text:
            d.text((size * 1.5, y), {"ー": "｜"}.get(ch, ch), font=f, fill=255, anchor="mt", stroke_width=sw, stroke_fill=255)
            y += size * (1 + spacing)
    elif spacing:
        x = size
        for ch in text:
            d.text((x, size), ch, font=f, fill=255, stroke_width=sw, stroke_fill=255)
            x += f.getlength(ch) + spacing * size
    else:
        d.text((size, size), text, font=f, fill=255, stroke_width=sw, stroke_fill=255)
    return m.crop(m.getbbox())


# ---------------------------------------------------------------- バーコード
_EAN_L = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
_EAN_G = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"]
_EAN_R = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"]
_EAN_FIRST = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]
_ITF = ["NNWWN", "WNNNW", "NWNNW", "WWNNN", "NNWNW", "WNWNN", "NWWNN", "NNNWW", "WNNWN", "NWNWN"]


def gtin(body):
    """チェックディジットを足す (JAN・ITF 共通。右の桁から 3, 1, 3, ... の重み)"""
    s = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed(body)))
    return body + str((10 - s % 10) % 10)


def _ean13(code):
    """JAN (EAN-13) の 95 モジュールの白黒 ("1" = 黒)"""
    d = [int(c) for c in code]
    left = "".join((_EAN_L if p == "L" else _EAN_G)[x] for p, x in zip(_EAN_FIRST[d[0]], d[1:7]))
    return "101" + left + "01010" + "".join(_EAN_R[x] for x in d[7:]) + "101"


def _itf(code, wide=2.5):
    """ITF (2つずつ組にして、1つ目を黒の太さ・2つ目を白の太さで表す) の [(幅, 黒か)]"""
    els = [(1, True), (1, False), (1, True), (1, False)]
    for a, b in zip(code[0::2], code[1::2]):
        for pa, pb in zip(_ITF[int(a)], _ITF[int(b)]):
            els += [(wide if pa == "W" else 1, True), (wide if pb == "W" else 1, False)]
    return els + [(wide, True), (1, False), (1, True)]


# ---------------------------------------------------------------- 面と版
class Face:
    """印刷する面1つ。mm (左上が原点、下が +y) で描き、SS 倍の大きさの RGBA の画像に版を重ねていく"""

    def __init__(self, w, h):
        self.w, self.h, self.u = w, h, BOX_PPM * SS
        self.img = Image.new("RGBA", (round(w * self.u), round(h * self.u)), (0, 0, 0, 0))

    def plate(self, color):
        return Plate(self, color)

    def paste(self, rgba, xy):
        """RGBA の画像を (x, y) (画素) に重ねる。はみ出した所は切る"""
        x, y = xy
        l, t = max(0, -x), max(0, -y)
        r, b = min(rgba.width, self.img.width - x), min(rgba.height, self.img.height - y)
        if r > l and b > t:
            self.img.alpha_composite(rgba.crop((l, t, r, b)), dest=(x + l, y + t))


class Plate:
    """1色の版: 面と同じ大きさのマスクに形を描き、with を抜けると color で塗る。
    形は v=255 で描き足し、v=0 で抜く (抜いた所は下の版や段ボールの地が見える)"""

    def __init__(self, face, color):
        self.face, self.color, self.u = face, color, face.u
        self.mask = Image.new("L", face.img.size, 0)
        self.d = ImageDraw.Draw(self.mask)

    def __enter__(self):
        return self

    def __exit__(self, kind, *_):
        if kind is None:
            over = Image.new("RGBA", self.mask.size, (*self.color, 255))
            over.putalpha(self.mask)
            self.face.img.alpha_composite(over)

    def _w(self, line):
        return max(1, round(line * self.u))

    def rect(self, x0, y0, x1, y1, r=0, line=None, v=255):
        """長方形。r = 角の丸み、line = 線の太さ (無ければ塗る)"""
        u = self.u
        box = [x0 * u, y0 * u, x1 * u - 1, y1 * u - 1]
        kw = dict(fill=v) if line is None else dict(outline=v, width=self._w(line))
        if r:
            self.d.rounded_rectangle(box, radius=r * u, **kw)
        else:
            self.d.rectangle(box, **kw)

    def ellipse(self, cx, cy, rx, ry=None, line=None, v=255, angle=0.0):
        """楕円 (angle = 長さ rx の軸の傾き、度、反時計回り)"""
        ry = rx if ry is None else ry
        a = math.radians(angle)
        pts = [(cx + rx * math.cos(t) * math.cos(a) + ry * math.sin(t) * math.sin(a),
                cy - rx * math.cos(t) * math.sin(a) + ry * math.sin(t) * math.cos(a)) for t in np.linspace(0, 2 * math.pi, 145)]
        if line is None:
            self.poly(pts, v)
        else:
            self.line(pts, line, v)

    def poly(self, pts, v=255):
        self.d.polygon([(x * self.u, y * self.u) for x, y in pts], fill=v)

    def line(self, pts, w, v=255):
        self.d.line([(x * self.u, y * self.u) for x, y in pts], fill=v, width=self._w(w), joint="curve")

    def dashed(self, pts, w, dash=2.0, gap=1.5, v=255):
        """点線 (折れ線に沿って dash mm 描いて gap mm 空ける)"""
        pts = np.array(pts, float)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        for a in np.arange(0, s[-1], dash + gap):
            ts = np.linspace(a, min(a + dash, s[-1]), 6)
            self.line(list(zip(np.interp(ts, s, pts[:, 0]), np.interp(ts, s, pts[:, 1]))), w, v)

    def text(self, s, box, kind="sans", v=255, fit="box", align="c", turn=0, rot=0.0, **kw):
        """字を box (mm の (x0, y0, x1, y1)) に置く。fit: "box" = 字の外接の箱を box にぴったり合わせる (縦横の比が変わる) /
        "h" = 高さを合わせ、横は字の比のまま align ("l" "c" "r") に寄せる / "w" = 幅を合わせ、縦は真ん中。
        turn = 字を先に回す角度 (90 / 180 / 270。box は回した後の向き)、rot = 置いた後に box の中心のまわりに回す角度 (度、反時計回り)"""
        g = _glyphs(s, kind, **kw)
        if turn:
            g = g.transpose({90: Image.ROTATE_90, 180: Image.ROTATE_180, 270: Image.ROTATE_270}[turn])
        u = self.u
        x0, y0, x1, y1 = (c * u for c in box)
        bw, bh = x1 - x0, y1 - y0
        if fit == "box":
            tw, th = bw, bh
        elif fit == "h":
            tw, th = g.width * bh / g.height, bh
        else:
            tw, th = bw, g.height * bw / g.width
        g = g.resize((max(1, round(tw)), max(1, round(th))), Image.LANCZOS)
        x, y = x0 + {"l": 0, "c": (bw - tw) / 2, "r": bw - tw}[align], y0 + (bh - th) / 2
        if rot:
            cx, cy = x + g.width / 2, y + g.height / 2
            g = g.rotate(rot, resample=Image.BICUBIC, expand=True)
            x, y = cx - g.width / 2, cy - g.height / 2
        self.mask.paste(v, (round(x), round(y)), g)

    def lines(self, rows, x0, y0, x1, step, h, kind="sans", v=255, **kw):
        """小さな字の段落 (行ごとに幅 x0〜x1 まで。短い行は字の比のまま左に寄せる)"""
        for i, row in enumerate(rows):
            g = _glyphs(row, kind, **kw)
            fit = "box" if g.width / g.height * h > x1 - x0 else "h"
            self.text(row, (x0, y0 + i * step, x1, y0 + i * step + h), kind, v, fit=fit, align="l", **kw)

    def arc_text(self, s, cx, cy, r, cap, kind, a0, a1, v=255):
        """円弧に沿った字 (上の弧で左から右へ。字の上が外を向く)。r = 字の高さの真ん中の半径、cap = 大文字の高さ (mm)、
        a0 → a1 = 最初と最後の字の中心の角度 (度、反時計回り)。字の大きさの比とベースラインはフォントのまま"""
        size = 200
        f = _font(kind, size)
        top, bottom = f.getbbox("H")[1], f.getbbox("H")[3]
        k = cap * self.u / (bottom - top)
        widths = np.array([f.getlength(ch) for ch in s])
        centers = np.cumsum(widths) - widths / 2
        angs = a0 + (a1 - a0) * (centers - centers[0]) / (centers[-1] - centers[0])
        rb = r - cap / 2                                     # ベースラインの半径
        for ch, ang in zip(s, angs):
            m = Image.new("L", (size * 2, size * 2), 0)
            ImageDraw.Draw(m).text((size, size), ch, font=f, fill=255, anchor="ms")
            m = m.resize((max(1, round(m.width * k)), max(1, round(m.height * k))), Image.LANCZOS)
            m = m.rotate(ang - 90, resample=Image.BICUBIC)
            t = math.radians(ang)
            px, py = (cx + rb * math.cos(t)) * self.u, (cy - rb * math.sin(t)) * self.u
            self.mask.paste(v, (round(px - m.width / 2), round(py - m.height / 2)), m)

    def glyph_row(self, chars, xs, y0, kind, stroke=0.0, v=255):
        """筆の字を1字ずつ置く: 字ごとに外接の箱の横の範囲を xs [(x0, x1), ...] (mm) に合わせ (縦横の比はそのまま)、
        字のベースラインを揃えて、一番上に出る字の上端を y0 に置く"""
        size = 240
        f = _font(kind, size)
        items = []
        for ch, (a, b) in zip(chars, xs):
            m = Image.new("L", (size * 3, size * 3), 0)
            ImageDraw.Draw(m).text((size, size * 2), ch, font=f, fill=255, anchor="ls", stroke_width=round(stroke * size), stroke_fill=255)
            bb = m.getbbox()
            k = (b - a) * self.u / (bb[2] - bb[0])
            items.append((m.crop(bb), k, a, bb[1] - size * 2))
        base = y0 * self.u - min(k * top for _, k, _, top in items)
        for g, k, a, top in items:
            g = g.resize((max(1, round(g.width * k)), max(1, round(g.height * k))), Image.LANCZOS)
            self.mask.paste(v, (round(a * self.u), round(base + k * top)), g)

    def ean13(self, code, box, v=255):
        """JAN (EAN-13) のバーコード。box = 線の範囲 (mm)。両端と真ん中の区切りの線は下へ長く、数字は線の下"""
        x0, y0, x1, y1 = box
        mods = _ean13(code)
        mw = (x1 - x0) / len(mods)
        dh = (y1 - y0) * 0.16
        for i, c in enumerate(mods):
            if c == "1":
                guard = i < 3 or 45 <= i < 50 or i >= 92
                self.rect(x0 + i * mw, y0, x0 + (i + 1) * mw + 0.02, y1 + (dh * 0.6 if guard else 0), v=v)
        for s, a, b in ((code[0], -8, -1), (code[1:7], 3, 45), (code[7:], 50, 92)):
            self.text(s, (x0 + a * mw, y1 + dh * 0.15, x0 + b * mw, y1 + dh * 1.05), "mono", v, fit="h", align="c")

    def itf(self, code, box, bearer=1.2, label=True, v=255):
        """ITF のバーコード。box = 線の範囲 (mm)。上下にベアラーバー (太い枠の線)、数字は下 (label)"""
        x0, y0, x1, y1 = box
        els = _itf(code)
        unit = (x1 - x0) / sum(w for w, _ in els)
        x = x0
        for w, black in els:
            if black:
                self.rect(x, y0, x + w * unit + 0.02, y1, v=v)
            x += w * unit
        if bearer:
            self.rect(x0 - 4, y0 - bearer, x1 + 4, y0, v=v)
            self.rect(x0 - 4, y1, x1 + 4, y1 + bearer, v=v)
        if label:
            digits = f"{code[0:3]} {code[3:8]} {code[8:13]} {code[13]}"
            self.text(digits, (x0 + 4, y1 + bearer + 1.0, x1 - 4, y1 + bearer + 4.6), "mono", v, fit="h", align="c")


def _star(R, u, paper, ink, rot=3.0):
    """い・ろ・は・す の星 (RGBA の画像。中心が画像の真ん中)。R = 中心から先端まで (mm)。
    形は正三角形を2つ重ねた六芒星 (先端は rot 度から 60 度おき、くぼみは 0.577R)。中の濃淡が風車のように見える:
    中心からくぼみへ向かう「折り目」の線 (中心の近くほど時計回りにずれて曲がる) のすぐ反時計回りの側が濃い緑のべた、
    そこから反時計回りに離れるほど網点が薄くなり、次の折り目の手前で急にまた濃くなる。
    網点の濃さ (インクの面積の割合) で紙 (paper) とインク (ink) の色を混ぜる (写真を縮めて網点が溶けた色に合わせる)。右下の腕に水滴のきらめき"""
    n = int(math.ceil(2.1 * R * u))
    c = n / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) + 0.5
    X, Y = (xx - c) / (R * u), (c - yy) / (R * u)
    r = np.hypot(X, Y)
    inside = np.zeros(X.shape, bool)
    for off in (0, 60):
        m = np.full(X.shape, -9.0, np.float32)
        for j in range(3):
            a = math.radians(rot + off + 120 * j + 180)
            m = np.maximum(m, X * math.cos(a) + Y * math.sin(a))
        inside |= m <= 0.5
    th = np.degrees(np.arctan2(Y, X))
    fold = rot + 30 - 17 * np.clip(1 - r / 0.577, 0, 1)        # 折り目の角度 (くぼみの向き。中心の近くは時計回りへずれる)
    psi = np.mod(th - fold, 60)                                  # 折り目から反時計回りに測った角度 (0〜60)
    # 網点の濃さ (写真の濃淡を半径・角度ごとに測って合わせた): 折り目から psi0 度まではべた、その先は外ほど早く薄くなる (下限 floor)
    k = 0.012 + 0.008 * np.clip((r - 0.4) / 0.35, 0, 1)
    floor = 0.66 - 0.3 * np.clip((r - 0.15) / 0.3, 0, 1)
    psi0 = 12 - 6 * np.clip((r - 0.45) / 0.15, 0, 1)
    cov = np.clip(1 - k * np.maximum(psi - psi0, 0), floor, 1)
    cov = np.clip(cov + 0.4 * np.exp(-(r / 0.06) ** 2), 0, 1)   # 中心の点
    # 水滴: 網点を薄く (光って見える)、右下の縁が濃い。左上に白いきらめき
    a = math.radians(rot - 59)
    dx, dy = X - 0.5 * math.cos(a), Y - 0.5 * math.sin(a)
    dr = np.hypot(dx, dy) / 0.14
    drop = dr < 1
    rim = np.clip((dr - 0.75) / 0.25, 0, 1) * np.clip((dx - dy) / 0.14 + 0.3, 0, 1)
    cov = np.where(drop, 0.35 + 0.65 * rim + 0.25 * np.clip(-(dx + dy) / 0.14, 0, 1) * (1 - rim), cov)
    col = (np.array(paper, np.float32) * (1 - cov[..., None]) + np.array(ink, np.float32) * cov[..., None]) / 255
    sx, sy = dx + 0.045, dy - 0.04
    spark = np.clip(np.exp(-np.abs(sx * sy) / 0.0003) * np.clip(1 - np.hypot(sx, sy) / 0.1, 0, 1) * 1.5
                    + np.exp(-(np.hypot(sx, sy) / 0.03) ** 2), 0, 1)
    col = col * (1 - spark[..., None]) + spark[..., None]
    rgba = np.dstack([np.clip(col, 0, 1) * 255, inside * 255.0]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def _bottle_outline(x0, y0, w, h, lean=0.0):
    """ペットボトルの外形の点 (mm)。lean = 傾き (度、反時計回り)"""
    prof = [(0.33, 0.0), (0.33, 0.075), (0.30, 0.085), (0.30, 0.10), (0.34, 0.12), (0.34, 0.15), (0.20, 0.25), (0.08, 0.33),
            (0.06, 0.40), (0.08, 0.55), (0.12, 0.62), (0.10, 0.70), (0.06, 0.78), (0.05, 0.93), (0.10, 0.97), (0.16, 1.0)]
    right = [(1 - px, py) for px, py in reversed(prof)]
    pts = [(px, py) for px, py in prof] + right
    a = math.radians(lean)
    cx, cy = 0.5, 0.5
    out = []
    for px, py in pts:
        x, y = (px - cx) * w, (py - cy) * h
        out.append((x0 + w / 2 + x * math.cos(a) + y * math.sin(a), y0 + h / 2 - x * math.sin(a) + y * math.cos(a)))
    return out


def _smooth_curve(points, xs, sigma_mm=6.0):
    """測った点 [(x, y)] を通るなめらかな線の、xs での y"""
    px, py = zip(*points)
    ys = np.interp(xs, px, py)
    step = xs[1] - xs[0]
    return gaussian_filter1d(ys, sigma_mm / step, mode="nearest")


def _wear(base, rect, ppm, seed):
    """面の縁を少し暗く (角がこすれて汚れた感じ)"""
    x0, y0, x1, y1 = rect
    h, w = y1 - y0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / ppm   # 縁からの距離 (mm)
    rng = np.random.default_rng(seed)
    low = np.asarray(Image.fromarray(rng.standard_normal((h // 40 + 2, w // 40 + 2)).astype(np.float32)).resize((w, h), Image.BICUBIC))
    dark = 0.07 * np.exp(-edge / 2.5) * np.clip(0.8 + 0.6 * low, 0.2, 1.6)
    base[y0:y1, x0:x1] *= (1 - dark)[..., None]


# ---------------------------------------------------------------- い・ろ・は・す 天然水 ラベルレス 560ml×24本
W_KRAFT = (206, 173, 121)      # 段ボールの地 (写真の色 (218,185,130) を少し暗くした反射率)
W_CREAM = (241, 234, 223)      # クリームの帯
W_MINT = (164, 198, 175)       # ミントの波 (網点の平均)
W_BLACK = (30, 26, 23)
W_GREEN = (10, 104, 55)        # 字・ボトルの絵の緑
STAR_INK = (3, 116, 59)       # 星の濃い緑 (べたの所。薄い所は網点なので紙の色と混ぜる)
WATER_JAN = gtin("490210213941")         # 4902102139410 (ボトルの JAN)
WATER_ITF = gtin("0490210213941")        # 04902102139410 (ケースの ITF。写真の 049 02102 13941 …)
# 正面のクリームの帯の上下の縁 (写真から測った高さ。mm)。上の縁は波打ち、ミントの帯の上の縁は右へ少しずつ下がる
_CREAM_TOP = [(0, 89), (15, 88.5), (30, 88), (45, 86), (60, 84), (75, 83), (90, 82.5), (105, 83), (120, 84), (135, 85.5), (150, 88.5),
              (165, 90), (180, 92), (200, 93), (220, 91.5), (240, 88.5), (260, 86.5), (280, 86.5), (300, 87.5), (320, 90), (340, 93),
              (360, 95.5), (380, 96.5), (400, 96), (417, 95)]
_CREAM_BOT = [(0, 214), (15, 213), (30, 212), (45, 210), (60, 208), (75, 207), (90, 206.5), (105, 207), (120, 208.5), (135, 211.5),
              (150, 213.5), (165, 214.5), (180, 215.5), (200, 214), (220, 212), (240, 210), (260, 208), (280, 208), (300, 209),
              (320, 211.5), (340, 215), (360, 216), (380, 216), (400, 215.5), (417, 215)]


def _water_info(p, x, y, s=1.0, name=False):
    """左上の表示 (黒): 560ml×24 / 下線 / ペットボトル / ケース販売専用 (黒地に抜き) / ラベルレス。
    (x, y) = 下線の左端・560ml の上端の所、s = 正面に対する大きさ (写真を正面から見た形に直して測った)。name = ラベルレス を描かない (上面)"""
    def b(x0, y0, x1, y1):
        return x + x0 * s, y + y0 * s, x + x1 * s, y + y1 * s
    p.text("560ml×24", b(11.4, 0.1, 73.8, 11.7), weight=800)
    p.rect(*b(0.2, 13.9, 84.6, 14.9))
    p.text("ペットボトル", b(11.0, 16.1, 74.4, 27.7), weight=800)
    p.rect(*b(-0.2, 29.9, 84.6, 46.5), r=2.0 * s)
    p.text("ケース販売専用", b(5.5, 32.6, 78.9, 43.8), weight=700, v=0)
    if not name:
        p.text("ラベルレス", b(5.8, 48.5, 78.4, 60.5), weight=800)


def _water_badge(p, f, x, y, s=1.0):
    """「ラベルレス ボトル」の札 (斜めの枠2つと、きらめきの線) と「リサイクル しやすい」。(x, y) = ラベルレスの枠の中心"""
    a = math.radians(7)

    def tag(cx, cy, w, h, text, fill):
        pts = [(cx + px * math.cos(a) + py * math.sin(a), cy - px * math.sin(a) + py * math.cos(a))
               for px, py in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        if fill:
            p.poly(pts, v=0)
        p.line(pts + pts[:1], 0.7 * s)
        p.text(text, (cx - w / 2 + 2 * s, cy - h / 2 + 1.6 * s, cx + w / 2 - 2 * s, cy + h / 2 - 1.6 * s), weight=700, rot=7)

    tag(x, y, 31 * s, 8.5 * s, "ラベルレス", True)
    tag(x + 29 * s, y - 3.6 * s, 25 * s, 8 * s, "ボトル", False)
    cx, cy = x + 15 * s, y - 9.5 * s
    for k in range(5):   # きらめきの線
        t = math.radians(45 + k * 22.5)
        p.line([(cx + 2.5 * s * math.cos(t), cy - 2.5 * s * math.sin(t)), (cx + 5 * s * math.cos(t), cy - 5 * s * math.sin(t))], 0.8 * s)
    p.text("リサイクル", (x + 4 * s, y + 15.5 * s, x + 42 * s, y + 23.5 * s), weight=700)
    p.text("しやすい", (x + 6 * s, y + 25 * s, x + 39 * s, y + 33 * s), weight=700)


def _water_brand(f, p_black, p_green, x, y, s):
    """星の右の い・ろ・は・す (筆の字・丸い点・®) と 日本の天然水 / NATURAL MINERAL WATER。(x, y) = 正面での い の左上 (140.6, 116) に当たる所"""
    def X(v):
        return x + (v - 140.6) * s

    def Y(v):
        return y + (v - 116) * s
    p_black.glyph_row("いろはす", [(X(140.6), X(172.6)), (X(184.5), X(214.9)), (X(226.9), X(260.4)), (X(269.2), X(302.8))],
                      Y(116), "brush", stroke=0.045)
    for cx, d in ((179.3, 5.4), (221.0, 5.4), (266.0, 4.9)):
        p_black.ellipse(X(cx), Y(133.8), d * s / 2)
    p_black.ellipse(X(307.6), Y(143.2), 2.7 * s, line=0.45 * s)
    p_black.text("R", (X(306.4), Y(141.6), X(308.9), Y(144.9)), "geo")
    p_green.text("日本の天然水", (X(169.4), Y(156), X(273.2), Y(173.1)), weight=500)
    p_green.text("NATURAL MINERAL WATER", (X(143.8), Y(178.7), X(293.2), Y(185.9)), "geo", spacing=0.16)


def water_front(f):
    xs = np.arange(0, 417.5, 0.5)
    top, bot = _smooth_curve(_CREAM_TOP, xs), _smooth_curve(_CREAM_BOT, xs)
    with f.plate(W_MINT) as p:   # ミントの波の帯 (クリームの帯の外に見える所だけが残る)
        p.poly([(8, 77.0 + 0.0194 * 8), (409, 77.0 + 0.0194 * 409), (409, 218.7), (8, 218.7)])
        p.rect(308, 173, 400, 214, v=0)    # ITF の枠の中はクラフト紙のまま
    with f.plate(W_CREAM) as p:
        sel = (xs >= 8) & (xs <= 409)
        p.poly(list(zip(xs[sel], top[sel])) + list(zip(xs[sel][::-1], bot[sel][::-1])))
        p.rect(308, 173, 400, 214, v=0)    # ITF の枠の中はクラフト紙のまま
    f.paste(_star(52.7, f.u, W_CREAM, STAR_INK), (round((81.5 - 52.7 * 1.05) * f.u), round((147.9 - 52.7 * 1.05) * f.u)))
    with f.plate(W_GREEN) as g:
        g.poly(_bottle_outline(329.1, 107.7, 21.6, 55.0, lean=5))
        _water_badge(g, f, 351, 129.5)
        with f.plate(W_BLACK) as k:
            _water_brand(f, k, g, 140.6, 116, 1.0)
            _water_info(k, 11.2, 13.7)
            # 右上: JAN と、品番の枠
            k.rect(335, 22, 405, 48.5, line=0.7)
            k.ean13(WATER_JAN, (340.5, 24.2, 399.5, 41.0))
            k.rect(335, 51, 405, 70, line=0.7)
            k.text("製品コード", (337, 52.4, 352, 55.2), weight=600)
            k.text("000000", (339, 56.5, 401, 68), "round", spacing=0.1)
            # 右下: ITF (太い黒枠の中、数字は区切りの線の下)
            k.rect(308, 173, 400, 214, line=1.8)
            k.itf(WATER_ITF, (313, 176.5, 395, 199.5), bearer=0.0, label=False)
            k.rect(308, 200.6, 400, 202.3)
            k.text("049 02102 13941 0", (318, 205.0, 390, 209.8), "mono", fit="h")


def water_side(f):
    """側面 (左右とも。写真を正面から見た形に直して測った): 上はクラフト紙に表示・注意書き・手を掛ける穴の切り込み・ITF・品番・カッター注意、
    黒い帯「お店で開封しないでください。」、開け口の切り込みの線、下にクリームの帯 (星・い・ろ・は・す・ボトルの札)、右寄りに薄いミントのボトルの写真"""
    with f.plate(W_MINT) as p:                     # ボトルの写真 (左上の角は肩の丸み)。カッター注意の枠の所はクラフト紙のまま
        p.poly([(211.8, 218.5), (211.8, 78)] + [(225.8 - 14 * math.cos(t), 77.2 - 14 * math.sin(t)) for t in np.linspace(0, math.pi / 2, 10)]
               + [(267, 63.2), (267, 218.5)])
        p.rect(236.6, 36, 268, 73.6, v=0)
    with f.plate((204, 222, 204)) as p:            # 写真の明るい所 (ボトルの左の光と、肩)
        p.rect(214, 82, 233, 216, r=6)
        p.rect(226, 66, 236, 90, r=4)
    with f.plate((224, 232, 214)) as p:
        p.rect(217, 92, 227, 212, r=4)
    with f.plate((214, 228, 210)) as p:            # ボトルの浮き彫りの星と ILOHAS の字
        p.text("ILOHAS", (240, 120, 248, 203), "geo", turn=270, spacing=0.35)
        for k in range(6):
            t = math.radians(90 + 60 * k)
            p.line([(250, 96), (250 + 9 * math.cos(t), 96 - 9 * math.sin(t))], 1.2)
    with f.plate(W_CREAM) as p:
        p.rect(7.2, 140, 210.6, 219.2)
    f.paste(_star(20.3, f.u, W_CREAM, STAR_INK), (round((37.9 - 20.3 * 1.05) * f.u), round((180 - 20.3 * 1.05) * f.u)))
    with f.plate((158, 124, 84)) as p:             # 開け口の切り込みの線 (段ボールの切れ目)
        def rounded(pts, r=5):
            out = [pts[0]]
            for (ax, ay), (bx, by), (cx, cy) in zip(pts, pts[1:], pts[2:]):
                for t in np.linspace(0, 1, 7):     # 角を丸める (2次のベジェ)
                    px, py = bx + (ax - bx) * r / math.dist((ax, ay), (bx, by)), by + (ay - by) * r / math.dist((ax, ay), (bx, by))
                    qx, qy = bx + (cx - bx) * r / math.dist((cx, cy), (bx, by)), by + (cy - by) * r / math.dist((cx, cy), (bx, by))
                    out.append(((1 - t) ** 2 * px + 2 * (1 - t) * t * bx + t * t * qx, (1 - t) ** 2 * py + 2 * (1 - t) * t * by + t * t * qy))
            return out + [pts[-1]]
        p.line(rounded([(0, 114.7), (103, 114.7), (103, 137.3), (209, 137.3)]), 0.5)
        p.line(rounded([(106, 137.3), (106, 115.5), (172, 115.5), (172, 137.3)]), 0.5)
    with f.plate(W_GREEN) as g:
        g.poly(_bottle_outline(152, 155, 17.2, 50.4, lean=4))
        _water_badge(g, f, 172.5, 180, 0.62)
        g.text("日本の天然水", (75.0, 186.8, 125.8, 194.8), weight=500)
        with f.plate(W_BLACK) as k:
            k.glyph_row("いろはす", [(61.3 + (a - 140.6) * 0.49, 61.3 + (b - 140.6) * 0.49) for a, b in
                                    ((140.6, 172.6), (184.5, 214.9), (226.9, 260.4), (269.2, 302.8))], 165.8, "brush", stroke=0.045)
            for cx, d in ((179.3, 5.4), (221.0, 5.4), (266.0, 4.9)):
                k.ellipse(61.3 + (cx - 140.6) * 0.49, 165.8 + (133.8 - 116) * 0.49, d * 0.49 / 2)
            k.ellipse(61.3 + (307.6 - 140.6) * 0.49, 165.8 + (143.2 - 116) * 0.49, 1.35, line=0.25)
            _water_info(k, 7.4, 6.9, 0.97)
            k.lines(["●このケースには、ラベルのないペットボトル製品が入っています。ケースのままお買い求めください。持ち運びの際は手かけ穴をご利用ください。",
                     "●落としたり、強い衝撃を与えたりしないでください。直射日光・高温多湿をさけ、においの強い所に置かないでください。",
                     "●凍らせないでください。開栓後はすぐにお飲みください。"], 7.6, 73.2, 205, 5.1, 3.4, weight=500)
            # 手を掛ける穴: 押して開ける所の切り込み (点線) と、内側に折る線 (下の辺)
            k.dashed(rounded([(102.4, 49.5), (102.4, 36.5), (128, 21.5), (160, 21.5), (175, 38), (175, 49.5)], 4), 0.55, dash=1.6, gap=1.2)
            k.line([(102.4, 49.8), (175, 49.8)], 0.45)
            # ITF (右の黒い帯に ITF の字を抜く)・品番・カッター注意
            k.rect(201, 9.8, 264.8, 36.4, line=2.2)
            k.rect(256, 9.8, 264.8, 36.4)
            k.text("ITF", (258.3, 15, 262.5, 32.5), "geo", turn=270, v=0)
            k.itf(WATER_ITF, (205, 13.2, 252.5, 26.2), bearer=0.0, label=False)
            k.rect(201, 26.6, 256, 28.4)
            k.text("049 02102 13941 0", (209, 29.4, 248, 32.6), "mono", fit="h")
            k.rect(200.8, 38, 236.2, 61, line=0.9)
            k.text("品番コード", (207.5, 40.8, 229.5, 44.0), weight=600)
            k.text("000000", (204, 46.2, 233, 58), "round", spacing=0.08)
            k.rect(238, 38.6, 264.6, 72, line=0.9)
            k.rect(238, 63.6, 264.6, 64.4)
            k.line([(242.5, 42.5), (260.5, 60.5)], 1.6)
            k.line([(261, 43), (252.5, 52)], 0.9)
            k.line([(250, 54.5), (243, 61.5)], 0.9)
            k.text("カッター注意", (240, 65.6, 262.6, 70.2), weight=600)
            # 黒い帯「お店で開封しないでください。」
            k.rect(0, 94.2, 209.6, 111.2)
            k.text("お店で開封しないでください。", (30, 97.0, 188, 108.4), weight=800, v=0)
            # 賞味期限 (インクジェットの点の字)
            k.text("賞味期限", (120, 58, 140, 62), weight=500)
            k.text("27.04.14 HS", (120, 63, 170, 68.5), "mono", fit="h", align="l")


def water_top(f):
    """上面 (画像の上 = 箱の奥)。奥のふたにクリームの帯 (星と字・ボトルの札)・Ⓗ・リサイクルの印、手前のふたに黒い帯と表示、真ん中にふたの合わせ目"""
    with f.plate(W_CREAM) as p:
        p.rect(92, 22, 335, 96)
    f.paste(_star(21, f.u, W_CREAM, STAR_INK), (round((122 - 21 * 1.05) * f.u), round((59 - 21 * 1.05) * f.u)))
    with f.plate(W_GREEN) as g:
        g.poly(_bottle_outline(258, 36, 13.5, 36, lean=5))
        _water_badge(g, f, 279, 50, 0.7)
        with f.plate(W_BLACK) as k:
            _water_brand(f, k, g, 148, 44, 0.48)
            k.ellipse(352, 58, 7, line=0.9)                    # Ⓗ
            k.text("H", (348.5, 53.5, 355.5, 62.5), "geo")
            for j in range(3):                                 # 段ボールのリサイクルの印 (矢印3つの輪)
                t0 = math.radians(90 + 120 * j)
                arc = [(395 + 7 * math.cos(t0 - t), 58 - 7 * math.sin(t0 - t)) for t in np.linspace(0.25, 1.75, 12)]
                k.line(arc, 1.1)
                ex, ey = arc[-1]
                tt = t0 - 1.75
                k.poly([(ex + 2.2 * math.cos(tt), ey - 2.2 * math.sin(tt)), (ex - 2.2 * math.cos(tt), ey + 2.2 * math.sin(tt)),
                        (ex + 2.4 * math.sin(tt), ey + 2.4 * math.cos(tt))])
            k.text("ダンボール", (384, 67.5, 406, 71.5), weight=600)
            k.rect(2, 112, 92, 132, line=0.5)
            k.lines(["■いろはすの保管場所にご注意ください。", "においの強い所に置くと、においが移ることがあります。"], 4, 115, 90, 5, 3, weight=500)
            k.line([(0, 138), (417, 138)], 0.5)                # ふたの合わせ目
            # 手前のふた
            k.rect(24, 150, 282, 170)
            k.text("お店で開封しないでください。", (40, 153, 266, 167), weight=800, v=0)
            k.rect(290, 148, 410, 157.5)
            k.text("■ケース内のペットボトル製品にはラベルがありません", (292, 149.6, 408, 155.8), weight=600, v=0)
            k.lines(["お店での販売、店頭での陳列はできません。", "ケースのままお買い求めください。"], 292, 160, 405, 4.4, 3, weight=500)
            k.text("い・ろ・は・す 天然水", (34, 176, 104, 186), weight=800)
            _water_info(k, 30, 186, 0.82, name=True)
            for j, x in enumerate((120, 152, 184)):           # 取り扱いの印 (手かぎ無用・水ぬれ注意・天地無用)
                k.rect(x, 176, x + 30, 196, line=0.6)
                if j == 0:
                    k.line([(x + 9, 180), (x + 21, 192)], 1.0)
                    k.line([(x + 21, 180), (x + 9, 192)], 1.0)
                elif j == 1:
                    k.poly([(x + 6, 187), (x + 15, 179), (x + 24, 187)])
                    k.line([(x + 15, 187), (x + 15, 193), (x + 13, 193)], 0.9)
                else:
                    for dx in (10, 20):
                        k.poly([(x + dx - 3.5, 185), (x + dx, 179), (x + dx + 3.5, 185)])
                        k.line([(x + dx, 184), (x + dx, 192)], 1.2)
            k.lines(["手かぎ無用", "水ぬれ注意", "天地無用"], 121, 199, 150, 4.2, 3, weight=600)
            legal = ["●品名 ナチュラルミネラルウォーター ●原材料名 水(鉱水) ●内容量 560ml×24",
                     "●賞味期限 側面に記載 ●保存方法 高温・直射日光をさけてください",
                     "●採水地 山梨県北杜市白州町 ●販売者 コカ・コーラ カスタマーマーケティング(株)",
                     "東京都港区六本木6-2-31 ●製造所 コカ・コーラ ボトラーズジャパン(株) 白州工場",
                     "■栄養成分表示(100ml当たり) エネルギー0kcal, たんぱく質0g, 脂質0g,",
                     "炭水化物0g, 食塩相当量0.003g, カルシウム0.72mg, マグネシウム0.23mg 硬度27"]
            k.lines(legal, 222, 174, 410, 6.2, 3.4, weight=500)


def make_water():
    name = "box_water"
    e, atlas = FURNITURE[name], box_atlas(name)
    W, D, H = e["w"] * 1000, e["d"] * 1000, e["h"] * 1000
    base = _paper(*BOX_IMAGE, W_KRAFT, 211, grain=0.035, mottle=0.03, flute=0.010, ppm=BOX_PPM)
    for part, (w, h), draw in (("front", (W, H), water_front), ("right", (D, H), water_side), ("top", (W, D), water_top)):
        f = Face(w, h)
        draw(f)
        _apply_ink(base, f.img, atlas[part], opacity=0.94)
    for k, part in enumerate(("front", "right", "top", "plain")):
        _wear(base, atlas[part], BOX_PPM, 300 + k)
    save(Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)), "box_water.jpg", quality=90)


# ---------------------------------------------------------------- 伊藤園 お～いお茶 緑茶 ラベルレス 460ml×30本
T_KRAFT = (209, 187, 160)      # 段ボールの地 (写真の色 (220,196,168) を少し暗くした反射率。黄緑の地の抜きもこの色)
T_LIGHT = (98, 162, 46)        # 黄緑の地
T_DARK = (14, 99, 52)          # 濃い緑
TEA_JAN = gtin("490108564069")       # 4901085640692
TEA_ITF = gtin("0490108564069")      # 04901085640692 (ケースの ITF。写真の 049 01085 … と同じ並び)


def _ito_mark(p, cx, cy, s=1.0):
    """伊藤園の印 (4枚の葉 (楕円) を十字に、間を X 字に空けて並べる)。(cx, cy) = 中心、幅は約 21.6mm x s"""
    for (dx, dy, a, b, ang) in ((1.6, -4.8, 4.0, 3.0, -15), (-6.5, -0.9, 4.4, 2.8, 5), (5.9, -1.0, 4.8, 3.1, -8), (-1.7, 4.1, 4.6, 3.6, -35)):
        p.ellipse(cx + dx * s, cy + dy * s, a * s, b * s, angle=ang)


def _oi_logo(p, x, y, s=1.0):
    """お～いお茶 の筆の字のロゴ (縦に並べる)。字ごとの外接の箱は写真を正面から見た形に直して測った。
    (x, y) = ロゴの左上 (正面の 140, 84.2 に当たる所)、s = 大きさ"""
    def pt(px, py):
        return x + (px - 140) * s, y + (py - 84.2) * s

    def b(x0, y0, x1, y1):
        return (*pt(x0, y0), *pt(x1, y1))
    p.text("お", b(167.8, 84.2, 201.8, 116.6), "gyosho", stroke=0.008)
    p.text("い", b(176.2, 138.4, 192.2, 148.8), "gyosho", stroke=0.008)
    p.text("お", b(140.0, 112.8, 173.2, 155.6), "gyosho", stroke=0.012)
    p.text("茶", b(147.6, 157.4, 193.2, 209.4), "gyosho", stroke=0.012)
    # ～ は縦の波線 (書体の〜は平らすぎるので線で描く)。筆の入りを太く
    wave = [pt(182.8 + 1.4 * math.sin(t * 2.4 * math.pi + 0.5), 120.0 + 15.6 * t) for t in np.linspace(0, 1, 24)]
    p.line(wave, 1.1 * s)
    p.ellipse(*wave[0], 0.9 * s)


def _eco_badge(f, cx, cy, s=1.0):
    """Eco&Happy の丸い印 (地の色の丸に濃い緑の輪・弧に沿った Eco&Happy・エコハピ・手書きの ラベルレス・黄緑のボトルの線)。
    (cx, cy) = 中心、大きさは写真を正面から見た形に直して測った (輪の半径 29.4mm x s)。地の色の丸は呼ぶ側で抜いておく"""
    with f.plate(T_LIGHT) as p:
        p.line(_bottle_outline(cx - 5.3 * s, cy - 13.8 * s, 10.3 * s, 38 * s), 0.7 * s)
    with f.plate(T_DARK) as p:
        p.ellipse(cx, cy, 29.4 * s, line=1.8 * s)
        p.arc_text("Eco&Happy", cx, cy, 24.0 * s, 4.8 * s, "round", 139, 42)
        p.text("エコハピ", (cx - 9.6 * s, cy - 16.6 * s, cx + 11.4 * s, cy - 13.4 * s), weight=700)
        p.text("ラベルレス", (cx - 26.6 * s, cy - 4.4 * s, cx + 26.6 * s, cy + 5.4 * s), "hand")


def tea_front(f):
    """正面 (= 背面)。位置は写真を正面から見た形に直して測った (瓶に隠れた右の端は、同じ型のラベル付きの箱の写真に合わせた)"""
    with f.plate(T_LIGHT) as p:
        p.rect(0, 30.6, 373, 220)
        p.rect(16.4, 54.6, 196.4, 77.6, v=0)                  # Smart Bottle BOX の帯 (抜き)
        p.rect(16.2, 88.0, 131.2, 205.6, v=0)                 # 濃い緑の四角 (この上に塗る)
        p.ellipse(244.6, 111.8, 33.0, v=0)                    # Eco&Happy の丸
        p.rect(285, 39.2, 347, 68.4, r=3, v=0)                # A/B の品番の枠
        p.rect(285, 122, 351, 160, r=3, v=0)                  # バーコードの枠 (JAN の上の段と ITF の下の段)
        p.rect(242.6, 156.4, 351, 208.8, r=3, v=0)
    _eco_badge(f, 244.6, 111.8)
    with f.plate(T_DARK) as p:
        _ito_mark(p, 27.2, 42.4)
        p.text("伊藤園", (41.0, 36.0, 87.0, 49.2), "mincho", stroke=0.02)
        p.text("PET", (95.8, 34.4, 121.6, 45.0), weight=800)
        p.text("460ml", (122.4, 34.2, 183.2, 51.0), weight=800)
        p.text("×", (187.8, 38.2, 198.8, 49.4), weight=700)
        p.text("30本", (202.8, 34.4, 243.2, 51.0), weight=800)
        p.text("横積禁止", (255.6, 34.0, 277.2, 38.2), weight=700)
        p.rect(252.4, 39.2, 280.4, 68.4, line=1.1)            # 天地無用の矢印
        for x in (261.9, 271.0):
            p.poly([(x - 3.8, 49.4), (x, 42.4), (x + 3.8, 49.4)])
            p.rect(x - 1.8, 49, x + 1.8, 61.4)
        p.rect(257.4, 63.4, 276.0, 65.4)
        p.rect(285, 39.2, 347, 68.4, r=3, line=1.0)           # A/B の品番
        p.rect(285, 53.3, 347, 54.3)
        p.text("A:64069", (289, 41.8, 343, 51.3), weight=700)
        p.text("B:64069", (289, 56.3, 343, 65.8), weight=700)
        p.text("Smart Bottle BOX", (19.8, 57.9, 193.4, 74.5), "round")
        p.rect(16.2, 88.0, 131.2, 205.6)                      # 濃い緑の四角と、抜いた字
        p.text("ラベルレス", (23.8, 101.2, 123.2, 120.4), weight=800, v=0)
        p.text("30本", (25.8, 127.4, 121.0, 169.2), weight=800, v=0)
        p.text("入り", (56.0, 177.0, 90.2, 195.8), weight=800, v=0)
        _oi_logo(p, 140.0, 84.2)
        # バーコード: 上の段 = JAN (ケースJANコード)、下の段 = ITF (ITFコード)、その下に「ケースのまま保管してください」
        p.ean13(TEA_JAN, (292, 125.5, 336, 146.5))
        p.text("ケースJANコード", (338.8, 124.5, 342.8, 153), weight=600, vertical=True)
        p.itf(TEA_ITF, (253, 164.8, 333, 184.4), bearer=3.3, label=False)
        p.text("049 01085 64069 2", (262, 188.4, 324, 192.0), "mono", fit="h")
        p.text("ITFコード", (338.8, 161, 342.8, 188), weight=600, vertical=True)
        p.rect(247.6, 195.8, 346, 205.8, r=1.5)
        p.text("ケースのまま保管してください", (251.5, 197.4, 342, 204.2), weight=700, v=0)


def tea_side(f):
    """側面 (左右とも): 上はクラフト紙に緑の表示 (原材料などの枠・品名)、下は黄緑の地に Eco&Happy・ロゴ・バーコード、一番下に濃い緑の帯"""
    tab = [(0, 79), (150, 79), (156, 103), (309, 103), (309, 220), (0, 220)]   # 黄緑の地の上の縁 (開け口の切り込みに沿う段)
    with f.plate(T_LIGHT) as p:
        p.poly(tab)
        p.ellipse(42, 140, 26, v=0)
        p.rect(206, 112, 298, 184, r=3, v=0)
    _eco_badge(f, 42, 140, 0.8)
    with f.plate((150, 120, 84)) as p:                      # 開け口の切り込みの線 (段ボールの切れ目の茶色)
        p.line([(0, 79.5), (150, 79.5), (156, 103.5), (309, 103.5)], 0.6)
    with f.plate(T_DARK) as p:
        p.rect(8, 8, 96, 72, line=0.6)                        # 原材料などの表示の枠
        p.lines(["●名称 緑茶(清涼飲料水)", "●原材料名 緑茶(国産)、ビタミンC", "●内容量 460ml", "●賞味期限 上部に記載",
                 "●保存方法 高温・直射日光をさけてください", "●販売者 株式会社伊藤園", "東京都渋谷区本町3-47-10"],
                11, 12, 93, 8.2, 4.4, weight=600)
        p.rect(118, 48, 206, 58)
        p.text("ケースのまま保管してください", (121, 49.5, 203, 56.5), weight=700, v=0)
        p.lines(["●ケースを開けるときは、カッターでボトルを", "傷つけないようにご注意ください。"], 118, 61, 206, 5.4, 3.6, weight=600)
        p.text("PET460ml×30本", (252, 22, 262, 92), weight=800, vertical=True)
        p.rect(268, 26, 292, 52, line=1.0)
        for x in (276, 284):
            p.poly([(x - 3, 35), (x, 30), (x + 3, 35)])
            p.rect(x - 0.8, 34.5, x + 0.8, 45)
        _oi_logo(p, 76, 116, 0.5)
        p.ean13(TEA_JAN, (214, 116, 254, 140))
        p.itf(TEA_ITF, (214, 152, 290, 172), bearer=1.0)
        p.rect(0, 188, 309, 220)                              # 一番下の濃い緑の帯と「ラベルレス30本入り」
        p.text("ラベルレス30本入り", (60, 193, 249, 214), weight=800, v=0)


def tea_top(f):
    """上面 (画像の上 = 箱の奥)。奥のふたに横に寝かせたボトルの線画とロゴ、手前のふたに逆さの表示 (奥から読む向き)"""
    with f.plate(T_DARK) as p:
        p.line([(0, 154.5), (373, 154.5)], 0.5)                 # ふたの合わせ目
        bottle = [(34, 22), (52, 16), (66, 14), (300, 14), (318, 20), (330, 24), (342, 24), (342, 36), (330, 36), (318, 40),
                  (300, 46), (66, 46), (52, 44), (34, 38), (34, 22)]
        p.line(bottle, 1.0)                                      # 寝かせたボトルの線画
        for x in (112, 186):
            p.line([(x, 14), (x, 46)], 0.7)
        p.rect(198, 18, 262, 42, r=11, line=1.0)
        p.text("お～いお茶", (206, 23, 254, 37), "gyosho", stroke=0.04)
        p.ellipse(310, 84, 18, line=1.2)
        p.text("Eco&Happy", (296, 76, 324, 82), "round")
        p.text("ラベルレス", (295, 85, 325, 92), "hand")
        # 手前のふた: 奥から読む向き (180 度回した字)
        p.text("460ml", (40, 186, 120, 222), weight=800, turn=180)
        p.text("PET", (122, 206, 146, 220), weight=800, turn=180)
        for i, row in enumerate(["お～いお茶 緑茶 ラベルレス", "スマートボトル 30本入り", "伊藤園"]):
            p.text(row, (160, 240 - i * 12, 260, 248 - i * 12), weight=700, turn=180, fit="h", align="r")
        p.rect(270, 180, 350, 230, line=0.7)
        p.text("賞味期限", (300, 222, 320, 227), weight=600, turn=180)
        p.text("2027.04.08 L3", (276, 196, 344, 204), "mono", turn=180, fit="h")


def make_tea():
    name = "box_tea"
    e, atlas = FURNITURE[name], box_atlas(name)
    W, D, H = e["w"] * 1000, e["d"] * 1000, e["h"] * 1000
    base = _paper(*BOX_IMAGE, T_KRAFT, 212, grain=0.03, mottle=0.025, flute=0.008, ppm=BOX_PPM)
    for part, (w, h), draw in (("front", (W, H), tea_front), ("right", (D, H), tea_side), ("top", (W, D), tea_top)):
        f = Face(w, h)
        draw(f)
        _apply_ink(base, f.img, atlas[part], opacity=0.95)
    for k, part in enumerate(("front", "right", "top", "plain")):
        _wear(base, atlas[part], BOX_PPM, 310 + k)
    save(Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)), "box_tea.jpg", quality=90)


if __name__ == "__main__":
    assert gtin("490108564106") == "4901085641064"   # 写真の 濃い茶 のケースの JAN と同じになる
    make_water()
    make_tea()
