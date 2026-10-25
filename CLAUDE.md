# blender-works

Claude Code から Blender を操作して 3D モデリングするプロジェクト。

> **セッションを再開したら、まず `docs/HANDOFF.md` を読む。** 現在の進捗・決まったこと・未決事項・次の手順・ユーザーとの進め方が書いてある。
> 家具を作ったり配置を変えたりしたら、HANDOFF.md の「現在の状態」の表も更新する。

## 最終目標

自分のポートフォリオサイトのデザインとして、大学時代に住んでいたワンルームを3DCGで作る。
サイト内で部屋を360度見回せ、各家具にクリック判定を付けて自作のウェブアプリへリンクさせる。

- スタイル: [felixrieseberg.com](https://felixrieseberg.com/) のような写実寄り。**夜**、明るい白色のシーリングライト (最初は電球色だったが「暗すぎる」と言われて変えた)。家具付きのワンルーム
  (2026-10-18 にローポリから方向転換。ローポリは安っぽいとの判断)
- 資料: 間取り図のみ (写真なし)。少しずつ作って微修正を繰り返す
- 作成物: 部屋の外殻 + 以下のオブジェクト
  カーテン / 本棚 / ワークデスク / デスクトップPC / ベッド / テレビ台 / テレビ / ソファー / ローテーブル / ラグ
- 見せ方: カメラは1か所に固定して首振りだけ (歩かない)。デスク2の前の椅子に座って、メインモニター (PC の隣) に向かった目線を最初の向きにする
- 最終出力: `models/room.glb` + `models/room_lightmap.webp` (拡散光) + `models/room_glossmap.webp` (ツヤ) (Web 側は three.js)

## モデリング規約 (Web でのクリック判定を前提にする)

- 1 Blender unit = 1 m。Z up。座標系は `scripts/room_spec.py` の冒頭に定義:
  原点 = 南西の隅の床 / +X = 東 (西壁からの距離) / +Y = 北 (南壁からの距離) / +Z = 上。東西南北は間取り図の向き (上=北) に合わせた便宜上の呼び方
- 居室は内寸 4.7m (X) × 3.6m (Y) × 天井高 2.4m (10.0帖=16.2㎡と間取り図の縦横比から 4.5m と推定 → ユーザー指定で 5.0 → 4.5 → 4.7m)。
  開口部: 東壁=掃き出し窓 (高さ 1.8。カーテンレールをエアコンの下へ下げたため) / 西壁=ドアと収納折れ戸 / 北壁=出窓 (X 0.30〜2.00。腰高窓。壁の外へ0.45m出る。ガラスはコの字。天板の高さ0.90m) / 南壁=なし。
  エアコンは東壁の北寄り。東壁のカーテンレールと天井の間に壁掛け時計
- ユーザーは家具の位置を「どの壁から何 m、向きは○向き、大きさ 幅×奥行×高さ」で指示する。
  指示は `tools/make_guide.py` が作る `renders/guide_plan.png` (座標ガイド図) と同じ言い方に揃える
- クリック対象の家具は、1つの親 Empty (`bookshelf`, `desk1`, `desk2`, `pc`, `monitor_main`, `monitor_sub`, `bed`, `tv_stand`, `tv`, `sofa`, `table`, `rug`, `curtain`。デスクとモニターは2台ずつ) の下に
  パーツのメッシュをぶら下げる (間に Empty を挟んでもよい。テレビ台は `tv_stand` → `tv_shelf1` → メッシュ)。Web 側は子メッシュに当たった後に親をたどって名前で判定する
- 床・壁・天井は `room_floor` `room_wall_*` `room_ceiling` とし、クリック対象にしない
- 照明は Blender (Cycles) で2枚に焼き付け、Web 側はリアルタイムのライトを使わない (`scripts/bake.py`)。拡散光のライトマップと、
  目の位置 (`layout.VIEW`。カメラは動かないので) から見たツヤ・映り込みのグロスマップ (床に天井の明かりが映る)。
  形を変えたら必ず焼き直す (`build_all.py` が毎回やる)。glb と2枚の画像は対で使う
- 写実寄りにするため、テクスチャ (Poly Haven の CC0 素材) と細かい形を使う。直方体は角を 4mm 面取りする (`boxes_object` の `bevel`。床・壁・天井は 0)。
  布張りの物 (ソファー・マットレス・敷きパッド・マウス・エアコン) は角の丸い、ふくらんだ箱 `soft_boxes_object` (しわ `wrinkle`・もたれ `lean`)。ソファーは角ばった形 (丸み 1.2〜2.5cm) が好み。
  枕・クッション・トートバッグは2枚の布の縁を縫い合わせた形 `props.pillow_object` (縁が薄く真ん中が厚い)。毛布は Blender の布のシミュレーションでたぐり寄せた塊 (`furniture_bed._messy_blanket`)。
  布の色は `common.fabric_material(name, "cotton"|"canvas"|"towel", 色)` (白っぽい綿・帆布・キルティングのタオル地の画像に色を掛ける)。曲がった布は焼き付けの島を自分の展開で作る (`lightmap_uv`。`bake.py`)
  テクスチャは UV `UVMap` (実寸の箱投影、1 = 1m。`common.add_box_uvs` が `build_scene()` の最後に、UVMap の無い全メッシュへ付ける) に貼る。UV `lightmap` は焼き付け専用なので触らない。
  木目は `common.wood_material(name, "walnut"|"oak"|"honey"|"light", target=色)` (プリセットは `common.WOOD`。`target` で画像を暗くして色を合わせる)。
  **木目がはっきり見えてよいのはテーブル・デスク・フローリング (とベッドの枠) だけ** (ユーザー指定「少し気味が悪い」)。それ以外は木目を薄くした `*_soft` (`honey_soft` `oak_soft` `walnut_soft` `light_soft`) を使う。
  床・扉の色は物件情報 (https://unilife.co.jp/view/10170、同じ建物の別の部屋の写真) に合わせた。
  明るくしたい・色を大きく変えたい画像は `tools/make_textures.py` で Poly Haven の元画像から作る (glTF の色の倍率は 1 を超えられないため)
- 光る物 (照明のカバー・表示ランプ・モニターの画面) は材質に `emission` を付ける (画像ごと光らせるときは `make_material(..., texture=..., emission_texture=True)`)。
  ガラスは `alpha<1` (名前に `frosted` が入る材質はすりガラス)。どちらもライトマップを使わず Web 側で光らせる/透かす
- 家具の上や中の小物は、`props.world_group` (部屋の座標のままの Empty) を親の家具の下に挟んで入れる (クリックすると親の家具になる)。
  細い管 (針金など) はライトマップの島が潰れるので `tubes_object(..., light_from="近くの物")` で光を借りる
- **高さの約束**: ソファーの肘掛けの上面・スツールの高さ・ベッドの見えている上面 (マットレスに掛けた敷きパッドの上。毛布はその上に乗る) は全て `layout.BED_TOP` (0.57m) に揃える (ユーザー指定)。
  ベッドの寸法を変えるときは `BED_TOP` だけ直す (マットレス本体の上面は 0.56m)
  白いサイドテーブルの高さはソファーの座面 `layout.SOFA_SEAT` (0.42m) に揃える (ユーザー指定)
- ユーザーの指示は短い言葉で来ることが多い。曖昧なら妥当に解釈して作り、**解釈と座標 (X/Y の範囲・向き・高さ) を明記して返す**。質問で止めない。
  コミットはユーザーが求めるまでしない

## 仕組み

WSL から Windows 版 Blender 5.2 LTS (`/mnt/c/Users/kouta/AppData/Local/Programs/Blender Foundation/Blender 5.2/blender.exe`) を
バックグラウンド起動し、Python (bpy) スクリプトでモデルを作る。焼き付けは Cycles + GPU (GTX 1660 SUPER, OptiX)。
(旧 2.92 も `C:\Program Files\Blender Foundation\Blender 2.92` に残っている。`BLENDER_EXE=... ./run_blender.sh` で切り替えられる)

```bash
./run_blender.sh scripts/<name>.py
```

- `scripts/common.py` — 材質 (`'#RRGGBB'` で指定。`texture=` で画像 × 色。`roughness`/`specular` はツヤの焼き付けに効く)・木目の材質 `wood_material`・布の材質 `fabric_material`・画像の色合わせ `tint`・テクスチャ用 UV `add_box_uvs`・
  `boxes_object` (直方体の集合を1メッシュにする。角を面取り。傾いた6面体は `solids_object`)・`soft_boxes_object` (角の丸いふくらんだ箱)・レンダリング・保存/書き出しのヘルパー
- `scripts/props.py` — 小物用のヘルパー (common の上に乗る。`from props import *` で common も入る): 本 `book_row` `book_stack` `books_object` (背は `textures/book_spines.jpg` の柄)・
  回転体 `lathe_object`・管 `tubes_object`・帯 `strap_mesh`・回した直方体 `rot_box` + `place`・絵の板 `image_quad` `framed_picture`・口の開いた箱 `open_box`・
  形を曲げる `deform` と布のしわ `folds`・部屋の座標で置く物の親 `world_group`・枕とクッション `pillow_object`・印刷のある箱の面ごとの UV `atlas_box_uvs` (箱の面を1枚の画像に並べて貼る)
- `scripts/room_spec.py` — 部屋の寸法と開口部 (bpy 非依存。ガイド図ツールも読む)
- `scripts/build_room.py` — 部屋の外殻 (床・壁・天井・窓・ドア・収納扉・エアコン・シーリングライト `room_ceiling_light`・インターホン `room_intercom`)。
  物件写真に合わせて: はちみつ色のツヤのあるフローリング・白いエンボスの壁紙・木目のドア (縦長のすりガラス2本・真鍮色のレバー)・収納の折れ戸 (真鍮色のつまみ)・
  ドア/収納/窓のまわりの木の額縁・濃い木目の巾木・こげ茶のアルミサッシ (掃き出し窓の下半分はすりガラス。当時の写真)。エアコン (写真の形) は Empty `aircon` → `aircon_body` (丸い箱の本体・前面パネル・南の端の表示部・閉じた風向きの板) + `aircon_parts` (すき間・吹き出し口・表示の窓とランプ・社名の代わりの帯)。
  その下 (北の端の真下) に専用のコンセント `room_outlet_aircon` (プラグと線)、テレビの上の東壁に壁掛けのリモコン `room_aircon_remote`
- `scripts/views.py` — 確認画像用の昼のプレビュー照明とカメラ (真上 / 南西・南東・北東の断面 / 隅の目線)。`.glb` には出ない
- `scripts/lighting.py` — 夜の照明 (焼き付け用)。光源はシーリングライトの乳白カバーの発光 (強さと色は `room_spec.CEILING_LIGHT`) と、出窓の外の弱い青白い面光源
- `scripts/bake.py` — 焼き付け。全メッシュに UV `lightmap` を作り (Smart UV Project で島に分け、目に近い島ほど大きく棚詰め)、全メッシュの複製を1つにまとめて
  Cycles で拡散光 (DIFFUSE) とツヤ (GLOSSY、目の位置のカメラ `bake_eye` から見た向き) を焼き、OIDN でノイズを取って WebP (8bit sRGB) に保存する。
  明るさの倍率 K は glb の extras (`lightmap_intensity` `glossmap_intensity`)、目の位置は `eye` `home_target` で Web へ渡す。
  カスタムプロパティ `lightmap_proxy` (= `tubes_object` の `light_from`) が付いた物は島を作らず、借りる先の1点の光を使う。
  `lightmap_uv` (= 自分で作った重ならない展開の UV の名前。カーテン・毛布・`pillow_object`) が付いた物は、Smart UV の代わりにその展開で島を作る (曲面の細かい島の継ぎ目がまだらに見えるため)
- `scripts/build_all.py` — 外殻 + 家具を組み立て、確認画像 → 夜の照明の焼き付け → `models/room.blend` `room.glb` `room_lightmap.webp` `room_glossmap.webp` を出す (4096px・256 サンプルで約 10 分。焼き付けが拡散光 5 分 + ツヤ 2.5 分)。
  家具は `build_scene()` に足していく。形を急いで確かめるときは `--samples 32 --size 2048 --no-render` (約 55 秒。ざらつく)
- `scripts/closeup.py` — 家具の近くから見た確認画像 `renders/closeup_*.png` を撮る (`VIEWS` を書き換えて使う。見たら消す)。`build_scene()` を使うので glb は書き換えない
- `scripts/layout.py` — **家具の配置データ** (bpy 非依存。位置 x,y・置く高さ z0・幅/奥行/高さ・正面の向き)。ガイド図と各 furniture_*.py が読む。
  斜めに置く物だけ `yaw` (facing からさらに反時計回りに回す角度) を持つ。回転は `rotation_deg()`、足元の四隅は `corners()`。
  ユーザーから位置・向き・大きさの指示が来たら、まずここを直す。ビューアの目の位置 `VIEW` (メインモニターの前の椅子。焼き付けも使う) もここ
- `scripts/furniture_bed.py` — ダブルベッド (頭=北の出窓の下、長辺は南北)。`bed_frame` (土台と脚。暗くしたウォールナット) + `bed_headboard` (木目を薄く) + `bed_bedding` (くすんだピンクの厚いマットレス。**土台と同じ幅と長さで、土台の上面は見えない** (ユーザー指定)) +
  `bed_cover` (敷きパッド = ユーザーの言う「ベッドカバー」。グレーのタオル地にキルティングの縫い目 `fabric_material(..., "towel", ...)`。縁の丸い布) +
  `bed_pillow` (ネイビー。`props.pillow_object`) + `bed_blanket` (黒のフリースの毛布。広げた布を、形のキー "gather" へ縁を弱く引きながら布のシミュレーションでたぐり寄せ、
  高さ 約 26cm の無造作な塊にする。曲げの硬さを強くして大きく丸いヒダ。毎回同じ形。焼き付けの島は布の展開 + 裏面)。
  ヘッドボードの高さ 0.85m は出窓の天板の下面 (0.86m) に当たらない高さ
- `scripts/furniture_sofa.py` — 2人掛けソファー (青みがかったグレーのヘリンボーンの布、東向き。背面をベッドの東端にくっつける。丸い木の脚)。`sofa_body` + `sofa_cushions` + `sofa_legs`。
  背もたれに立て掛けたクッション2つ (北の席 = 細いボーダー `sofa_pillow_stripe` / 南の席 = ライトグレー `sofa_pillow_gray`。写真。`props.pillow_object`)。
  布の部分は全て `soft_boxes_object` (角の丸みは小さく、角ばった形)。肘掛けは飾りなしの平らな箱 (上面はふくらませない)。背クッションは `lean` で後ろへ傾けている
- `scripts/furniture_stool.py` — 木のスツール (`reference/864-g01-2.jpg`、座面 0.4 角)。北壁とソファーの北端の間に、西側をベッドの東端にくっつけて置く。
  クリック対象には未登録 (`CLICKABLE` に入れていない)
- `scripts/furniture_side_table.py` — 白いサイドテーブル (細い丸脚4本)。スツールの東隣、北壁沿い。クリック対象には未登録
- `scripts/furniture_rug.py` — ラグ (写真の柄: ベージュのキルトに犬・猫の絵と筆記体の字。画像 `textures/rug_print.jpg` をラグ全体に1枚。角は丸く、縁はふっくら)。ソファーと同じ大きさで、ソファーの前
- `scripts/furniture_table.py` — ローテーブル (ウォールナットの天板 + 短辺ごとに「ロ」の字の黒い角脚)。ラグの中心。
  天板の上の小物 `table_items` (印刷を貼ったティッシュの箱 (`textures/tissue_box.jpg`) とリモコン・ウェットティッシュ・黄色いタイマー。写真)
- `scripts/furniture_boxes.py` — 出窓の天板に置いた段ボール箱2箱。ユーザー指定の実在の商品の箱: `box_tea` = 伊藤園 ラベルレス お～いお茶 緑茶 460ml×30本 (Smart Bottle BOX) /
  `box_water` = い・ろ・は・す ラベルレス 560ml×24本 (ラベルレスの箱は 560ml)。外寸は商品の寸法 (`layout.py`)。きれいに並べず、それぞれ斜め (`yaw`。お茶 +15° / 水 -15°。目の高さが箱の上面とほぼ同じなので、小さな角度では傾きが見えない)。
  印刷 `textures/box_tea.jpg` `box_water.jpg` (`tools/make_boxes.py`) を `props.atlas_box_uvs` で面ごとに貼る (面の並びは `layout.box_atlas`)。実物は糊で閉じてあるのでテープは無い
- `scripts/furniture_desk.py` — 南壁沿いのデスク2台 (ドア側から `desk1` = 明るいオーク / `desk2` = ウォールナット)。天板 `desk1_top` + 黒い角脚4本と幕板 `desk1_legs` + 奥の X の補強 `desk1_brace` (desk2 も同じ)。
  デスク2の上の小物 `desk2_items` (小物入れとペン・緑の瓶・イヤホンのケース・スマートフォンとケーブル・メモ帳。写真)
- `scripts/furniture_bookshelf.py` — 南壁の東端の本棚 (ウォールナット、2列×4段の箱積み、`reference/61ui-F6+2nL._AC_SL1000_.jpg`)。
  扉4枚は正面から見て上の段から 左・右・左・右 (`DOORS`)。`bookshelf_body` (枠・棚板・背板) + `bookshelf_doors`。
  扉の無い4マスの本・かご、扉の絵と賞状、天板の書類、床に立て掛けた月夜の絵は `bookshelf_items` (写真 `reference/IMG_1099`)
- `scripts/furniture_tv_stand.py` — テレビ台 (正方形の箱の L 字の棚2つ。背板なしのトンネル状、オーク)。北東の隅の L字棚1 (南向き) と、
  その東端の箱に乗せた上下逆さの L字棚2 (西向き、エアコンの下)。`cube_shelf()` が箱の位置の集合から板を組む。箱の大きさは `layout.TV_BOARD` と L字棚1 の幅で決まる。
  Empty `tv_stand` (部屋の原点) → Empty `tv_shelf1` `tv_shelf2` → `tv_shelf1_body` `tv_shelf2_body`。
  棚の中の物 `tv_stand_items` (白とコバルトブルーの布のバスケット・炊飯器と酒瓶・薬のかご・紺のかご・白いかごや箱。写真)
- `scripts/furniture_tv.py` — テレビ (液晶、電源オフ。仮に 32型)。L字棚2 の上に西向き。`tv_body` (薄い画面の板・背面のふくらみ・首・台座) + `tv_screen` + `tv_marks` (下の枠の赤い待機ランプ (光る) と銀の帯)
- `scripts/furniture_pc.py` — デスク1の上のデスクトップPC (ケース = In Win 301 白。正面のロゴは `emission` で光る。東の側面は濃い色のガラスの板) とプリンター (ブラザー DCP-J1800N 白。`printer` はクリック対象に未登録)。
  ケースの上の黒い機器とリモコン `pc_top_items` (写真)
- `scripts/furniture_keyboard.py` — キーボード (黒のフルサイズ、キーを1つずつ) とマウス。**仮** (ユーザーにまだ聞いていない)。メインモニターの前。Empty `keyboard` `mouse`。クリック対象には未登録
- `scripts/furniture_monitor.py` — デスク2の上のモニター2台 (`monitor_main` 24型、高さを変えられるスタンド。白い画面 `monitor_main_image` が光る (`textures/screen_main.png`) /
  `monitor_sub` 20型。画面は消えている) と、
  サブの台の白い箱2つ (`monitor_boxes`。かぶせるふた付き。クリック対象に未登録)。サブと箱は座る人の方へ斜め (layout.py の `yaw`)。
  白い箱の高さとサブの位置は layout.py で「画面の上端がメインと揃う高さ」「回した後の画面の西端がメインの東端の隣」として計算している
- `scripts/furniture_curtain.py` — カーテン (くすんだグレージュっぽい茶色の無地の布 `textures/curtain_fabric_1k.jpg`。2枚とも閉じた状態 (ユーザー指定。`PANELS`)。上はヒダをつまみ下へ広がる。
  リング `curtain_rings` とフック `curtain_hooks` で銀色の丸いレールに吊るす。レールはエアコンの下端の少し下 `layout.CURTAIN_ROD_Z`)。家具の見本でもある: 親 Empty (名前 = クリック判定用) + 子メッシュ。`FACING_DEG` で正面の向きを決める。
  直方体は `boxes_object`、ヒダや曲面は `mesh_object` で作る (法線は反時計回りに見える側が表。裏から見える1枚の面は `make_material(double_sided=True)`)。ヒダの布は自前の UV `UVMap` (布に沿った長さ) と焼き付けの島の展開 (`lightmap_uv`) を付ける
- `scripts/furniture_clock.py` — 壁掛けのアナログ時計 (カーテンレールと天井の間の真ん中、直径 0.36。茶色の枠・白い文字盤 `textures/clock_face.jpg`。写真)。針 `clock_hour` `clock_minute` `clock_second` はビューアが今の時刻に回す (`updateClock`)。クリック対象には未登録
- `scripts/furniture_tension_shelf.py` — 突っ張り棚 (デスク2の奥、X 2.54〜3.50。床から天井までの黒い柱2本 + 棚板2枚。本・夕焼けの絵・絵本。写真)。クリック対象には未登録
- `scripts/furniture_hanger_rail.py` — 南壁のフックのレール (X 1.30〜2.50、つまみ6つ)。白と黒のトートバッグ・ワイシャツ・S字フック (写真)。クリック対象には未登録
- `scripts/smoke_test.py` — 単体の見本
- `tools/make_guide.py` — 座標ガイド図 `renders/guide_plan.png` を作る (`python3 tools/make_guide.py`)
- `tools/make_textures.py` — Poly Haven の元画像から、色を合わせたテクスチャ (床 `floor_honey` / 扉 `oak_honey` / 壁紙 `wall_vinyl` / 布) を `textures/` に作る (`python3 tools/make_textures.py`)。
  布 (`FABRICS`: カーテン・毛布 (黒のフリース)・白っぽい綿と帆布) は見本を 2x2 に並べ、cm 単位のむらと横糸の筋を足す (離れて見ると細かい織り目は消えるため)。
  敷きパッドのタオル地 (`TOWEL` → `towel_quilt_1k.jpg`) は `terry_cloth` に 45° の菱形のキルティング (縫い目のくぼみ・破線の糸・マスのふくらみ) を描き足す
- `tools/make_prints.py` — 自作の画像 (本の背の柄・メインモニターの画面・時計の文字盤・絵・賞状・絵本・クッションのボーダー・かごの編み目・ティッシュの箱の印刷 (面を1枚に並べる)・ラグの柄) を `textures/` に作る。文字は架空の題 (実在の商品の字や柄は描かない)
- `tools/make_boxes.py` — 出窓の段ボール箱2つの印刷 (`textures/box_tea.jpg` `box_water.jpg`)。**ユーザー指定の実在の商品なので、例外として実物の箱に似せる** (ネットの商品写真を正面から見た形に直して mm で測った)。
  色ごとの版 `Plate` に形を描き、`v=0` で抜く。字は Windows のフォント (ロゴは似た書体を1字ずつ置く)。バーコードは商品の JAN・ITF を正しく符号にする。紙の地とインクの重ね方は `make_prints` の `_paper` `_apply_ink`
- `tools/inspect_glb.py` — `.glb` のノード名・三角形数・半透明材質を確認する
- `viewer/index.html` — three.js のビューア (`models/room.glb` と2枚の焼き付け画像を読む)。目の位置 `EYE` (デスク2の前の椅子、メインモニターの正面) と最初の向き `HOME_TARGET` は、glb の extras (`layout.VIEW`) で上書きされる。
  ドラッグで見回し・ホイールでズーム・クリック判定。材質は MeshLambertMaterial (シーンにライトは無い): lightMap = 拡散光 (色 × 焼いた光) + emissiveMap = グロスマップ (ツヤを足す)。
  仕上げ: AgX トーンマッピング (`EXPOSURE`)・bloom・色ずれ・周辺減光・フィルムノイズ (`FINISH_SHADER`)。窓の外の夜景はコードで描いた仮の物 (`makeNightSky`)。
  確認用クエリ: `?pos=X,Y` (`?pos=X,Y,高さ` も可) `?look=north` `?at=X,Y,Z` (部屋の座標の点を向く) `?pitch=度` `?exposure=3` `?tone=aces` `?post=0` (仕上げなし) `?mode=orbit` (俯瞰。V キーでも切替)。
  視野は横の角度 `HFOV_DEFAULT` (既定 100°) 基準で縦は画面比から決める (`?hfov=90` で試せる)。
  縦85° (16:9 で横約117°) にしたら魚眼のようで不快と指摘された。70° (横約102°) は「狭い」と言われた。視野角では広さを稼げないので、広くしたいなら部屋の寸法側で対応する。
  クリックできる物は `CLICKABLE` に glb のノード名で登録する (家具を作ったらここへ足す。`url` を入れるとリンクになる)
- `tools/serve.sh` — ビューア用サーバー (`http://localhost:8000/viewer/`)
- `tools/shot_viewer.sh` — ヘッドレス Edge でビューアのスクショを撮る (`?look=west&pos=3.8,1.8` `?mode=orbit` `?probe=ノード名` など)。
  Edge の操作は `tools/cdp_shot.py` (Windows 側の Python で動く DevTools Protocol のクライアント。glb の読み込み完了まで待ってから撮る)。
  `?debug&probe=<ノード名>` はそのノードの中心をクリック判定して、当たった家具名か none を画面に出す
- `renders/` — レンダリング画像 (PNG)。Read ツールで見て形状を確認する
- `models/` — `.blend` / `.glb` / 焼き付け画像 (`room_lightmap.webp` `room_glossmap.webp`) の成果物
- `textures/` — テクスチャ画像 (Poly Haven の CC0 と、`tools/make_textures.py` がそれから作った物。glb に埋め込まれる)。
  元: 木目の突板 `walnut_veneer` `oak_veneer_01`・フローリング `laminate_floor_03` (2k)・壁 `white_stucco`・布 `poly_wool_herringbone` `cotton_jersey` `rough_linen` `terlenka` `polar_fleece` `terry_cloth` (タオル地)
- `reference/` — 間取り図 (webp) と家具の参考画像、当時の部屋の写真 (`IMG_1099.HEIC` = L字棚の側から南壁 / `IMG_1100.HEIC` = ベッドの足元から L字棚 /
  `IMG_7064.JPG` = 同じく L字棚、インスタントカメラで画質が悪い。HEIC は Pillow で読めないので ImageMagick の `convert` で JPG にしてから見る)。物件の写真はウェブ (https://unilife.co.jp/view/10170) にある

## 作業の流れ

1. 家具ごとに `scripts/furniture_<name>.py` を書き、`build_all.py` から呼ぶ
2. `./run_blender.sh scripts/build_all.py` → `renders/*.png` (特に `iso_sw` `iso_ne` `eye_*`) で形を、ビューアのスクショ (`tools/shot_viewer.sh`) で夜の見た目を確認
3. 形・比率・色・位置を直して繰り返す。`python3 tools/inspect_glb.py` で名前と三角形数も確認する

## 注意

- Blender は 5.2。ネットの古い (2.9x/3.x) コードは名前が違うことがある: Principled BSDF の `Specular` → `Specular IOR Level`、
  `Emission` → `Emission Color`、`Material.blend_method` → `surface_render_method`、`use_nodes` は不要 (新しい材質は最初からノード付き)、
  EEVEE の `use_gtao` などは無い、コンポジターは `scene.compositing_node_group` (ノードグループ + Group Output)
- 焼き付けの落とし穴: 焼き先はメッシュの**アクティブな UV** (画像ノードにつないだ UV ではない)。物体ごとに焼くと毎回シーンを準備し直して遅い (23個で3分半 → まとめて1回で18秒)
- Windows プロセスなのでパスは `wslpath -w` で変換する。スクリプト内では環境変数 `WORKSPACE_WIN` (= `common.ROOT`) を使う
- 確認画像のレンダラは EEVEE、焼き付けは Cycles。どちらもヘッドレスで動作確認済み
