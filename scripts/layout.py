"""家具の配置 (bpy 非依存)。ガイド図 (tools/make_guide.py) と各 furniture_*.py の両方がここを読む。

座標系は room_spec.py と同じ (原点 = 南西の隅の床 / X=東 / Y=北 / Z=上、単位 m)。
各エントリ:
  x, y  置く場所の中心 (足元の中心)         z0  置く面の高さ (床なら 0)
  w     幅 (正面から見て左右)  d 奥行  h 高さ
  facing  正面が向く方角 "south" | "east" | "north" | "west"
  yaw     (省略可) facing からさらに、上から見て反時計回りに回す角度 (度)。斜めに置いた物 (サブモニター) だけに使う
  color   ガイド図で塗る色 (R, G, B)
"""
import math

from room_spec import *

# 家具の「正面」はローカルの -Y 向き。回転 0 で南向き、Z 軸まわりに反時計回りに増える (common.py もこれを使う)
FACING_DEG = {"south": 0, "east": 90, "north": 180, "west": 270}


def rotation_deg(entry):
    """家具を Z 軸まわりに回す角度 (度、反時計回り)。正面の向き + yaw"""
    return FACING_DEG[entry["facing"]] + entry.get("yaw", 0.0)


def corners(entry):
    """足元の四隅を、部屋の座標で [(x, y), ...] として返す (斜めに置いた物も正しく回す)。"""
    a = math.radians(rotation_deg(entry))
    c, s = math.cos(a), math.sin(a)
    hw, hd = entry["w"] / 2, entry["d"] / 2
    return [(entry["x"] + lx * c - ly * s, entry["y"] + lx * s + ly * c)
            for lx, ly in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))]


# ベッドの見えている上面 (マットレスに掛けたグレーのベッドカバーの上。マットレス本体の上面は 0.56)。ソファーの肘掛けの高さをこれに揃える
# (スツールも揃えていたが、2026-10-26 にユーザー指定で 3cm 低くした)
BED_TOP = 0.57
# ソファーの座面の高さ。白いサイドテーブルの高さをこれに揃える (ユーザー指定)
SOFA_SEAT = 0.42
# 木のスツール (ソファーの北と、本棚とデスク2の前の2つ。全く同じ物) の座面の1辺と高さ。
# 2026-10-26 に 0.40 角・BED_TOP から 3cm ずつ小さくした (ユーザー指定「もう一回り小さかった気がします。縦横高さを3cmずつ小さくして」)
_STOOL, _STOOL_H = 0.37, BED_TOP - 0.03
# ソファーの南北の中心: 北端を、北壁にくっつけたスツールとサイドテーブルの南の辺にくっつける (ソファーの幅 1.40)。
# ラグとローテーブルも同じ Y (ラグはソファーの前に同じ幅で敷き、ローテーブルはラグの中心)
_SOFA_Y = ROOM_D - _STOOL - 1.40 / 2
# カーテンレールの中心の高さ: エアコンの下端の少し下 (ユーザー指定)。掃き出し窓の上端 (room_spec.EAST_WINDOW の z1 = 1.80) はこの下
CURTAIN_ROD_Z = AIRCON["z0"] - 0.05

_win = EAST_WINDOW
_bay_cx = (NORTH_BAY["x0"] + NORTH_BAY["x1"]) / 2

# テレビ台の箱 (furniture_tv_stand.py)。L字棚1 の幅 1.3 = 板4枚 + 内法3つ から箱の間隔が決まり、L字棚2 も同じ箱
TV_BOARD = 0.018                     # 板の厚み
_TV_W1 = 1.30                        # L字棚1 の幅 (ユーザー指定 X 3.2〜4.5)
_TV_PITCH = (_TV_W1 - TV_BOARD) / 3  # 箱の間隔 (板1枚 + 内法)
_TV_W2 = 2 * _TV_PITCH + TV_BOARD    # L字棚2 の幅 (箱2つ)
_TV_TOP2 = TV_BOARD + 2 * _TV_PITCH + TV_BOARD   # L字棚2 の上面の高さ (L字棚1 に乗る分、板1枚だけ高い)

# 出窓の段ボール箱 2箱の幅 (box_tea / box_water)
_BOX_TEA_W, _BOX_WATER_W = 0.373, 0.417
# 段ボール箱の印刷の画像 (tools/make_boxes.py が描き、scripts/furniture_boxes.py が面ごとに貼る): 1mm = BOX_PPM 画素、大きさ BOX_IMAGE
BOX_PPM = 2.8
BOX_IMAGE = (2048, 1536)

