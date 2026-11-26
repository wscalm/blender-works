"""デスク2の上の小物の画像を textures/ に描く (python3 tools/make_desk_items.py)。どれもユーザーが商品を指定した物:

  book_physics1.jpg / book_physics2.jpg   文庫本「物理さんで無双してたらモテモテになりました (1)・(2)」(モンスター文庫) の表紙・裏表紙・背・小口。
                                          表紙は reference/books/physics_vol*.jpg (BOOK☆WALKER の表紙の画像) をそのまま貼る。裏表紙と背は表紙の色で描く。
                                          面の並びは scripts/layout.py の book_atlas
  coaster_top.jpg       セリアのラバーウッドコースター (角) の上面: 白っぽいラバーウッドの木目と、こげ茶の「ORIGINAL / TASTE」の字
  penstand_band.jpg     ダイソーのペンスタンドの、編んだ帯の表面 (灰色の PP の組みひも。帯に沿った畝と細かい綾。1枚 = BAND_MM。
                        色は商品名のチャコールグレーより明るい灰色 (2026-10-27 ユーザー指定「もう少し明るいグレー」))
  keyboard_legends.png  Logicool G813 のキーの字 (光る。キーボードの上面全体を描く。キーの位置は scripts/keyboard_spec.py)。
                        色は公式の写真の「虹色が左から右へ流れる」光り方を止めた物 (左の G キーが青 → 紫 → 赤 → 黄 → 右のテンキーが水色)
  keyboard_brushed.jpg  G813 の上面のアルミの板 (濃い灰色のヘアライン。筋は画像の縦 = キーボードの左右)
  mouse_g604_top.png    Logicool G604 の上から見た面 (つなぎ目の線・手のひらの点々・G のロゴ・ホイールの横の三角)。マウスの外形の枠 (80 x 130mm) 全体を描く
  paper_trash.jpg       新聞紙やチラシを折った卓上のゴミ箱 (2026-10-27): 机の上の新聞紙のゴミ箱の壁の外・内・底と、畳んだゴミ箱 (新聞紙・スーパーのチラシ・
                        住宅のチラシ) の表と縁。面の並びは scripts/layout.py の trash_atlas。新聞とチラシの文・店・会社は架空
  shade_ramp.png        明るさの段階 (横の位置 u = リニアの明るさ 0〜1)。綿棒のように細くて焼き付けの島が作れない物の面ごとの陰を、UV の u で付ける
乱数の種は固定なので、毎回同じ画像になる。
"""
import colorsys
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import keyboard_spec as KB
from layout import BOOK_PPM, FURNITURE, TRASH_PAPERS, TRASH_PPM, book_atlas, trash_atlas

TEX = os.path.join(HERE, "..", "textures")
REF = os.path.join(HERE, "..", "reference", "books")
FONTS = "/mnt/c/Windows/Fonts"


def font(name, size, variation=None, index=0):
    f = ImageFont.truetype(os.path.join(FONTS, name), max(1, round(size)), index=index)
    if variation:
        f.set_variation_by_name(variation)
    return f


def noise(size, sigma, seed, scale=(1.0, 1.0)):
    """なめらかなむら (平均 0・標準偏差およそ 1)。scale = ぼかしの幅 (横, 縦) 画素"""
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((size[1], size[0])).astype(np.float32)
    img = Image.fromarray(((n * 32) + 128).clip(0, 255).astype(np.uint8))
    if scale != (1.0, 1.0):   # 横と縦で違う幅でぼかす (縮めてから戻す)
        small = img.resize((max(1, round(size[0] / scale[0])), max(1, round(size[1] / scale[1]))), Image.BILINEAR)
        img = small.resize(size, Image.BICUBIC)
    a = np.asarray(img, dtype=np.float32) - 128
    return a / max(a.std(), 1e-3) * sigma


def save(img, name, quality=90):
    path = os.path.join(TEX, name)
    if name.endswith(".png"):
        img.save(path, optimize=True)
    else:
        img.convert("RGB").save(path, quality=quality)
    print(f"{name}: {img.size[0]}x{img.size[1]}  {os.path.getsize(path) / 1024:.0f} KB")


# ---------------------------------------------------------------- 文庫本
BOOKS = {   # 名前: (表紙の画像, 表紙の地の色, 背の字の色, 巻)
    "book1": ("physics_vol1.jpg", (243, 168, 196), (40, 34, 40), 1),
    "book2": ("physics_vol2.jpg", (247, 190, 110), (40, 34, 40), 2),
}
TITLE = "物理さんで無双してたらモテモテになりました"


def _vertical(d, cx, y, s, f, fill, step):
    """縦書き (1字ずつ下へ)"""
    for ch in s:
        d.text((cx, y), ch, font=f, fill=fill, anchor="mt")
        y += step
    return y


