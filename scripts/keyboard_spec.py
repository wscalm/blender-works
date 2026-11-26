"""Logicool G813 (日本語配列) のキーの並び (bpy 非依存)。scripts/furniture_keyboard.py (形) と tools/make_desk_items.py (光る字の画像) が読む。

寸法は公式の上から見た写真 (G913 の日本語配列。キーの並びは G813 と同じ) から測った mm。
座標: x = 左端 (座る人から見て左) から、y = 奥の端から (どちらも mm)。キーはその中心と大きさ (w x h)。
"""
W, D, H = 475.0, 150.0, 22.0    # 外寸 (幅 x 奥行 x 高さ)
U = 19.05                       # キーの間隔 (1u)
GAP = 1.8                       # キーとキーのすき間 (1u のキーの外寸 = U - GAP)
X_MAIN = 33.1                   # メインのキー (ESC・半角/全角・TAB…) の左端
ROW = dict(m=14.0, f=37.1, n=61.3, q=80.3, a=99.5, z=118.5, b=137.6)   # 行の中心 (奥の端から)。m = M1〜MR の丸いボタンの行
NAV_X = (335.1, 354.1, 373.0)                 # 矢印・INS などの列の中心
PAD_X = (398.9, 417.9, 437.1, 456.2)          # テンキーの列の中心
G_X = 18.7                                    # G1〜G5 の列の中心
ROUND = 13.1                                  # 丸いボタンの直径
ROLLER = dict(x0=394.1, x1=461.1, y1=21.5, r0=402.9, r1=451.7, y=6.5, d=11.0)   # 音量のローラーの凹み (奥の端から) とローラー
G_LOGO = dict(x=18.6, y=13.9, size=15.6)      # 左上の G のロゴ (光る)
LOCK_LEDS = [("CAPS LOCK", 270.6, False), ("NUM LOCK", 290.0, True)]   # 状態の表示 (字は y 10.2、ランプは y 16.1)。NUM LOCK だけ点いている

# メインの行: (幅 u, 字, 下の字) / 数 = すき間 (u)。日本語配列のキーの字は写真のまま (かなは無い)
_MAIN = {
    "f": [(1, "ESC"), 2 / 3] + [(1, f"F{i}") for i in range(1, 5)] + [2 / 3] + [(1, f"F{i}") for i in range(5, 9)]
         + [2 / 3] + [(1, f"F{i}") for i in range(9, 13)],
    "n": [(1, "半角/\n全角"), (1, "1", "!"), (1, "2", '"'), (1, "3", "#"), (1, "4", "$"), (1, "5", "%"), (1, "6", "&"),
          (1, "7", "'"), (1, "8", "("), (1, "9", ")"), (1, "0"), (1, "-", "="), (1, "^", "~"), (1, "¥", "|"), (1, "BS")],
    "q": [(1.5, "TAB")] + [(1, c) for c in "QWERTYUIOP"] + [(1, "@", "`"), (1, "[", "{"), (1.5, "ENTER")],
    "a": [(1.75, "CAPS")] + [(1, c) for c in "ASDFGHJKL"] + [(1, ";", "+"), (1, ":", "*"), (1, "]", "}"), (1.25, "ENTER2")],
    "z": [(2.25, "SHIFT")] + [(1, c) for c in "ZXCVBNM"] + [(1, ",", "<"), (1, ".", ">"), (1, "/", "?"), (1, "\\", "_"), (1.75, "SHIFT")],
    "b": [(1.5, "CTRL"), (1.25, "WIN"), (1.25, "ALT"), (1, "無変換"), (3.75, "SPACE"), (1, "変換"), (1.25, "カタカナ\nひらがな"),
          (1.25, "ALT"), (1.25, "MENU"), (1.5, "CTRL")],
}
# 矢印・INS など (列 0〜2) とテンキー (列 0〜3)。(行, 列, 字, 下の字, 幅 u, 高さ u)
_NAV = [("f", 0, "PRTSC"), ("f", 1, "SCRLK"), ("f", 2, "PAUSE"), ("n", 0, "INS"), ("n", 1, "HOME"), ("n", 2, "PG UP"),
        ("q", 0, "DEL"), ("q", 1, "END"), ("q", 2, "PG DN"), ("z", 1, "↑"), ("b", 0, "←"), ("b", 1, "↓"), ("b", 2, "→")]