FURNITURE = {
    # 東壁の掃き出し窓に掛ける。窓の中央に合わせる。2枚とも閉めた状態 (ユーザー指定)
    # h = 布の上端。レールは金属の角いレールで、布のフックをランナーに引っ掛ける。布の上端がレールより 1.3cm 上に出てレールの前を隠す
    # (2026-10-27 ユーザー指定「カーテンとの距離はかなり近く、低い視点から見るとカーテンレールは見えない」。furniture_curtain.Z_TOP)
    "curtain": dict(label="カーテン", x=ROOM_W - 0.06, y=(_win["y0"] + _win["y1"]) / 2, z0=0.0,
                    w=2.0, d=0.12, h=CURTAIN_ROD_Z + 0.02, facing="west", color=(125, 111, 99)),
    # 壁掛けのアナログ時計 (ユーザー指定: カーテンレールと天井の間の真ん中)。東壁、カーテンの中央の上。直径 0.36 (写真 reference/IMG_1100 から)。
    # z0 = 下端。針はビューアが今の時刻に合わせて回す
    "clock": dict(label="時計", x=ROOM_W - 0.025, y=(_win["y0"] + _win["y1"]) / 2, z0=(CURTAIN_ROD_Z + ROOM_H) / 2 - 0.18,
                  w=0.36, d=0.05, h=0.36, facing="west", color=(240, 240, 238)),
    # ダブルベッド。頭を北壁 (出窓の下) に付け、長辺を南北に向ける (西壁のクローゼットの扉と平行)。
    # 範囲 X 0.40〜1.80 / Y 1.5〜3.6 (ユーザー指定)。ヘッドボードの高さ 0.85m は出窓の天板 (下面 0.86m) のすぐ下。
    # 正面 = 足元側 (南)
    "bed": dict(label="ベッド (頭=北)", x=1.10, y=2.55, z0=0.0,
                w=1.40, d=2.10, h=0.85, facing="south", color=(74, 50, 38)),
    # 2人掛けソファー。ベッドの東隣 (西壁のクローゼットと反対側)。正面 = 東 = 座るとテレビ (東壁) が前に来る。
    # 足元の範囲 X 1.80〜2.55 (背面をベッドの東端 1.80 にくっつける。座面のクッションは 2cm 前に出る)
    # Y 1.83〜3.23 (北端と北壁の間にスツールとサイドテーブル。2026-10-26 にスツールが小さくなった分、北へ 3cm 詰めた (ユーザー指定))。
    # h = 背もたれの上端。肘掛けの高さは BED_TOP、座面は SOFA_SEAT。
    # 2026-10-27 ユーザー指定「背もたれを 7cm 高く、座面とひじ掛け部分を 5cm 短く」: 背もたれ 0.78 → 0.85、奥行 0.80 → 0.75 (背面はベッドに付けたまま、前が 5cm 下がる)
    "sofa": dict(label="ソファー", x=1.80 + 0.75 / 2, y=_SOFA_Y, z0=0.0,
                 w=1.40, d=0.75, h=0.85, facing="east", color=(124, 136, 152)),
    # 木のスツール (reference/864-g01-2.jpg)。北壁とソファーの北端の間で、西側をベッドの東端 (X=1.80) にくっつける。
    # 座面は 0.37 角・高さ 0.54 (_STOOL・_STOOL_H。ユーザー指定。0.4 角・ベッドの上面の高さから 3cm ずつ小さくした)。範囲 X 1.80〜2.17 / Y 3.23〜3.60 (北壁にくっつく)
    "stool": dict(label="スツール", x=1.80 + _STOOL / 2, y=ROOM_D - _STOOL / 2, z0=0.0,
                  w=_STOOL, d=_STOOL, h=_STOOL_H, facing="south", color=(214, 178, 124)),
    # 白いサイドテーブル (天板も細い丸脚4本も白)。スツールの東隣にくっつけ、北壁沿いに置く。
    # Y (奥行) はスツールと同じ 3.23〜3.60、幅 0.70 (ユーザー指定。X 2.20〜2.80 → 2.90)。2026-10-26 にスツールが小さくなった分、西へ 3cm 詰めた (ユーザー指定) ので X 2.17〜2.87。
    # 高さはソファーの座面 (SOFA_SEAT) に揃える (ユーザー指定)
    "side_table": dict(label="サイドテーブル", x=1.80 + _STOOL + 0.70 / 2, y=ROOM_D - _STOOL / 2, z0=0.0,
                       w=0.70, d=_STOOL, h=SOFA_SEAT, facing="south", color=(240, 240, 236)),
    # ラグ (ほぼ白のベージュ)。ソファーの前に敷く。西端 2.70 は、前のソファーの本体の前面 (2.60) から 0.1 (ソファーを 5cm 短くしたので今は 0.15)。
    # 範囲 X 2.70〜3.70 / Y 1.83〜3.23 (ソファーの幅と同じ)。厚み 1.2cm。
    # 2026-10-27 ユーザー指定「カーテン方向に 10cm 伸ばす」: 東端 3.60 → 3.70 (柄の画像 tools/make_prints.py の RUG_D も合わせる)
    "rug": dict(label="ラグ", x=3.20, y=_SOFA_Y, z0=0.0,
                w=1.40, d=1.00, h=0.012, facing="west", color=(232, 224, 208)),
    # ローテーブル。ラグの中心に、長辺を南北 (ソファーと平行) に置く。0.45 (X) x 0.85 (Y)、高さ 0.30 (ユーザー指定)。
    # 2026-10-27 ユーザー指定「カーテン方向に 10cm 伸ばす」: 東西 0.35 → 0.45 (西端 2.975 はそのまま、東端 3.325 → 3.425。ラグと一緒に伸ばしたので、今もラグの中心)。
    # 天板はウォールナットの木目 (デスク2と同じ)。黒い角脚は短辺ごとに「ロ」の字の枠 (脚2本を天板の下と床でつなぐ)
    "table": dict(label="ローテーブル", x=3.20, y=_SOFA_Y, z0=0.012,
                  w=0.85, d=0.45, h=0.30, facing="west", color=(110, 76, 56)),
    # 南壁に沿って、ドア側 (西) からデスク1・デスク2・本棚の順に、すき間なく並べる (ユーザー指定)。正面 = 北 (南壁を向いて座る)
    # 部屋の東西を変えるたびに3つとも一緒にずらす (本棚と東壁の間の 0.2 はそのまま)。今は部屋 4.7 に合わせた位置
    # デスクは2台とも、南壁との間に 0.1 のすき間を空ける (ユーザー指定。幅はこちらで決めた)。本棚は壁にくっついたまま
    # デスク1: X 1.3〜2.3 / Y 0.1〜0.6 / 高さ 0.75 (1.2x0.7 から長辺・短辺とも 0.2 小さくした)。天板はナチュラルな明るい木目、黒い脚4本
    "desk1": dict(label="デスク1", x=1.80, y=0.35, z0=0.0,
                  w=1.00, d=0.50, h=0.75, facing="north", color=(196, 160, 112)),
    # デスク2: X 2.3〜3.5 / Y 0.1〜0.6 / 高さ 0.75 (1.4x0.7 から 0.2 ずつ小さく)。天板はウォールナット、黒い脚4本。西端をデスク1、東端を本棚にくっつける
    "desk2": dict(label="デスク2", x=2.90, y=0.35, z0=0.0,
                  w=1.20, d=0.50, h=0.75, facing="north", color=(110, 76, 56)),
    # 本棚: X 3.5〜4.5 / Y 0〜0.4 / 高さ 2.0。ウォールナット。
    # 2列 x 4段の正方形の箱を積んだ形 (reference/61ui-F6+2nL._AC_SL1000_.jpg)。扉は4枚で、上の段から 左・右・左・右 (正面から見て)
    "bookshelf": dict(label="本棚", x=4.00, y=0.20, z0=0.0,
                      w=1.00, d=0.40, h=2.00, facing="north", color=(92, 62, 44)),
    # 突っ張り棒の棚 (写真 reference/IMG_1099)。デスク2の奥 (南壁とデスクのすき間) に、床から天井まで突っ張る黒い柱2本と、宙に浮いた黒っぽい棚板2枚。
    # 幅は「デスク2の左 (東端) から 5分の4」(ユーザー指定) = X 2.54〜3.50。棚板は奥行 0.30 (Y 0.01〜0.31、デスクの奥の上に出る)。h = 天井まで
    "tension_shelf": dict(label="突っ張り棚", x=3.02, y=0.16, z0=0.0,
                          w=0.96, d=0.30, h=ROOM_H, facing="north", color=(58, 54, 52)),
    # ハンガーを掛けるフックのレール (写真)。南壁の、突っ張り棚の西隣から、デスクの幅 (1.2。ユーザー指定「デスク幅と同じ」) だけ西へ。
    # X 1.30〜2.50 (西端はデスク1の西端と同じ)。z0 = レールの下端 (中心 1.85 は写真で突っ張り棚の上の棚板と同じくらい)。白いトートバッグ・黒いトートバッグ・ワイシャツを掛ける
    "hanger_rail": dict(label="フックのレール", x=1.90, y=0.009, z0=1.825,
                        w=1.20, d=0.018, h=0.05, facing="north", color=(213, 205, 194)),
    # テレビ台は正方形の箱の棚2つを組み合わせたもの (ユーザー指定)。どちらも背板が無く、奥の壁が見えるトンネル状。色はデスク1と同じオーク。
    # L字棚1: 箱4つ (下に3つ並べ、西端の上に1つ積む)。北東の隅に、北壁と東壁にくっつける。Y 3.2〜3.6、幅 1.3 (ユーザー指定 X 3.2〜4.5。部屋を 4.7 にしたので今は X 3.4〜4.7)。
    # 正面 = 南 (箱の口が部屋側)。h = 2段の部分の高さ
    "tv_shelf1": dict(label="L字棚1", x=ROOM_W - _TV_W1 / 2, y=ROOM_D - 0.20, z0=0.0,
                      w=_TV_W1, d=0.40, h=2 * _TV_PITCH + TV_BOARD, facing="south", color=(214, 178, 124)),
    # L字棚2: 箱3つの L 字を上下逆さにして、エアコンの下の東壁に西向きに置く。正面 (西) から見て
    #   □□      上の段の北の箱は L字棚1 の東端の箱の上に乗る。下の段の南の箱は床に立つ
    #    □      (その分、棚全体が板1枚ぶん浮くので、床に着く板は下へ伸ばす)
    # 上の段の箱2つ分の幅にテレビを載せる。奥行 0.40 は L字棚1 と同じ
    "tv_shelf2": dict(label="L字棚2", x=ROOM_W - 0.20, y=ROOM_D - _TV_W2 / 2, z0=TV_BOARD,
                      w=_TV_W2, d=0.40, h=2 * _TV_PITCH + TV_BOARD, facing="west", color=(214, 178, 124)),
    # テレビ: L字棚2 の上面の中央に、西向き (ソファーの方) に置く。大きさは仮に 32型 (ユーザーの指定なし)
    "tv": dict(label="テレビ", x=ROOM_W - 0.20, y=ROOM_D - _TV_W2 / 2, z0=_TV_TOP2,
               w=0.73, d=0.18, h=0.49, facing="west", color=(30, 30, 34)),
    # 出窓の天板 (高さ 0.90m) に置いた箱買いの段ボール箱 (ユーザー指定の商品。大きさは商品の情報)。正面 (商品名の面) は室内側 (南)。
    # お茶 = 伊藤園 ラベルレス お～いお茶 緑茶 460ml x 30本 (37.3 x 30.9 x 22.0cm) / 水 = い・ろ・は・す ラベルレス 560ml x 24本 (41.7 x 27.6 x 22.8cm)。
    # きれいに並べず、それぞれ傾ける (ユーザー指定): お茶は反時計回りに 15° (西の端が手前)・少し奥、水は時計回りに 15° (東の端が手前)。
    # 目の高さが箱の上面とほぼ同じなので、小さな角度 (2〜4°、7°/11°) では目の位置から傾きが見えなかった。
    # 目は箱の南東にあるので、お茶 (反時計回り) は目の方へ正面を向け、水 (時計回り) は東の側面を大きく見せて、2箱の向きの違いを出す。
    # 2箱の間は一番近い所で 6cm。2箱を合わせた範囲の中心が出窓の中央 (X 1.15。窓の幅を変えても追従する)。奥はガラスの下の枠 (Y 4.01) の手前
    "box_tea": dict(label="箱(お茶)", x=_bay_cx - 0.265, y=ROOM_D + 0.20, z0=NORTH_BAY["sill_z"],
                    w=_BOX_TEA_W, d=0.309, h=0.220, facing="south", yaw=15.0, color=(101, 169, 47)),
    "box_water": dict(label="箱(水)", x=_bay_cx + 0.255, y=ROOM_D + 0.185, z0=NORTH_BAY["sill_z"],
                      w=_BOX_WATER_W, d=0.276, h=0.228, facing="south", yaw=-15.0, color=(217, 186, 131)),
}