def make_book(name):
    cover_file, base, ink, vol = BOOKS[name]
    rects, size = book_atlas(name)
    img = Image.new("RGB", size, base)
    # 表紙
    x0, y0, x1, y1 = rects["top"]
    cover = Image.open(os.path.join(REF, cover_file)).convert("RGB").resize((x1 - x0, y1 - y0), Image.LANCZOS)
    img.paste(cover, (x0, y0))
    d = ImageDraw.Draw(img)
    # 裏表紙 (机に伏せてあるので見えない): 表紙の地の色に、あらすじの白い枠と灰色の行・バーコード
    x0, y0, x1, y1 = rects["bottom"]
    k = BOOK_PPM
    d.rectangle([x0 + 10 * k, y0 + 18 * k, x1 - 10 * k, y0 + 88 * k], fill=(255, 252, 248))
    for i in range(12):
        yy = y0 + (24 + i * 5) * k
        d.line([(x0 + 15 * k, yy), (x1 - (15 + (i % 4 == 3) * 30) * k, yy)], fill=(150, 140, 145), width=2)
    d.rectangle([x0 + 10 * k, y1 - 34 * k, x0 + 50 * k, y1 - 10 * k], fill=(255, 255, 255))
    for i in range(40):
        if (i * 7) % 5 < 3:
            xx = x0 + 12 * k + i * 4
            d.line([(xx, y1 - 31 * k), (xx, y1 - 16 * k)], fill=(20, 20, 20), width=2)
    # 背 (帯の向き: 右 = 本の頭、上 = 表紙の側)。縦長に描いてから時計回りに 90° 回して貼る
    x0, y0, x1, y1 = rects["right"]
    L, T = x1 - x0, y1 - y0
    sp = Image.new("RGB", (T, L), base)
    sd = ImageDraw.Draw(sp)
    sd.rectangle([0, 0, T, 9 * k], fill=(255, 255, 255))
    f = font("YuGothB.ttc", T * 0.34)
    y = _vertical(sd, T / 2, 12 * k, TITLE, f, ink, T * 0.36)
    r = T * 0.30
    cy = y + r + 2 * k
    sd.ellipse([T / 2 - r, cy - r, T / 2 + r, cy + r], fill=(255, 255, 255))
    sd.text((T / 2, cy), str(vol), font=font("bahnschrift.ttf", r * 1.5, "Bold"), fill=(214, 60, 110), anchor="mm")
    _vertical(sd, T / 2, cy + r + 3 * k, "kt60", font("bahnschrift.ttf", T * 0.36, "SemiBold"), ink, T * 0.36)
    sd.rectangle([T * 0.12, L - 14 * k, T * 0.88, L - 4 * k], fill=(30, 30, 34))   # 下にレーベルの印 (黒い四角)
    img.paste(sp.rotate(-90, expand=True), (x0, y0))
    # 紙の小口: クリーム色に、紙の重なりの細い筋。上下の端にカバーの色の線
    x0, y0, x1, y1 = rects["left"]
    w, h = x1 - x0, y1 - y0
    rng = np.random.default_rng(vol)
    rows = (rng.standard_normal(h) * 5).astype(np.float32)
    a = np.full((h, w, 3), (236, 230, 216), np.float32) + rows[:, None, None] + noise((w, h), 2.5, vol, (40, 1))[..., None]
    page = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pd = ImageDraw.Draw(page)
    pd.line([(0, 0), (w, 0)], fill=base, width=2)
    pd.line([(0, h - 1), (w, h - 1)], fill=base, width=2)
    img.paste(page, (x0, y0))
    return img


# ---------------------------------------------------------------- コースター
COASTER_PX = 512


def make_coaster():
    """白っぽいラバーウッド (まっすぐな細い木目と、うっすら濃い筋) にこげ茶の ORIGINAL / TASTE。字の上 = 画像の上 = 奥"""
    n = COASTER_PX
    mm = n / (FURNITURE["coaster"]["w"] * 1000)
    rng = np.random.default_rng(11)
    y = np.arange(n, dtype=np.float32)
    warp = sum(a * np.sin(2 * np.pi * (y / n) * f + rng.uniform(0, 6.3)) for f, a in ((1, 3.0), (2.3, 1.2), (5.1, 0.4)))   # 木目のわずかな揺れ (px)
    x = (np.arange(n, dtype=np.float32)[None, :] + warp[:, None]) % n
    lines = np.zeros(n, np.float32)
    for width, amp in ((1.5, 1.0), (5, 1.2), (18, 1.4)):   # 細い筋・太い筋・色のむら (横の 1D のむらを、縦に揺らしながら伸ばす)
        c = rng.standard_normal(n).astype(np.float32)
        kern = np.exp(-0.5 * (np.arange(-3 * width, 3 * width + 1) / width) ** 2)
        c = np.convolve(np.tile(c, 3), kern / kern.sum(), "same")[n:2 * n]
        lines += amp * c / c.std()
    grain = np.interp(x, np.arange(n), lines, period=n) * 4.5 + noise((n, n), 1.0, 12, (8, 8)) * 2
    flecks = np.maximum(noise((n, n), 1.0, 13, (2, 10)) - 1.8, 0) * 14                    # 放射組織の小さな斑
    base = np.array((228, 205, 168), np.float32)
    a = base + (grain - flecks)[..., None] * np.array((1.0, 0.95, 0.8), np.float32)
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    # 字: 細長い太字。焼き印のように少しむらのあるこげ茶
    mask = Image.new("L", (n, n), 0)
    md = ImageDraw.Draw(mask)
    f = font("ARIALNB.TTF", 4.6 * mm)
    cx = n / 2
    for i, word in enumerate(("ORIGINAL", "TASTE")):
        y = (11.5 + i * 5.6) * mm
        x = cx - (f.getlength(word) + (len(word) - 1) * 0.35 * mm) / 2
        for ch in word:   # 字の間を少し広げる
            md.text((x, y), ch, font=f, fill=255, anchor="lm")
            x += f.getlength(ch) + 0.35 * mm
    ink = np.asarray(mask.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
    ink *= 0.88 + 0.12 * np.clip(noise((n, n), 1.0, 14, (3, 3)), -1, 1)
    out = np.asarray(img, np.float32) * (1 - ink[..., None]) + np.array((78, 50, 32), np.float32) * ink[..., None]
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


# ---------------------------------------------------------------- ペンスタンドの帯
BAND_MM = 22.0   # penstand_band.jpg 1枚の実寸 (正方形)。帯の幅と同じくらい
BAND_PX = 256


def make_penstand_band():
    """PP の平たい組みひもの帯 (帯の向き = 画像の横)。帯に沿った太い畝 (糸の束) と、その上の細かい斜めの綾の筋。
    色は明るめの灰色 (2026-10-27 にユーザー指定でチャコールグレー (平均 67) から明るく)。
    横の帯と縦の帯が市松に並ぶので、畝の向きでマスの違いが見える"""
    n = BAND_PX
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    rows = 0.5 + 0.5 * np.sin(2 * math.pi * 7 * y / n)                 # 帯に沿った畝 (1枚に 7 本 = 約 3mm 間隔。上下につながる)
    rows = rows ** 0.6
    twill = np.sin(2 * math.pi * (16 * x / n + 7 * y / n) * 2)         # 畝の上の細かい斜めの筋 (左右・上下につながる)
    a = 86 + 28 * rows + 5 * twill * rows + noise((n, n), 3.0, 21)
    a = np.stack([a, a, a * 1.04], -1)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))


# ---------------------------------------------------------------- キーボード
def legend_color(x_mm, y_mm):
    """キーの光の色: 左 (G キー) の青から右 (テンキー) の水色へ、虹の順に変わる (公式の写真の色の流れ)"""
    t = x_mm / KB.W
    stops = [(0.0, 215), (0.18, 255), (0.36, 300), (0.52, 340), (0.62, 380), (0.70, 410), (0.78, 450), (0.86, 480), (1.0, 545)]
    for (t0, h0), (t1, h1) in zip(stops, stops[1:]):
        if t <= t1:
            h = h0 + (h1 - h0) * (t - t0) / (t1 - t0)
            break
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, 0.95, 1.0)
    return round(r * 255), round(g * 255), round(b * 255)


