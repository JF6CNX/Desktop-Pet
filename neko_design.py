"""
ねこのデザイン（このファイルだけ書きかえれば、ねこの見た目を変えられます）

  - 下の「せってい」の数字や色を変えて保存すると、動いているペットに数秒で反映されます。
    （書きまちがえてエラーになったときは、前の見た目のまま動き続けます）
  - 色は (赤, 緑, 青) で、それぞれ 0〜255。
  - 位置や大きさの単位は「ペットの絵の 1px」。ねこの体の中心は x = CX（126）です。
  - 形そのものを変えたいときは、下の draw_body() の中を書きかえてください。

見た目だけ確かめたいとき:
    python desktop_pet.py --preview neko_preview.png
"""

# ============================================================
#  せってい
# ============================================================
CHARACTER = "person"          # "person"＝ひと（hito.png の絵） / "cat"＝ねこ（このファイルの設定でかく）

FUR = (252, 250, 246)         # 体の色（白ねこ）
CAP = (122, 114, 114)         # もよう（八割れ）と耳の灰色
OUTLINE = (62, 50, 46)        # ふちの線の色（こげ茶）
WHITE = (255, 255, 255)       # 胸・くつしたの白
EAR_INNER = None              # 耳の内側の色。None で耳と同じ色
NOSE = (62, 50, 46)           # 鼻と口の線の色
SHOW_NOSE = False             # 鼻をかくか
MOUTH_IN = (214, 70, 64)      # あいた口の中

OUTLINE_W = 1.6               # ふちの太さ

# 目
EYE_STYLE = "itome"           # "itome"＝糸目 / "round"＝まんまるの目
EYE_LINE = (50, 40, 38)       # 糸目の線の色
EYE_COLOR = (50, 40, 38)      # まんまるの目の色（"round" のときと、びっくりしたとき）
EYE_GAP = 13                  # 目のまんなかの、顔の中心からの距離
EYE_LEN = 20                  # 糸目の長さ
EYE_Y = 3                     # 目の高さ（頭の中心から下へ。大きいほど下）
EYE_TILT = 4                  # 糸目のかたむき（外がわのはしが、内がわよりどれだけ下がるか。0 で水平）

# 口
MOUTH = "open"                # "open"＝あいた口（にこっ） / "w"＝ωの口
MOUTH_Y = 5                   # 口の高さ（目の高さから下へ。大きいほど下）

# ほくろ
MOLE = True                   # ほくろをかくか
MOLE_X = 9                    # ほくろの横の位置（顔の中心から右へ。マイナスで左）
MOLE_Y = 8                    # ほくろのたての位置（目の高さから下へ）
MOLE_SIZE = 1.1               # ほくろの大きさ
MOLE_COLOR = (50, 40, 38)     # ほくろの色

# もよう・小物
PATTERN = "hachiware"         # "hachiware"＝八割れ / "cap"＝頭の上だけ灰色 / "none"＝もようなし
EYE_CLEAR = True              # 目のまわりにはもようをかぶせない
# 八割れの線（頭のたての半分を 1 とした高さ。マイナスが上、0 が頭のまんなか）
HACHI_TOP = -0.7              # 「八」のてっぺん（顔のまんなかより上）
HACHI_SIDE = 0.05             # 顔の中心から頭のはばぶん横へ行ったところの線の高さ（左右おなじ＝線対称）
CHEST = False                 # 白い胸（体が白いときはいらない）
SOCKS = False                 # 手足の先を白いくつしたに
COLLAR = None                 # 首輪の色。例 (214, 64, 44) で赤い首輪。None でなし

# ふく（None にするとはだか）
CLOTHES = "sweat"             # "sweat"＝ふつうの服（トレーナーとジーンズ） / "kimono"＝着物とはかま / "none"＝なし
SHIRT = (190, 52, 48)         # トレーナー（着物）の色
SHIRT_RIB = (150, 36, 34)     # トレーナーのえり・そで口（着物のえりはいつも白）
OBI = (112, 72, 160)          # 帯の色（着物のとき）
PANTS = (78, 98, 142)         # ジーンズ（はかま）の色
PANTS_LINE = (196, 190, 182)  # はかまのひだの線
ZORI = (200, 50, 44)          # ぞうりの鼻緒

# 形
HEAD_W, HEAD_H = 32, 23       # 頭の横はば・たての半分の長さ
HEAD_Y = 50                   # 頭の中心の高さ（小さいほど上）
FACE_TURN = 0                 # 顔の向き（右ななめ前から見ているので、こっちを向くよう右へ。0 で正面）
EAR_H = 31                    # 耳の高さ（頭の中心から耳の先まで）
EAR_SIZE = 1.0                # 耳の大きさ（1 がふつう。大きいほど大きい耳）
BODY_W = 24                   # 胴のはば（半分）
TAIL = True                   # しっぽをかくか