# ---- 机の上の物。机の位置から決めるので、机をずらせば一緒に動く ----
_d1, _d2 = FURNITURE["desk1"], FURNITURE["desk2"]
_d1_x0 = _d1["x"] - _d1["w"] / 2               # デスク1の西端
_d2_x0 = _d2["x"] - _d2["w"] / 2               # デスク2の西端 (= デスク1の東端)
_desk_y0 = _d1["y"] - _d1["d"] / 2             # デスクの奥の端 (南)
_desk_y1 = _d1["y"] + _d1["d"] / 2             # デスクの手前の端 (北)
_PC_W, _PC_D = 0.208, 0.37
_PR_W, _PR_D = 0.400, 0.343
_pc_x0 = _d2_x0 - 0.005 - _PC_W                # PC の西端 (東端はデスク2との境目の 5mm 手前)
# モニター (scripts/furniture_monitor.py)。寸法は商品の図面とカタログの値
_MAIN_W, _MAIN_D, _MAIN_H = 0.5503, 0.2306, 0.522   # GigaCrysta LCD-GC242HXB: 幅 x 台座の奥行 x 高さ (スタンドを一番上まで伸ばした高さ)
_MAIN_FRONT = 0.0424                           # 画面の前面は台座の中心より 4.24cm 前 (台座の前の端から 72.9mm 奥)
# GigaCrysta の台座の形 (台座の中心が原点のローカル座標、上から見て反時計回り)。前の辺 → 右 (正面から見て) の青い斜めの面 → 奥の角 → … → 左の青い面。
# 文庫本を左右の青い辺に沿わせて置くので、ここに置く (furniture_monitor.py もこれを使う)
GC_BASE = [(-0.1225, -0.1153), (0.1225, -0.1153), (0.1384, 0.0927), (0.0409, 0.1153), (-0.0409, 0.1153), (-0.1384, 0.0927)]
# メインモニターの中心 (デスク2の西寄り)。デスク2の西端から 0.35。
# 2026-10-25 に 0.33 → 0.35: 台座の西の青い辺に沿わせた文庫本 (2) の西に、コースターとペン立て (どちらも約 9cm 角) を机の西の端までに並べる幅が要るため
_MAIN_X = _d2_x0 + 0.35
_MAIN_Y = _desk_y0 + 0.01 + _MAIN_D / 2        # 台座の中心 (台座の後ろはデスクの奥の端から 1cm)
_main_screen_y = _MAIN_Y + _MAIN_FRONT         # メインの画面の前面の Y
_SUB_W, _SUB_D, _SUB_H = 0.462, 0.143, 0.300   # REGZA 19S22: 幅 x 台座の奥行 x 高さ (スタンド込み)
_SUB_FRONT = 0.0286                            # 画面の前面は台座の中心より 2.86cm 前 (台座の前の端から 43mm 奥)
_SUB_YAW = 30.0                                # サブモニターを座る人 (メインの前) の方へ向ける角度
# サブの台座の中心: 回した後の画面の西の端 (前面) が、メインの画面の東の端から 1cm 東・メインの画面の前面と同じ Y に来る位置
_t = math.radians(_SUB_YAW)
_SUB_X = _MAIN_X + _MAIN_W / 2 + 0.01 + _SUB_W / 2 * math.cos(_t) + _SUB_FRONT * math.sin(_t)
_SUB_Y = _main_screen_y + _SUB_W / 2 * math.sin(_t) - _SUB_FRONT * math.cos(_t)
# サブの台 (ユーザー指定の組み方): 白い小物入れ2つ (縦 x 横 x 高さ) を、口が手前に見えるように立てて (高さ = 縦) 左右に並べ、2つ用のふたをかぶせる。
# ふたの内側は、小物入れ2つを並べた形より縦横 4mm ずつ広い。ふたの縦横はサブの台座 (230 x 143mm) と同じくらい (ユーザー指定)。
# 小物入れの縦と横はふたから決め (ユーザーの目安 10 x 7cm より大きくなった)、高さは目安の比 (縦の 0.6 倍) にした
_LID_W, _LID_D, _LID_T = 0.233, 0.146, 0.0015   # ふたの外寸 (台座より 1.5mm ずつ大きい)・紙の厚み
_CASE_A = _LID_D - 2 * _LID_T - 0.004            # 小物入れの縦 = 立てたときの高さ (0.139)
_CASE = (_CASE_A, (_LID_W - 2 * _LID_T - 0.004) / 2, 0.6 * _CASE_A)   # 小物入れの 縦 x 横 x 高さ (0.139 x 0.113 x 0.083)
_SUB_BOX_H = _CASE_A + _LID_T                    # 台の高さ = 立てた小物入れ + ふたの天板 (0.1405)
_KB_W, _KB_D = 0.475, 0.150                    # キーボード Logicool G813 (幅 475 x 奥行 150 x 高さ 22mm)
_MS_W, _MS_D = 0.080, 0.130                    # マウス Logicool G604 (幅 80 x 長さ 130 x 高さ 45mm)
_KB_X = _MAIN_X + 0.02                         # キーボードの中心: 座る人 (メインの正面) より 2cm 東 (右手側の PC との間にマウスの場所を空ける)
_COASTER = 0.095                               # セリアのラバーウッドコースター (角)。大きさは写真からの見積もり (約 9.5cm 角・厚み 9mm)
_COASTER_X0, _COASTER_Y0 = _d2_x0 + 0.009, _desk_y0 + 0.18   # コースターの西の端・奥の端 (机の西の端から 9mm)
_PEN = 0.080                                   # ダイソーのペンスタンド L。商品は 9 x 9 x 11cm だが、2026-10-27 にユーザー指定で縦横を 1cm ずつ小さく (8 x 8 x 11cm)
_TRASH = 0.090                                 # 新聞紙やチラシを折って作った卓上のゴミ箱 (上の開いた箱)。1辺はコースターくらい (ユーザー指定)
_TRASH_H = round(_TRASH * 0.9, 4)              # ゴミ箱の高さ: 2026-10-27 ユーザー指定で1辺の 0.9 倍 (8.1cm)。畳むと底の正方形 (1辺) の板になる