GRAY = (120, 122, 128)   # 光っていない字 (M2・M3・MR) と、上面に印刷した字
ARROWS = {"↑": (0, -1), "↓": (0, 1), "←": (-1, 0), "→": (1, 0)}   # 画像の上 = キーボードの奥


def _icon(d, name, cx, cy, s, fill):
    """丸いボタンとキーの記号 (s = 大きさの目安 px)"""
    w = max(1, round(s * 0.11))
    if name == "WIN":                    # Windows の印 (4枚の板)
        g, q = s * 0.06, s * 0.27
        for sx in (-1, 1):
            for sy in (-1, 1):
                d.rectangle([cx + (g if sx > 0 else -q), cy + (g if sy > 0 else -q), cx + (q if sx > 0 else -g), cy + (q if sy > 0 else -g)], fill=fill)
    elif name == "MENU":                 # メニューの印 (四角に横線)
        w = max(1, round(s * 0.06))
        d.rectangle([cx - s * 0.2, cy - s * 0.25, cx + s * 0.2, cy + s * 0.25], outline=fill, width=w)
        for i in (-1, 0, 1):
            d.line([(cx - s * 0.1, cy + i * s * 0.11), (cx + s * 0.1, cy + i * s * 0.11)], fill=fill, width=w)
    elif name in ARROWS:                 # 矢印 (フォントに無いので線と三角で描く)
        ux, uy = ARROWS[name]
        px, py = -uy, ux
        L, hw = s * 0.36, s * 0.16
        d.line([(cx - ux * L, cy - uy * L), (cx + ux * L * 0.4, cy + uy * L * 0.4)], fill=fill, width=w)
        tip = (cx + ux * L, cy + uy * L)
        d.polygon([tip, (tip[0] - ux * s * 0.3 + px * hw, tip[1] - uy * s * 0.3 + py * hw),
                   (tip[0] - ux * s * 0.3 - px * hw, tip[1] - uy * s * 0.3 - py * hw)], fill=fill)
    elif name == "SPACE":
        d.rectangle([cx - s * 0.32, cy - w / 2, cx + s * 0.32, cy + w / 2], fill=fill)
    elif name in ("↵", "BS"):           # Enter の折れた矢印 / BackSpace の左矢印
        if name == "BS":
            d.line([(cx - s * 0.32, cy), (cx + s * 0.32, cy)], fill=fill, width=w)
            d.polygon([(cx - s * 0.42, cy), (cx - s * 0.16, cy - s * 0.18), (cx - s * 0.16, cy + s * 0.18)], fill=fill)
        else:
            d.line([(cx + s * 0.3, cy - s * 0.25), (cx + s * 0.3, cy + s * 0.08), (cx - s * 0.25, cy + s * 0.08)], fill=fill, width=w)
            d.polygon([(cx - s * 0.36, cy + s * 0.08), (cx - s * 0.14, cy - s * 0.08), (cx - s * 0.14, cy + s * 0.24)], fill=fill)
    elif name in ("PREV", "PLAY", "NEXT", "MUTE"):
        h = s * 0.2
        if name == "PREV":
            d.rectangle([cx - s * 0.3, cy - h, cx - s * 0.24, cy + h], fill=fill)
            for o in (0.0, 0.22):
                d.polygon([(cx - s * 0.24 + o * s, cy), (cx - s * 0.02 + o * s, cy - h), (cx - s * 0.02 + o * s, cy + h)], fill=fill)
        elif name == "NEXT":
            d.rectangle([cx + s * 0.24, cy - h, cx + s * 0.3, cy + h], fill=fill)
            for o in (0.0, 0.22):
                d.polygon([(cx + s * 0.24 - o * s, cy), (cx + s * 0.02 - o * s, cy - h), (cx + s * 0.02 - o * s, cy + h)], fill=fill)
        elif name == "PLAY":
            d.polygon([(cx - s * 0.26, cy - h), (cx - s * 0.26, cy + h), (cx + s * 0.02, cy)], fill=fill)
            d.rectangle([cx + s * 0.08, cy - h, cx + s * 0.14, cy + h], fill=fill)
            d.rectangle([cx + s * 0.2, cy - h, cx + s * 0.26, cy + h], fill=fill)
        else:
            d.polygon([(cx - s * 0.3, cy - h * 0.5), (cx - s * 0.18, cy - h * 0.5), (cx - s * 0.02, cy - h * 1.1),
                       (cx - s * 0.02, cy + h * 1.1), (cx - s * 0.18, cy + h * 0.5), (cx - s * 0.3, cy + h * 0.5)], fill=fill)
            d.line([(cx + s * 0.08, cy - h * 0.6), (cx + s * 0.3, cy + h * 0.6)], fill=fill, width=w)
            d.line([(cx + s * 0.08, cy + h * 0.6), (cx + s * 0.3, cy - h * 0.6)], fill=fill, width=w)
    elif name == "GAME":                 # ゲームモード (ジョイスティック)
        d.rectangle([cx - s * 0.28, cy + s * 0.12, cx + s * 0.28, cy + s * 0.26], fill=fill)
        d.line([(cx, cy + s * 0.12), (cx, cy - s * 0.12)], fill=fill, width=w)
        r = s * 0.11
        d.ellipse([cx - r, cy - s * 0.12 - 2 * r, cx + r, cy - s * 0.12], fill=fill)
    elif name == "LIGHT":                # 明るさ (太陽)
        r = s * 0.12
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fill, width=w)
        for i in range(8):
            a = i * math.pi / 4
            d.line([(cx + math.cos(a) * s * 0.2, cy + math.sin(a) * s * 0.2), (cx + math.cos(a) * s * 0.3, cy + math.sin(a) * s * 0.3)], fill=fill, width=w)