# ============================================================
#  かきかた（形を変えたいときはここ）
# ============================================================
def _shirt():
    return None if CLOTHES == "none" else SHIRT


def _pants():
    return None if CLOTHES == "none" else PANTS


def paw_color():
    return WHITE if SOCKS else FUR


def sleeve_color():
    """腕の色（ふくを着ていたらそでの色）"""
    return _shirt() or FUR


def arm_widths():
    """腕の (ふちこみの太さ, 中の太さ)。着物はそでがふっくら"""
    w = 6.4 if (_shirt() and CLOTHES == "kimono") else 4.6
    return w + 2 * OUTLINE_W, w


def draw_body(a, im, d, eyes, fx, breath, sway, CX):
    """a: 描画係（a.ell / a.line / a.poly / a.arc / a.P が使える）
    eyes: open / focus / wide / blink / sleep / happy / squint
    fx: 顔の向き（左右）、breath: 呼吸、sway: しっぽのゆれ"""
    from PIL import Image, ImageChops, ImageDraw
    import math

    P = a.P
    cx = CX
    b = breath * 0.6
    O = OUTLINE_W
    turn = FACE_TURN
    hx, hy, hrx, hry = cx + fx * 0.6 + turn * 0.3, HEAD_Y - b, HEAD_W, HEAD_H + b * 0.3
    tx, ty, trx, tryy = cx, 93, BODY_W, 24
    fo = hx + fx * 0.4 + turn * 0.7                      # 顔のパーツの中心（こっちを向くと右へよる）
    persp = turn / 30                                    # 奥がわ（画面の左）の目は少し小さく近く

    # しっぽ：体の右から上にのびて、先が少し曲がる
    if TAIL:
        tail = [(cx + 20, 88), (cx + 36, 78), (cx + 45, 62), (cx + 45 + sway * 0.5, 48),
                (cx + 42 + sway, 40)]
        a.line(d, tail, fill=OUTLINE, w=5 + 2 * O)
        a.ell(d, *tail[-1], 2.5 + O, 2.5 + O, OUTLINE, ol=None)
        a.line(d, tail, fill=FUR, w=5)
        a.ell(d, *tail[-1], 2.5, 2.5, FUR, ol=None)

    # 耳（もようが cap なら灰色）
    ear_col = CAP if PATTERN in ("cap", "hachiware") else FUR
    k = EAR_H / 31
    for side in (-1, 1):
        ear = [(hx + side * 28, hy - 3), (hx + side * 9, hy - 17 * k),
               (hx + side * 24 + sway * 0.2, hy - 31 * k)]
        inner = [(hx + side * 23, hy - 9 * k), (hx + side * 14, hy - 16 * k),
                 (hx + side * 22 + sway * 0.2, hy - 25 * k)]
        # 耳の大きさ：頭のふちの耳のつけね (ax_, ay_) を中心に、のばしたりちぢめたり
        ax_, ay_ = hx + side * 18.5, hy - hry * 0.72
        grow = lambda pts: [(ax_ + (x - ax_) * EAR_SIZE, ay_ + (y - ay_) * EAR_SIZE) for x, y in pts]
        ear, inner = grow(ear), grow(inner)
        a.poly(d, ear, ear_col, ol=OUTLINE, w=2 * O)
        if EAR_INNER:
            a.poly(d, inner, EAR_INNER)

    # 胴（ふちを先に描いて、中を後から塗る）
    a.ell(d, tx, ty, trx + O, tryy + O, OUTLINE, ol=None)
    a.ell(d, tx, ty, trx, tryy, _shirt() or FUR, ol=None)
    if _shirt() and CLOTHES == "kimono":                    # 着物：白いえりを左右から重ねる（右前）、帯
        a.ell(d, tx, ty + 6, trx, 4.5, OBI, ol=None)
        for x0, x1 in ((-9, 4), (9, -4)):
            a.line(d, [(cx + x0, hy + hry - 6), (cx + x1, ty - 4)], fill=OUTLINE, w=4.4)
            a.line(d, [(cx + x0, hy + hry - 6), (cx + x1, ty - 4)], fill=WHITE, w=2.8)
    elif _shirt():                                          # トレーナーのえり（首のまわり）
        a.arc(d, hx, hy + hry - 3, 9, 30, 150, fill=SHIRT_RIB, w=3)
    elif CHEST:
        a.ell(d, cx, ty - 4, min(14, trx - 4), 16, WHITE, ol=None)

    # 首輪
    if COLLAR:
        col = []
        for i in range(17):
            x = -1 + i / 8
            col.append((hx + x * (hrx - 3), hy + (hry + 2.2) * math.sqrt(max(0.0, 1 - x * x * 0.8))))
        a.line(d, col, fill=OUTLINE, w=4 + 2 * O * 0.7)
        a.line(d, col, fill=COLLAR, w=4)

    # 頭
    a.ell(d, hx, hy, hrx + O, hry + O, OUTLINE, ol=None)
    a.ell(d, hx, hy, hrx, hry, FUR, ol=None)

    # もよう（頭の形で切りぬく）。灰色をぬってから、白くしたいところをぬきなおす
    ey = hy + EYE_Y
    lx, rxx = fo - EYE_GAP * (1 - persp * 0.5), fo + EYE_GAP * (1 + persp * 0.2)
    eye_len = {-1: EYE_LEN * (1 - persp), 1: EYE_LEN * (1 + persp * 0.3)}
    if PATTERN in ("cap", "hachiware"):
        head = Image.new("L", im.size, 0)
        ImageDraw.Draw(head).ellipse([P(hx - hrx), P(hy - hry), P(hx + hrx), P(hy + hry)], fill=255)
        pat = Image.new("L", im.size, 255)
        pd = ImageDraw.Draw(pat)
        if PATTERN == "hachiware":
            # 八割れ：頭のてっぺんから左右へ、まっすぐな線で「八」の字に分ける（目より上）
            # 頭のてっぺんは灰色のまま。顔のまんなかより上から、まっすぐな2本の線で白くなる
            xl, xr = hx - hrx - 3, hx + hrx + 3
            ya = hy + hry * HACHI_TOP
            slope = (hy + hry * HACHI_SIDE - ya) / hrx           # 左右おなじかたむき（顔の中心で線対称）
            yl2, yr2 = ya + slope * (fo - xl), ya + slope * (xr - fo)
            pd.polygon([(P(x), P(y)) for x, y in (
                (xl, yl2), (fo, ya), (xr, yr2), (xr, hy + hry + 3), (xl, hy + hry + 3))], fill=0)
        else:
            fw, fh, fy = hrx * 1.02, hry * 0.9, hy + hry * 0.28      # 白い顔
            pd.ellipse([P(fo - fw), P(fy - fh), P(fo + fw), P(fy + fh)], fill=0)
        if EYE_CLEAR and PATTERN != "hachiware":         # 目のまわりは白いまま
            for x, side in ((lx, -1), (rxx, 1)):
                cxe = x + side * EYE_LEN * 0.1
                pd.ellipse([P(cxe - EYE_LEN * 0.6 - 2.5), P(ey - 5), P(cxe + EYE_LEN * 0.6 + 2.5), P(ey + 5)], fill=0)
        im.paste(CAP + (255,), mask=ImageChops.multiply(head, pat))
        d = ImageDraw.Draw(im)

    # 目
    line_col = EYE_COLOR if EYE_STYLE == "round" else EYE_LINE
    ee = "open" if EYE_STYLE == "itome" else eyes    # 糸目は、なにがあってもいつもの糸目のまま
    if ee == "wide":                                   # びっくりしたときだけ目がひらく
        for x in (lx, rxx):
            a.ell(d, x, ey, 3.2, 3.6, EYE_COLOR, ol=None)
            a.ell(d, x + 1, ey - 1.2, 1, 1, (255, 255, 255), ol=None)
    elif ee in ("open", "focus") and EYE_STYLE == "round":
        h = 3.4 if ee == "open" else 2.2
        for x in (lx, rxx):
            a.ell(d, x, ey + (0 if ee == "open" else 1), 2.8, h, EYE_COLOR, ol=None)
    elif ee in ("open", "focus", "blink"):             # 糸目：外がわが下がった細い線
        tilt = EYE_TILT * (0.7 if ee == "focus" else 1.0)
        for x, side in ((lx, -1), (rxx, 1)):
            inner = (x - side * eye_len[side] * 0.4, ey - tilt / 2)
            outer = (x + side * eye_len[side] * 0.6, ey + tilt / 2)
            a.line(d, [inner, outer], fill=line_col, w=1.9)
    elif ee == "sleep":
        for x in (lx, rxx):
            a.arc(d, x, ey - 3, 5, 30, 150, fill=line_col, w=1.9)
    elif ee == "happy":
        for x in (lx, rxx):
            a.arc(d, x, ey + 3, 5, 200, 340, fill=line_col, w=1.9)
    elif ee == "squint":
        a.line(d, [(lx - 4, ey - 4), (lx + 3, ey), (lx - 4, ey + 4)], fill=line_col, w=1.9)
        a.line(d, [(rxx + 4, ey - 4), (rxx - 3, ey), (rxx + 4, ey + 4)], fill=line_col, w=1.9)

    # 鼻・口
    nx, ny = fo + fx * 0.1, ey + MOUTH_Y
    if SHOW_NOSE:
        a.poly(d, [(nx - 1.8, ny - 1.2), (nx + 1.8, ny - 1.2), (nx, ny + 0.6)], NOSE)
    if eyes == "wide":
        a.ell(d, nx, ny + 4.5, 2, 2.4, NOSE, ol=None)
    elif MOUTH == "open" and eyes != "sleep":
        a.arc(d, nx - 2.2, ny + 1.2, 2.2, 10, 150, fill=NOSE, w=1.3)
        a.arc(d, nx + 2.2, ny + 1.2, 2.2, 30, 170, fill=NOSE, w=1.3)
        mouth = [(nx - 2.6, ny + 3), (nx + 2.6, ny + 3), (nx + 1.8, ny + 6.4), (nx, ny + 7.4), (nx - 1.8, ny + 6.4)]
        a.poly(d, mouth, MOUTH_IN, ol=NOSE, w=1.1)
    else:
        a.arc(d, nx - 2.4, ny + 1.4, 2.4, 10, 170, fill=NOSE, w=1.3)
        a.arc(d, nx + 2.4, ny + 1.4, 2.4, 10, 170, fill=NOSE, w=1.3)

    # ほくろ
    if MOLE:
        a.ell(d, fo + MOLE_X, ey + MOLE_Y, MOLE_SIZE, MOLE_SIZE, MOLE_COLOR, ol=None)

    # 机の下でぶらぶらしている後ろあし
    for side in (-1, 1):
        fx0 = cx + side * 9
        if _pants() and CLOTHES == "kimono":             # はかま：すそが広がる
            leg = [(fx0 - 4, 128), (fx0 + 4, 128), (fx0 + side * 1.5 + 5.5, 140), (fx0 + side * 1.5 - 5.5, 140)]
            a.poly(d, leg, PANTS, ol=OUTLINE, w=O)
            for k in (-2, 1.5):
                a.line(d, [(fx0 + k * 0.6, 130), (fx0 + side * 1.5 + k, 139)], fill=PANTS_LINE, w=0.8)
        else:
            a.line(d, [(fx0, 128), (fx0 + side * 1.5, 142)], fill=OUTLINE, w=6.4 + 2 * O)
            a.line(d, [(fx0, 128), (fx0 + side * 1.5, 142)], fill=_pants() or FUR, w=6.4)
        a.ell(d, fx0 + side * 1.5, 143, 4.6, 3.4, paw_color(), ol=OUTLINE, w=O)
        if _pants() and CLOTHES == "kimono":             # たびに、ぞうりの赤い鼻緒
            a.line(d, [(fx0 + side * 1.5 - 2.6, 143.4), (fx0 + side * 1.5, 141.6), (fx0 + side * 1.5 + 2.6, 143.4)],
                   fill=ZORI, w=1.3)
    return d


# ============================================================
#  アプリの「ねこのみため」画面で変えた値（neko_settings.json）を上にかぶせる
# ============================================================
import json as _json
import os as _os

SETTINGS_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "neko_settings.json")
DEFAULTS = {k: v for k, v in dict(globals()).items() if k.isupper() and k != "SETTINGS_FILE"}


def load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = _json.load(f)
    except (OSError, ValueError):
        return
    for k, v in data.items():
        if k in DEFAULTS:
            globals()[k] = tuple(v) if isinstance(v, list) else v


def save_settings(changes):
    """changes: {名前: 値}。元の値とちがうものだけ保存する"""
    data = {}
    for k in DEFAULTS:
        v = globals()[k]
        if v != DEFAULTS[k]:
            data[k] = list(v) if isinstance(v, tuple) else v
    for k, v in changes.items():
        globals()[k] = v
        if v != DEFAULTS.get(k):
            data[k] = list(v) if isinstance(v, tuple) else v
        else:
            data.pop(k, None)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        _json.dump(data, f, ensure_ascii=False, indent=1)


def reset_settings():
    for k, v in DEFAULTS.items():
        globals()[k] = v
    try:
        _os.remove(SETTINGS_FILE)
    except OSError:
        pass


load_settings()
