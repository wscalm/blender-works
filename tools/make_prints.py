"""印刷物・画面の画像をコードで描いて textures/ に保存する (python3 tools/make_prints.py)。

写真 (reference/IMG_1099・IMG_1100) に写っている物の「雰囲気」を、実物の絵柄や文字を写さずに描く:
  books_atlas.jpg      本の背・表紙・天・小口 (64 冊分の柄を1枚に並べる。scripts/props.py の BOOK_ATLAS と並びを合わせる)
  screen_main.png      メインモニターの画面 (白い背景の管理画面風。グラフと文字の代わりの灰色の帯)
  clock_face.jpg       壁掛け時計の文字盤 (数字・分の点・温度計と湿度計の小さな目盛り)
  print_sunset.jpg     突っ張り棚の上の絵 (夕焼けの海と椰子の木)
  print_moon.jpg       本棚に立て掛けた絵 (月夜の海とイルカ)
  print_love.jpg       本棚の扉に飾った青紫の絵
  book_box.jpg         本棚の扉に飾った本の箱 (紺の表紙に赤い帯)
  certificate.jpg      本棚の扉に飾った賞状 (文字の代わりに灰色の線)
  picture_book.jpg     突っ張り棚の上の絵本 (茶色の表紙)
  stripe_fabric.jpg    ソファーの細いボーダーのクッション
  basket_woven.jpg     テレビ台の灰色の編みかご (細い帯を縦横に編んだ柄。1枚 = 0.20m)
  basket_check.jpg     テレビ台の白黒の市松のかご (1枚 = 0.12m)
  basket_mesh.jpg      白い樹脂のかご (角の丸い穴が並ぶ。穴は濃い灰色で描く。1枚 = 0.128m)
  tissue_box.jpg       ローテーブルのティッシュの箱 (白に紺の帯。面の並びは TISSUE_ATLAS)
  rug_print.jpg        ラグ全体の柄 (ベージュのキルトに犬・猫の絵と筆記体の字、薄茶の縁取り。写真 reference/IMG_1100)
文字はでたらめな字の並び (読める文にはしない。実在の商品の字や柄は描かない)。
出窓の段ボール箱 (box_tea.jpg・box_water.jpg) だけは、ユーザーが商品を指定したので tools/make_boxes.py が実物の箱に似せて描く (紙の地 _paper とインクの重ね方 _apply_ink はここの物を使う)。
乱数の種は固定なので、毎回同じ画像になる。
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "textures")
GOTHIC = "/usr/share/fonts/opentype/ipaexfont-gothic/ipaexg.ttf"
MINCHO = "/usr/share/fonts/opentype/ipaexfont-mincho/ipaexm.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# 本の背に並べる字 (意味のない並びにする)
KANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん"
KATA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワンー"
KANJI = "入門実践基礎設計言語理論応用技術開発世界物語記録研究方法解説図鑑新版事典教室講座演習問題集" \
        "数学情報工学計算機構造処理通信社会文化歴史思想夜空海風花雪月光影旅人時間季節日本東京"
LATIN = ["Python", "C++", "Java", "Linux", "Web", "SQL", "Git", "Unity", "AI", "Go", "Rust", "CSS", "UNIX", "TCP/IP"]


def hexc(code):
    code = code.lstrip("#")
    return tuple(int(code[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def noise_layer(size, amount, seed, blur=0.6):
    """細かいむら (紙・布・印刷のざらつき)。-amount〜+amount の値の配列"""
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((size[1], size[0]))
    img = Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    return (np.asarray(img, dtype=np.float32) - 128) / 40 * amount


def add_noise(img, amount, seed, blur=0.6):
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    a += noise_layer(img.size, amount, seed, blur)[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def save(img, name, quality=90):
    path = os.path.join(TEX, name)
    if name.endswith(".png"):
        img.save(path, optimize=True)
    else:
        img.convert("RGB").save(path, quality=quality)
    print(f"{name}: {img.size[0]}x{img.size[1]}  {os.path.getsize(path) / 1024:.0f} KB")


# ---------------------------------------------------------------- 本
# 1冊分のマス = 64 x 512 px。左の 40 px が背、右の 24 px を上から 表紙 (256) / 天 (128) / 小口 (128) に分ける。
# 32 列 x 2 段 = 64 冊分。番号 i のマスは 列 i % 32、段 i // 32 (scripts/props.py の BOOK_ATLAS と同じ並び)
CELL_W, CELL_H, SPINE_W = 64, 512, 40
COLS, ROWS = 32, 2
PAPER = (238, 231, 214)
# 柄の種類ごとの番号の範囲 (scripts/props.py の BOOK_KINDS と合わせる)
BOOK_KINDS = {
    "tech": range(0, 20),     # 技術書 (A5〜B5。色はいろいろ)
    "dark": range(20, 28),    # 濃い色の上製本 (金の字)
    "manga": range(28, 44),   # 漫画・単行本 (白い背に色の題字)
    "bunko": range(44, 60),   # 文庫 (淡い色)
    "misc": range(60, 64),    # 白・クリームの教科書など
}


def _vertical_text(d, x_center, y, chars, size, font_path, color, gap=0.12):
    """縦書き: 字を上から1つずつ並べる。最後の字の下端の y を返す"""
    f = ImageFont.truetype(font_path, size)
    for ch in chars:
        d.text((x_center, y), ch, font=f, fill=color, anchor="mt")
        y += size * (1 + gap)
    return y


def _rotated_word(img, word, x_center, y_top, size, color, font_path=SANS_BOLD):
    """背の向きに 90°回した英字 (技術書の題の一部)。下端の y を返す"""
    f = ImageFont.truetype(font_path, size)
    w = int(f.getlength(word)) + 4
    tile = Image.new("RGBA", (w, size + 6), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((2, 1), word, font=f, fill=(*color, 255))
    tile = tile.rotate(-90, expand=True)
    img.paste(tile, (int(x_center - tile.width / 2), int(y_top)), tile)
    return y_top + tile.height


def _book_design(i, rng):
    """i 番目の本の柄: (地の色, 帯の色, 字の色, 種類)"""
    kind = next(k for k, r in BOOK_KINDS.items() if i in r)
    if kind == "tech":
        base = hexc(rng.choice(["#F2F1EC", "#2B4C7E", "#3C8D5A", "#C9483F", "#E8933A", "#4FA6C9", "#8A8F96",
                                "#222327", "#E9E1C8", "#6B4C93", "#F2F1EC", "#1F6F8B", "#D8D23A", "#F2F1EC"]))
    elif kind == "dark":
        base = hexc(rng.choice(["#1E2433", "#2A2A2C", "#1F3328", "#4A2326", "#262B3A", "#3A2E24"]))
    elif kind == "manga":
        base = hexc(rng.choice(["#F4F2EC", "#F4F2EC", "#F4F2EC", "#1E1E22", "#C23B3B", "#2E4F8F", "#F4F2EC"]))
    elif kind == "bunko":
        base = hexc(rng.choice(["#F2C4CE", "#CFE6B4", "#BFE0F0", "#F3EDA6", "#F4F3EE", "#E2CFF0", "#F6D3B4",
                                "#A9D8C8", "#F2C4CE", "#BFE0F0"]))
    else:
        base = hexc(rng.choice(["#F3F0E6", "#ECE6D2", "#F6F6F2", "#E6E9EC"]))
    accent = hexc(rng.choice(["#C9483F", "#2B4C7E", "#E8933A", "#3C8D5A", "#6B4C93", "#1E1E22", "#D4AF37", "#4FA6C9"]))
    ink = (24, 24, 26) if lum(base) > 140 else (244, 242, 236)
    if kind == "dark":
        ink = hexc("#D4B25A")   # 金の箔押し
    return base, accent, ink, kind


def _draw_spine(img, x0, y0, base, accent, ink, kind, rng):
    d = ImageDraw.Draw(img)
    w, h = SPINE_W, CELL_H
    d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=base)
    cx = x0 + w / 2
    if kind == "tech":
        if rng.random() < 0.6:   # 上の帯
            d.rectangle([x0, y0, x0 + w - 1, y0 + int(h * rng.uniform(0.07, 0.14))], fill=accent)
        band = int(h * rng.uniform(0.82, 0.88))
        d.rectangle([x0, y0 + band, x0 + w - 1, y0 + h - 1], fill=mix(base, accent, 0.6) if rng.random() < 0.5 else accent)
        y = y0 + int(h * 0.17)
        if rng.random() < 0.6:
            y = _rotated_word(img, rng.choice(LATIN), cx, y, 17, ink) + 6
        y = _vertical_text(d, cx, y, rng.sample(KANJI + KATA, rng.randint(4, 8)), 21, GOTHIC, ink)
        _vertical_text(d, cx, y0 + band - 70, rng.sample(KANA + KANJI, 3), 12, GOTHIC, ink)
        d.ellipse([cx - 7, y0 + band + 14, cx + 7, y0 + band + 28], outline=(244, 242, 236) if lum(accent) < 150 else (30, 30, 30), width=2)
    elif kind == "dark":
        for yy in (0.06, 0.08, 0.92, 0.94):   # 金の細い線
            d.line([x0 + 3, y0 + h * yy, x0 + w - 4, y0 + h * yy], fill=ink, width=2)
        y = _vertical_text(d, cx, y0 + int(h * 0.16), rng.sample(KANJI, rng.randint(3, 6)), 22, MINCHO, ink, gap=0.3)
        _vertical_text(d, cx, y + 30, rng.sample(KANJI, 3), 13, MINCHO, ink)
    elif kind == "manga":
        top = int(h * rng.uniform(0.3, 0.42))
        d.rectangle([x0, y0, x0 + w - 1, y0 + top], fill=accent)
        t_ink = (250, 248, 240) if lum(accent) < 150 else (20, 20, 20)
        _vertical_text(d, cx, y0 + 10, rng.sample(KATA + KANJI, rng.randint(4, 6)), 22, GOTHIC, t_ink, gap=0.05)
        _vertical_text(d, cx, y0 + top + 20, rng.sample(KANA + KANJI, 4), 13, GOTHIC, ink)
        f = ImageFont.truetype(SANS_BOLD, 22)
        d.text((cx, y0 + h - 60), str(rng.randint(1, 24)), font=f, fill=ink, anchor="mm")   # 巻数
        d.rectangle([x0 + 8, y0 + h - 30, x0 + w - 9, y0 + h - 18], fill=accent)
    elif kind == "bunko":
        if rng.random() < 0.5:
            d.rectangle([x0, y0, x0 + w - 1, y0 + int(h * 0.05)], fill=mix(base, (255, 255, 255), 0.5))
        y = _vertical_text(d, cx, y0 + int(h * 0.08), rng.sample(KANA + KANJI, rng.randint(4, 9)), 19, MINCHO, ink, gap=0.08)
        _vertical_text(d, cx, max(y + 24, y0 + int(h * 0.6)), rng.sample(KANJI, 3), 13, MINCHO, ink)
        d.rectangle([x0 + 10, y0 + h - 44, x0 + w - 11, y0 + h - 24], outline=ink, width=2)   # 出版社の印
        f = ImageFont.truetype(SANS_BOLD, 11)
        d.text((cx, y0 + h - 12), f"{rng.randint(1, 9)}-{rng.randint(1, 99)}", font=f, fill=ink, anchor="mm")
    else:
        d.rectangle([x0, y0 + int(h * 0.1), x0 + w - 1, y0 + int(h * 0.13)], fill=accent)
        _vertical_text(d, cx, y0 + int(h * 0.18), rng.sample(KANJI, rng.randint(4, 7)), 20, GOTHIC, (40, 40, 44))
    # 背の丸み: 両端を少し暗く
    a = np.asarray(img.crop((x0, y0, x0 + w, y0 + h)), dtype=np.float32)
    t = np.abs(np.linspace(-1, 1, w))
    a *= (1 - 0.18 * t ** 3)[None, :, None]
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8)), (x0, y0))


def make_books_atlas():
    img = Image.new("RGB", (CELL_W * COLS, CELL_H * ROWS), PAPER)
    d = ImageDraw.Draw(img)
    for i in range(COLS * ROWS):
        rng = random.Random(1000 + i)
        x0, y0 = (i % COLS) * CELL_W, (i // COLS) * CELL_H
        base, accent, ink, kind = _book_design(i, rng)
        _draw_spine(img, x0, y0, base, accent, ink, kind, rng)
        xs = x0 + SPINE_W
        d.rectangle([xs, y0, xs + 23, y0 + 255], fill=base)                      # 表紙 (地の色)
        d.rectangle([xs, y0 + 256, xs + 23, y0 + 383], fill=PAPER)               # 天: 紙の色 + 縁 (表紙と背の厚み)
        d.rectangle([xs, y0 + 256, xs + 23, y0 + 259], fill=base)
        d.rectangle([xs, y0 + 256, xs + 2, y0 + 383], fill=base)
        d.rectangle([xs + 21, y0 + 256, xs + 23, y0 + 383], fill=base)
        for k in range(5):                                                       # 紙の重なりの細い線
            xx = xs + 4 + k * 3 + rng.randint(0, 1)
            d.line([xx, y0 + 262, xx, y0 + 381], fill=mix(PAPER, (150, 140, 120), 0.25), width=1)
        d.rectangle([xs, y0 + 384, xs + 23, y0 + 511], fill=PAPER)               # 小口
        for k in range(7):
            xx = xs + 2 + k * 3 + rng.randint(0, 1)
            d.line([xx, y0 + 386, xx, y0 + 509], fill=mix(PAPER, (150, 140, 120), 0.3), width=1)
    img = add_noise(img, 5, 1, 0.5)
    save(img, "books_atlas.jpg", quality=92)


# ---------------------------------------------------------------- 画面
def make_screen():
    """白い管理画面 (写真では白い画面に棒グラフ・円グラフ・折れ線)。上にオレンジの帯、左に灰色の項目の列、下にタスクバー"""
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    rng = random.Random(7)
    gray, light, line = (120, 124, 130), (226, 229, 233), (236, 238, 241)
    d.rectangle([0, 0, W, 34], fill=(245, 166, 35))                          # 上の帯
    d.rounded_rectangle([14, 10, 120, 24], 4, fill=(255, 235, 200))
    for k in range(4):
        d.rounded_rectangle([W - 60 - k * 46, 11, W - 28 - k * 46, 23], 4, fill=(255, 214, 150))
    d.rectangle([0, 34, 190, H - 30], fill=(247, 248, 250))                   # 左の項目
    d.line([190, 34, 190, H - 30], fill=light, width=2)
    for k in range(14):
        y = 60 + k * 34
        if k == 2:
            d.rectangle([0, y - 10, 190, y + 16], fill=(255, 238, 214))
        d.rounded_rectangle([22, y, 22 + rng.randint(70, 140), y + 8], 4, fill=gray if k == 2 else (170, 174, 180))
    d.rounded_rectangle([220, 56, 480, 72], 6, fill=(70, 74, 80))             # 見出し
    d.rounded_rectangle([220, 82, 380, 90], 4, fill=(180, 184, 190))
    for k in range(4):                                                        # 数字のカード
        x = 220 + k * 262
        d.rounded_rectangle([x, 110, x + 246, 190], 8, outline=light, width=2, fill=(255, 255, 255))
        d.rounded_rectangle([x + 16, 126, x + 96, 134], 4, fill=(180, 184, 190))
        d.rounded_rectangle([x + 16, 148, x + 16 + rng.randint(80, 150), 172], 6, fill=(60, 64, 70))
    # 棒グラフ
    d.rounded_rectangle([220, 210, 860, 450], 8, outline=light, width=2)
    d.rounded_rectangle([238, 226, 400, 236], 4, fill=(150, 154, 160))
    colors = [(76, 175, 80), (66, 133, 244), (156, 39, 176), (255, 193, 7), (120, 124, 130)]
    for k in range(18):
        x = 270 + k * 32
        hgt = int(30 + 170 * abs(math.sin(k * 0.55 + 0.8)) * (0.4 + 0.6 * math.exp(-((k - 8) / 5) ** 2)))
        d.rectangle([x, 430 - hgt, x + 16, 430], fill=colors[k % len(colors)])
    d.line([250, 431, 840, 431], fill=light, width=2)
    # 円グラフ (ドーナツ)
    d.rounded_rectangle([880, 210, 1250, 450], 8, outline=light, width=2)
    box = [960, 240, 1170, 450 - 30 + 10]
    start = -90
    for frac, c in ((0.38, (66, 133, 244)), (0.24, (76, 175, 80)), (0.2, (255, 167, 38)), (0.18, (171, 71, 188))):
        d.pieslice(box, start, start + frac * 360, fill=c)
        start += frac * 360
    cxy = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    d.ellipse([cxy[0] - 62, cxy[1] - 62, cxy[0] + 62, cxy[1] + 62], fill=(255, 255, 255))
    # 折れ線
    d.rounded_rectangle([220, 470, 1250, 680], 8, outline=light, width=2)
    pts = [(250 + k * 25, 600 - 60 * math.exp(-k / 6) - 8 * math.sin(k * 0.9) + rng.uniform(-3, 3)) for k in range(40)]
    for y in (520, 560, 600, 640):
        d.line([240, y, 1230, y], fill=line, width=1)
    d.line(pts, fill=(110, 116, 124), width=3)
    d.rectangle([0, H - 30, W, H], fill=(232, 236, 241))                      # タスクバー
    for k in range(7):
        x = W / 2 - 120 + k * 36
        d.rounded_rectangle([x, H - 23, x + 18, H - 7], 3, fill=[(0, 120, 215), (255, 185, 0), (90, 90, 96)][k % 3])
    save(img, "screen_main.png")


# ---------------------------------------------------------------- 時計
def make_clock_face():
    """文字盤 (写真: 白地に黒い数字 1〜12、分の点、下に温度計と湿度計の小さな目盛り、その下に横線)。画像の外接円 = 文字盤の縁"""
    S = 2048   # 2 倍で描いて縮める (字のふちをなめらかに)
    img = Image.new("RGB", (S, S), (246, 245, 241))
    d = ImageDraw.Draw(img)
    c, R = S / 2, S / 2
    ink = (26, 26, 28)
    for k in range(60):   # 分の点 (時の所は大きく)
        a = 2 * math.pi * k / 60
        r = R * 0.93
        x, y = c + r * math.sin(a), c - r * math.cos(a)
        s = R * (0.012 if k % 5 == 0 else 0.007)
        d.ellipse([x - s, y - s, x + s, y + s], fill=ink)
    f = ImageFont.truetype(SERIF, int(R * 0.2))
    for k in range(1, 13):
        a = 2 * math.pi * k / 12
        r = R * 0.76
        d.text((c + r * math.sin(a), c - r * math.cos(a)), str(k), font=f, fill=ink, anchor="mm")
    d.rounded_rectangle([c - R * 0.12, c - R * 0.44, c + R * 0.12, c - R * 0.40], 6, fill=(90, 90, 94))   # 銘柄 (読めない帯)
    for sx, label in ((-1, "°C"), (1, "%")):   # 温度計・湿度計
        ox, oy, r = c + sx * R * 0.27, c + R * 0.12, R * 0.15
        for k in range(21):
            a = math.radians(-120 + 240 * k / 20)
            l = 0.25 if k % 5 == 0 else 0.13
            d.line([ox + r * math.sin(a), oy - r * math.cos(a), ox + r * (1 - l) * math.sin(a), oy - r * (1 - l) * math.cos(a)],
                   fill=(110, 110, 114), width=4 if k % 5 == 0 else 2)
        a = math.radians(-35 if sx < 0 else 25)
        d.line([ox, oy, ox + r * 0.85 * math.sin(a), oy - r * 0.85 * math.cos(a)], fill=ink, width=6)
        d.ellipse([ox - 10, oy - 10, ox + 10, oy + 10], fill=ink)
        d.text((ox, oy + r * 0.45), label, font=ImageFont.truetype(SANS_BOLD, int(R * 0.05)), fill=(110, 110, 114), anchor="mm")
    d.line([c - R * 0.16, c + R * 0.5, c + R * 0.16, c + R * 0.5], fill=(120, 120, 124), width=5)
    img = img.resize((1024, 1024), Image.LANCZOS)
    img = add_noise(img, 2, 3)
    save(img, "clock_face.jpg", quality=92)


# ---------------------------------------------------------------- 絵
def _gradient(size, stops, axis=1):
    """stops = [(位置 0〜1, (r, g, b)), ...] の縦 (axis=1) のグラデーション"""
    w, h = size
    t = np.linspace(0, 1, h if axis == 1 else w)
    out = np.zeros((len(t), 3))
    for i in range(3):
        out[:, i] = np.interp(t, [p for p, _ in stops], [c[i] for _, c in stops])
    if axis == 1:
        arr = np.repeat(out[:, None, :], w, axis=1)
    else:
        arr = np.repeat(out[None, :, :], h, axis=0)
    return arr


def make_sunset():
    """夕焼けの海 (写真: 紫と青の空、赤とオレンジの夕日、暗い海、左に椰子の木の影)。油絵のような筆のむら"""
    W, H = 1024, 800
    rng = np.random.default_rng(11)
    arr = _gradient((W, H), [(0, (52, 60, 120)), (0.3, (120, 70, 130)), (0.5, (225, 110, 70)), (0.58, (250, 175, 90)),
                             (0.6, (70, 60, 90)), (0.8, (30, 40, 80)), (1, (18, 22, 46))])
    img = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(40):   # 雲 (横長の筆の跡)
        x, y = rng.uniform(-100, W), rng.uniform(40, H * 0.52)
        w, h = rng.uniform(120, 380), rng.uniform(14, 40)
        c = tuple(int(v) for v in rng.choice([(255, 150, 90), (200, 90, 120), (90, 80, 150), (255, 200, 140)])) + (int(rng.uniform(60, 140)),)
        d.ellipse([x, y, x + w, y + h], fill=c)
    d.ellipse([W * 0.58, H * 0.52, W * 0.66, H * 0.6], fill=(255, 220, 150, 230))   # 夕日
    for _ in range(90):   # 海に映る光
        y = rng.uniform(H * 0.61, H * 0.95)
        x = W * 0.62 + rng.normal(0, 30 + (y - H * 0.6) * 0.35)
        d.line([x - rng.uniform(10, 40), y, x + rng.uniform(10, 40), y], fill=(255, 170, 90, int(rng.uniform(80, 200))), width=3)
    img = img.filter(ImageFilter.GaussianBlur(2.2))
    d = ImageDraw.Draw(img, "RGBA")
    dark = (14, 14, 24, 255)
    for px, lean, hgt in ((90, -60, 540), (190, 40, 450)):   # 椰子の木の影: 少し曲がった幹 + 垂れ下がる葉
        trunk = [(px + lean * (t ** 1.6), H - hgt * t) for t in np.linspace(0, 1, 12)]
        for k in range(len(trunk) - 1):
            d.line([trunk[k], trunk[k + 1]], fill=dark, width=int(16 - 7 * k / len(trunk)))
        top = trunk[-1]
        for k in range(11):   # 葉: 上へ伸びてから垂れる弧。軸に沿って小葉を斜め下へ
            a = math.radians(-180 + k * 18 + rng.uniform(-6, 6))
            length = rng.uniform(120, 170)
            rib = [(top[0] + length * t * math.cos(a), top[1] - length * t * 0.45 * math.sin(-a) * (1 - t) - 30 * t
                    + length * 0.9 * t * t) for t in np.linspace(0, 1, 14)]
            d.line(rib, fill=dark, width=4)
            for j in range(2, len(rib) - 1):
                (x0, y0), (x1, y1) = rib[j - 1], rib[j]
                ang = math.atan2(y1 - y0, x1 - x0)
                leaf = 28 * (1 - j / len(rib)) + 8
                for s in (-1, 1):
                    b = ang + s * 1.1 + 0.5
                    d.line([(x1, y1), (x1 + leaf * math.cos(b), y1 + leaf * abs(math.sin(b)))], fill=dark, width=3)
    d.rectangle([0, H * 0.9, W, H], fill=(10, 12, 22, 255))
    img = add_noise(img.filter(ImageFilter.GaussianBlur(0.8)), 7, 12, 1.2)
    save(img, "print_sunset.jpg")


def make_moon():
    """月夜の海 (写真: 濃い青の夜空に大きな月、跳ねるイルカの影、波のしぶき)"""
    W, H = 800, 1000
    rng = np.random.default_rng(21)
    arr = _gradient((W, H), [(0, (6, 14, 50)), (0.45, (20, 50, 120)), (0.7, (14, 40, 100)), (1, (4, 10, 34))])
    img = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")
    mx, my, mr = W * 0.5, H * 0.38, W * 0.27
    for k in range(10, 0, -1):   # 月のまわりの光
        r = mr * (1 + k * 0.08)
        d.ellipse([mx - r, my - r, mx + r, my + r], fill=(120, 160, 230, 10))
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(222, 230, 240, 255))
    for _ in range(14):   # 月の模様
        x, y, r = mx + rng.normal(0, mr * 0.4), my + rng.normal(0, mr * 0.4), rng.uniform(12, 40)
        if math.hypot(x - mx, y - my) + r < mr:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(190, 200, 215, 120))
    for _ in range(120):   # 星
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.55)
        s = rng.uniform(0.8, 2.2)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(230, 235, 255, int(rng.uniform(120, 255))))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    d = ImageDraw.Draw(img, "RGBA")
    # イルカ: 月の前を弧を描いて跳ぶ影。体の中心線を弧に沿わせ、太さ (口先は細く、胴は太く、尾の付け根で細い) を両側に付ける
    dark = (8, 14, 34, 255)
    n = 40
    length = mr * 2.3
    arc_r = mr * 1.25
    c0 = (mx - mr * 0.1, my + mr * 1.05)            # 弧の中心 (月の下)
    a0, a1 = math.radians(150), math.radians(30)    # 口先 (左) → 尾 (右)。上へ跳ねる弧

    def center(t):
        a = a0 + (a1 - a0) * t
        return c0[0] + arc_r * math.cos(a), c0[1] - arc_r * math.sin(a), a

    def thickness(t):   # 中心線からの半分の太さ (体長に対する割合)
        if t < 0.06:
            return 0.02 + 0.25 * t
        if t < 0.12:
            return 0.035 + 0.9 * (t - 0.06)
        if t < 0.85:
            return 0.09 * math.sin(math.pi * min(1, (t - 0.12) / 0.73 * 0.85 + 0.15)) + 0.02
        return 0.025
    upper, lower = [], []
    for k in range(n + 1):
        t = k / n
        x, y, a = center(t)
        nx, ny = math.cos(a), -math.sin(a)          # 弧の外向き = 背中側
        th = thickness(t) * length
        upper.append((x + nx * th, y + ny * th))
        lower.append((x - nx * th * 0.8, y - ny * th * 0.8))
    d.polygon(upper + lower[::-1], fill=dark)
    x, y, a = center(0.42)                           # 背びれ (背中側に後ろへ倒れた三角)
    nx, ny = math.cos(a), -math.sin(a)
    tx, ty = math.sin(a), math.cos(a)               # 尾の向き
    base = 0.09 * length
    d.polygon([(x + nx * base - tx * 30, y + ny * base - ty * 30), (x + nx * base + tx * 30, y + ny * base + ty * 30),
               (x + nx * (base + 70) + tx * 55, y + ny * (base + 70) + ty * 55)], fill=dark)
    x, y, a = center(0.25)                           # 胸びれ (腹側)
    nx, ny = math.cos(a), -math.sin(a)
    d.polygon([(x - nx * 30, y - ny * 30), (x - nx * 30 + tx * 40, y - ny * 30 + ty * 40),
               (x - nx * 85 + tx * 50, y - ny * 85 + ty * 50)], fill=dark)
    x, y, a = center(1.0)                            # 尾びれ (体と直角に2枚)
    nx, ny = math.cos(a), -math.sin(a)
    tx, ty = math.sin(a), math.cos(a)
    for s in (1, -1):
        d.polygon([(x - tx * 10, y - ty * 10), (x + nx * s * 60 + tx * 30, y + ny * s * 60 + ty * 30),
                   (x + nx * s * 20 + tx * 20, y + ny * s * 20 + ty * 20)], fill=dark)
    for _ in range(160):   # しぶきと波
        x, y = rng.normal(W * 0.36, 70), rng.uniform(H * 0.66, H * 0.8)
        s = rng.uniform(1, 4)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(200, 220, 255, int(rng.uniform(80, 220))))
    for k in range(30):
        y = H * 0.78 + k * 7
        d.line([0, y, W, y + rng.uniform(-6, 6)], fill=(60, 110, 190, 60), width=3)
    save(add_noise(img, 5, 22), "print_moon.jpg")


def make_love_print():
    """青紫の絵 (写真: 本棚の扉に飾った、光の中に人の影がある青紫の絵)。人物は描かず、光の模様だけ"""
    W, H = 600, 760
    rng = np.random.default_rng(31)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot((xx - W * 0.5) / W, (yy - H * 0.42) / H)
    t = np.clip(r / 0.7, 0, 1)[..., None]
    arr = (1 - t) * np.array([200, 190, 245]) + t * np.array([40, 50, 150])
    img = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(18):   # 光の筋
        a = math.radians(k * 20 + rng.uniform(-6, 6))
        d.line([W * 0.5, H * 0.42, W * 0.5 + 600 * math.cos(a), H * 0.42 + 600 * math.sin(a)], fill=(255, 255, 255, 28), width=18)
    for _ in range(80):
        x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1, 3.5)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 255, 255, int(rng.uniform(90, 230))))
    f = ImageFont.truetype(SERIF, 64)
    d.text((W / 2, H * 0.14), "LOVE", font=f, fill=(250, 248, 255, 230), anchor="mm")
    img = img.filter(ImageFilter.GaussianBlur(1.0))
    ImageDraw.Draw(img).rectangle([0, 0, W - 1, H - 1], outline=(235, 235, 245), width=10)   # 白い縁
    save(add_noise(img, 4, 32), "print_love.jpg")


def make_book_box():
    """本の箱 (写真: 紺と灰色の写真の表紙に、縦書きの白い題と赤い帯)"""
    W, H = 400, 560
    arr = _gradient((W, H), [(0, (90, 110, 140)), (0.5, (30, 40, 60)), (1, (15, 20, 30))])
    img = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(img)
    rng = random.Random(41)
    d.rectangle([W * 0.55, 30, W - 30, H * 0.68], fill=(190, 40, 40))
    _vertical_text(d, W * 0.73, 50, rng.sample(KANJI, 4), 46, MINCHO, (255, 255, 255))
    d.rectangle([0, H * 0.84, W, H], fill=(214, 60, 40))
    _vertical_text(d, W * 0.2, 60, rng.sample(KANJI, 3), 40, GOTHIC, (245, 245, 245))
    d.rectangle([20, H * 0.87, W - 20, H * 0.87 + 18], fill=(255, 240, 230))
    save(add_noise(img, 5, 42), "book_box.jpg")


def make_certificate():
    """賞状 (写真: 白い台紙に飾り枠の賞状。文字は灰色の線にする)"""
    W, H = 600, 840
    img = Image.new("RGB", (W, H), (250, 249, 244))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, W - 41, H - 41], fill=(244, 240, 228))
    for k, c in enumerate([(205, 180, 120), (230, 214, 170), (205, 180, 120)]):   # 飾り枠
        d.rectangle([56 + k * 10, 56 + k * 10, W - 57 - k * 10, H - 57 - k * 10], outline=c, width=5)
    rng = random.Random(51)
    d.rounded_rectangle([W / 2 - 150, 150, W / 2 + 150, 182], 6, fill=(80, 80, 84))   # 題
    for k in range(9):   # 本文
        y = 260 + k * 40
        d.rounded_rectangle([110, y, W - 110 - rng.randint(0, 120), y + 12], 5, fill=(150, 150, 156))
    d.rounded_rectangle([W - 260, H - 190, W - 110, H - 176], 5, fill=(140, 140, 146))
    d.ellipse([W - 160, H - 165, W - 110, H - 115], outline=(200, 70, 60), width=4)   # 印
    save(add_noise(img, 3, 52), "certificate.jpg")


def make_picture_book():
    """絵本 (写真: 茶色の表紙に、オレンジの丸い大きな題字)"""
    W, H = 600, 720
    arr = _gradient((W, H), [(0, (105, 64, 44)), (1, (78, 46, 32))])
    img = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(img)
    rng = random.Random(61)
    f = ImageFont.truetype(GOTHIC, 70)
    title = "ねむれない"          # 架空の題 (でたらめな仮名だと、近づいて読んだときに変)
    x = W / 2 - 78 * (len(title) - 1) / 2
    for ch in title:
        d.text((x, 285 + rng.randint(-10, 10)), ch, font=f, fill=(238, 140, 60), anchor="mm")
        x += 78
    f2 = ImageFont.truetype(GOTHIC, 110)
    d.text((W / 2, 410), "くま", font=f2, fill=(245, 160, 70), anchor="mm")
    d.text((W / 2, 600), "のよる", font=ImageFont.truetype(GOTHIC, 80), fill=(240, 150, 64), anchor="mm")
    d.rounded_rectangle([60, 70, W - 60, 92], 8, fill=(200, 170, 140))
    save(add_noise(img, 5, 62), "picture_book.jpg")


def make_stripes():
    """細いボーダー (白地に薄い灰色の線。1枚の実寸は scripts/furniture_sofa.py の STRIPE_SIZE)"""
    S = 512
    a = np.full((S, S, 3), (242, 242, 240), dtype=np.float32)
    period = S / 10                      # 1枚に 10 本
    y = np.arange(S)
    band = ((y % period) < period * 0.42)
    a[band] = (186, 190, 194)
    img = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    save(add_noise(img, 6, 71, 0.7), "stripe_fabric.jpg")


def make_baskets():
    """かごの柄3つ (テレビ台の小物。scripts/furniture_tv_stand.py)"""
    # 編みかご: 64px の升ごとに、帯3本の向きを縦・横と互い違いにする (平織り風)。帯の縁は影で暗く
    S, B = 512, 64
    a = np.zeros((S, S, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:S, 0:S]
    vertical = ((xx // B + yy // B) % 2) == 0
    t = np.where(vertical, xx % (B / 3), yy % (B / 3)) / (B / 3)          # 帯の中の位置 0〜1
    along = np.where(vertical, yy % B, xx % B) / B                         # 帯に沿った位置 (升の端で影)
    shade = 0.62 + 0.38 * np.sin(np.pi * t) ** 0.5
    shade *= 0.8 + 0.2 * np.sin(np.pi * along) ** 0.3
    base = np.array((214, 211, 204), dtype=np.float32)
    a[:] = base * shade[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    save(add_noise(img, 7, 81, 0.6), "basket_woven.jpg")
    # 白黒の市松 (8 x 8 升)。升の中に細い編み目
    S, n = 256, 8
    c = S // n
    a = np.where((((xx[:S, :S] // c) + (yy[:S, :S] // c)) % 2 == 0)[..., None],
                 np.array((236, 235, 230), np.float32), np.array((28, 28, 30), np.float32))
    weave = 0.88 + 0.12 * np.sin(np.pi * ((xx[:S, :S] + yy[:S, :S]) % 8) / 8)
    img = Image.fromarray((a * weave[..., None]).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    save(add_noise(img, 6, 82, 0.6), "basket_check.jpg")
    # 白い樹脂のかご: 32px おきに、角の丸い横長の穴 (20 x 12px)
    img = Image.new("RGB", (256, 256), (240, 240, 237))
    d = ImageDraw.Draw(img)
    for gy in range(0, 256, 32):
        for gx in range(0, 256, 32):
            d.rounded_rectangle([gx + 6, gy + 10, gx + 26, gy + 22], 5, fill=(96, 98, 100))
    save(add_noise(img.filter(ImageFilter.GaussianBlur(0.8)), 3, 83), "basket_mesh.jpg")


# ---------------------------------------------------------------- ティッシュの箱 (と、tools/make_boxes.py が使う紙の地・インク)
# 箱の面ごとに、1枚の画像の中の長方形を貼る (scripts/props.py の atlas_box_uvs)。面の並び (画素) は貼る側の ATLAS と同じにする
NAVY = (30, 56, 120)
TISSUE_PPM = 1.6             # ティッシュの箱 (24 x 11.5 x 8.5cm)
TISSUE_ATLAS = dict(front=(0, 0, 384, 136), side=(0, 144, 184, 280), top=(0, 288, 384, 472), plain=(192, 144, 384, 280))


def _paper(w, h, color, seed, grain=0.05, mottle=0.035, flute=0.0, ppm=1.6):
    """紙の地 ((h, w, 3) の float): 大きな色むら + 細かいざらつき。flute > 0 で段ボールの中芯の段 (縦の筋、8.5mm おき)"""
    rng = np.random.default_rng(seed)
    low = rng.standard_normal((h // 48 + 2, w // 48 + 2)).astype(np.float32)
    low = np.asarray(Image.fromarray(low).resize((w, h), Image.BICUBIC), np.float32)
    shade = 1 + mottle * low + noise_layer((w, h), grain, seed, 0.6)
    if flute:
        shade *= 1 + flute * np.sin(2 * np.pi * np.arange(w) / (8.5 * ppm))[None, :]
    return np.array(color, np.float32) * shade[..., None]


def _face(w_mm, h_mm, ppm, ss=3):
    """印刷する面1つ: 透明な RGBA の画像 (ss 倍の大きさで描いて、あとで縮める) と描く道具、1mm の画素数"""
    img = Image.new("RGBA", (round(w_mm * ppm * ss), round(h_mm * ppm * ss)), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img), ppm * ss


def _apply_ink(base, ink, rect, opacity=0.93):
    """base (画像全体の地) の rect の範囲に、インクの画像 ink を重ねる。インクにも地のむらを残す"""
    x0, y0, x1, y1 = rect
    a = np.asarray(ink.convert("RGBa").resize((x1 - x0, y1 - y0), Image.LANCZOS).convert("RGBA"), np.float32)
    alpha = a[..., 3:] / 255 * opacity
    region = base[y0:y1, x0:x1]
    shade = region.mean(axis=2, keepdims=True) / region.mean()
    base[y0:y1, x0:x1] = region * (1 - alpha) + a[..., :3] * shade * alpha


def _font(path, mm, u):
    return ImageFont.truetype(path, max(4, round(mm * u)))


def make_tissue_box():
    """ティッシュの箱 (写真 reference/IMG_1100: 白い箱に紺の帯と細い字。取り出し口のフィルム)。商品名は書かない"""
    W, H = 512, 512
    base = _paper(W, H, (244, 244, 241), 95, grain=0.025, mottle=0.012)
    script = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
    sky = (111, 168, 220, 255)
    for part, (w, h) in (("front", (240, 85)), ("side", (115, 85))):
        img, d, u = _face(w, h, TISSUE_PPM)
        d.rectangle([0, 72 * u, w * u, h * u], fill=(*NAVY, 255))                 # 下の紺の帯
        d.rectangle([0, 69.5 * u, w * u, 70.5 * u], fill=sky)
        d.text((w / 2 * u, 40 * u), "Premium Soft", font=_font(script, 10 if part == "front" else 7, u), fill=(*NAVY, 255), anchor="mm")
        d.text((w / 2 * u, 53 * u), "200 SHEETS", font=_font(SANS_BOLD, 3.2, u), fill=(150, 160, 178, 255), anchor="mm")
        if part == "front":   # 葉の飾り
            for k in range(5):
                cx, cy = 40 + k * 7, 34 - 6 * math.sin(k / 4 * math.pi)
                d.ellipse([(cx - 2.6) * u, (cy - 1.3) * u, (cx + 2.6) * u, (cy + 1.3) * u], fill=sky)
        _apply_ink(base, img, TISSUE_ATLAS[part])
    img, d, u = _face(240, 115, TISSUE_PPM)
    for y in (6, 103):                                                              # 長い辺に沿った水色の線
        d.rectangle([0, y * u, 240 * u, (y + 6) * u], fill=sky)
    d.rounded_rectangle([40 * u, 42 * u, 200 * u, 73 * u], radius=15 * u, fill=(226, 230, 234, 255),
                        outline=(196, 202, 210, 255), width=max(1, round(0.6 * u)))   # 取り出し口のフィルム
    d.line([(55 * u, 57.5 * u), (185 * u, 57.5 * u)], fill=(150, 156, 166, 255), width=max(1, round(0.6 * u)))
    _apply_ink(base, img, TISSUE_ATLAS["top"])
    save(Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)), "tissue_box.jpg", quality=90)


# ---------------------------------------------------------------- ラグ
RUG_W, RUG_D, RUG_CORNER = 1.40, 0.90, 0.08   # ラグの大きさと角の丸み (m)。scripts/layout.py (rug) と scripts/furniture_rug.py の CORNER_R


def _dog(s, rng):
    """座った茶色の犬 (トイプードル風。巻き毛は円の集まり)。s x s の RGBA"""
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fur = mix((150, 100, 62), (176, 128, 84), rng.random())
    dark, light = mix(fur, (60, 36, 20), 0.35), mix(fur, (240, 220, 196), 0.35)

    def blob(cx, cy, r, color, n=9):
        d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=color)
        for k in range(n):
            a = 2 * math.pi * k / n + rng.uniform(0, 0.5)
            rr, px, py = r * rng.uniform(0.35, 0.5), cx + r * 0.85 * math.cos(a), cy + r * 0.85 * math.sin(a)
            d.ellipse([(px - rr) * s, (py - rr) * s, (px + rr) * s, (py + rr) * s], fill=color)

    blob(0.72, 0.64, 0.06, fur, 5)           # しっぽ
    blob(0.5, 0.65, 0.2, fur)                # 体
    blob(0.42, 0.85, 0.06, fur, 5)           # 前足
    blob(0.58, 0.85, 0.06, fur, 5)
    blob(0.5, 0.36, 0.16, fur)               # 頭
    blob(0.34, 0.43, 0.075, dark, 6)         # 垂れた耳
    blob(0.66, 0.43, 0.075, dark, 6)
    d.ellipse([0.42 * s, 0.39 * s, 0.58 * s, 0.5 * s], fill=light)   # 口のまわり
    for ex in (0.44, 0.56):
        d.ellipse([(ex - 0.017) * s, 0.315 * s, (ex + 0.017) * s, 0.35 * s], fill=(34, 24, 18))
    d.ellipse([0.475 * s, 0.395 * s, 0.525 * s, 0.43 * s], fill=(44, 30, 24))
    return img


def _cat(s, rng):
    """座った灰色の猫 (しま模様、胸と口のまわりが白)。s x s の RGBA"""
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gray = mix((146, 148, 154), (176, 172, 168), rng.random())
    dark, white = mix(gray, (50, 50, 56), 0.4), (238, 236, 232)
    d.arc([0.56 * s, 0.56 * s, 0.94 * s, 0.94 * s], 190, 340, fill=gray, width=max(2, round(0.055 * s)))   # しっぽ
    d.ellipse([0.24 * s, 0.48 * s, 0.76 * s, 0.9 * s], fill=gray)                                           # 体
    d.ellipse([0.38 * s, 0.56 * s, 0.62 * s, 0.86 * s], fill=white)                                         # 胸
    for sx in (-1, 1):
        d.polygon([((0.5 + sx * 0.17) * s, 0.33 * s), ((0.5 + sx * 0.15) * s, 0.12 * s), ((0.5 + sx * 0.02) * s, 0.24 * s)], fill=gray)   # 耳
        d.polygon([((0.5 + sx * 0.145) * s, 0.27 * s), ((0.5 + sx * 0.14) * s, 0.17 * s), ((0.5 + sx * 0.07) * s, 0.235 * s)], fill=(214, 172, 166))
    d.ellipse([0.31 * s, 0.2 * s, 0.69 * s, 0.53 * s], fill=gray)                                           # 頭
    d.ellipse([0.4 * s, 0.37 * s, 0.6 * s, 0.52 * s], fill=white)                                           # 口のまわり
    for k in (-1, 0, 1):                                                                                    # 額と体のしま
        d.line([((0.5 + k * 0.05) * s, 0.22 * s), ((0.5 + k * 0.045) * s, 0.29 * s)], fill=dark, width=max(1, round(0.018 * s)))
        d.arc([(0.28 + 0.0) * s, (0.58 + k * 0.08) * s, 0.4 * s, (0.66 + k * 0.08) * s], 120, 240, fill=dark, width=max(1, round(0.016 * s)))
        d.arc([0.6 * s, (0.58 + k * 0.08) * s, 0.72 * s, (0.66 + k * 0.08) * s], -60, 60, fill=dark, width=max(1, round(0.016 * s)))
    for ex in (0.43, 0.57):
        d.ellipse([(ex - 0.02) * s, 0.34 * s, (ex + 0.02) * s, 0.38 * s], fill=(52, 60, 44))
    d.polygon([(0.485 * s, 0.415 * s), (0.515 * s, 0.415 * s), (0.5 * s, 0.435 * s)], fill=(196, 128, 124))
    return img


def _paw(s, color):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0.28 * s, 0.45 * s, 0.72 * s, 0.85 * s], fill=color)
    for cx, cy in ((0.2, 0.36), (0.38, 0.2), (0.62, 0.2), (0.8, 0.36)):
        d.ellipse([(cx - 0.1) * s, (cy - 0.12) * s, (cx + 0.1) * s, (cy + 0.12) * s], fill=color)
    return img


def make_rug():
    """ラグの柄 (写真 reference/IMG_1100: ベージュのキルトの地に、茶色の犬・灰色の猫の絵と筆記体の字。縁は薄茶の縁取り)。
    ラグ全体で1枚 (1m = 1280px、画像の上 = ラグのローカル +Y = ソファーから見て奥)。角は丸い"""
    ppm = 1.28                                    # 1mm の画素数
    W, H = round(RUG_W * 1000 * ppm), round(RUG_D * 1000 * ppm)
    base = _paper(W, H, (229, 221, 206), 101, grain=0.03, mottle=0.012)
    # 布の目: 綿の見本の明るさのむら (0.54m で1枚) を薄く
    cloth = Image.open(os.path.join(TEX, "canvas_light_1k.jpg")).convert("L").resize((round(540 * ppm),) * 2, Image.LANCZOS)
    c = np.asarray(cloth, np.float32)
    c = np.tile(c, (H // c.shape[0] + 1, W // c.shape[1] + 1))[:H, :W]
    base *= (1 + 0.35 * (c / c.mean() - 1))[..., None]
    # 縫い込んだ柄を描く (3倍の大きさで描いて縮める)
    rng = random.Random(102)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cols, rows = 5, 3
    spots = []
    for r in range(rows):
        for k in range(cols):
            x = (k + 0.5 + rng.uniform(-0.2, 0.2) + (0.25 if r % 2 else -0.15)) / cols * W
            y = (r + 0.5 + rng.uniform(-0.15, 0.15)) / rows * H
            spots.append((x, y))
    for i, (x, y) in enumerate(spots):
        size = round(rng.uniform(130, 170) * ppm)
        art = (_dog if (i + i // cols) % 3 else _cat)(size * 3, rng).resize((size, size), Image.LANCZOS)
        if rng.random() < 0.5:
            art = art.transpose(Image.FLIP_LEFT_RIGHT)
        art = art.rotate(rng.uniform(-25, 25), resample=Image.BICUBIC, expand=True)
        layer.alpha_composite(art, (int(x - art.width / 2), int(y - art.height / 2)))
    script = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", round(22 * ppm))
    words = ["happy days", "my sweet pets", "with love", "best friends", "good dog", "sleepy cat", "lovely", "sunny walk"]
    for i, word in enumerate(words):   # 筆記体の字と足あと: 絵の間に
        x, y = (spots[i][0] + spots[(i + 1) % len(spots)][0]) / 2, (spots[i][1] + spots[i + cols if i + cols < len(spots) else i][1]) / 2 + 60 * ppm
        tile = Image.new("RGBA", (round(220 * ppm), round(40 * ppm)), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((tile.width / 2, tile.height / 2), word, font=script, fill=(168, 146, 124, 255), anchor="mm")
        tile = tile.rotate(rng.uniform(-12, 12), resample=Image.BICUBIC, expand=True)
        layer.alpha_composite(tile, (int(x - tile.width / 2) % (W - tile.width), int(y - tile.height / 2) % (H - tile.height)))
    for _ in range(14):
        p = _paw(round(28 * ppm) * 3, (200, 176, 148, 255)).resize((round(28 * ppm),) * 2, Image.LANCZOS)
        p = p.rotate(rng.uniform(0, 360), resample=Image.BICUBIC, expand=True)
        layer.alpha_composite(p, (rng.randint(60, W - 60 - p.width), rng.randint(60, H - 60 - p.height)))
    a = np.asarray(layer, np.float32)
    alpha = a[..., 3:] / 255 * 0.9
    shade = base.mean(axis=2, keepdims=True) / base.mean()
    base = base * (1 - alpha) + a[..., :3] * shade * alpha
    # キルト: 波打つ縫い目 (5cm おき) と、その間のふくらみ
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32) / ppm   # mm
    t = ((yy - 9 * np.sin(2 * np.pi * xx / 150) - 4 * np.sin(2 * np.pi * xx / 61 + 1.3)) / 50) % 1.0
    dist = np.minimum(t, 1 - t) * 50                       # 縫い目からの距離 (mm)
    quilt = 0.975 + 0.035 * np.sin(np.pi * np.minimum(dist / 25, 1)) ** 0.6 - 0.05 * np.exp(-(dist / 0.7) ** 2)
    base *= quilt[..., None]
    # 縁取り (幅 14mm、薄茶) と内側の縫い目。角は丸い
    band, r = 14 * ppm, RUG_CORNER * 1000 * ppm
    px, py = np.minimum(xx * ppm, W - xx * ppm), np.minimum(yy * ppm, H - yy * ppm)   # 縁からの距離 (px)
    cx, cy = np.maximum(r - px, 0), np.maximum(r - py, 0)
    edge = np.where((cx > 0) & (cy > 0), r - np.hypot(cx, cy), np.minimum(px, py))   # 丸い角を考えた、縁からの距離
    binding = np.array((196, 172, 142), np.float32) * (1 + noise_layer((W, H), 0.04, 103, 0.8))[..., None]
    k = np.clip((band - edge) / 1.5 + 0.5, 0, 1)[..., None]
    base = base * (1 - k) + binding * k
    stitch = (np.abs(edge - band - 4 * ppm) < 0.6 * ppm) & ((xx + yy).astype(int) % 6 < 4)
    base[stitch] *= 0.86
    save(Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)), "rug_print.jpg", quality=88)


if __name__ == "__main__":
    make_books_atlas()
    make_screen()
    make_clock_face()
    make_sunset()
    make_moon()
    make_love_print()
    make_book_box()
    make_certificate()
    make_picture_book()
    make_stripes()
    make_baskets()
    make_tissue_box()
    make_rug()