def make_keyboard_legends():
    k = KB.LEGEND_PPM
    img = Image.new("RGB", KB.LEGEND_IMAGE, (0, 0, 0))
    d = ImageDraw.Draw(img)
    big = font("bahnschrift.ttf", 3.6 * k, "SemiBold")       # 英字・数字
    small = font("bahnschrift.ttf", 2.1 * k, "SemiBold")     # TAB・SHIFT・PRTSC などの字
    sub_f = font("bahnschrift.ttf", 2.8 * k, "SemiBold")     # 数字のキーの下の記号
    pad_sub = font("bahnschrift.ttf", 1.8 * k, "SemiBold")   # テンキーの HOME などの小さな字
    jp = font("YuGothB.ttc", 2.0 * k)
    for key in KB.keys():
        label, sub = key["label"], key["sub"]
        if not label:
            continue
        x, y, w, h = (key[c] * k for c in ("x", "y", "w", "h"))
        top = y - h / 2
        color = legend_color(key["x"], key["y"])
        if key["kind"] == "round":
            if label in ("M2", "M3", "MR"):
                color = GRAY
            elif label == "M1":
                color = (255, 236, 90)
            if label in ("M1", "M2", "M3", "MR"):
                d.text((x, y), label, font=font("bahnschrift.ttf", 3.4 * k, "SemiBold"), fill=color, anchor="mm")
            else:
                _icon(d, label, x, y, 11 * k, color)
            continue
        cy = top + 4.6 * k                                     # 字はキーの上の方
        if label in ("WIN", "MENU", "SPACE", "BS") or label in ARROWS:
            _icon(d, label, x, cy if label not in ARROWS else y, 9 * k, color)
        elif key["kind"] == "enter":
            _icon(d, "↵", x + 2 * k, y + 5 * k, 10 * k, color)
        elif "\n" in label or any(ord(c) > 0x3000 for c in label):   # 日本語の字 (半角/全角・無変換・変換・カタカナ ひらがな)
            for i, line in enumerate(label.split("\n")):
                d.text((x, cy - 0.6 * k + i * 2.6 * k), line, font=jp, fill=color, anchor="mm")
        elif len(label) == 1 or (label[0] in "FG" and label[1:].isdigit()):   # 1字・F1〜F12・G1〜G5 は大きな字
            d.text((x, cy), label, font=big, fill=color, anchor="mm")
        else:
            d.text((x, cy), label, font=small, fill=color, anchor="mm")
        if sub in ARROWS:
            _icon(d, sub, x, top + 11.2 * k, 6 * k, color)
        elif sub:   # 下の字: 記号は大きめ、HOME・PG UP などは小さく
            d.text((x, top + 11.0 * k), sub, font=sub_f if len(sub) == 1 else pad_sub, fill=color, anchor="mm")
    # 上面に印刷・光る物: 左上の G のロゴ (光る青)、CAPS LOCK / NUM LOCK の字 (灰色)
    g = KB.G_LOGO
    s = g["size"] * k
    cx, cy = g["x"] * k, g["y"] * k
    wd = s * 0.2
    d.arc([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], 40, 320, fill=(40, 200, 255), width=round(wd))
    d.rectangle([cx - wd / 2 + s * 0.1, cy - wd / 2 + s * 0.05, cx + s / 2, cy + wd / 2 + s * 0.05], fill=(40, 200, 255))
    d.rectangle([cx + s / 2 - wd, cy + s * 0.05, cx + s / 2, cy + s / 2], fill=(40, 200, 255))
    lab = font("bahnschrift.ttf", 1.7 * k, "SemiBold")
    for text, lx, _ in KB.LOCK_LEDS:
        d.text((lx * k, 10.2 * k), text, font=lab, fill=GRAY, anchor="mm")
    return img


def make_keyboard_brushed():
    """濃い灰色のアルミのヘアライン (筋は画像の縦)。1枚 = 0.5m"""
    n = 512
    a = 50 + noise((n, n), 1.0, 31, (1.0, 220)) * 6 + noise((n, n), 1.0, 32, (0.6, 40)) * 3
    rgb = np.stack([a * 0.96, a * 0.98, a * 1.05], -1)
    return Image.fromarray(rgb.clip(0, 255).astype(np.uint8))


# ---------------------------------------------------------------- マウス
MOUSE_PPM = 6.4   # mouse_g604_top.png: 1mm の画素数 (幅 80 x 長さ 130mm 全体)