def _world_xy(entry, lx, ly):
    """家具のローカル座標 (lx, ly) を部屋の座標にする"""
    a = math.radians(rotation_deg(entry))
    return entry["x"] + lx * math.cos(a) - ly * math.sin(a), entry["y"] + lx * math.sin(a) + ly * math.cos(a)


def _along_edge(a, b, w, l, outward_west, gap=0.0004):
    """辺 a (前の角) → b (奥の角) に長い方の辺を沿わせ、前を揃えて外側に置いた w x l の物の中心と yaw (北向きからの角度)。
    物の頭 (ローカル +Y) は奥を向く。gap = 辺とのすき間"""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, ny = (dy, -dx) if (dy < 0) == outward_west else (-dy, dx)   # 外向きの法線 (西 or 東)
    cx = a[0] + dx * l / 2 + nx * (w / 2 + gap)
    cy = a[1] + dy * l / 2 + ny * (w / 2 + gap)
    return cx, cy, (math.degrees(math.atan2(-dx, dy)) - FACING_DEG["north"] + 180) % 360 - 180
FURNITURE.update({
    # デスクトップPC。ケースは In Win 301 白 (IW-CF07B 301-White、幅 208 x 高さ 365 x 奥行 370mm)。
    # デスク1の天板の東端に、デスク2との境目ぎりぎりまで寄せて置く (ユーザー指定)。正面 (電源ボタン・IN WIN のロゴ) = 北 = 座る側。
    # ガラスの側面は正面から見て左 = 東 (メインモニター・椅子の側)。デスクのかなり手前に置く (ユーザー指定。手前の端から 1cm)
    "pc": dict(label="PC", x=_pc_x0 + _PC_W / 2, y=_desk_y1 - 0.01 - _PC_D / 2, z0=_d1["h"],
               w=_PC_W, d=_PC_D, h=0.365, facing="north", color=(240, 240, 240)),
    # プリンター。ブラザー PRIVIO DCP-J1800N (白、幅 400 x 奥行 343 x 高さ 172mm。ユーザーが商品ページを指定)。
    # デスク1の残りの場所 (西端〜PC の西端) の中央。PC と同じく、かなり手前 (手前の端から 1cm)
    "printer": dict(label="プリンター", x=(_d1_x0 + _pc_x0) / 2, y=_desk_y1 - 0.01 - _PR_D / 2, z0=_d1["h"],
                    w=_PR_W, d=_PR_D, h=0.172, facing="north", color=(226, 226, 222)),
    # メインモニター: アイ・オー・データ GigaCrysta LCD-GC242HXB/D (23.6型。ユーザー指定)。デスク2の西寄り = PC に近い側 (ユーザー指定)。
    # 机に直に置く (モニタースタンドは無し。ユーザー指定)。高さを変えられるスタンドを一番上まで伸ばして、画面の中心を目線の高さ近く (1.11m) にしている
    "monitor_main": dict(label="メインモニター", x=_MAIN_X, y=_MAIN_Y, z0=_d2["h"],
                         w=_MAIN_W, d=_MAIN_D, h=_MAIN_H, facing="north", color=(30, 30, 34), screen_front=_MAIN_FRONT),
    # サブモニターの台 (白い小物入れ2つ + ふた。ユーザー指定)。左の小物入れはふたの奥の縁へ、右は手前の縁へ寄せる
    # (前後にすき間があると、ふたがずれて安定しないため)。サブモニターと一緒に斜めに置く。w x d = ふたの外寸
    "monitor_boxes": dict(label="白い箱", x=_SUB_X, y=_SUB_Y, z0=_d2["h"],
                          w=_LID_W, d=_LID_D, h=_SUB_BOX_H, facing="north", yaw=_SUB_YAW, color=(244, 244, 240),
                          case=_CASE, lid_t=_LID_T),
    # サブモニター: 東芝 REGZA 19S22 (19型の液晶テレビ。ユーザー指定)。メインの東隣で、白い箱の台に乗せる (ユーザー指定)。
    # 台の高さは組み方で決まるので、画面の上端はメインより 8cm 低い (写真 IMG_1099 でも 10cm ほど低い)。
    # 座るのはメインの前なので、座る人の方へ斜めに向ける (ユーザー指定。角度 30°はこちらで決めた)
    "monitor_sub": dict(label="サブモニター", x=_SUB_X, y=_SUB_Y, z0=_d2["h"] + _SUB_BOX_H,
                        w=_SUB_W, d=_SUB_D, h=_SUB_H, facing="north", yaw=_SUB_YAW, color=(30, 30, 34), screen_front=_SUB_FRONT),
})

