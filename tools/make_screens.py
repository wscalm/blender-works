"""デスク2のモニター2台の画面と、枠の印刷を textures/ に描く (python3 tools/make_screens.py)。

  screen_main.png   メインモニター (アイ・オー・データ GigaCrysta LCD-GC242HXB/D、1920x1080) の画面。
                    VS Code (Dark+ のテーマ・日本語の表示) で Upper10 (長～～～い言葉のデータベース。Flask) の app.py を開き、
                    下のターミナルで flask run している。いちばん下に Windows 10 のタスクバー
  screen_sub.png    サブモニター (東芝 REGZA 19S22、1366x768) の画面。Chrome の窓2つを左右に並べている (Windows のスナップ):
                    左 = https://www.wasowaso.com/Upper10 / 右 = Flask の日本語訳ドキュメント https://msiz07-flask-docs-ja.readthedocs.io/ja/latest/
  mark_*.png        枠の印刷 (メイン: GigaCrysta のロゴとボタンの印 / サブ: TOSHIBA と REGZA の字)。1mm = MARK_PPM 画素
  screen_echo.png   デスク2の Amazon Echo Show 5 (960x480) の時計の画面 (ユーザー指定: https://gadget.jungo.jp/echo-show-5/ の記事の写真の物)。
                    明るい青の背景 (左上が水色、右と下へ濃い青) に、左にアナログ時計 (細いセリフの数字・白い針・薄い緑の秒針)、右に日付・曜日・天気と気温

ページの中身は、ヘッドレス Edge で撮った reference/screens/*.png をそのまま貼る (Chrome の窓の中身の大きさ 681x646 で撮る):
  SIZE=681,646 tools/shot_viewer.sh "https://www.wasowaso.com/Upper10" reference/screens/upper10.png
  SIZE=681,646 tools/shot_viewer.sh "https://msiz07-flask-docs-ja.readthedocs.io/ja/latest/" reference/screens/flask_docs.png
VS Code の中のコード (app.py) とフォルダの中身は、Upper10 の実際のページ (URL・画面の名前・static/ の場所) に合わせて作った架空の物。
字は Windows のフォント (/mnt/c/Windows/Fonts の Consolas・Segoe UI・游ゴシック・MS ゴシック。アイコンは Segoe MDL2 Assets)。
時計は夜の 23:41 (画像なので動かない)。Echo Show の時計と日付もこれに合わせる (2022/11/15 は火曜日。天気は夜なので月と雲)。
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pygments.lexers import PythonLexer
from pygments.token import Token

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "..", "textures")
SHOTS = os.path.join(HERE, "..", "reference", "screens")
FONTS = "/mnt/c/Windows/Fonts"

UI, UI_SB, UI_BOLD = ("segoeui.ttf", 0), ("seguisb.ttf", 0), ("segoeuib.ttf", 0)
JP, JP_BOLD = ("YuGothM.ttc", 1), ("YuGothB.ttc", 2)      # Yu Gothic UI / Yu Gothic UI Semibold
MONO, MONO_JP = ("consola.ttf", 0), ("msgothic.ttc", 0)   # エディターとターミナル (日本語は MS ゴシックで代わりに出る)
ICON = ("segmdl2.ttf", 0)
CLOCK = ("23:41", "2022/11/15")


@lru_cache(None)
def font(spec, size):
    return ImageFont.truetype(os.path.join(FONTS, spec[0]), size, index=spec[1])


def runs(s):
    """文字列を、日本語の文字の続きとそれ以外の続きに分ける"""
    out = []
    for ch in s:
        jp = ord(ch) >= 0x2E80
        if out and out[-1][1] == jp:
            out[-1][0] += ch
        else:
            out.append([ch, jp])
    return out


def text(d, x, y, s, fill, size, latin=UI, jp=JP):
    """左端 x・ベースライン y から書く (英数字は latin、日本語は jp のフォント)。戻り値 = 書き終わりの x"""
    for run, is_jp in runs(s):
        f = font(jp if is_jp else latin, size)
        d.text((x, y), run, font=f, fill=fill, anchor="ls")
        x += f.getlength(run)
    return x


def text_w(s, size, latin=UI, jp=JP):
    return sum(font(jp if is_jp else latin, size).getlength(r) for r, is_jp in runs(s))


def icon(d, cx, cy, code, size, fill):
    """Segoe MDL2 Assets のアイコンを中心 (cx, cy) に描く"""
    d.text((cx, cy), chr(code), font=font(ICON, size), fill=fill, anchor="mm")


def mix(a, b, t):
    a, b = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) if isinstance(c, str) else c for c in (a, b)]
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


# ---------------------------------------------------------------- 小さな絵 (アプリとファイルのアイコン)
def windows_logo(d, cx, cy, s, fill):
    """Windows 10 のスタートボタンの窓の印 (4枚の板)"""
    g = s * 0.08
    h = (s - g) / 2
    x0, y0 = cx - s / 2, cy - s / 2
    for i in range(2):
        for j in range(2):
            d.rectangle([x0 + i * (h + g), y0 + j * (h + g), x0 + i * (h + g) + h, y0 + j * (h + g) + h], fill=fill)


def vscode_logo(d, cx, cy, s):
    """VS Code のアイコン (青いリボン) を簡単にした物"""
    k = s / 16
    pts = lambda p: [(cx + (x - 8) * k, cy + (y - 8) * k) for x, y in p]
    d.polygon(pts([(11.5, 0.6), (15.4, 2.4), (15.4, 13.6), (11.5, 15.4), (4.2, 8.6), (1.6, 10.6), (0.6, 10.0),
                   (0.6, 6.0), (1.6, 5.4), (4.2, 7.4)]), fill=(0, 122, 204))
    d.polygon(pts([(11.5, 4.6), (11.5, 11.4), (7.0, 8.0)]), fill=(37, 37, 38))
    d.polygon(pts([(11.5, 0.6), (15.4, 2.4), (15.4, 13.6), (11.5, 15.4)]), fill=(31, 156, 240))


def chrome_logo(d, cx, cy, r):
    for a0, color in ((-150, (219, 68, 55)), (-30, (244, 180, 0)), (90, (15, 157, 88))):
        d.pieslice([cx - r, cy - r, cx + r, cy + r], a0, a0 + 120, fill=color)
    d.ellipse([cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5], fill=(255, 255, 255))
    d.ellipse([cx - r * 0.38, cy - r * 0.38, cx + r * 0.38, cy + r * 0.38], fill=(66, 133, 244))


def edge_logo(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(16, 132, 214))
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 20, 160, fill=(52, 196, 120))
    d.ellipse([cx - r * 0.55, cy - r * 0.35, cx + r * 0.35, cy + r * 0.45], fill=(8, 82, 160))


def folder_icon(d, cx, cy, s):
    x0, y0 = cx - s / 2, cy - s * 0.38
    d.rectangle([x0, y0, x0 + s * 0.42, y0 + s * 0.15], fill=(230, 176, 52))
    d.rectangle([x0, y0 + s * 0.1, x0 + s, y0 + s * 0.76], fill=(255, 204, 77))
    d.rectangle([x0, y0 + s * 0.5, x0 + s, y0 + s * 0.76], fill=(58, 158, 217))


def file_icon(d, x, cy, kind):
    """VS Code の標準 (Seti) のファイルのアイコン。x = アイコンの左端 (16px 幅)"""
    c = x + 8
    if kind == "py":   # 青い2つの丸い四角 (Python の印)
        d.rounded_rectangle([c - 6, cy - 6, c + 1, cy + 1], 2, fill=(81, 154, 186))
        d.rounded_rectangle([c - 1, cy - 1, c + 6, cy + 6], 2, fill=(81, 154, 186))
        d.ellipse([c - 4, cy - 5, c - 2, cy - 3], fill=(37, 37, 38))
        d.ellipse([c + 2, cy + 3, c + 4, cy + 5], fill=(37, 37, 38))
    elif kind == "html":
        d.text((c, cy), "<>", font=font(("consolab.ttf", 0), 13), fill=(227, 121, 51), anchor="mm")
    elif kind == "css":
        d.text((c, cy), "#", font=font(("consolab.ttf", 0), 14), fill=(81, 154, 186), anchor="mm")
    elif kind == "js":
        d.text((c, cy), "JS", font=font(UI_BOLD, 10), fill=(203, 203, 65), anchor="mm")
    elif kind == "md":
        d.ellipse([c - 6, cy - 6, c + 6, cy + 6], outline=(81, 154, 186), width=2)
        d.rectangle([c - 1, cy - 2, c + 1, cy + 3], fill=(81, 154, 186))
        d.rectangle([c - 1, cy - 5, c + 1, cy - 4], fill=(81, 154, 186))
    elif kind == "txt":
        for k, w in enumerate((10, 12, 8, 11)):
            d.rectangle([c - 6, cy - 6 + k * 3.5, c - 6 + w, cy - 5 + k * 3.5], fill=(212, 215, 214))
    elif kind == "git":
        d.polygon([(c, cy - 7), (c + 7, cy), (c, cy + 7), (c - 7, cy)], fill=(65, 83, 91))
        d.line([(c - 2, cy - 3), (c - 2, cy + 3)], fill=(37, 37, 38), width=2)
        d.line([(c - 2, cy - 2), (c + 2, cy + 1)], fill=(37, 37, 38), width=2)
    elif kind == "db":
        d.rectangle([c - 5, cy - 4, c + 5, cy + 5], fill=(245, 83, 133))
        d.ellipse([c - 5, cy - 7, c + 5, cy - 2], fill=(250, 140, 174))
        d.ellipse([c - 5, cy + 2, c + 5, cy + 7], fill=(245, 83, 133))
    elif kind == "json":
        d.text((c, cy), "{}", font=font(("consolab.ttf", 0), 12), fill=(203, 203, 65), anchor="mm")


def branch_icon(d, x, cy, fill, s=1.0):
    """git のブランチの印 (丸3つと線)"""
    r = 2.2 * s
    a, b, c = (x + 3 * s, cy - 6 * s), (x + 3 * s, cy + 6 * s), (x + 11 * s, cy - 3 * s)
    d.line([a, b], fill=fill, width=max(1, round(1.4 * s)))
    d.line([(c[0], c[1] + r), (c[0], cy + 1 * s), (a[0], cy + 4 * s)], fill=fill, width=max(1, round(1.4 * s)))
    for p in (a, b, c):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], outline=fill, width=max(1, round(1.4 * s)))


# ---------------------------------------------------------------- Windows 10 のタスクバー
TASKBAR_H = 40
TASKBAR = (17, 21, 28)      # 黒 (壁紙の青がわずかに透ける)
ACCENT = (118, 185, 237)    # 起動中のアプリの下線 (アクセントの色を明るくした物)


def taskbar(img, y0, main):
    """main = 主のディスプレイ (検索ボックスと通知領域あり)。サブは スタート・アプリ・時計 だけ"""
    W = img.width
    d = ImageDraw.Draw(img)
    d.rectangle([0, y0, W, y0 + TASKBAR_H], fill=TASKBAR)
    cy = y0 + TASKBAR_H / 2
    windows_logo(d, 24, cy, 15, (255, 255, 255))
    x = 48
    if main:   # 検索ボックス
        d.rectangle([x, y0, x + 344, y0 + TASKBAR_H - 1], fill=(243, 243, 243))
        icon(d, x + 22, cy, 0xE721, 15, (40, 40, 40))
        text(d, x + 44, cy + 5, "ここに入力して検索", (118, 118, 118), 14, jp=JP)
        x += 344
        icon(d, x + 24, cy, 0xE7C4, 18, (255, 255, 255))   # タスク ビュー
        x += 48
    apps = [("edge", False, False), ("explorer", False, False), ("chrome", True, False), ("vscode", True, main)]
    for name, running, active in apps:
        if active:
            d.rectangle([x, y0, x + 48, y0 + TASKBAR_H], fill=(52, 57, 66))
        c = x + 24
        if name == "edge":
            edge_logo(d, c, cy, 11)
        elif name == "explorer":
            folder_icon(d, c, cy, 24)
        elif name == "chrome":
            chrome_logo(d, c, cy, 11)
        else:
            vscode_logo(d, c, cy, 24)
        if running:   # 下線 (Chrome は窓が2つなので右端を少し重ねて描く)
            d.rectangle([x + (0 if active else 4), y0 + TASKBAR_H - 2, x + 48 - (0 if active else 4), y0 + TASKBAR_H], fill=ACCENT)
            if name == "chrome":
                d.rectangle([x + 44, y0 + 3, x + 46, y0 + TASKBAR_H - 3], fill=(38, 43, 51))
        x += 48
    # 右端: (主のディスプレイだけ) 隠れているアイコン・OneDrive・ネットワーク・音量・IME、時計、通知
    x = W - 5
    d.line([(x, y0 + 4), (x, y0 + TASKBAR_H - 4)], fill=(70, 74, 80))
    if main:
        x -= 48
        icon(d, x + 24, cy, 0xE91C, 16, (255, 255, 255))   # 通知 (アクション センター)
    tw = max(text_w(s, 12) for s in CLOCK)
    x -= tw + 16
    for k, s in enumerate(CLOCK):
        text(d, x + 8 + (tw - text_w(s, 12)) / 2, y0 + 17 + k * 16, s, (255, 255, 255), 12)
    if main:
        for code in (None, 0xE995, 0xE839, 0xE753, 0xE70E):
            x -= 32 if code else 30
            if code:
                icon(d, x + 16, cy, code, 15, (255, 255, 255))
            else:
                text(d, x + 7, cy + 6, "あ", (255, 255, 255), 15, jp=JP)


# ---------------------------------------------------------------- VS Code (メインモニター)
VS = dict(title=(60, 60, 60), activity=(51, 51, 51), side=(37, 37, 38), editor=(30, 30, 30), tabs=(37, 37, 38),
          tab=(45, 45, 45), status=(0, 122, 204), fg=(204, 204, 204), dim=(133, 133, 133), border=(68, 68, 68))
SYN = dict(text=(212, 212, 212), kw=(86, 156, 214), ctrl=(197, 134, 192), str=(206, 145, 120), com=(106, 153, 85),
           num=(181, 206, 168), func=(220, 220, 170), cls=(78, 201, 176), var=(156, 220, 254), const=(79, 193, 255),
           esc=(215, 186, 125))
BRACKETS = [(255, 215, 0), (218, 112, 214), (23, 159, 255)]   # 括弧の色分け (入れ子の深さ順)
GIT_M, GIT_U, GIT_IGNORED = (226, 192, 141), (115, 201, 145), (140, 140, 140)

APP_PY = '''\
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, session, url_for)

app = Flask(__name__, static_url_path="/Upper10/static")
app.config.from_pyfile("config.py")

DATABASE = os.path.join(app.root_path, "words.sqlite3")
MIN_LENGTH = 10  # 10文字以上の言葉だけを集める
PER_PAGE = 50


def get_db():
    """リクエストの間だけデータベースにつなぐ"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def admin_required(view):
    """管理者としてログインしていなければ 403 を返す"""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@app.route("/Upper10")