def make_mouse_top():
    """G604 を真上から見た面 (前 = 画像の上、親指の側 = 画像の左)。座標は公式の上からの写真を mm に直した物"""
    k = MOUSE_PPM
    W, H = round(80 * k), round(130 * k)
    a = np.full((H, W), 30.0, np.float32) + noise((W, H), 1.2, 41)
    img = Image.fromarray(np.stack([a, a, a * 1.04], -1).clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    P = lambda x, yf: (W / 2 + x * k, yf * k)   # x = 中心から右へ (mm)、yf = 前の端から (mm)
    # 手のひらの点々 (縦長の小さな楕円。左の方と親指の羽根)
    for row in range(40):
        yf = 58 + row * 1.25
        for col in range(60):
            x = -40 + col * 1.25 + (row % 2) * 0.62
            if yf > 104.5 - (x + 22) * 0.29 or yf < 61 - (x + 20) * 0.135:
                continue
            if x > 18 - (yf - 60) * 0.2:             # 右の方 (G のロゴのあたり) は点が無い
                continue
            cx, cy = P(x, yf)
            d.ellipse([cx - 0.28 * k, cy - 0.42 * k, cx + 0.28 * k, cy + 0.42 * k], fill=(22, 22, 24))
    line = (14, 14, 15)
    lw = max(2, round(0.45 * k))
    d.rectangle([P(1.0, 0), P(11.6, 41.5)], fill=(17, 17, 18))            # 左右のボタンの間の溝 (ツヤのある黒)
    d.rounded_rectangle([P(2.2, 19.6), P(12.0, 43.0)], radius=2 * k, fill=(6, 6, 7))   # ホイールの穴
    d.line([P(-26, 60.2), P(39, 51.6)], fill=line, width=lw)             # ボタンと手のひらのつなぎ目
    d.line([P(-21, 104.6), P(37, 95.4)], fill=line, width=lw)            # 手のひらと後ろのつなぎ目
    for x in (1.0, 11.6):                                                 # 真ん中の溝 (ホイールの左右)
        d.line([P(x, 0), P(x, 58.0)], fill=line, width=lw)
    d.rounded_rectangle([P(1.6, 41.5), P(11.0, 66.5)], radius=4.6 * k, outline=line, width=lw)   # ホイールの後ろのボタン
    d.line([P(1.6, 54), P(11.0, 54)], fill=line, width=lw)
    for x, s in ((-2.8, -1), (15.4, 1)):                                  # ホイールの横の三角 (左右に倒す)
        cx, cy = P(x, 31.8)
        d.polygon([(cx + s * 1.1 * k, cy - 1.3 * k), (cx + s * 1.1 * k, cy + 1.3 * k), (cx - s * 1.0 * k, cy)], fill=(60, 60, 63))
    # G のロゴ (少しツヤのある濃い灰色)
    cx, cy = P(23.8, 65.0)
    s, wd = 8.4 * k, 1.7 * k
    d.arc([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], 40, 320, fill=(66, 66, 70), width=round(wd))
    d.rectangle([cx + s * 0.05, cy - wd / 2 + s * 0.05, cx + s / 2, cy + wd / 2 + s * 0.05], fill=(66, 66, 70))
    d.rectangle([cx + s / 2 - wd, cy + s * 0.05, cx + s / 2, cy + s / 2], fill=(66, 66, 70))
    return img.filter(ImageFilter.GaussianBlur(0.4))


# ---------------------------------------------------------------- 紙のゴミ箱 (2026-10-27)
# 新聞紙やチラシを折って作った卓上のゴミ箱 (ユーザー指定。参考の動画「畳める！チラシで作る深めのゴミ箱」)。机の上の1つは新聞紙で組み立てた物、
# サブの台の右の小物入れの中は畳んだ物 (新聞紙・スーパーのチラシ・住宅のチラシ)。新聞とチラシの文・店・会社は架空
SHEET_MM = 400                     # 紙1枚の絵の大きさ (正方形)。ゴミ箱の面はここから切り抜く
PAPER_NEWS = (232, 229, 219)       # 新聞紙の地 (少し灰色がかった生成り)
PAPER_WHITE = (247, 246, 241)      # チラシの紙
NEWS_TEXT = ("きょうの県内は高気圧に覆われておおむね晴れる見込みで、日中の最高気温は平年並みとなる。朝晩は冷え込むため体調管理に注意したい。"
             "市の中央公園では週末に秋の収穫祭が開かれ、地元の農家が育てた野菜や果物が並ぶ。会場では餅つきや子ども向けの工作教室も予定されている。"
             "市場ではキャベツや大根の入荷が増え、店頭の価格は先月より落ち着いてきた。県立図書館は来月から平日の開館時間を午後八時まで延ばす。"
             "駅前の商店街では古い街並みを生かした催しが続き、週末は多くの人でにぎわった。")
NEWS_HEADS = ("収穫祭にぎわう", "野菜の値段落ち着く", "図書館夜八時まで", "秋晴れ続く", "商店街に人波", "工作教室に親子")
NEWS_ADS = (((28, 72, 150), "秋の住まい相談会", "入場無料・予約優先　0120-000-000"),
            ((196, 36, 40), "家具 大処分市", "ソファー・ベッド・収納 最大半額"),
            ((22, 120, 70), "市民文化祭", "11月3日　市民ホール　入場無料"))


def _ink_paper(base, ink, colors=None, seed=0, grain=1.0):
    """紙の地 base に、色の版 colors (RGB。掛け算で重ねる) と黒のインク ink (0〜1) を刷る。紙の細かいむら (grain 倍) も足す"""
    n = ink.shape[0]
    paper = np.array(base, np.float32) + grain * (noise((n, n), 2.2, seed, (3, 3)) + noise((n, n), 1.5, seed + 1, (60, 60)))[..., None]
    if colors is not None:
        paper = paper * colors / 255.0
    out = paper * (1 - 0.86 * ink[..., None]) + np.array((30, 30, 34), np.float32) * 0.86 * ink[..., None]
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def _news_sheet(seed):
    """新聞の紙面: 段ごとに、縦書きの行 (1行 10 字) を右から左へ並べる。記事の右に見出し、ところどころ写真と色の広告の枠"""
    k = TRASH_PPM
    n = SHEET_MM * k
    rng = np.random.default_rng(seed)
    ink = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(ink)
    colors = Image.new("RGB", (n, n), (255, 255, 255))
    cd = ImageDraw.Draw(colors)
    body = font("yumin.ttf", 3.0 * k)
    px, py = 3.5 * k, 3.35 * k               # 行の間隔・字の間隔
    band, gap = 10 * py, 3.2 * k             # 1段の高さ・段の間
    text, ti = NEWS_TEXT, int(rng.integers(len(NEWS_TEXT)))
    y = -rng.uniform(0, band + gap)          # 紙面の途中を切った物なので、段の位置をずらす
    while y < n:
        x = n + rng.uniform(0, 30 * k)
        while x > -10 * k:
            w = rng.uniform(55, 150) * k             # 記事の幅
            x0 = x - w
            r = rng.random()
            if r < 0.05:   # 色の広告の枠 (1段分)
                col, title, sub = NEWS_ADS[int(rng.integers(len(NEWS_ADS)))]
                aw = rng.uniform(95, 140) * k
                cd.rectangle([x - aw, y, x, y + band], fill=col)
                cd.text((x - aw / 2, y + band * 0.40), title, font=font("YuGothB.ttc", aw / len(title) * 0.8), fill=(255, 255, 255), anchor="mm")
                cd.text((x - aw / 2, y + band * 0.80), sub, font=font("YuGothB.ttc", aw / len(sub) * 0.85), fill=(255, 250, 220), anchor="mm")
                x -= aw + px
                continue
            if r < 0.15:   # 写真 (灰色の濃淡のぼけた形)
                pw, ph = int(min(w, 70 * k)), int(band)
                photo = noise((pw, ph), 1.0, int(rng.integers(1 << 30)), (pw / 6, ph / 5)) * 0.2 + 0.45
                photo += np.linspace(-0.12, 0.12, ph)[:, None]
                photo = Image.fromarray((photo.clip(0.05, 0.95) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3 * k))
                ink.paste(photo, (int(x - pw), int(y)))
                d.text((x - pw / 2, y + band + 0.4 * k), "写真・市内で", font=font("YuGothM.ttc", 2.4 * k), fill=200, anchor="mt")
                x -= pw + px
                continue
            if r < 0.55:   # 見出し (縦書きの太字。白抜きのこともある)
                head = NEWS_HEADS[int(rng.integers(len(NEWS_HEADS)))]
                fs = rng.choice([7.0, 8.5, 10.0]) * k
                per = max(1, int(band // (fs * 1.02)))
                cols = [head[i:i + per] for i in range(0, len(head), per)]
                hw = len(cols) * fs * 1.15
                rev = rng.random() < 0.3
                if rev:
                    d.rectangle([x - hw - 0.8 * k, y, x, y + band], fill=235)
                f = font("yumindb.ttf", fs)
                for c, line in enumerate(cols):
                    _vertical(d, x - (c + 0.5) * fs * 1.15, y + 0.3 * k, line, f, 0 if rev else 255, fs * 1.02)
                x -= hw + 1.5 * k
            while x > x0:   # 本文 (縦書き)
                for j in range(10):
                    ch = text[ti % len(text)]
                    ti += 1
                    d.text((x - px / 2, y + j * py), ch, font=body, fill=235, anchor="mt")
                x -= px
            d.line([(x + px * 0.2, y), (x + px * 0.2, y + band)], fill=150, width=1)   # 記事の間の細い罫
            x -= px * 0.6
        if rng.random() < 0.5:
            d.line([(0, y + band + gap / 2), (n, y + band + gap / 2)], fill=150, width=1)
        y += band + gap
    a = np.asarray(ink.filter(ImageFilter.GaussianBlur(0.45)), np.float32) / 255
    return _ink_paper(PAPER_NEWS, a, np.asarray(colors, np.float32), seed)


GOODS = (("国産キャベツ 1玉", "98", (110, 170, 70), "circle"), ("ふじりんご", "158", (210, 40, 45), "circle"),
         ("にんじん 3本", "128", (240, 130, 30), "long"), ("豚こま切れ 100g", "138", (236, 150, 150), "slab"),
         ("食パン 6枚切", "118", (222, 180, 120), "slab"), ("たまご 10個", "228", (250, 246, 236), "eggs"),
         ("牛乳 1000ml", "178", (240, 244, 250), "box"), ("バナナ 1房", "148", (246, 210, 60), "long"),
         ("鶏もも肉 100g", "98", (240, 196, 170), "slab"), ("みかん 1袋", "298", (250, 150, 30), "circle"),
         ("木綿豆腐", "58", (250, 250, 244), "box"), ("生しいたけ", "198", (120, 84, 60), "circle"))


def _flyer_red():
    """スーパーのチラシ (架空の店): 黄色の地に赤い帯の見出し、白い枠の商品の絵と赤い値段。上下につなげて 1枚 (SHEET_MM 角) を埋める"""
    k = TRASH_PPM
    n = SHEET_MM * k
    img = Image.new("RGB", (n, n), (255, 220, 56))
    d = ImageDraw.Draw(img)
    big, mid, small = font("YuGothB.ttc", 26 * k), font("YuGothB.ttc", 7.5 * k), font("YuGothM.ttc", 4.2 * k)
    price = font("bahnschrift.ttf", 21 * k, "Bold")
    y, gi = 0, 0
    while y < n:
        d.rectangle([0, y, n, y + 52 * k], fill=(212, 30, 36))
        d.text((n / 2, y + 22 * k), "秋の大感謝祭", font=big, fill=(255, 255, 255), anchor="mm")
        d.text((n / 2, y + 44 * k), "フレッシュいちば 中央店　10月26日(土)・27日(日) 限り", font=mid, fill=(255, 238, 110), anchor="mm")
        y += 58 * k
        for _ in range(3):   # 商品の段 (1段に 4 つ)
            cw = (n - 10 * k) / 4
            for c in range(4):
                name, yen, col, shape = GOODS[gi % len(GOODS)]
                gi += 1
                x0, y0 = 5 * k + c * cw + 2 * k, y
                x1, y1 = x0 + cw - 4 * k, y + 86 * k
                d.rounded_rectangle([x0, y0, x1, y1], 4 * k, fill=(255, 255, 255), outline=(230, 60, 40), width=max(1, int(0.6 * k)))
                cx, cy = (x0 + x1) / 2, y0 + 26 * k
                if shape == "circle":
                    d.ellipse([cx - 17 * k, cy - 16 * k, cx + 17 * k, cy + 16 * k], fill=col)
                    d.ellipse([cx - 9 * k, cy - 11 * k, cx - 2 * k, cy - 5 * k], fill=tuple(min(255, v + 60) for v in col))
                elif shape == "long":
                    for o in (-8, 0, 8):
                        d.rounded_rectangle([cx - 24 * k, cy + (o - 3) * k, cx + 22 * k, cy + (o + 3) * k], 3 * k, fill=col)
                elif shape == "slab":
                    d.rounded_rectangle([cx - 22 * k, cy - 13 * k, cx + 22 * k, cy + 13 * k], 5 * k, fill=col, outline=(180, 120, 110))
                elif shape == "eggs":
                    for ex in range(5):
                        for ey in range(2):
                            d.ellipse([cx + (ex * 9 - 22) * k, cy + (ey * 11 - 11) * k, cx + (ex * 9 - 15) * k, cy + (ey * 11 - 2) * k],
                                      fill=col, outline=(200, 190, 170))
                else:
                    d.rectangle([cx - 12 * k, cy - 18 * k, cx + 12 * k, cy + 16 * k], fill=col, outline=(90, 120, 190), width=max(1, int(0.8 * k)))
                    d.rectangle([cx - 12 * k, cy - 4 * k, cx + 12 * k, cy + 4 * k], fill=(60, 110, 200))
                d.text((cx, y0 + 50 * k), name, font=small, fill=(30, 30, 30), anchor="mm")
                d.text((cx + 4 * k, y0 + 68 * k), yen, font=price, fill=(214, 24, 30), anchor="rm")
                d.text((cx + 6 * k, y0 + 71 * k), "円", font=mid, fill=(214, 24, 30), anchor="lm")
                d.text((cx, y0 + 81 * k), f"税込{round(int(yen) * 1.08)}円", font=small, fill=(90, 90, 90), anchor="mm")
            y += 92 * k
    a = np.zeros((n, n), np.float32)
    return _ink_paper(PAPER_WHITE, a, np.asarray(img, np.float32), 31, grain=0.35)


def _flyer_blue():
    """住宅のチラシ (架空の会社): 白地に青い帯の見出し、家の写真 (空と家の形)、間取り図、字の行と電話番号。上下につなげて埋める"""
    k = TRASH_PPM
    n = SHEET_MM * k
    img = Image.new("RGB", (n, n), (255, 255, 255))
    d = ImageDraw.Draw(img)
    blue = (26, 82, 160)
    head, mid, small = font("YuGothB.ttc", 20 * k), font("YuGothB.ttc", 8 * k), font("YuGothM.ttc", 3.6 * k)
    y = 0
    while y < n:
        d.rectangle([0, y, n, y + 40 * k], fill=blue)
        d.text((14 * k, y + 20 * k), "新築一戸建て 見学会", font=head, fill=(255, 255, 255), anchor="lm")
        d.text((n - 14 * k, y + 20 * k), "全4区画　駅から徒歩8分", font=mid, fill=(255, 255, 255), anchor="rm")
        y += 46 * k
        # 家の写真: 空のグラデーション・家の壁と屋根と窓・植え込み
        px0, px1, py1 = 10 * k, n * 0.62, y + 120 * k
        sky = np.linspace(0, 1, int(py1 - y))[:, None, None]
        top, bottom = np.array((120, 170, 225)), np.array((215, 232, 246))
        grad = (top * (1 - sky) + bottom * sky).repeat(int(px1 - px0), 1).astype(np.uint8)
        img.paste(Image.fromarray(grad), (int(px0), int(y)))
        hx0, hx1, hy0, hy1 = px0 + 40 * k, px1 - 50 * k, y + 45 * k, py1 - 10 * k
        d.rectangle([hx0, hy0, hx1, hy1], fill=(236, 226, 208))
        d.polygon([(hx0 - 8 * k, hy0), ((hx0 + hx1) / 2, y + 12 * k), (hx1 + 8 * k, hy0)], fill=(70, 72, 80))
        for wx in range(int(hx0 + 14 * k), int(hx1 - 20 * k), int(30 * k)):
            d.rectangle([wx, hy0 + 14 * k, wx + 16 * k, hy0 + 30 * k], fill=(120, 150, 180), outline=(250, 250, 250), width=max(1, k))
        d.rectangle([hx1 - 26 * k, hy1 - 34 * k, hx1 - 12 * k, hy1], fill=(120, 80, 50))
        for bx in range(int(px0), int(px1), int(14 * k)):
            d.ellipse([bx, py1 - 14 * k, bx + 18 * k, py1 + 2 * k], fill=(70, 130, 70))
        # 右: 価格と間取り図
        rx = px1 + 10 * k
        d.text((rx, y + 10 * k), "価格", font=mid, fill=(40, 40, 40), anchor="lt")
        d.text((rx, y + 22 * k), "2,980万円", font=font("YuGothB.ttc", 15 * k), fill=(200, 30, 40), anchor="lt")
        gx0, gy0, gx1, gy1 = rx, y + 46 * k, n - 10 * k, py1
        d.rectangle([gx0, gy0, gx1, gy1], outline=(40, 40, 40), width=max(1, int(0.8 * k)))
        for f in (0.38, 0.66):
            d.line([(gx0 + (gx1 - gx0) * f, gy0), (gx0 + (gx1 - gx0) * f, gy1)], fill=(40, 40, 40), width=max(1, int(0.5 * k)))
        d.line([(gx0, (gy0 + gy1) / 2), (gx0 + (gx1 - gx0) * 0.66, (gy0 + gy1) / 2)], fill=(40, 40, 40), width=max(1, int(0.5 * k)))
        for (fx, fy), label in (((0.19, 0.25), "洋室6帖"), ((0.19, 0.75), "洋室5帖"), ((0.52, 0.5), "LDK"), ((0.83, 0.5), "和室")):
            d.text((gx0 + (gx1 - gx0) * fx, gy0 + (gy1 - gy0) * fy), label, font=small, fill=(40, 40, 40), anchor="mm")
        y = py1 + 8 * k
        # 字の行と電話番号
        for i in range(6):
            d.line([(14 * k, y + i * 6 * k), (n - (14 + (i % 3) * 30) * k, y + i * 6 * k)], fill=(150, 150, 156), width=max(1, int(1.6 * k)))
        y += 40 * k
        d.rectangle([0, y, n, y + 22 * k], fill=(232, 240, 250))
        d.text((14 * k, y + 11 * k), "みどり住宅　お問い合わせ 0120-000-000", font=mid, fill=blue, anchor="lm")
        y += 30 * k
    a = np.zeros((n, n), np.float32)
    return _ink_paper(PAPER_WHITE, a, np.asarray(img, np.float32), 41, grain=0.35)


def _crop(sheet, cx, cy, angle, s):
    """紙の絵から、中心 (cx, cy) の s 角の正方形を angle 度回して切り抜く"""
    big = sheet.crop((int(cx - s), int(cy - s), int(cx + s), int(cy + s))).rotate(angle, resample=Image.BICUBIC)
    return big.crop((s // 2, s // 2, s // 2 + s, s // 2 + s))


def _flap(base, flap, tri, seed, shadow=0.24):
    """紙の面 base の上に、三角 tri (画像の座標の3点。最初の2点の辺 = 折り返しの縁) の部分だけ、折り返した紙 flap を重ねる。
    縁の外側 (下の紙) に細い影、縁の内側に明るい線"""
    s = base.size[0]
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).polygon(tri, fill=255)
    out = Image.composite(flap, base, m)
    (x0, y0), (x1, y1), (x2, y2) = tri
    nx, ny = y1 - y0, -(x1 - x0)
    ln = math.hypot(nx, ny)
    nx, ny = nx / ln, ny / ln
    if (x2 - x0) * nx + (y2 - y0) * ny > 0:   # 法線を三角の外 (下の紙の側) へ
        nx, ny = -nx, -ny
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    dist = (xx - x0) * nx + (yy - y0) * ny   # 縁からの距離 (外 = 正)
    rng = np.random.default_rng(seed)
    wob = 1 + 0.25 * np.sin((xx * ny - yy * nx) / s * 6.0 + rng.uniform(0, 6))   # 影の太さの揺れ
    shade = np.where(dist > 0, shadow * np.exp(-np.maximum(dist, 0) / (3.2 * wob)), 0) + np.where((dist <= 0) & (dist > -1.6), -0.10, 0)
    a = np.asarray(out, np.float32) * (1 - shade[..., None])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def _creases(img, sides, depth=0.07, width=5.0):
    """面の縁 (sides = "l" "r" "t" "b" の組み合わせ) を少し暗くする (折り目の角が丸くなって陰る)"""
    s = img.size[0]
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    k = np.ones((s, s), np.float32)
    for side, dist in (("l", xx), ("r", s - 1 - xx), ("t", yy), ("b", s - 1 - yy)):
        if side in sides:
            k *= 1 - depth * np.exp(-dist / width)
    return Image.fromarray((np.asarray(img, np.float32) * k[..., None]).clip(0, 255).astype(np.uint8))


def _layers(img, edges, paper, seed):
    """畳んだゴミ箱の縁に見える、少しずつずれた紙の重なりの線 (edges = "b" "r" の組み合わせ)"""
    s = img.size[0]
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    dark = tuple(int(v * 0.72) for v in paper)
    for i, off in enumerate((3, 7, 10)):
        if "b" in edges:
            y = s - 1 - off - rng.uniform(0, 1.5)
            d.line([(rng.uniform(4, 30), y), (s - off, y)], fill=dark, width=1)
        if "r" in edges:
            x = s - 1 - off - rng.uniform(0, 1.5)
            d.line([(x, rng.uniform(4, 30)), (x, s - off)], fill=dark, width=1)
    return img


def _edge_strip(w, h, paper, accents, seed, vertical):
    """畳んだゴミ箱の縁の面: 紙の重なり (4〜5枚) の筋。vertical なら筋が縦 (板の左右の縁)"""
    rng = np.random.default_rng(seed)
    L = h if not vertical else w      # 筋を横切る向きの画素数
    cols = []
    for i in range(L):
        layer = int(i / L * 5)
        c = np.array(accents[layer % len(accents)] if accents else paper, np.float32)
        if i % max(1, L // 5) == 0:
            c = c * 0.55   # 紙と紙の境目
        cols.append(c * rng.uniform(0.94, 1.02))
    a = np.array(cols, np.float32)
    a = np.repeat(a[:, None, :], w if not vertical else h, 1)
    if vertical:
        a = a.transpose(1, 0, 2)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def make_paper_trash():
    """紙のゴミ箱の画像 (面の並びは layout.trash_atlas): 机の上の新聞紙のゴミ箱の壁の外と内・底、畳んだゴミ箱の表 (紙3種類)・縁の筋。
    壁には三角の折り返し (参考の動画の形。外は風車のように同じ向き、内は逆向き) と、その縁の影を描く"""
    rects, size = trash_atlas()
    img = Image.new("RGB", size, PAPER_NEWS)
    sheets = {"news": _news_sheet(5), "news_in": _news_sheet(6), "red": _flyer_red(), "blue": _flyer_blue()}
    s = rects["out0"][2] - rects["out0"][0]
    n = SHEET_MM * TRASH_PPM
    rng = np.random.default_rng(27)
    pick = lambda: (rng.uniform(s, n - s), rng.uniform(s, n - s))

    def put(name, face):
        img.paste(face, rects[name][:2])

    for i in range(4):   # 壁の外: 下の紙 + 左下の三角の折り返し (90°回った字)。左右の角と下は折り目で少し陰る
        base = _crop(sheets["news"], *pick(), 0, s)
        flap = _crop(sheets["news"], *pick(), 90, s)
        face = _flap(base, flap, [(0, 0), (s, s), (0, s)], i)
        put(f"out{i}", _creases(face, "lrb"))
    for i in range(4):   # 壁の内 (新聞の裏の面): 右下の三角の折り返し
        base = _crop(sheets["news_in"], *pick(), 180, s)
        flap = _crop(sheets["news_in"], *pick(), 270, s)
        face = _flap(base, flap, [(s, 0), (0, s), (s, s)], 10 + i, shadow=0.3)
        put(f"in{i}", _creases(face, "lrb", depth=0.12, width=7))
    # 内側の底: 4枚の三角が真ん中で合わさる (風車の順に重なる)
    c = s / 2
    face = _crop(sheets["news_in"], *pick(), 0, s)
    for j, tri in enumerate(([(0, 0), (s, 0), (c, c)], [(s, 0), (s, s), (c, c)], [(s, s), (0, s), (c, c)], [(0, s), (0, 0), (c, c)])):
        flap = _crop(sheets["news_in"], *pick(), 90 * j, s)
        face = _flap(face, flap, [tri[2], tri[0], tri[1]], 20 + j, shadow=0.28)
    put("bottom", _creases(face, "lrtb", depth=0.18, width=9))
    # 畳んだゴミ箱の表 (正方形に斜めの折り返し。下と右の縁に紙の重なり)
    accents = {"news": None, "red": [(255, 220, 56), PAPER_WHITE, (212, 30, 36), PAPER_WHITE, (255, 220, 56)],
               "blue": [PAPER_WHITE, (26, 82, 160), PAPER_WHITE, (215, 232, 246), PAPER_WHITE]}
    k = TRASH_PPM
    spots = {"news": ((210 * k, 150 * k), (120 * k, 260 * k)), "red": ((150 * k, 240 * k), (300 * k, 330 * k)),
             "blue": ((110 * k, 110 * k), (330 * k, 120 * k))}   # 表に見せる所 (下の紙・折り返し)。チラシは商品と値段・家の写真
    for paper in TRASH_PAPERS:
        sheet = sheets[paper]
        base = _crop(sheet, *spots[paper][0], 0, s)
        flap = _crop(sheet, *spots[paper][1], 90, s)
        face = _flap(base, flap, [(0, 0), (s, s), (0, s)], 30, shadow=0.3)
        tone = PAPER_NEWS if paper == "news" else PAPER_WHITE
        put(f"fold_{paper}", _creases(_layers(face, "br", tone, 31), "lt", depth=0.08, width=4))
        x0, y0, x1, y1 = rects[f"edge_v_{paper}"]
        img.paste(_edge_strip(x1 - x0, y1 - y0, tone, accents[paper], 40, True), (x0, y0))
        x0, y0, x1, y1 = rects[f"edge_h_{paper}"]
        img.paste(_edge_strip(x1 - x0, y1 - y0, tone, accents[paper], 41, False), (x0, y0))
    x0, y0, x1, y1 = rects["plain"]
    img.paste(_ink_paper(PAPER_NEWS, np.zeros((x1 - x0, x1 - x0), np.float32), None, 50).crop((0, 0, x1 - x0, y1 - y0)), (x0, y0))
    return img


# ---------------------------------------------------------------- 明るさの段階 (2026-10-27)
def make_shade_ramp():
    """横の位置 u (0〜1) のリニアの明るさが u になる灰色の段階 (画像は sRGB で持つので、u を sRGB に直して書く)"""
    u = (np.arange(256, dtype=np.float32) + 0.5) / 256
    v = np.where(u <= 0.0031308, u * 12.92, 1.055 * u ** (1 / 2.4) - 0.055) * 255
    return Image.fromarray(np.repeat(np.round(v)[None, :], 4, axis=0).astype(np.uint8)).convert("RGB")


if __name__ == "__main__":
    for name in BOOKS:
        save(make_book(name), f"book_physics{BOOKS[name][3]}.jpg", quality=92)
    save(make_coaster(), "coaster_top.jpg")
    save(make_penstand_band(), "penstand_band.jpg")
    save(make_keyboard_legends(), "keyboard_legends.png")
    save(make_keyboard_brushed(), "keyboard_brushed.jpg")
    save(make_mouse_top(), "mouse_g604_top.png")
    save(make_paper_trash(), "paper_trash.jpg", quality=88)
    save(make_shade_ramp(), "shade_ramp.png")