# ---- デスク2の上の小物 (2026-10-25 ユーザー指定)。左右は座る人から見た向き (南を向いて座るので、左 = 東・右 = 西) ----
_EYE = (_MAIN_X, _main_screen_y + 0.70)        # ビューアの目の位置 (VIEW) の X, Y
_base = [_world_xy(FURNITURE["monitor_main"], x, y) for x, y in GC_BASE]   # メインの台座の角 (部屋の座標): 0 = 前の東・1 = 前の西・2 = 西の奥・5 = 東の奥
_BOOK = (0.105, 0.148)                         # 文庫本 (A6) の幅 x 長さ
_b1 = _along_edge(_base[0], _base[5], *_BOOK, outward_west=False)   # 本 (1): 台座の東 (左) の青い辺に沿わせる
_b2 = _along_edge(_base[1], _base[2], *_BOOK, outward_west=True)    # 本 (2): 台座の西 (右) の青い辺に沿わせる
_ms_y = _COASTER_Y0 + _COASTER + 0.012 + _MS_D / 2   # マウスの中心: コースターの 1.2cm 手前
_ECHO = (_MAIN_X + 0.344, _desk_y0 + 0.089)    # Echo Show 5 の足元の中心 (本 (1) とサブの台の間。どちらとも 2.5cm ほど空く)
_TRASH_XY = (_KB_X + _KB_W / 2 + 0.0065 + _TRASH / 2, _ECHO[1] + 0.17)   # ゴミ箱の中心: Echo Show の 17cm 前 (2026-10-27 ユーザー指定「少し奥」で 3cm 奥へ)、キーボードの東の端の 6.5mm 東
FURNITURE.update({
    # キーボード: Logicool G ゲーミングキーボード G813 (ユーザー指定)。座る人 (メインの正面) より 2cm 東、デスクの手前の端から 8cm
    "keyboard": dict(label="キーボード", x=_KB_X, y=_desk_y1 - 0.08 - _KB_D / 2, z0=_d2["h"],
                     w=_KB_W, d=_KB_D, h=0.022, facing="north", color=(30, 30, 34)),
    # マウス: Logicool G604 LIGHTSPEED (ユーザー指定)。右手側 (西) の、キーボードと PC の間の真ん中。
    # コースターの手前 (ユーザー指定「マウスの奥にコースター」)。手のひらの側を座る人の右肩へ少し向ける (yaw)
    "mouse": dict(label="マウス", x=(_KB_X - _KB_W / 2 + _pc_x0 + _PC_W) / 2, y=_ms_y, z0=_d2["h"],
                  w=_MS_W, d=_MS_D, h=0.045, facing="north", yaw=-8.0, color=(30, 30, 34)),
    # 文庫本 2冊 (ユーザー指定): モニターの足の左に「物理さんで無双してたらモテモテになりました (1)」、右に「(2)」。重ねず、それぞれ足の青い辺に接する。
    # 表紙を上にして、本の頭をモニターの方 (奥) へ。長い辺を青い辺に沿わせ (斜め 4.4°)、手前の端を台座の前の角に揃えた。厚みは見積もり
    "book1": dict(label="本(1)", x=_b1[0], y=_b1[1], z0=_d2["h"], w=_BOOK[0], d=_BOOK[1], h=0.0135,
                  facing="north", yaw=_b1[2], color=(236, 128, 168)),
    "book2": dict(label="本(2)", x=_b2[0], y=_b2[1], z0=_d2["h"], w=_BOOK[0], d=_BOOK[1], h=0.012,
                  facing="north", yaw=_b2[2], color=(240, 164, 72)),
    # セリアの木製のコースター (ラバーウッドコースター ロゴ柄 角。ユーザー指定): 本 (2) のさらに右 (西)、マウスの奥。ORIGINAL TASTE の字の上を奥へ
    "coaster": dict(label="コースター", x=_COASTER_X0 + _COASTER / 2, y=_COASTER_Y0 + _COASTER / 2, z0=_d2["h"],
                    w=_COASTER, d=_COASTER, h=0.009, facing="north", color=(222, 196, 160)),
    # ダイソーのペンスタンド (チャコールグレー、サイズ L。ユーザー指定。色は 2026-10-27 にユーザー指定でもう少し明るいグレー): コースターの奥 (1cm 空ける)。
    # 編んだ帯の四角柱に、白い柄のハサミ・黒いボールペン2本・赤ペン
    "pen_stand": dict(label="ペン立て", x=_COASTER_X0 + _COASTER / 2, y=_COASTER_Y0 - 0.010 - _PEN / 2, z0=_d2["h"],
                      w=_PEN, d=_PEN, h=0.110, facing="north", color=(100, 101, 106)),
    # Amazon Echo Show 5 (第3世代 チャコール。ユーザー指定): 本 (1) とサブモニターの台の間。画面を座る人の方へ向ける。w x d = 足元 (148 x 73mm)、高さ 86mm
    "echo_show": dict(label="Echo Show 5", x=_ECHO[0], y=_ECHO[1], z0=_d2["h"], w=0.148, d=0.073, h=0.086, facing="north",
                      yaw=math.degrees(math.atan2(_ECHO[0] - _EYE[0], _EYE[1] - _ECHO[1])), color=(44, 44, 48)),
    # 新聞紙で折った卓上のゴミ箱 (2026-10-27 ユーザー指定「Echo show 5 の前の空間に置かれている」。参考の動画の「畳めるゴミ箱」)。
    # Echo Show とキーボードの東の端の間の、Echo Show の前 (座る人の側)。続きの指示「少し奥・高さを 0.9 倍」で 3cm 奥へ、高さ 8.1cm に
    # (Echo Show の手前の端と 6cm 空く。目の位置から Echo Show の画面の左下に少しかかる)。
    # 東はサブの台の白い箱の角と 1cm 空く。手で置いた物なので、時計回りに 3°だけ斜め
    "trash_box": dict(label="ゴミ箱", x=_TRASH_XY[0], y=_TRASH_XY[1], z0=_d2["h"], w=_TRASH, d=_TRASH, h=_TRASH_H, facing="north", yaw=-3.0,
                      color=(206, 203, 194)),
})
# 2つ目の木のスツール (2026-10-26 ユーザー指定「本棚とデスク2の足の前に、ソファー横のスツールと全く同じスツールを適当にずらして」)。
# 大きさ・高さ・色はソファー横の stool のまま。デスク2の東端 (= 本棚の西端) の前に両方にまたがって置き、斜めに回す (きれいに揃えない)。
# 2026-10-27 にラグの側 (北) へ 20cm 寄せた (ユーザー指定)。一番奥の角はデスク2の前の縁から 22cm 手前、北の角とラグの南の辺は 55cm 空く。座面に丸い座布団 (furniture_stool._cushion)
_d2_x1 = _d2["x"] + _d2["w"] / 2               # デスク2の東端 (= 本棚の西端)
FURNITURE["stool2"] = dict(FURNITURE["stool"], label="スツール2", x=_d2_x1 + 0.05, y=_desk_y1 + 0.45, yaw=16.0)
# ビューアの目の位置 (椅子に座ってメインモニターに向かう目線) と、最初に向く先。部屋の座標 (m)。
# glb の extras でビューアへ渡す。焼き付けもここを使う (目に近い物ほどライトマップを細かくする・ツヤを目の位置から見た向きで焼く)
VIEW = dict(eye=(*_EYE, 1.15),                               # 画面から 0.7m、目の高さ 1.15
            target=(_MAIN_X, _main_screen_y, 1.0))           # メインモニターの真正面の少し下