def top():
    return render_template("top.html")


@app.route("/Upper10/view_records")
def view_records():
    keyword = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    rows = get_db().execute(
        "SELECT word, reading, length FROM words"
        " WHERE word LIKE ? ORDER BY length DESC LIMIT ? OFFSET ?",
        (f"%{keyword}%", PER_PAGE, (page - 1) * PER_PAGE),
    ).fetchall()
    return render_template("view_records.html", rows=rows, q=keyword, page=page)


@app.route("/Upper10/request", methods=["GET", "POST"])
def request_word():
    if request.method == "POST":
        word = request.form.get("word", "").strip()
        reading = request.form.get("reading", "").strip()
        if len(word) < MIN_LENGTH:
            flash(f"{MIN_LENGTH}文字以上の言葉を入力してください")
            return redirect(url_for("request_word"))
        db = get_db()
        db.execute(
            "INSERT INTO requests (word, reading, created_at) VALUES (?, ?, ?)",
            (word, reading, datetime.now()),
        )
        db.commit()
        flash("リクエストを受け付けました。ありがとうございます！")
        return redirect(url_for("request_word"))
    return render_template("request.html")


@app.route("/Upper10/view_stats")
def view_stats():
    stats = get_db().execute(
        "SELECT length, COUNT(*) AS n FROM words GROUP BY length ORDER BY length"
    ).fetchall()
    return render_template("view_stats.html", stats=stats)