_PAD = [("n", 0, "NUM"), ("n", 1, "/"), ("n", 2, "*"), ("n", 3, "-"),
        ("q", 0, "7", "HOME"), ("q", 1, "8", "↑"), ("q", 2, "9", "PG UP"), ("q", 3, "+", "", 1, 2),
        ("a", 0, "4", "←"), ("a", 1, "5"), ("a", 2, "6", "→"),
        ("z", 0, "1", "END"), ("z", 1, "2", "↓"), ("z", 2, "3", "PG DN"), ("z", 3, "ENTER", "", 1, 2),
        ("b", 0, "0", "INS", 2, 1), ("b", 2, ".", "DEL")]
_ROUND = [("m", 76.1, "M1"), ("m", 94.0, "M2"), ("m", 111.9, "M3"), ("m", 129.8, "MR"),
          ("m", 164.9, "GAME"), ("m", 182.9, "LIGHT"),                              # ゲームモード・明るさ
          ("f", 400.7, "PREV"), ("f", 418.6, "PLAY"), ("f", 436.4, "NEXT"), ("f", 454.6, "MUTE")]


def keys():
    """全部のキーとボタン: [dict(x, y, w, h, label, sub, kind), ...] (mm)。kind = "key" | "round" | "enter" (L 字の Enter の上の段) | "enter2" (下の段)"""
    out = []
    for row, items in _MAIN.items():
        u = 0.0
        for it in items:
            if not isinstance(it, tuple):
                u += it
                continue
            w, label, sub = (it + ("",))[:3]
            kind = {"ENTER": "enter", "ENTER2": "enter2"}.get(label, "key")
            out.append(dict(x=X_MAIN + (u + w / 2) * U, y=ROW[row], w=w * U - GAP, h=U - GAP,
                            label="" if kind == "enter2" else label, sub=sub, kind=kind))
            u += w
    for row, col, label in _NAV:
        out.append(dict(x=NAV_X[col], y=ROW[row], w=U - GAP, h=U - GAP, label=label, sub="", kind="key"))
    rows = list(ROW)
    for row, col, label, *rest in _PAD:
        sub, wu, hu = (list(rest) + ["", 1, 1][len(rest):])[:3]
        y0 = y1 = ROW[row]
        if hu == 2:              # 縦に2段 (+ と ENTER): 次の行まで伸ばす
            y1 = ROW[rows[rows.index(row) + 1]]
        out.append(dict(x=PAD_X[col] + (wu - 1) * U / 2, y=(y0 + y1) / 2, w=wu * U - GAP, h=y1 - y0 + U - GAP,
                        label=label, sub=sub, kind="key"))
    for i, row in enumerate("nqazb"):
        out.append(dict(x=G_X, y=ROW[row], w=U - GAP, h=U - GAP, label=f"G{i + 1}", sub="", kind="key"))
    for row, x, label in _ROUND:
        out.append(dict(x=x, y=ROW[row], w=ROUND, h=ROUND, label=label, sub="", kind="round"))
    return out


def enter_shape():
    """L 字の Enter の上の段と下の段 (keys() の "enter" と "enter2")"""
    k = keys()
    return next(e for e in k if e["kind"] == "enter"), next(e for e in k if e["kind"] == "enter2")


# 光る字の画像 (textures/keyboard_legends.png): キーボードの上面全体 (W x D mm) を 1mm = LEGEND_PPM 画素で描く。
# 各キーの天面に貼る板の UV は、その位置 (x / W, 1 - y / D)
LEGEND_PPM = 5
LEGEND_IMAGE = (round(W * LEGEND_PPM), round(D * LEGEND_PPM))