def box_atlas(name):
    """段ボール箱の印刷の画像の中の面の並び {面: (左, 上, 右, 下)} (画素)。上の段に正面と側面、下の段に上面と印刷の無い面 (底)。
    背面は正面と、左右の側面は同じ絵 (実物の箱も同じ)。面の間は 16px 空ける (縮めた画像で隣の面の色がにじまないように)"""
    e = FURNITURE[name]
    w, d, h = (round(e[k] * 1000 * BOX_PPM) for k in ("w", "d", "h"))
    g = 16
    front, side = (0, 0, w, h), (w + g, 0, w + g + d, h)
    return dict(front=front, back=front, left=side, right=side, top=(0, h + g, w, h + g + d), plain=(w + g, h + g, w + g + d, h + g + d))


BOOK_PPM = 4   # 文庫本の画像 (tools/make_desk_items.py が描き、scripts/furniture_desk_items.py が面ごとに貼る): 1mm = BOOK_PPM 画素


def book_atlas(name):
    """文庫本の画像の中の面の並び {面: (左, 上, 右, 下)} (画素) と画像の大きさ。上の段に表紙と裏表紙、下の段に背と小口 (天・地・前の小口は同じ)。
    面は props.atlas_box_uvs の呼び方 (top = 表紙、right = 背 (+X)、left/front/back = 紙の小口)"""
    e = FURNITURE[name]
    w, l, t = (round(e[k] * 1000 * BOOK_PPM) for k in ("w", "d", "h"))
    g = 16
    pages = (l + g, l + g, 2 * l + g, l + g + t)
    rects = dict(top=(0, 0, w, l), bottom=(w + g, 0, 2 * w + g, l), right=(0, l + g, l, l + g + t),
                 left=pages, front=pages, back=pages)
    return rects, (2 * l + g, l + g + t)