@app.route("/Upper10/manual")
def manual():
    return render_template("manual.html")


@app.route("/Upper10/admin")
@admin_required
def admin():
    pending = get_db().execute(
        "SELECT * FROM requests WHERE status = 'pending' ORDER BY created_at"
    ).fetchall()
    return render_template("admin.html", requests=pending)
'''
FIRST_LINE = 41                 # 画面のいちばん上に見えている行
CURSOR = (73, 42)               # カーソルの (行, 列)。2つ目の flash の閉じ括弧の手前
CHANGED = {63: "added", 69: "modified", 70: "modified", 73: "modified"}   # git の変更 (行の左の色の帯。読みの欄を足した)
CONTROL = {"if", "elif", "else", "for", "while", "break", "continue", "return", "try", "except", "finally", "raise",
           "with", "yield", "import", "from", "as", "pass", "assert", "del", "global", "nonlocal", "await", "async"}
CLASSES = {"Flask", "Row"}
VARIABLES = {"g", "request", "session", "app", "os", "sqlite3"}


def highlight(src):
    """Python のコードを、行ごとの [(文字列, 色), ...] にする (VS Code の Dark+ と Pylance の色分けに似せる)"""
    toks = []
    for ttype, value in PythonLexer().get_tokens(src):
        if ttype in Token.Punctuation and len(value) > 1:
            toks += [(ttype, ch) for ch in value]
        else:
            toks.append((ttype, value))
    sig = [i for i, (t, v) in enumerate(toks) if v.strip()]
    nxt = {a: toks[b][1] for a, b in zip(sig, sig[1:])}
    prv = {b: toks[a][1] for a, b in zip(sig, sig[1:])}
    lines, cur, depth, stack, in_import = [], [], 0, [], False
    for i, (ttype, value) in enumerate(toks):
        color = SYN["text"]
        if ttype in Token.Comment:
            color = SYN["com"]
        elif ttype in Token.Literal.String.Affix or ttype in Token.Literal.String.Interpol:
            color = SYN["kw"]
        elif ttype in Token.Literal.String.Escape:
            color = SYN["esc"]
        elif ttype in Token.Literal.String:
            color = SYN["str"]
        elif ttype in Token.Literal.Number:
            color = SYN["num"]
        elif ttype in Token.Keyword or ttype in Token.Operator.Word:
            color = SYN["ctrl"] if value in CONTROL else SYN["kw"]
            if value in ("import", "from"):
                in_import = True
        elif ttype in Token.Name.Decorator:
            color = SYN["func"]
        elif ttype in Token.Name:
            after = nxt.get(i, "")
            if prv.get(i) == "@" or ttype in Token.Name.Function or ttype in Token.Name.Builtin and value not in ("self", "cls"):
                color = SYN["func"]
            elif ttype in Token.Name.Class or value in CLASSES or ttype in Token.Name.Namespace:
                color = SYN["cls"]
            elif value.isupper() and len(value) > 1:
                color = SYN["const"]
            elif value in VARIABLES or ttype in Token.Name.Variable:
                color = SYN["cls"] if in_import and value in ("os", "sqlite3") else SYN["var"]
            elif after == "(" or in_import:
                color = SYN["func"]
            else:
                color = SYN["var"]
        elif ttype in Token.Punctuation and value in "([{":
            color = BRACKETS[depth % 3]
            stack.append(color)
            depth += 1
        elif ttype in Token.Punctuation and value in ")]}":
            depth = max(0, depth - 1)
            color = stack.pop() if stack else SYN["text"]
        parts = value.split("\n")
        for k, part in enumerate(parts):
            if k > 0:
                lines.append(cur)
                cur = []
                if not stack:
                    in_import = False
            if part:
                cur.append((part, color))
    if cur:
        lines.append(cur)
    return lines


def code_text(d, x, y, s, fill, cw):
    """等幅の字 (英数字は cw 幅。日本語は MS ゴシックの幅) で書く。戻り値 = 書き終わりの x"""
    for run, is_jp in runs(s):
        if is_jp:
            f = font(MONO_JP, 14)
            d.text((round(x), y), run, font=f, fill=fill, anchor="ls")
            x += f.getlength(run)
        else:
            for ch in run:
                if ch != " ":
                    d.text((round(x), y), ch, font=font(MONO, 14), fill=fill, anchor="ls")
                x += cw
    return x


def make_vscode():
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), VS["editor"])
    d = ImageDraw.Draw(img)
    win_h = H - TASKBAR_H
    title_h, act_w, side_w, tabs_h, crumb_h, status_h, panel_h = 30, 48, 300, 35, 22, 22, 262
    status_y = win_h - status_h
    panel_y = status_y - panel_h
    ex0 = act_w + side_w                     # エディターの左端
    ey0 = title_h + tabs_h + crumb_h         # コードの上端
    cw, lh = font(MONO, 14).getlength("M"), 19

    # --- タイトルバー: アイコン・メニュー・題名・レイアウトの切り替え・窓のボタン
    d.rectangle([0, 0, W, title_h], fill=VS["title"])
    vscode_logo(d, 18, 15, 16)
    x = 36
    for item in ("ファイル(F)", "編集(E)", "選択(S)", "表示(V)", "移動(G)", "実行(R)", "ターミナル(T)", "ヘルプ(H)"):
        x = text(d, x + 8, 20, item, VS["fg"], 13) + 8
    t = "app.py - Upper10 - Visual Studio Code"
    text(d, (W - text_w(t, 13)) / 2, 20, t, VS["fg"], 13)
    for k, code in enumerate((0xE921, 0xE923, 0xE8BB)):
        icon(d, W - 138 + k * 46 + 23, 15, code, 10, VS["fg"])
    for k in range(3):   # レイアウトの切り替え (サイドバー・パネル・2つ目のサイドバー)
        bx = W - 138 - 96 + k * 26
        d.rectangle([bx, 9, bx + 14, 20], outline=VS["fg"])
        d.rectangle(([bx, 9, bx + 4, 20], [bx, 16, bx + 14, 20], [bx + 10, 9, bx + 14, 20])[k], fill=VS["fg"])

    # --- アクティビティバー
    d.rectangle([0, title_h, act_w, status_y], fill=VS["activity"])
    y = title_h + 24
    d.rectangle([0, y - 24, 1, y + 23], fill=(255, 255, 255))   # 選ばれている印 (エクスプローラー)
    icon(d, 24, y, 0xE8C8, 24, (255, 255, 255))
    icon(d, 24, y + 48, 0xE721, 22, VS["dim"])
    branch_icon(d, 14, y + 96, VS["dim"], 1.45)
    d.ellipse([29, y + 100, 45, y + 116], fill=(0, 122, 204))     # 変更したファイルの数の印
    d.text((37, y + 108), "3", font=font(UI_SB, 10), fill=(255, 255, 255), anchor="mm")
    icon(d, 22, y + 144, 0xE768, 21, VS["dim"])
    icon(d, 31, y + 150, 0xEBE8, 11, VS["dim"])
    icon(d, 24, y + 192, 0xEA86, 22, VS["dim"])
    icon(d, 24, status_y - 72, 0xE77B, 22, VS["dim"])
    icon(d, 24, status_y - 24, 0xE713, 22, VS["dim"])

    # --- サイドバー (エクスプローラー)
    d.rectangle([act_w, title_h, ex0, status_y], fill=VS["side"])
    text(d, act_w + 20, title_h + 22, "エクスプローラー", (187, 187, 187), 11)
    icon(d, ex0 - 22, title_h + 18, 0xE712, 14, VS["fg"])
    y = title_h + 35

    def section(label, open_, yy):
        icon(d, act_w + 12, yy + 11, 0xE70D if open_ else 0xE76C, 9, VS["fg"])
        text(d, act_w + 22, yy + 15, label, VS["fg"], 11, latin=UI_BOLD, jp=JP_BOLD)
        return yy + 22
    y = section("開いているエディター", False, y)
    y = section("UPPER10", True, y)
    tree = [   # (深さ, 名前, 種類 (None = フォルダ), フォルダを開いているか, git の状態)
        (0, ".vscode", None, False, None), (0, "__pycache__", None, False, "ignored"), (0, "static", None, True, "M"),
        (1, "css", None, True, "M"), (2, "top.css", "css", False, "M"), (2, "view_records.css", "css", False, None),
        (1, "images", None, False, None), (1, "js", None, False, None), (0, "templates", None, True, "M"),
        (1, "admin.html", "html", False, None), (1, "manual.html", "html", False, None),
        (1, "request.html", "html", False, "M"), (1, "top.html", "html", False, None),
        (1, "view_records.html", "html", False, None), (1, "view_stats.html", "html", False, None),
        (0, "venv", None, False, "ignored"), (0, ".gitignore", "git", False, None), (0, "app.py", "py", False, "M"),
        (0, "config.py", "py", False, None), (0, "README.md", "md", False, None),
        (0, "requirements.txt", "txt", False, None), (0, "words.sqlite3", "db", False, "ignored"),
    ]
    for depth, name, kind, open_, git in tree:
        x = act_w + 12 + depth * 8
        if name == "app.py":
            d.rectangle([act_w, y, ex0, y + 21], fill=(55, 55, 61))
        color = {"M": GIT_M, "ignored": GIT_IGNORED}.get(git, VS["fg"])
        if kind is None:
            icon(d, x + 8, y + 11, 0xE70D if open_ else 0xE76C, 9, VS["fg"])
            text(d, x + 20, y + 15, name, color, 13)
        else:
            file_icon(d, x + 14, y + 11, kind)
            text(d, x + 36, y + 15, name, color, 13)
        if git == "M":   # 変更の印: ファイルは M、フォルダは点
            if kind is None:
                d.ellipse([ex0 - 18, y + 8, ex0 - 13, y + 13], fill=GIT_M)
            else:
                text(d, ex0 - 20, y + 15, "M", GIT_M, 12)
        y += 22
    yb = status_y - 44
    d.line([(act_w, yb), (ex0, yb)], fill=VS["border"])
    section("アウトライン", False, yb)
    d.line([(act_w, yb + 22), (ex0, yb + 22)], fill=VS["border"])
    section("タイムライン", False, yb + 22)

    # --- タブ
    d.rectangle([ex0, title_h, W, title_h + tabs_h], fill=VS["tabs"])
    x = ex0
    for name, kind, git, active in (("app.py", "py", "M", True), ("top.html", "html", None, False),
                                    ("top.css", "css", "M", False), ("view_records.html", "html", None, False)):
        label = name + ("  M" if git else "")
        w = 10 + 16 + 6 + text_w(label, 13) + 34
        d.rectangle([x, title_h, x + w, title_h + tabs_h], fill=VS["editor"] if active else VS["tab"])
        d.line([(x + w, title_h), (x + w, title_h + tabs_h)], fill=VS["tabs"])
        file_icon(d, x + 10, title_h + 18, kind)
        fg = GIT_M if git else (255, 255, 255)
        text(d, x + 32, title_h + 22, label, fg if active else mix(fg, VS["tab"], 0.4), 13)
        if active:
            icon(d, x + w - 18, title_h + 18, 0xE8BB, 9, VS["fg"])
        x += w + 1
    for k, code in enumerate((0xE768, 0xE70D, None, 0xE712)):   # 右上: Python の実行・分割・その他
        cx = W - 110 + k * 26
        if code is None:
            d.rectangle([cx - 7, title_h + 11, cx + 7, title_h + 24], outline=VS["fg"])
            d.line([(cx, title_h + 11), (cx, title_h + 24)], fill=VS["fg"])
        else:
            icon(d, cx, title_h + 18, code, 13 if code != 0xE70D else 8, VS["fg"])

    # --- パンくずリスト
    y = title_h + tabs_h
    file_icon(d, ex0 + 14, y + 11, "py")
    x = text(d, ex0 + 34, y + 15, "app.py", (169, 169, 169), 13)
    icon(d, x + 10, y + 11, 0xE76C, 8, (169, 169, 169))
    d.polygon([(x + 25, y + 6), (x + 31, y + 9), (x + 31, y + 15), (x + 25, y + 18), (x + 19, y + 15), (x + 19, y + 9)],
              outline=(180, 128, 215), width=2)
    text(d, x + 36, y + 15, "request_word", (169, 169, 169), 13)

    # --- エディター: 行番号・git の帯・インデントの線・コード・カーソル・ミニマップ
    lines = highlight(APP_PY)
    gutter_r = ex0 + 52            # 行番号の右端
    code_x = ex0 + 70
    mm_x, sb_x = W - 14 - 116, W - 14
    view_lines = (panel_y - ey0) // lh + 1
    indent = [len(src) - len(src.lstrip(" ")) if src.strip() else None for src in APP_PY.split("\n")]
    for i in range(len(indent)):   # 空の行は前後の行の深い方のインデントを続ける (VS Code と同じ)
        if indent[i] is None:
            a = next((indent[j] for j in range(i - 1, -1, -1) if indent[j] is not None), 0)
            b = next((indent[j] for j in range(i + 1, len(indent)) if indent[j] is not None), 0)
            indent[i] = min(a, b)
    cur_line, cur_col = CURSOR
    for k in range(view_lines):
        n = FIRST_LINE + k               # 行番号 (1 から)
        if n > len(lines):
            break
        top = ey0 + k * lh
        base = top + 14
        if n == cur_line:   # カーソルのある行の枠
            d.rectangle([gutter_r + 4, top, mm_x - 1, top + lh - 1], outline=(40, 40, 40), width=2)
        num = str(n)
        d.text((gutter_r, base), num, font=font(MONO, 14), fill=(198, 198, 198) if n == cur_line else VS["dim"], anchor="rs")
        if n in CHANGED:
            color = (72, 126, 2) if CHANGED[n] == "added" else (27, 129, 168)
            d.rectangle([gutter_r + 8, top, gutter_r + 10, top + lh - 1], fill=color)
        for lvl in range(0, indent[n - 1] // 4):   # インデントの線 (カーソルのある塊は明るく)
            gx = round(code_x + lvl * 4 * cw)
            active = lvl == 1 and 59 <= n <= 74
            d.line([(gx, top), (gx, top + lh - 1)], fill=(112, 112, 112) if active else (64, 64, 64))
        x = code_x
        for part, color in lines[n - 1]:
            x = code_text(d, x, base, part, color, cw)
        if n == cur_line:
            src = APP_PY.split("\n")[n - 1]
            cx = code_x + text_w(src[:cur_col - 1], 14, latin=MONO, jp=MONO_JP)
            d.rectangle([round(cx), top, round(cx) + 1, top + lh - 1], fill=(174, 175, 173))
    for i, line in enumerate(lines):   # ミニマップ (1文字 = 幅 1px・高さ 2px)
        y = ey0 + 4 + i * 2
        x = mm_x + 6
        for part, color in line:
            for ch in part:
                if ch != " ":
                    d.rectangle([x, y, x + (1 if ord(ch) >= 0x2E80 else 0), y + 1], fill=mix(color, VS["editor"], 0.45))
                x += 2 if ord(ch) >= 0x2E80 else 1
    d.line([(sb_x, ey0), (sb_x, panel_y)], fill=(50, 50, 50))   # スクロールバーの概要ルーラー (変更とカーソルの印)
    total = (panel_y - ey0) / len(lines)
    for n, kind in CHANGED.items():
        d.rectangle([sb_x + 2, ey0 + (n - 1) * total, sb_x + 5, ey0 + n * total], fill=(72, 126, 2) if kind == "added" else (27, 129, 168))
    d.rectangle([sb_x + 1, ey0 + (cur_line - 1) * total, W - 1, ey0 + (cur_line - 1) * total + 1], fill=(160, 160, 160))

    # --- パネル (ターミナル)
    d.rectangle([ex0, panel_y, W, status_y], fill=VS["editor"])
    d.line([(ex0, panel_y), (W, panel_y)], fill=(68, 68, 68))
    x = ex0 + 20
    for label in ("問題", "出力", "デバッグ コンソール", "ターミナル"):
        active = label == "ターミナル"
        x2 = text(d, x, panel_y + 22, label, (231, 231, 231) if active else (150, 150, 150), 11)
        if active:
            d.line([(x, panel_y + 30), (x2, panel_y + 30)], fill=(231, 231, 231))
        x = x2 + 24
    x = W - 20
    for code in (0xE8BB, 0xE70E, 0xE712, 0xE74D, None, 0xE70D, 0xE710):
        x -= 26
        if code is None:
            d.rectangle([x + 6, panel_y + 12, x + 20, panel_y + 24], outline=VS["fg"])
            d.line([(x + 13, panel_y + 12), (x + 13, panel_y + 24)], fill=VS["fg"])
        else:
            icon(d, x + 13, panel_y + 18, code, 13 if code != 0xE70D else 8, VS["fg"])
    x = text(d, x - 90, panel_y + 22, "powershell", VS["fg"], 12)
    d.rectangle([x - 90 - 22, panel_y + 12, x - 90 - 10, panel_y + 24], outline=VS["fg"])
    red, yellow, cyan, green, gray = (241, 76, 76), (229, 229, 16), (17, 168, 205), (35, 209, 139), (118, 118, 118)
    term = [
        [("(venv) ", green), ("PS C:\\work\\Upper10> ", None), ("flask", (245, 245, 67)), (" --app", gray), (" app", None),
         (" --debug", gray), (" run", None)],
        [(" * Serving Flask app 'app'", None)],
        [(" * Debug mode: on", None)],
        [("WARNING: This is a development server. Do not use it in a production deployment. "
          "Use a production WSGI server instead.", red)],
        [(" * Running on http://127.0.0.1:5000", None)],
        [("Press CTRL+C to quit", yellow)],
        [(" * Restarting with stat", None)],
        [(" * Debugger is active!", None)],
        [(" * Debugger PIN: 128-406-939", None)],
        [("127.0.0.1 - - [15/Nov/2022 23:38:12] ", None), ('"GET /Upper10 HTTP/1.1" 200 -', None)],
        [("127.0.0.1 - - [15/Nov/2022 23:38:12] ", None), ('"GET /Upper10/static/css/top.css HTTP/1.1" 304 -', cyan)],
        [("127.0.0.1 - - [15/Nov/2022 23:40:55] ", None), ('"GET /Upper10/request HTTP/1.1" 200 -', None)],
    ]
    for k, segs in enumerate(term):
        x, y = ex0 + 20, panel_y + 50 + k * 17
        for s, color in segs:
            x = code_text(d, x, y, s, color or VS["fg"], cw)
    d.rectangle([ex0 + 20, panel_y + 50 + len(term) * 17 - 13, ex0 + 20 + cw, panel_y + 50 + len(term) * 17 + 3],
                outline=VS["fg"])   # ターミナルのカーソル (フォーカスが無いので枠だけ)

    # --- ステータスバー
    d.rectangle([0, status_y, W, win_h], fill=VS["status"])
    white = (255, 255, 255)
    by = status_y + 16
    branch_icon(d, 10, status_y + 11, white, 0.9)
    x = text(d, 26, by, "main*", white, 12)
    icon(d, x + 14, status_y + 11, 0xE72C, 11, white)
    x = text(d, x + 32, by, "⊗ 0  ⚠ 0", white, 12, latin=("seguisym.ttf", 0))
    x = W - 12
    icon(d, x - 8, status_y + 11, 0xE7ED, 12, white)
    x -= 34
    icon(d, x - 6, status_y + 11, 0xE77B, 12, white)
    x -= 22
    for item in ("3.10.8 ('venv': venv)", "{ } Python", "CRLF", "UTF-8", "スペース: 4", f"行 {CURSOR[0]}、列 {CURSOR[1]}"):
        x -= text_w(item, 12)
        text(d, x, by, item, white, 12)
        x -= 22

    taskbar(img, win_h, main=True)
    return img


# ---------------------------------------------------------------- Chrome の窓2つ (サブモニター)
CH = dict(frame=(231, 234, 237), tab=(255, 255, 255), toolbar=(255, 255, 255), omni=(241, 243, 244),
          icon=(95, 99, 104), text=(32, 33, 36), sep=(218, 220, 224), border=(170, 170, 172))


def chrome_window(img, x0, w, h, shot, title, url, favicon=None):
    """スナップした (半分の幅の) Chrome の窓。フォーカスは VS Code にあるので、どちらも非アクティブの色"""
    d = ImageDraw.Draw(img)
    strip, bar = 41, 39
    d.rectangle([x0, 0, x0 + w - 1, strip], fill=CH["frame"])
    tx0, tw = x0 + 8, 240   # タブ (上の角が丸く、下の端が外へ反る)
    d.rounded_rectangle([tx0, 7, tx0 + tw, strip + 8], 8, fill=CH["tab"])
    for sx in (tx0 - 8, tx0 + tw):
        d.rectangle([sx, strip - 8, sx + 8, strip], fill=CH["tab"])
    d.pieslice([tx0 - 16, strip - 16, tx0, strip], 0, 90, fill=CH["frame"])
    d.pieslice([tx0 + tw, strip - 16, tx0 + tw + 16, strip], 90, 180, fill=CH["frame"])
    if favicon:
        img.paste(favicon, (tx0 + 12, 17), favicon)
    else:   # ファビコンの無いページは地球の印
        icon(d, tx0 + 20, 25, 0xE774, 14, CH["icon"])
    tab = Image.new("RGB", (tw - 64, 24), CH["tab"])   # 題名 (右端は薄れて消える)
    text(ImageDraw.Draw(tab), 0, 17, title, (60, 64, 67), 12)
    fade = Image.linear_gradient("L").rotate(90).resize((24, 24))
    tab.paste(Image.new("RGB", (24, 24), CH["tab"]), (tab.width - 24, 0), fade)
    img.paste(tab, (tx0 + 36, 13))
    icon(d, tx0 + tw - 20, 25, 0xE8BB, 9, CH["icon"])
    icon(d, tx0 + tw + 22, 25, 0xE710, 11, CH["icon"])
    for k, code in enumerate((0xE921, 0xE922, 0xE8BB)):   # 窓のボタン
        icon(d, x0 + w - 135 + k * 45 + 22, 15, code, 10, (40, 40, 40))
    y = strip + 1   # ツールバー: 戻る・進む・再読み込み・アドレスバー・プロフィール・メニュー
    d.rectangle([x0, y, x0 + w - 1, y + bar], fill=CH["toolbar"])
    cy = y + bar / 2
    for k, (code, color) in enumerate(((0xE72B, CH["icon"]), (0xE72A, (189, 193, 198)), (0xE72C, CH["icon"]))):
        icon(d, x0 + 20 + k * 34, cy, code, 15, color)
    ox0, ox1 = x0 + 112, x0 + w - 80
    d.rounded_rectangle([ox0, cy - 14, ox1, cy + 14], 14, fill=CH["omni"])
    icon(d, ox0 + 16, cy, 0xE72E, 12, CH["icon"])
    text(d, ox0 + 34, cy + 5, url, CH["text"], 14)
    icon(d, ox1 - 16, cy, 0xE734, 14, CH["icon"])
    d.ellipse([x0 + w - 66, cy - 10, x0 + w - 46, cy + 10], fill=(26, 115, 232))
    text(d, x0 + w - 60, cy + 5, "S", (255, 255, 255), 13, latin=UI_SB)
    for k in (-5, 0, 5):
        d.ellipse([x0 + w - 24 - 1.6, cy + k - 1.6, x0 + w - 24 + 1.6, cy + k + 1.6], fill=CH["icon"])
    y += bar
    d.line([(x0, y), (x0 + w - 1, y)], fill=CH["sep"])
    img.paste(shot.crop((0, 0, w - 2, h - y - 2)), (x0 + 1, y + 1))   # ページ (窓の枠 1px の内側)
    d.rectangle([x0, 0, x0 + w - 1, h - 1], outline=CH["border"])


def make_chrome_pair():
    W, H = 1366, 768
    img = Image.new("RGB", (W, H), (0, 0, 0))
    win_h, half = H - TASKBAR_H, W // 2
    flask_icon = Image.open(os.path.join(SHOTS, "flask_icon.png")).convert("RGBA")
    flask_icon.thumbnail((16, 16), Image.LANCZOS)
    chrome_window(img, 0, half, win_h, Image.open(os.path.join(SHOTS, "upper10.png")).convert("RGB"),
                  "長～～～い言葉のデータベースTOP", "wasowaso.com/Upper10")
    chrome_window(img, half, W - half, win_h, Image.open(os.path.join(SHOTS, "flask_docs.png")).convert("RGB"),
                  "Flaskへようこそ — Flask Documentation (2.2.x)", "msiz07-flask-docs-ja.readthedocs.io/ja/latest/",
                  favicon=flask_icon)
    taskbar(img, win_h, main=False)
    return img


# ---------------------------------------------------------------- Echo Show 5 の時計の画面
ECHO = (960, 480)
ECHO_BG = ((22, 178, 206), (6, 96, 182), (8, 90, 206), (4, 52, 170))   # 背景の四隅 (左上・右上・左下・右下)。記事の写真の色
SERIF_NUM = ("BOD_B.TTF", 0)   # 文字盤の数字 (Bodoni MT Bold。写真のセリフの数字に近い)
PALE_GREEN = (190, 236, 196)


def make_echo():
    S = 2   # 2倍で描いて縮める
    W, H = ECHO[0] * S, ECHO[1] * S
    u, v = np.meshgrid(np.linspace(0, 1, W), np.linspace(0, 1, H))
    c = [np.array(x, np.float32) for x in ECHO_BG]
    bg = ((1 - u) * (1 - v))[..., None] * c[0] + (u * (1 - v))[..., None] * c[1] + ((1 - u) * v)[..., None] * c[2] + (u * v)[..., None] * c[3]
    bg += (np.exp(-((u - 0.28) ** 2 / 0.08 + (v - 0.25) ** 2 / 0.12)) * 14)[..., None] * np.array((0.6, 1.0, 0.7))   # 左上の明るいところ
    img = Image.fromarray(bg.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # アナログ時計 (23:41:12)
    cx, cy, R = 0.305 * W, 0.515 * H, 0.372 * H
    f = font(SERIF_NUM, round(0.088 * H))
    for n in range(1, 13):
        a = math.radians(n * 30)
        d.text((cx + R * math.sin(a), cy - R * math.cos(a)), str(n), font=f, fill=(255, 255, 255), anchor="mm")
    hh, mm, ss = 23, 41, 12
    hand = lambda deg, length, tail=0.0: ((cx - tail * math.sin(math.radians(deg)), cy + tail * math.cos(math.radians(deg))),
                                          (cx + length * math.sin(math.radians(deg)), cy - length * math.cos(math.radians(deg))))
    a_h, a_m, a_s = ((hh % 12) + mm / 60) * 30, (mm + ss / 60) * 6, ss * 6
    (x0, y0), (x1, y1) = hand(a_h, 0.235 * H)                     # 時針: 太く、先の方が薄い緑
    d.line([(x0, y0), (x1, y1)], fill=(255, 255, 255), width=round(0.017 * H))
    (xm, ym) = (x0 + (x1 - x0) * 0.45, y0 + (y1 - y0) * 0.45)
    d.line([(xm, ym), (x1, y1)], fill=PALE_GREEN, width=round(0.017 * H))
    r = 0.0085 * H
    d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=PALE_GREEN)
    d.line(hand(a_m, 0.43 * H), fill=(255, 255, 255), width=round(0.0075 * H))   # 分針: 細く長い白
    d.line(hand(a_s, 0.40 * H, tail=0.07 * H), fill=PALE_GREEN, width=max(2, round(0.004 * H)))   # 秒針
    r = 0.016 * H
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PALE_GREEN)
    r = 0.008 * H
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(40, 120, 90))
    # 右: 日付・曜日・天気 (夜なので雲と月)・気温
    x = 0.655 * W
    text(d, x, 0.315 * H, "11月15日", (255, 255, 255), round(0.074 * H), latin=UI_BOLD, jp=JP_BOLD)
    text(d, x, 0.425 * H, "火曜日", (255, 255, 255), round(0.074 * H), latin=UI_BOLD, jp=JP_BOLD)
    ix, iy, s_ = x + 0.045 * H, 0.555 * H, 0.10 * H
    d.ellipse([ix - 0.42 * s_, iy - 0.62 * s_, ix + 0.30 * s_, iy + 0.10 * s_], fill=(255, 236, 160))   # 月
    d.ellipse([ix - 0.22 * s_, iy - 0.76 * s_, ix + 0.50 * s_, iy - 0.04 * s_], fill=tuple(bg[int(iy - 0.4 * s_), int(ix + 0.14 * s_)].astype(int)))
    for (ox, oy, rr) in ((-0.30, 0.10, 0.26), (0.02, -0.02, 0.36), (0.36, 0.12, 0.24)):   # 雲 (丸を3つと平らな下)
        d.ellipse([ix + (ox - rr) * s_, iy + (oy - rr) * s_, ix + (ox + rr) * s_, iy + (oy + rr) * s_], fill=(236, 242, 248))
    d.rectangle([ix - 0.30 * s_, iy + 0.10 * s_, ix + 0.36 * s_, iy + 0.36 * s_], fill=(236, 242, 248))
    text(d, ix + 0.62 * s_, iy + 0.36 * s_, "9°", (255, 255, 255), round(0.115 * H), latin=UI_BOLD)
    return img.resize(ECHO, Image.LANCZOS)


# ---------------------------------------------------------------- 枠の印刷
MARK_PPM = 12   # 1mm の画素数
MARKS = {   # 名前: (幅 mm, 高さ mm, 地の色 = 枠の色)。scripts/furniture_monitor.py が同じ大きさの板に貼る
    "gigacrysta_logo": (50, 7, (20, 20, 22)),
    "gigacrysta_buttons": (84, 6, (20, 20, 22)),
    "toshiba": (28, 6, (16, 16, 18)),
    "regza": (26, 5, (16, 16, 18)),
}


def make_mark(name):
    w_mm, h_mm, bg = MARKS[name]
    s = 3   # 3倍で描いて縮める (字の縁をなめらかに)
    k = MARK_PPM * s
    img = Image.new("RGB", (w_mm * k, h_mm * k), bg)
    d = ImageDraw.Draw(img)
    cx, cy = img.width / 2, img.height / 2
    if name == "gigacrysta_logo":   # 斜体の字 (銀色)。実物は横に広い字なので、字の間を空けて横に伸ばし 幅 44mm・大文字の高さ 4mm にする
        f = font(("seguisbi.ttf", 0), round(5.7 * k))
        word = Image.new("L", img.size, 0)
        x = 0
        for c in "GigaCrysta":
            ImageDraw.Draw(word).text((x, cy), c, font=f, fill=255, anchor="lm")
            x += f.getlength(c) + 0.8 * k
        word = word.crop((0, 0, round(x - 0.8 * k), img.height)).resize((44 * k, img.height), Image.LANCZOS)
        img.paste((196, 198, 202), (round(cx - word.width / 2), 0), word)
    elif name == "gigacrysta_buttons":   # ボタンの位置の小さな ▽ が4つと電源の印 (画面の右下。左端 = 枠の中心から 134mm)
        for xm in (138.2, 152.9, 168.1, 183.3):
            x = (xm - 134) * k
            d.polygon([(x - 0.9 * k, cy - 0.6 * k), (x + 0.9 * k, cy - 0.6 * k), (x, cy + 0.7 * k)], fill=(170, 172, 176))
        x, r = (208.0 - 134) * k, 1.2 * k
        d.arc([x - r, cy - r, x + r, cy + r], -60, 240, fill=(170, 172, 176), width=round(0.25 * k))
        d.line([(x, cy - r - 0.2 * k), (x, cy)], fill=(170, 172, 176), width=round(0.25 * k))
    elif name == "toshiba":
        f = font(UI_BOLD, round(3.6 * k))
        x = cx - (sum(f.getlength(c) for c in "TOSHIBA") + 6 * 0.35 * k) / 2
        for c in "TOSHIBA":   # 字の間を少し広げる
            d.text((x, cy), c, font=f, fill=(150, 152, 156), anchor="lm")
            x += f.getlength(c) + 0.35 * k
    elif name == "regza":
        f = font(("segoeuil.ttf", 0), round(3.0 * k))
        x = cx - (sum(f.getlength(c) for c in "REGZA") + 4 * 0.9 * k) / 2
        for c in "REGZA":
            d.text((x, cy), c, font=f, fill=(92, 94, 98), anchor="lm")
            x += f.getlength(c) + 0.9 * k
    return img.resize((w_mm * MARK_PPM, h_mm * MARK_PPM), Image.LANCZOS)


def save(img, name):
    path = os.path.join(TEX, name)
    img.save(path, optimize=True)
    print(f"{name}: {img.size[0]}x{img.size[1]}  {os.path.getsize(path) / 1024:.0f} KB")


if __name__ == "__main__":
    save(make_vscode(), "screen_main.png")
    save(make_chrome_pair(), "screen_sub.png")
    save(make_echo(), "screen_echo.png")
    for name in MARKS:
        save(make_mark(name), f"mark_{name}.png")