def box_cases():
    """サブの台の小物入れ2つの外形 {"left": (x0, x1, y0, y1, 高さ), "right": ...} と板の厚み (monitor_boxes のローカル座標。正面 = -Y、X = 正面から見て右)。
    口を手前に向けて立て、左の小物入れはふたの奥の縁へ、右は手前の縁へ寄せる (ユーザー指定)。furniture_monitor.py (箱) と furniture_desk_items.py (中身) が使う"""
    e = FURNITURE["monitor_boxes"]
    a, b, c = e["case"]   # 小物入れの 縦 (= 立てた高さ) x 横 (= 幅) x 高さ (= 立てた奥行)
    iy = e["d"] / 2 - e["lid_t"]   # ふたの内側の奥行の半分
    return {"left": (-b, 0, iy - c, iy, a), "right": (0, b, -iy, -iy + c, a)}, e["lid_t"]


TRASH_PPM = 4                      # 紙のゴミ箱の画像 (tools/make_desk_items.py が描き、furniture_desk_items.py が面ごとに貼る): 1mm = TRASH_PPM 画素
TRASH_PAPERS = ("news", "red", "blue")   # 紙の種類: 新聞紙 / 赤と黄色のスーパーのチラシ / 青い住宅のチラシ


def trash_atlas():
    """紙のゴミ箱の画像の中の面の並び {名前: (左, 上, 右, 下)} (画素) と画像の大きさ。1つの枠 = ゴミ箱の1辺の正方形。
    out0〜3 / in0〜3 = 机の上のゴミ箱の壁の外 / 内 (前・右・奥・左。高さは1辺より低いので、枠の下から高さの分だけ使う)、bottom = 内側の底、fold_<紙> = 畳んだゴミ箱の表、
    edge_v_<紙> / edge_h_<紙> = 畳んだゴミ箱の縁 (紙の重なりの筋。縦長 / 横長)、plain = 無地の紙 (ゴミ箱の縁の上面など)"""
    s = round(_TRASH * 1000 * TRASH_PPM)
    g, t = 16, 16   # 枠の間・縁の帯の太さ
    cell = lambda col, row: (g + col * (s + g), g + row * (s + g), g + col * (s + g) + s, g + row * (s + g) + s)
    rects = {f"out{i}": cell(i, 0) for i in range(4)}
    rects.update({f"in{i}": cell(i, 1) for i in range(4)})
    rects["bottom"] = cell(0, 2)
    x4, y3 = g + 4 * (s + g), g + 3 * (s + g)
    for i, paper in enumerate(TRASH_PAPERS):
        rects[f"fold_{paper}"] = cell(i + 1, 2)
        rects[f"edge_v_{paper}"] = (x4 + i * (t + g), g, x4 + i * (t + g) + t, g + s)
        rects[f"edge_h_{paper}"] = (g, y3 + i * (t + g), g + s, y3 + i * (t + g) + t)
    rects["plain"] = (x4, 2 * g + s, x4 + 3 * t + 2 * g, 2 * g + s + 3 * t + 2 * g)
    return rects, (x4 + 3 * (t + g), y3 + 3 * (t + g))


def footprint(entry):
    """足元を囲む軸に平行な矩形を、部屋の座標で (x0, y0, x1, y1) として返す。"""
    xs, ys = zip(*corners(entry))
    return min(xs), min(ys), max(xs), max(ys)
