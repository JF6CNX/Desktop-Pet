"""
デスクトップペット「よる」（八割れねこ） — キーボード＆マウスつき

  - 目の前にキーボード、となりにマウスが常に置いてある
  - 本物のキーボードで押したキーと「同じ位置」のキーを、もちまるが押す
    （左半分は左手、右半分は右手。押されたキーは光る）
  - カーソルを動かすと、右手でマウスを同じ方向に動かす。クリックするとボタンが光る
  - しばらく何もしないと、うとうと寝る（何か操作すると起きる）
  - ドラッグでつまんで投げられる／クリックでジャンプ
  - 右クリックでメニュー

※ キーは「どの位置が押されたか」を表示に使うだけで、記録・保存はしません。

起動: pythonw desktop_pet.py   （黒い窓なし）
"""
import ctypes
import math
import os
import random
import sys
import time
import tkinter as tk

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageTk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import json
from tkinter import colorchooser, ttk
import hito
import jisaku
from tkinter import filedialog, messagebox

LANCZOS = getattr(Image, "Resampling", Image).LANCZOS
KEY = (1, 2, 3)            # 透過に使う色
KEY_HEX = "#010203"
SS = 3                     # 描画の拡大率（なめらかにするため）
UW, UH = 272, 154          # 論理サイズ（DPI 100% での px）

# ---- 色 ----
OUTLINE = (92, 70, 50)
BODY = (255, 222, 172)        # 小麦色のねこ
STRIPE = (226, 156, 92)
EAR_IN = (255, 178, 190)
NOSE = (240, 120, 140)
BELLY = (255, 246, 230)
CHEEK = (255, 168, 182)
LEAF = (126, 204, 112)
EYE = (40, 32, 28)
WHITE = (255, 255, 255)
KB_BODY = (46, 48, 52)        # チャコールの本体
KB_EDGE = (24, 24, 28)
KB_KEY = (114, 116, 124)         # 墨色のキー
KB_GLOW = KB_BODY              # バックライトなし
KB_HIT = (168, 188, 228)       # 押したキー（明るく光る）
KB_FN = (114, 116, 124)
KB_SIDE = (32, 33, 36)         # 本体の側面
KEY_SIDE = (58, 60, 66)        # キーの側面
HIT_SIDE = (110, 126, 162)
MOUSE_TOP = (62, 64, 70)       # 黒っぽいマウス
MOUSE_SIDE = (36, 37, 41)
MOUSE_LINE = (20, 20, 24)
MOUSE_WHEEL = (200, 204, 212)  # 金属のホイール
ZZZ = (96, 120, 210)
CHAIR = (138, 34, 56)          # えんじ色のいす
CHAIR_HI = (160, 48, 72)

# ---- 配置（論理座標） ----
# もちまるはこちら向きに座っているので、キーボードもマウスも「もちまるから見て正しい向き」
# ＝ こちらから見ると 180° 回転。右利きなのでマウスはもちまるの右手側（画面では左）。
CX = 126                   # 体の中心 x
BODY_BOTTOM = 101
DOG_X, DOG_Y = CX + 60, 68           # 反対がわ（画面の右）からのぞく黄色い犬
PLUSH_X, PLUSH_Y = CX - 45, 68   # ねこの右どなり（画面の左）からのぞくハスキーのぬいぐるみ
# キーボードは斜め上から見た台形：奥（もちまる側）が画面の上、手前（こちら側）が画面の下
KB_FAR = (75, 175, 80)      # 奥の辺   (左x, 右x, y)
KB_NEAR = (53, 175, 114)    # 手前の辺 (左x, 右x, y)  右ななめから見ているので左へずれる
KB_THICK = 6                # 本体の厚み（手前の側面）
KEY_H = 2.4                 # キーの高さ
KEY_H_DOWN = 0.5            # 押したときの高さ
# 机（キーボードとマウスの下）。奥の辺はねこの胸のあたりで、そこから下の体は机にかくれる
DESK_FAR = (24, 266, 77)
DESK_NEAR = (2, 256, 125)
SKEW = 0.36                     # 右ななめから見る角度（1px 手前に来るごとに左へずれる量）
DESK_THICK = 6
DESK_TOP = (212, 166, 110)       # 木の天板
DESK_GRAIN = (192, 144, 90)      # 木目
DESK_SIDE = (150, 100, 62)       # 天板の側面・脚（こげ茶の木）
DESK_EDGE = (84, 54, 32)         # ふちの線
WA_INDIGO = (48, 62, 112)        # 藍色
WA_RED = (196, 58, 46)           # 朱色
WA_GOLD = (222, 180, 72)         # 金色
WA_CREAM = (250, 240, 214)       # 生成り
WA_MATCHA = (128, 158, 78)       # 抹茶色
MOUSE_C = (44, 98)          # マウスは机にじか置き（キーボードの左となり）
# 手を休めておく場所（体の横、キーボードより上）
REST_L = (CX - 27, 77)
REST_R = (CX + 27, 77)


# ============================================================
#  キーボード配列：60% コンパクト・日本語配列（69キー、矢印キーつき）
#  キーは「物理的な位置（スキャンコード）」で持つので、Windows の
#  キーボード設定が日本語でも英語でも、押した場所と同じ所が光る。
#  (スキャンコード or None=すきま or "fn" or ENTER2=Enter の下半分, 幅[キー単位])
# ============================================================
FN = "fn"
G = None
ENTER2 = "enter2"
ROWS = [
    # Esc 1-0 - ^ ¥ BS
    [(0x01, 1)] + [(0x02 + i, 1) for i in range(10)] + [(0x0C, 1), (0x0D, 1), (0x7D, 1), (0x0E, 1)],
    # Tab Q-P @ [ Enter(上)
    [(0x0F, 1.5)] + [(0x10 + i, 1) for i in range(10)] + [(0x1A, 1), (0x1B, 1), (0x1C, 1.5)],
    # Control A-L ; : ] Enter(下)
    [(0x1D, 1.75)] + [(0x1E + i, 1) for i in range(9)] + [(0x27, 1), (0x28, 1), (0x2B, 1), (ENTER2, 1.25)],
    # Shift Z-/ ろ ↑ Shift
    [(0x2A, 2)] + [(0x2C + i, 1) for i in range(10)] + [(0x73, 1), (0xE048, 1), (0x36, 1)],
    # Fn 半全 ◇ Alt 無変換 Space 変換 かな Alt Fn ← ↓ →
    [(FN, 1), (0x29, 1), (0xE05B, 1), (0x38, 1), (0x7B, 1), (0x39, 3), (0x79, 1), (0x70, 1),
     (0xE038, 1), (FN, 1), (0xE04B, 1), (0xE050, 1), (0xE04D, 1)],
]
LAYOUT_U = 15              # 横幅（キー単位）
FGAP = 0.0                 # 1段目の下のすきま（F キー列がないので 0）

# 仮想キー → スキャンコード（MapVirtualKey で取りにくいものは固定で）
VK_FIXED = {
    0x25: 0xE04B, 0x26: 0xE048, 0x27: 0xE04D, 0x28: 0xE050,
    0x2D: 0xE052, 0x2E: 0xE053, 0x24: 0xE047, 0x23: 0xE04F, 0x21: 0xE049, 0x22: 0xE051,
    0x2C: 0xE037, 0x91: 0x46, 0x13: 0xE11D,
    0xA0: 0x2A, 0xA1: 0x36, 0xA2: 0x1D, 0xA3: 0xE01D, 0xA4: 0x38, 0xA5: 0xE038,
    0x5B: 0xE05B, 0x5C: 0xE05B, 0x5D: 0xE05D,
}
VK_SKIP = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x10, 0x11, 0x12,     # マウス・左右共通の修飾キー
           0x15, 0x19, 0xE5} | set(range(0xF0, 0xF7))                # IME 系（押しっぱなし扱いになりやすい）


PARTNER = {}


def build_layout():
    """キーを (s0, t0, s1, t1) の 0..1 座標で返す。s=左右, t=奥(0)→手前(1)。"""
    padu, gapu, fgap = 0.4, 0.07, FGAP
    tw = LAYOUT_U + 2 * padu
    th = len(ROWS) + fgap + 2 * padu
    rects, kinds, sc2idx = [], [], {}
    for r, row in enumerate(ROWS):
        x = padu
        y = padu + r + (fgap if r > 0 else 0)
        for sc, w in row:
            if sc is not G:
                s0, s1 = (x + gapu) / tw, (x + w - gapu) / tw
                t0, t1 = (y + gapu) / th, (y + 1 - gapu) / th
                # 180° 回転（もちまる側から見て正しい向き）
                rects.append((1 - s1, 1 - t1, 1 - s0, 1 - t0))
                kinds.append("fn" if sc == FN else "key")
                if sc == ENTER2:                  # Enter の下半分は Enter と一緒に光る
                    PARTNER[len(rects) - 1] = sc2idx[0x1C]
                elif sc != FN:
                    sc2idx[sc] = len(rects) - 1
            x += w
    return rects, kinds, sc2idx


def _lerp(a, b, t):
    return a + (b - a) * t


def project(s, t, lift=0.0, far=KB_FAR, near=KB_NEAR):
    """平面上の (s, t) → 画面座標。lift はその場所から上に持ち上げる量。"""
    xl = _lerp(far[0], near[0], t)
    xr = _lerp(far[1], near[1], t)
    return _lerp(xl, xr, s), _lerp(far[2], near[2], t) - lift


def key_quad(idx, lift=0.0, grow=0.0):
    s0, t0, s1, t1 = KEY_RECTS[idx]
    gs, gt = grow / 140, grow / 36
    s0, s1, t0, t1 = s0 - gs, s1 + gs, t0 - gt, t1 + gt
    return [project(s0, t0, lift), project(s1, t0, lift), project(s1, t1, lift), project(s0, t1, lift)]


def build_vkmap(sc2idx):
    vkmap = {}
    for vk, sc in VK_FIXED.items():
        if sc in sc2idx:
            vkmap[vk] = sc2idx[sc]
    try:
        mapvk = ctypes.windll.user32.MapVirtualKeyW
    except Exception:
        mapvk = None
    if mapvk:
        for vk in range(1, 255):
            if vk in vkmap or vk in VK_SKIP or 0x60 <= vk <= 0x6F:   # テンキーは無いので除外
                continue
            sc = mapvk(vk, 0)
            if sc and sc in sc2idx:
                vkmap[vk] = sc2idx[sc]
    else:                                         # 念のため（US 配列の仮想キー）
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            sc = mapvk_fallback(c)
            if sc in sc2idx:
                vkmap[ord(c)] = sc2idx[sc]
    return vkmap


def mapvk_fallback(c):
    rows = ["1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    starts = [0x02, 0x10, 0x1E, 0x2C]
    for s, row in zip(starts, rows):
        if c in row:
            return s + row.index(c)
    return None


KEY_RECTS, KEY_KINDS, SC2IDX = build_layout()
KEY_ORDER = sorted(range(len(KEY_RECTS)), key=lambda i: KEY_RECTS[i][1])   # 奥から手前へ描く
VK2IDX = build_vkmap(SC2IDX)
WATCH_VKS = sorted(VK2IDX)


def key_center(idx):
    s0, t0, s1, t1 = KEY_RECTS[idx]
    return project((s0 + s1) / 2, (t0 + t1) / 2, KEY_H)

# 左右の手の担当の境目：G と H のあいだ（回転後なので画面では H が左）
KB_MID = (key_center(SC2IDX[0x22])[0] + key_center(SC2IDX[0x23])[0]) / 2
# 画面左の手＝もちまるの右手 → J、画面右の手＝もちまるの左手 → F
HOME_L = key_center(SC2IDX[0x24])
HOME_R = key_center(SC2IDX[0x21])


# ============================================================
#  描画
# ============================================================
ART_INSTANCES = []
TOP_M = 18                # 上のよゆう（ジャンプしても頭がはみ出ないように）
APP_FILE = paths.app("app_settings.json")
APP_DEFAULTS = {"size": 100, "topmost": True, "locked": False, "typing": True, "mouse": True,
                "sleep_min": 1, "pos": None, "chars": ["person"],
                "hand": {"sh_x": 0, "sh_y": 0, "rest_x": 0, "rest_y": 0}}
STARTUP_FILE = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu",
                            "Programs", "Startup", "desktop_pet.cmd")


def load_app_settings():
    data = dict(APP_DEFAULTS)
    try:
        with open(APP_FILE, encoding="utf-8") as f:
            data.update({k: v for k, v in json.load(f).items() if k in APP_DEFAULTS})
    except (OSError, ValueError):
        pass
    return data


def save_app_settings(data):
    try:
        with open(APP_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def autostart_on():
    return os.path.exists(STARTUP_FILE)


def set_autostart(on):
    """Windows の「スタートアップ」フォルダに起動用のファイルを置く／消す"""
    try:
        if on:
            with open(STARTUP_FILE, "w", encoding="cp932", errors="replace") as f:
                f.write(paths.launch_command() + "\r\n")
        elif os.path.exists(STARTUP_FILE):
            os.remove(STARTUP_FILE)
    except OSError:
        pass
DESK_THEMES = {
    "wa": {"name": "和風", "top": DESK_TOP, "grain": DESK_GRAIN, "side": DESK_SIDE, "edge": DESK_EDGE, "band": "wave"},
    "lab": {"name": "研究室", "top": (172, 176, 166), "grain": None, "side": (136, 140, 132),
            "edge": (74, 76, 72), "band": "trim"},
}
HITO_NECK_Y = 57          # ひとの首の高さ（これより下の体は机にかくれる）


CUSTOM = jisaku.load_chara()       # 自作キャラの設定（パーツの点など）


CURRENT_CHAR = "person"            # いま動かしている（かいている）ペットのキャラ："person" / "custom"
CHAR_NAMES = {"person": "ひと", "custom": "自作キャラ"}


def is_custom():
    return CURRENT_CHAR == "custom"


def char_neck_y():
    return CUSTOM.get("neck_y", HITO_NECK_Y) if is_custom() else HITO_NECK_Y


def is_person():
    return True                    # ねこキャラはなくなったので、いつも「絵のキャラ」


# 手の位置の調整（設定画面の「手の位置」）。肩：はば・高さ、休めている手：はば・高さ
HAND = {"sh_x": 0, "sh_y": 0, "rest_x": 0, "rest_y": 0}


def shoulders():
    """（左の肩, 右の肩）"""
    if is_person():
        l, r = jisaku.shoulders(CUSTOM, CX, char_neck_y()) if is_custom() else \
            ((CX - 13, HITO_NECK_Y + 8), (CX + 21, HITO_NECK_Y + 8))
    else:
        l, r = (CX - 20, 73), (CX + 20, 73)
    dx, dy = HAND["sh_x"], HAND["sh_y"]
    return (l[0] - dx, l[1] + dy), (r[0] + dx, r[1] + dy)


def rest_pos():
    """キーをさわっていないときの手の場所（左の手, 右の手）"""
    if is_person():
        l, r = (CX - 26, 78), (CX + 22, 79)
    else:
        l, r = REST_L, REST_R
    dx, dy = HAND["rest_x"], HAND["rest_y"]
    return (l[0] - dx, l[1] + dy), (r[0] + dx, r[1] + dy)
LAYOUT_FILE = paths.app("layout.json")


def load_layout():
    """(テーマ, 小物のリスト)"""
    try:
        with open(LAYOUT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        theme = data.get("theme", "wa")
        if theme not in DESK_THEMES:
            theme = "wa"
        return theme, [it for it in data["items"] if it.get("type") in Art.ITEM_DEFS]
    except (OSError, ValueError, KeyError, TypeError, NameError):
        return "wa", Art.default_layout("wa")


def save_layout(art):
    try:
        with open(LAYOUT_FILE, "w", encoding="utf-8") as f:
            json.dump({"theme": art.theme, "items": art.layout}, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


class Art:
    def __init__(self, scale):
        self.scale = scale
        self.k = SS * scale
        self.W, self.H = int(UW * scale), int((UH + TOP_M) * scale)
        self.cw, self.ch = int(UW * self.k), int(UH * self.k)
        self.blank = Image.new("RGBA", (self.cw, self.ch), (0, 0, 0, 0))
        try:
            self.font_b = ImageFont.truetype("arialbd.ttf", int(self.P(15)))
            self.font_s = ImageFont.truetype("arialbd.ttf", int(self.P(10)))
        except OSError:
            self.font_b = self.font_s = ImageFont.load_default()
        try:
            self.font_j = ImageFont.truetype("meiryob.ttc", int(self.P(9)))
            self.font_h = ImageFont.truetype("meiryo.ttc", int(self.P(6.5)))
        except OSError:
            self.font_j = self.font_h = self.font_s
        self._body = {}
        self.ox = 0.0                     # 小物を置いた場所に合わせて横へずらす量
        self.oy = 0.0                     # 　　〃　　たてへずらす量
        self.theme, self.layout = load_layout()
        self.item_box = self._measure_items()
        ART_INSTANCES.append(self)
        self.desk = self._desk()
        self.chair = self._chair()

    def P(self, v):
        return v * self.k

    # 基本図形
    def ell(self, d, cx, cy, rx, ry, fill, ol=OUTLINE, w=3):
        cx, cy = cx + self.ox, cy + self.oy
        P = self.P
        d.ellipse([P(cx - rx), P(cy - ry), P(cx + rx), P(cy + ry)], fill=fill,
                  outline=ol, width=max(1, int(P(w))) if ol else 0)

    def line(self, d, pts, fill=EYE, w=2.5):
        d.line([(self.P(x + self.ox), self.P(y + self.oy)) for x, y in pts], fill=fill,
               width=max(1, int(self.P(w))), joint="curve")

    def arc(self, d, cx, cy, r, a0, a1, fill=EYE, w=2.5):
        cx, cy = cx + self.ox, cy + self.oy
        P = self.P
        d.arc([P(cx - r), P(cy - r), P(cx + r), P(cy + r)], a0, a1, fill=fill,
              width=max(1, int(P(w))))

    def rrect(self, d, box, r, fill, ol=OUTLINE, w=2.5):
        box = (box[0] + self.ox, box[1] + self.oy, box[2] + self.ox, box[3] + self.oy)
        P = self.P
        d.rounded_rectangle([P(box[0]), P(box[1]), P(box[2]), P(box[3])], radius=P(r),
                            fill=fill, outline=ol, width=max(1, int(P(w))) if ol else 0)

    # キーボードとマウスパッド（固定部分）
    def _desk(self):
        im = self.blank.copy()
        d = ImageDraw.Draw(im)
        T = DESK_THEMES.get(getattr(self, "theme", "wa"), DESK_THEMES["wa"])
        TOP, SIDE, EDGE = T["top"], T["side"], T["edge"]
        y0 = DESK_NEAR[2] + DESK_THICK
        # 左の脚
        x = DESK_NEAR[0] + 9
        self.rrect(d, (x - 4, y0 - 2, x + 4, UH - 1), 1, SIDE, ol=EDGE, w=1.8)
        xb = DESK_FAR[0] + 9                                        # 奥の左の脚（少し見える）
        self.rrect(d, (xb - 3, DESK_FAR[2] + 40, xb + 3, UH - 12), 1, tuple(int(c * 0.8) for c in SIDE),
                   ol=EDGE, w=1.4)
        # 右の引き出し（引き出しはキャラの方を向いている。こちらからは背板と右の側面）
        r = DESK_NEAR[1]
        x0, x1, dep = r - 62, r - 8, 30                # dep: 奥行き（画面のたての量）
        dx = dep * SKEW
        side = tuple(int(c * 0.82) for c in SIDE)
        self.poly(d, [(x1, y0 - 2), (x1 + dx, y0 - 2 - dep), (x1 + dx, UH - 1 - dep), (x1, UH - 1)],
                  side, ol=EDGE, w=1.8)
        self.rrect(d, (x0, y0 - 2, x1, UH - 1), 0.6, SIDE, ol=EDGE, w=1.8)
        for k in range(1, 4):                                       # 背板の板目
            xk = x0 + (x1 - x0) * k / 4
            self.line(d, [(xk, y0), (xk, UH - 2)], fill=tuple(int(c * 0.9) for c in SIDE), w=0.8)
        self.slab(d, DESK_FAR, DESK_NEAR, DESK_THICK, TOP, SIDE, ol=EDGE)
        if T["grain"]:                                              # 木目
            for t in (0.2, 0.45, 0.72):
                y = DESK_FAR[2] + (DESK_NEAR[2] - DESK_FAR[2]) * t
                l = DESK_FAR[0] + (DESK_NEAR[0] - DESK_FAR[0]) * t + 4
                rr = DESK_FAR[1] + (DESK_NEAR[1] - DESK_FAR[1]) * t - 4
                self.line(d, [(l, y), (l + (rr - l) * 0.3, y - 0.6), (l + (rr - l) * 0.6, y + 0.4)], fill=T["grain"], w=0.9)
                self.line(d, [(l + (rr - l) * 0.68, y + 3), (rr, y + 2.5)], fill=T["grain"], w=0.9)
        yt, yb = DESK_NEAR[2] + 0.8, DESK_NEAR[2] + DESK_THICK - 0.6
        if T["band"] == "wave":                                     # 側面の青海波
            self.rrect(d, (DESK_NEAR[0] + 1, yt, DESK_NEAR[1] - 1, yb), 0.1, WA_INDIGO, ol=None)
            for i in range(int((DESK_NEAR[1] - DESK_NEAR[0] - 6) / 6) + 1):
                wx = DESK_NEAR[0] + 4 + i * 6
                for rr in (3.0, 1.8):
                    self.arc(d, wx, yb + 0.6, rr, 180, 360, fill=WA_CREAM, w=0.6)
        else:                                                       # スチール机のふちの帯
            self.rrect(d, (DESK_NEAR[0] + 1, yt + 1, DESK_NEAR[1] - 1, yb - 0.5), 0.1,
                       tuple(int(c * 0.9) for c in SIDE), ol=None)
            self.line(d, [(DESK_NEAR[0] + 1, yt + 0.6), (DESK_NEAR[1] - 1, yt + 0.6)], fill=(205, 208, 200), w=0.8)
        self.line(d, [(DESK_NEAR[0], yb + 0.4), (DESK_NEAR[1], yb + 0.4)], fill=EDGE, w=1.6)
        self.desk_items(d)
        self.slab(d, KB_FAR, KB_NEAR, KB_THICK, KB_BODY, KB_SIDE, ol=KB_EDGE)
        return im

    def poly(self, d, pts, fill, ol=None, w=2):
        pts = [(x + self.ox, y + self.oy) for x, y in pts]
        ox, oy, self.ox, self.oy = self.ox, self.oy, 0.0, 0.0
        d.polygon([(self.P(x), self.P(y)) for x, y in pts], fill=fill)
        if ol:
            q = [(self.P(x), self.P(y)) for x, y in pts]
            d.line(q + [q[0]], fill=ol, width=max(1, int(self.P(w))), joint="curve")
        self.ox, self.oy = ox, oy

    def slab(self, d, far, near, thick, top, side, ol=OUTLINE):
        """斜め上から見た板（上面＋手前の側面）"""
        fl, fr, nl, nr = (far[0], far[2]), (far[1], far[2]), (near[0], near[2]), (near[1], near[2])
        frd, nrd, nld = (fr[0], fr[1] + thick), (nr[0], nr[1] + thick), (nl[0], nl[1] + thick)
        sil = [fl, fr, frd, nrd, nld, nl]
        self.poly(d, sil, side, ol=ol, w=2.2)
        dark = tuple(int(c * 0.82) for c in side)
        self.poly(d, [nr, fr, frd, nrd], dark)                      # 右の側面（少し暗く）
        self.poly(d, [fl, fr, nr, nl], top)
        self.line(d, [nl, nr], fill=ol, w=1.2)
        self.line(d, [nr, nrd], fill=ol, w=1.2)
        self.line(d, sil + [fl], fill=ol, w=2.2)

    # いす（ねこのうしろの背もたれと、机の下に見える座面・脚）
    def _chair(self):
        im = self.blank.copy()
        d = ImageDraw.Draw(im)
        OL = (40, 24, 30)
        if False:
            # （横向きのいす。いまはこちら向きのいすを使う）（背もたれは背中がわ＝右）
            cx = CX + 9
            self.poly(d, [(CX + 25, 36), (CX + 37, 38), (CX + 35, 94), (CX + 23, 94)], CHAIR, ol=OL, w=2)
            self.poly(d, [(CX + 27.5, 41), (CX + 34, 42.5), (CX + 32.5, 90), (CX + 26, 90)], CHAIR_HI)
            self.rrect(d, (CX - 18, 88, CX + 36, 95), 3, CHAIR, ol=OL, w=1.8)     # 座面（机にかくれる）
            self.back_items(d)
            self.rrect(d, (cx - 3, 95, cx + 3, 145), 1, (70, 72, 76), ol=OL, w=1.4)   # ガスシリンダー
        else:
            cx = CX
            # 背もたれ（えんじ色）
            self.rrect(d, (CX - 37, 40, CX + 37, 88), 13, CHAIR, ol=OL, w=2.2)
            self.rrect(d, (CX - 31, 46, CX + 31, 84), 10, CHAIR_HI, ol=None)
            self.back_items(d)                                          # ねこのとなりからのぞく子たち
            # 座面の下（机の下から見える）
            self.rrect(d, (CX - 30, 129, CX + 30, 134), 2.5, CHAIR, ol=OL, w=1.8)
            self.rrect(d, (CX - 3, 134, CX + 3, 145), 1, (70, 72, 76), ol=OL, w=1.4)         # ガスシリンダー
        # 5本脚のキャスター
        for x1, y1 in ((cx - 24, 148), (cx + 24, 148), (cx - 12, 150.5), (cx + 12, 150.5), (cx, 146)):
            self.line(d, [(cx, 145.5), (x1, y1)], fill=OL, w=3.6)
            self.line(d, [(cx, 145.5), (x1, y1)], fill=(64, 66, 70), w=2)
            self.ell(d, x1, y1 + 0.8, 1.8, 1.6, (30, 30, 34), ol=None)
        return im

    # ---- 机の上の小物（奥から手前の順に描く） ----
    def cyl(self, d, x, ybot, r, h, body, top, ol=OUTLINE, o=1.3):
        """斜め上から見た円柱（コップ・ペン立てなど）"""
        e = 0.38
        self.ell(d, x, ybot, r + o, (r + o) * e, ol, ol=None)
        self.rrect(d, (x - r - o, ybot - h, x + r + o, ybot), 0.1, ol, ol=None)
        self.ell(d, x, ybot - h, r + o, (r + o) * e, ol, ol=None)
        self.ell(d, x, ybot, r, r * e, body, ol=None)
        self.rrect(d, (x - r, ybot - h, x + r, ybot), 0.1, body, ol=None)
        self.ell(d, x, ybot - h, r, r * e, top, ol=None)

    # 小物は 1 つずつの部品。元の絵の位置 (x0, y0) でかいてあり、置いた場所までずらしてかく。
    # ITEM_DEFS: 種類 → (名前, x0, y0, 最初に置くときの横のずれ, かく関数, 種類)
    ITEM_DEFS = {
        "bonsai": ("盆栽（松）", 15, 85, 14, "it_bonsai", "wa"),
        "notebook": ("和とじノートと筆", 18, 123, 16, "it_notebook", "wa"),
        "fude": ("竹の筆立て", 210, 90, 0, "it_fude", "wa"),
        "ume": ("梅の一輪ざし", 228, 91, 0, "it_ume", "wa"),
        "andon": ("行灯", 252, 91, 4, "it_andon", "wa"),
        "kyusu": ("急須", 205, 115, 4, "it_kyusu", "wa"),
        "yunomi": ("湯のみ", 222, 118, 4, "it_yunomi", "wa"),
        "dango": ("三色だんご", 246, 117, 2, "it_dango", "wa"),
        # 研究室（最初の位置にそのまま置くので、ずれは奥行きのぶんだけ）
        "lab_books": ("専門書の本立て", 28, 86, 3.2, "it_lab_books", "lab"),
        "lab_papers": ("計算用紙と赤ペン", 22, 122, 16.2, "it_lab_papers", "lab"),
        "lab_pens": ("ペン立て", 207, 90, 4.7, "it_lab_pens", "lab"),
        "lab_supple": ("サプリのびん", 219, 89, 4.3, "it_lab_supple", "lab"),
        "lab_cup": ("お茶のカップ", 231, 91, 5.0, "it_lab_cup", "lab"),
        "lab_tumbler": ("銀のタンブラー", 243, 89, 4.3, "it_lab_tumbler", "lab"),
        "lab_pet": ("2Lの水", 257, 91, 5.0, "it_lab_pet", "lab"),
        "lab_lemon": ("レモン水", 194, 118, 14.8, "it_lab_lemon", "lab"),
        "lab_numpad": ("テンキー", 214, 116, 14.0, "it_lab_numpad", "lab"),
        "lab_tape": ("メジャー", 236, 118, 14.8, "it_lab_tape", "lab"),
        "lab_earphone": ("イヤホンケース", 251, 119, 15.1, "it_lab_earphone", "lab"),
        "fudeneko": ("フードのねこ", 52, 79, 0, "it_fudeneko", "chara"),
        "husky": ("灰色のいぬ", PLUSH_X, PLUSH_Y + 11, 0, "it_husky", "chara"),
        "yellowdog": ("黄色いいぬ", DOG_X, DOG_Y + 11, 0, "it_yellowdog", "chara"),
    }
    PEEK_Y = DESK_FAR[2] + 6          # これより奥に置いた子は、机のふちから顔を出す

    @classmethod
    def default_item(cls, kind):
        name, x0, y0, extra, fn, cat = cls.ITEM_DEFS[kind]
        if cat == "chara":
            return {"type": kind, "x": x0, "y": y0}
        return {"type": kind, "x": round(x0 + extra - (y0 - DESK_FAR[2]) * SKEW, 1), "y": y0}

    @classmethod
    def default_layout(cls, theme="wa"):
        return [cls.default_item(k) for k, v in cls.ITEM_DEFS.items() if v[5] in (theme, "chara")]

    def peeking(self, it):
        return self.ITEM_DEFS[it["type"]][5] == "chara" and it["y"] <= self.PEEK_Y

    def draw_item(self, d, it, part="all"):
        name, x0, y0, extra, fn, cat = self.ITEM_DEFS[it["type"]]
        self.ox, self.oy = it["x"] - x0, it["y"] - y0
        self._call_item(d, it["type"], part)
        self.ox = self.oy = 0.0

    def _call_item(self, d, kind, part):
        getattr(self, self.ITEM_DEFS[kind][4])(d, part)

    def desk_items(self, d):
        for it in sorted(self.layout, key=lambda i: i["y"]):
            self.draw_item(d, it, "paws" if self.peeking(it) else "all")

    def back_items(self, d):
        for it in sorted(self.layout, key=lambda i: i["y"]):
            if self.peeking(it):
                self.draw_item(d, it, "head")

    def _measure_items(self):
        """それぞれの小物の大きさ（つかめる範囲）を、いちどかいてはかる"""
        return {kind: self.measure_one(kind) for kind in self.ITEM_DEFS}

    def measure_one(self, kind):
        name, x0, y0, extra, fn, cat = self.ITEM_DEFS[kind]
        im = self.blank.copy()
        self._call_item(ImageDraw.Draw(im), kind, "all")
        bb = im.getchannel("A").getbbox() or (0, 0, 1, 1)
        k = self.k
        return (bb[0] / k - x0, bb[1] / k - y0, bb[2] / k - x0, bb[3] / k - y0)

    def item_rect(self, it):
        if it["type"] not in self.item_box:
            self.item_box[it["type"]] = self.measure_one(it["type"])
        b = self.item_box[it["type"]]
        return (it["x"] + b[0], it["y"] + b[1], it["x"] + b[2], it["y"] + b[3])

    def item_at(self, x, y):
        """(x, y) にある小物（手前のものから）"""
        for it in sorted(self.layout, key=lambda i: -i["y"]):
            x0, y0, x1, y1 = self.item_rect(it)
            if x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1:
                return it
        return None

    def rebuild(self):
        self.chair = self._chair()
        self.desk = self._desk()

    # ---- それぞれの小物 ----
    def it_bonsai(self, d, part):
        IND, OL = WA_INDIGO, (60, 40, 30)
        self.rrect(d, (8, 80, 22, 85), 1.2, IND, ol=OL, w=1.1)
        self.line(d, [(15, 81), (13, 76), (17, 71), (14, 67)], fill=(110, 72, 46), w=2)
        for fx_, fy_, rx_ in ((10, 71, 4.4), (19, 68, 4.8), (14, 64, 4), (20, 74, 3.2)):
            self.ell(d, fx_, fy_, rx_, 2.6, (64, 112, 64), ol=(40, 70, 40), w=0.9)

    def it_notebook(self, d, part):
        IND, CREAM, OL, BAMBOO = WA_INDIGO, WA_CREAM, (60, 40, 30), (196, 188, 112)
        self.poly(d, [(4, 101), (30, 99), (32, 121), (3, 123)], IND, ol=OL, w=1.1)
        self.poly(d, [(22, 102), (27, 101.6), (28.5, 113), (23.2, 113.4)], CREAM)          # 題せん
        for k in range(4):                                                                  # とじ糸
            yk = 103 + k * 5.6
            self.line(d, [(5.2, yk), (8, yk - 0.2)], fill=CREAM, w=0.8)
        self.line(d, [(10, 120), (30, 113.5)], fill=BAMBOO, w=1.8)                          # 筆
        self.line(d, [(30, 113.5), (34, 112.2)], fill=(30, 30, 30), w=2)

    def it_fude(self, d, part):
        OL, BAMBOO = (60, 40, 30), (196, 188, 112)
        self.cyl(d, 210, 90, 5.5, 11, BAMBOO, (150, 140, 80), ol=OL)
        self.line(d, [(204.5, 84.5), (215.5, 84.5)], fill=(150, 140, 80), w=0.8)
        for dx, tilt in ((-3, -3), (-1, -1), (1.5, 1.5), (3.2, 3.2)):
            self.line(d, [(210 + dx, 79), (210 + dx + tilt, 68 - abs(dx))], fill=BAMBOO, w=1.5)
            self.ell(d, 210 + dx + tilt, 68 - abs(dx), 0.8, 0.8, (60, 40, 30), ol=None)

    def it_ume(self, d, part):
        IND, RED, GOLD, OL = WA_INDIGO, WA_RED, WA_GOLD, (60, 40, 30)
        self.cyl(d, 228, 91, 3.6, 8, IND, IND, ol=OL)
        self.rrect(d, (226.6, 80, 229.4, 83.5), 0.5, IND, ol=OL, w=0.9)
        self.line(d, [(228, 81), (226, 72), (229, 64), (233, 58)], fill=(100, 64, 40), w=1.2)
        self.line(d, [(226.5, 74), (221, 68)], fill=(100, 64, 40), w=1)
        for px, py in ((233, 58), (221, 68), (229, 64), (225.5, 71.5)):
            for k in range(5):
                ang = k * 2 * math.pi / 5
                self.ell(d, px + 1.4 * math.cos(ang), py + 1.4 * math.sin(ang), 1.1, 1.1, RED, ol=None)
            self.ell(d, px, py, 0.6, 0.6, GOLD, ol=None)

    def it_andon(self, d, part):
        OL, ax = (60, 40, 30), 252
        self.rrect(d, (ax - 8, 88, ax + 8, 91.5), 0.5, (96, 60, 36), ol=OL, w=1)
        self.rrect(d, (ax - 7, 64, ax + 7, 88), 0.5, (255, 238, 188), ol=OL, w=1.2)
        for x_ in (ax - 7, ax, ax + 7):
            self.line(d, [(x_, 64), (x_, 88)], fill=(96, 60, 36), w=1.1)
        for y_ in (72, 80):
            self.line(d, [(ax - 7, y_), (ax + 7, y_)], fill=(96, 60, 36), w=0.8)
        self.rrect(d, (ax - 8.5, 61.5, ax + 8.5, 64.5), 0.5, (96, 60, 36), ol=OL, w=1)

    def it_kyusu(self, d, part):
        OL, kx, ky = (60, 40, 30), 205, 115
        self.line(d, [(kx + 5, ky - 6), (kx + 12, ky - 9)], fill=OL, w=3)                  # 横の持ち手
        self.line(d, [(kx + 5, ky - 6), (kx + 12, ky - 9)], fill=(150, 76, 48), w=1.8)
        self.poly(d, [(kx - 5, ky - 6), (kx - 10, ky - 10), (kx - 8.6, ky - 10.8), (kx - 3, ky - 8)],
                  (150, 76, 48), ol=OL, w=1)                                               # 注ぎ口
        self.ell(d, kx, ky - 5, 7, 5.5, (150, 76, 48), ol=OL, w=1.2)
        self.ell(d, kx, ky - 9.6, 4, 1.4, (128, 62, 40), ol=OL, w=0.9)
        self.ell(d, kx, ky - 11, 1.2, 0.9, (128, 62, 40), ol=OL, w=0.8)

    def it_yunomi(self, d, part):
        OL = (60, 40, 30)
        self.cyl(d, 222, 118, 4.5, 8, WA_CREAM, WA_MATCHA, ol=OL)
        self.rrect(d, (217.5, 113, 226.5, 115), 0.1, WA_INDIGO, ol=None)
        for k in (-1.5, 1.8):                                                               # ゆげ
            self.line(d, [(222 + k, 107), (223.5 + k, 104), (222 + k, 101), (223.5 + k, 98)],
                      fill=(220, 214, 206), w=0.9)

    def it_dango(self, d, part):
        self.ell(d, 246, 117, 10, 3.4, WA_CREAM, ol=WA_INDIGO, w=1.1)
        self.line(d, [(236, 117), (256, 114.5)], fill=(200, 170, 110), w=0.8)
        for k, col in enumerate(((246, 150, 170), (252, 250, 244), (150, 186, 100))):
            self.ell(d, 240.5 + k * 5.5, 116.2 - k * 0.7, 2.7, 2.4, col, ol=(150, 130, 120), w=0.7)


    # ---- 研究室の小物 ----
    def it_lab_books(self, d, part):
        OL = (50, 46, 44)
        self.rrect(d, (19, 72, 21, 86), 0.4, (120, 124, 130), ol=OL, w=0.8)          # ブックエンド
        x = 21.3
        for w_, h_, col in ((3.6, 15, (70, 160, 150)), (3, 13, (236, 228, 206)), (3.8, 16, (120, 168, 90)),
                            (3.2, 14, (150, 100, 60)), (3.4, 15.5, (240, 238, 232)), (2.8, 12, (150, 40, 52))):
            self.rrect(d, (x, 86 - h_, x + w_, 86), 0.4, col, ol=OL, w=0.8)
            self.line(d, [(x + w_ / 2, 86 - h_ + 3), (x + w_ / 2, 86 - h_ + 8)], fill=(40, 40, 40), w=0.5)
            x += w_ + 0.2
        self.rrect(d, (x + 0.2, 72, x + 2.2, 86), 0.4, (120, 124, 130), ol=OL, w=0.8)

    def it_lab_papers(self, d, part):
        self.poly(d, [(10, 101), (34, 98), (36, 121), (8, 123)], (240, 240, 236), ol=(150, 150, 150), w=0.9)
        self.poly(d, [(12, 99), (36, 99), (35, 119), (10, 120)], (252, 252, 250), ol=(150, 150, 150), w=0.9)
        for i in range(6):
            y = 102 + i * 2.9
            pts = [(13 + j * 3.3, y + (0.6 if j % 2 else -0.4)) for j in range(7)]
            self.line(d, pts, fill=(70, 96, 200), w=0.6)
        self.line(d, [(14, 118.5), (32, 113)], fill=(150, 20, 34), w=2)                  # 赤いペン
        self.line(d, [(32, 113), (35, 112.2)], fill=(200, 200, 206), w=1.2)

    def it_lab_pens(self, d, part):
        OL = (40, 40, 44)
        self.cyl(d, 207, 90, 4.8, 10, (40, 40, 44), (22, 22, 24), ol=OL)
        for dx, tilt, col in ((-2.6, -2.5, (40, 160, 80)), (-0.8, -1, (240, 220, 40)), (1.2, 1.2, (40, 90, 200)),
                              (2.8, 3, (210, 50, 60))):
            self.line(d, [(207 + dx, 80), (207 + dx + tilt, 70 - abs(dx))], fill=col, w=1.4)

    def it_lab_supple(self, d, part):
        OL = (40, 30, 20)
        self.cyl(d, 219, 89, 3.4, 9, (92, 52, 22), (70, 40, 16), ol=OL)
        self.rrect(d, (215.6, 82.5, 222.4, 86.5), 0.2, (240, 170, 50), ol=None)          # ラベル
        self.cyl(d, 219, 80, 3.2, 2.6, (246, 204, 40), (250, 220, 70), ol=OL)           # 黄色いふた

    def it_lab_cup(self, d, part):
        OL = (90, 70, 50)
        self.cyl(d, 231, 91, 4.4, 8, (244, 240, 232), (128, 78, 36), ol=OL)
        self.rrect(d, (226.6, 87, 235.4, 91), 0.1, (176, 120, 72), ol=None)            # 下半分は茶色
        self.ell(d, 231, 91, 4.4, 1.7, (176, 120, 72), ol=None)

    def it_lab_tumbler(self, d, part):
        self.cyl(d, 243, 89, 4.4, 15, (198, 202, 210), (140, 144, 152), ol=(96, 100, 108))
        self.line(d, [(241, 76), (241, 88)], fill=(236, 238, 242), w=1.1)

    def it_lab_pet(self, d, part):
        bx = 257
        body = [(bx - 6.5, 91), (bx - 6.5, 64), (bx - 3.6, 57), (bx - 1.8, 52), (bx + 1.8, 52), (bx + 3.6, 57),
                (bx + 6.5, 64), (bx + 6.5, 91)]
        self.poly(d, body, (222, 238, 250), ol=(104, 136, 172), w=1.2)
        self.rrect(d, (bx - 6.5, 70, bx + 6.5, 77), 0.2, (70, 130, 214), ol=None)
        self.line(d, [(bx - 4, 62), (bx - 4, 88)], fill=(250, 252, 255), w=1.1)
        self.rrect(d, (bx - 2.4, 47.5, bx + 2.4, 52.3), 0.8, (250, 250, 250), ol=(104, 136, 172), w=0.9)

    def it_lab_lemon(self, d, part):
        bx = 194
        body = [(bx - 4, 118), (bx - 4, 101), (bx - 2, 97), (bx - 1.4, 94), (bx + 1.4, 94), (bx + 2, 97),
                (bx + 4, 101), (bx + 4, 118)]
        self.poly(d, body, (226, 240, 248), ol=(110, 140, 170), w=1.1)
        self.rrect(d, (bx - 4, 106, bx + 4, 113), 0.2, (60, 110, 200), ol=None)         # ラベル
        self.rrect(d, (bx - 2.5, 108, bx + 2.5, 111), 0.4, (250, 220, 60), ol=None)
        self.rrect(d, (bx - 1.8, 91, bx + 1.8, 94.4), 0.6, (250, 250, 250), ol=(110, 140, 170), w=0.8)

    def it_lab_numpad(self, d, part):
        self.slab(d, (204, 224, 104), (203, 225, 115), 2.6, (150, 152, 158), (104, 106, 112), ol=(40, 40, 44))
        for r_ in range(4):
            for c_ in range(4):
                x0 = 205.4 + c_ * 4.7
                y0 = 105.4 + r_ * 2.4
                self.rrect(d, (x0, y0, x0 + 3.8, y0 + 1.8), 0.4, (84, 86, 92), ol=None)

    def it_lab_tape(self, d, part):
        self.rrect(d, (231, 110, 241, 118), 2.6, (36, 36, 40), ol=(20, 20, 22), w=1)
        self.rrect(d, (232.5, 111.5, 239.5, 114.5), 1.2, (246, 204, 40), ol=None)
        self.ell(d, 236, 116, 1.6, 1, (120, 120, 126), ol=None)

    def it_lab_earphone(self, d, part):
        self.ell(d, 251, 119.5, 6.5, 3.6, (22, 22, 24), ol=(40, 40, 44), w=1.1)
        self.ell(d, 251, 117.4, 6.5, 3.6, (52, 52, 56), ol=(40, 40, 44), w=1.1)
        self.ell(d, 251, 117.4, 3.4, 1.8, (66, 66, 72), ol=None)

    # ---- 絵の画像をそのまま使うキャラ ----
    SPRITES = {   # 名前: (ファイル, 使う範囲, 足もとの点, 高さ[ペットの絵の px])
        "fudeneko": ("fudeneko.png", (195, 163, 569, 699), (382, 699), 46),
    }

    def sprite(self, name):
        """画像を読みこんで、白い背景をすきとおらせ、この大きさにしたもの（1回だけ作る）"""
        cache = self.__dict__.setdefault("_sprites", {})
        if name not in cache:
            fname, box, foot, height = self.SPRITES[name]
            src = Image.open(paths.res(fname)).convert("RGB")
            for c in ((0, 0), (src.width - 1, 0), (0, src.height - 1), (src.width - 1, src.height - 1)):
                ImageDraw.floodfill(src, c, (255, 0, 255), thresh=30)
            mask = ImageChops.difference(src, Image.new("RGB", src.size, (255, 0, 255))).convert("L").point(
                lambda v: 255 if v > 0 else 0)
            rgba = src.convert("RGBA")
            rgba.putalpha(mask)
            rgba = rgba.crop(box)
            sc = self.P(height) / rgba.height
            rgba = rgba.resize((max(1, int(rgba.width * sc)), max(1, int(rgba.height * sc))), LANCZOS)
            cache[name] = (rgba, (foot[0] - box[0]) * sc)
        return cache[name]

    def draw_sprite(self, d, name, x, y, part):
        """足もとが (x, y) にくるように画像をはる。机の奥でのぞくときは、下を机にかくす"""
        if part == "paws":
            return
        spr, fx = self.sprite(name)
        bottom = y + self.oy + (16 if part == "head" else 0)
        d._image.paste(spr, (int(self.P(x + self.ox) - fx), int(self.P(bottom) - spr.height)), spr)

    def it_fudeneko(self, d, part):
        self.draw_sprite(d, "fudeneko", 52, 79, part)

    def it_husky(self, d, part):
        if part in ("all", "head"):
            self.plush_head(d, PLUSH_X, PLUSH_Y)
        if part in ("all", "paws"):
            self.plush_paws(d, PLUSH_X, PLUSH_Y)

    def it_yellowdog(self, d, part):
        if part in ("all", "head"):
            self.dog_head(d, DOG_X, DOG_Y)
        if part in ("all", "paws"):
            self.dog_paws(d, DOG_X, DOG_Y)

    # ---- ねこのとなりからのぞく2ひき（どちらも全身が小判型のだ円） ----
    DOG_COL, DOG_OL, DOG_MUZZLE = (252, 234, 158), (150, 124, 70), (150, 132, 120)
    PLUSH_GR, PLUSH_WH, PLUSH_OL = (170, 176, 188), (250, 250, 252), (96, 102, 114)

    def dog_paws(self, d, hx, hy):
        """机のふちにかけた、黄色い犬の前足"""
        for dx in (-5, 5):
            self.ell(d, hx + dx, hy + 11, 3.2, 2.3, self.DOG_COL, ol=self.DOG_OL, w=1.1)

    def dog_head(self, d, hx, hy):
        """全身が横長のだ円の、黄色い犬（丸い耳、点の目、茶色い鼻まわり）"""
        C, OL, MZ = self.DOG_COL, self.DOG_OL, self.DOG_MUZZLE
        for side in (-1, 1):                                                   # 丸い耳
            self.ell(d, hx + side * 9, hy - 9, 3.4, 2.8, C, ol=OL, w=1.2)
        self.ell(d, hx, hy + 2, 16, 11, C, ol=OL, w=1.3)                       # 小判型の体
        for side in (-1, 1):                                                   # 点の目
            self.ell(d, hx + side * 6.4, hy - 2, 1.3, 1.4, (34, 28, 26), ol=None)
        self.ell(d, hx, hy + 2.6, 4.6, 3.6, MZ, ol=None)                       # 鼻まわり
        self.ell(d, hx, hy + 1, 1.7, 1.2, (40, 32, 30), ol=None)                # 鼻
        self.line(d, [(hx, hy + 2.2), (hx, hy + 3.8)], fill=(40, 32, 30), w=0.7)
        self.line(d, [(hx - 1.8, hy + 4.8), (hx, hy + 3.8), (hx + 1.8, hy + 4.8)], fill=(40, 32, 30), w=0.7)

    def plush_paws(self, d, hx, hy):
        """机のふちにかけた、灰色の犬の前足"""
        for dx in (-5, 5):
            self.ell(d, hx + dx, hy + 11, 3, 2.2, self.PLUSH_WH, ol=self.PLUSH_OL, w=1.1)

    def plush_head(self, d, hx, hy):
        """全身が横長のだ円の、ねむそうな灰色の犬（上が灰色、下が白）"""
        GR, WH, OLP = self.PLUSH_GR, self.PLUSH_WH, self.PLUSH_OL
        EYE_B = (96, 196, 218)
        for side in (-1, 1):                                                   # 小さい三角の耳
            self.poly(d, [(hx + side * 4, hy - 8), (hx + side * 11, hy - 6), (hx + side * 9, hy - 12)],
                      GR, ol=OLP, w=1.3)
        self.ell(d, hx, hy + 2, 15, 11, GR, ol=OLP, w=1.4)                     # 小判型の体
        self.ell(d, hx, hy + 6.5, 12.5, 6, WH, ol=None)                        # 下半分は白
        self.poly(d, [(hx - 1.4, hy + 2), (hx, hy - 6), (hx + 1.4, hy + 2)], WH)
        for side in (-1, 1):                                                   # まゆげの白い点
            self.ell(d, hx + side * 4.4, hy - 4, 1.3, 0.9, WH, ol=None)
        for side in (-1, 1):                                                   # ねむそうな目
            ex, ey = hx + side * 4, hy - 0.8
            self.ell(d, ex, ey, 1.9, 1.5, EYE_B, ol=None)
            self.ell(d, ex, ey + 0.4, 0.8, 0.8, (30, 34, 44), ol=None)
            self.rrect(d, (ex - 2.2, ey - 1.8, ex + 2.2, ey - 0.1), 0.1, GR, ol=None)
            self.line(d, [(ex - 2.1, ey - 0.1), (ex + 2.1, ey - 0.1)], fill=(40, 44, 54), w=0.8)
        self.ell(d, hx, hy + 2.4, 1.5, 1.05, (30, 30, 36), ol=None)            # 鼻と口
        self.line(d, [(hx - 1.6, hy + 5), (hx, hy + 4.2), (hx + 1.6, hy + 5)], fill=(60, 64, 74), w=0.7)

    def keys(self, d, pressed):
        for idx in KEY_ORDER:
            down = idx in pressed or PARTNER.get(idx) in pressed
            h = KEY_H_DOWN if down else KEY_H
            self.poly(d, key_quad(idx, 0, grow=0.9), KB_HIT if down else KB_GLOW)   # バックライト
            base = key_quad(idx, 0)
            top = key_quad(idx, h)
            self.poly(d, [top[0], top[1], base[1], base[2], base[3], top[0]],
                      HIT_SIDE if down else KEY_SIDE)
            self.poly(d, [top[3], top[2], base[2], base[3]], HIT_SIDE if down else KEY_SIDE)
            face = KB_HIT if down else (KB_FN if KEY_KINDS[idx] == "fn" else KB_KEY)
            self.poly(d, top, face)

    # 体（腕なし）。eyes/fx/breath/sway/z でキャッシュ
    def body(self, eyes, fx, breath, sway, z, flap=0):
        """キャラの体（腕なし）。ペットごとのキャラ（CURRENT_CHAR）でかく"""
        key = (CURRENT_CHAR, eyes, fx, breath, sway, z, flap)
        if key in self._body:
            return self._body[key]
        im = self.blank.copy()
        d = ImageDraw.Draw(im)
        custom_ok = False
        if is_custom():
            if getattr(self, "_custom", None) is None:
                self._custom = jisaku.CustomChara(CUSTOM, self.k)
            custom_ok = self._custom.ok()
            if custom_ok:
                self._custom.render(self, im, CX, char_neck_y(), eyes, fx, breath, sway, flap)
                d = ImageDraw.Draw(im)
        if is_person() and not custom_ok:          # 自作キャラがまだ完成していないときは、ひとでかく
            if getattr(self, "_hito", None) is None:
                self._hito = hito.Hito(self.k)
            self._hito.render(self, im, CX, HITO_NECK_Y, eyes, fx, breath, sway, flap)
            d = ImageDraw.Draw(im)
        if z is not None:
            drift = z * 2
            d.text((self.P(CX - 66), self.P(26 - drift)), "Z", font=self.font_b, fill=ZZZ)
            d.text((self.P(CX - 54), self.P(42 - drift)), "z", font=self.font_s, fill=ZZZ)

        self._body[key] = im
        return im

    MOUSE_SHAPE = [(-1, -11), (4, -10.6), (7, -8.5), (10.5, -7.5), (12, -4), (11, -0.5),
                   (8, 1.5), (7.2, 4), (6.2, 7.5), (4.5, 10), (1.5, 11.2), (-2, 11), (-5, 9.5),
                   (-6.6, 6), (-7.2, 1), (-7.2, -4), (-5.5, -8.5)]

    def mouse(self, d, mx, my, lb, rb):
        k, sy = 1.2, 0.85                          # 大きさ／斜め上から見ているので少しつぶす
        pts = lambda ps, dy=0: [(mx + x * k, my + y * k * sy + dy) for x, y in ps]
        self.poly(d, pts(self.MOUSE_SHAPE, 3), MOUSE_SIDE, ol=MOUSE_LINE, w=2.2)   # 側面
        self.poly(d, pts(self.MOUSE_SHAPE), MOUSE_TOP, ol=MOUSE_LINE, w=2.2)
        right = [(0, 3), (7.2, 3), (6.2, 7.5), (4.5, 10), (1.5, 11.2), (0, 11.2)]
        left = [(0, 3), (-7.2, 3), (-6.6, 6), (-5, 9.5), (-2, 11), (0, 11.1)]
        if lb:                                     # もちまるの左ボタン＝画面の右
            self.poly(d, pts(right), KB_HIT)
        if rb:
            self.poly(d, pts(left), KB_HIT)
        self.line(d, pts([(-7.1, 3), (7.1, 3)]), fill=MOUSE_LINE, w=1.2)          # ボタンの境目
        self.line(d, pts([(0, 3), (0, 11.1)]), fill=MOUSE_LINE, w=1.2)
        self.line(d, pts([(7.6, -6.5), (8, 1.2)]), fill=MOUSE_LINE, w=1)          # 親指の台の境目
        # ホイール（金属）と、親指のホイール
        self.rrect(d, (mx - 1.6, my + 5 * sy, mx + 1.6, my + 10.8 * sy), 1, MOUSE_WHEEL, ol=MOUSE_LINE, w=0.8)
        self.rrect(d, (mx + 10.1, my - 5.4 * sy, mx + 12.7, my - 2.4 * sy), 0.8, MOUSE_WHEEL, ol=MOUSE_LINE, w=0.7)

    def compose(self, sc):
        """sc: dict（Pet.scene 参照）→ 透過キー色つき RGB 画像"""
        # 上によゆうのある画用紙に、ぜんぶ TOP_M だけ下げてかく
        M = int(self.P(TOP_M))
        im = Image.new("RGBA", (self.cw, self.ch + M), (0, 0, 0, 0))
        im.paste(self.chair, (0, M), self.chair)
        dy = sc["dy"]
        body = self.body(sc["eyes"], sc["fx"], sc["breath"], sc["sway"], sc["z"], sc.get("flap", 0))
        im.paste(body, (0, M + int(self.P(dy))), body)
        desk = self.desk
        im.paste(desk, (0, M), desk)
        d = ImageDraw.Draw(im)
        self.ox, self.oy = 0.0, TOP_M

        self.keys(d, sc["pressed"])

        # マウス（手にそう形の大きめマウス。もちまるから見て右手用なので、
        # 親指の台は画面の右がわ、ボタンはもちまるから遠い側＝画面の下）
        mx, my = MOUSE_C[0] + sc["moff"][0], MOUSE_C[1] + sc["moff"][1] * 0.6
        self.mouse(d, mx, my, sc["lb"], sc["rb"])

        # 腕（ちょっとのびる）
        if is_person():
            c = hito.arm_colors()
            hand_img = None
            if is_custom() and getattr(self, "_custom", None) is not None and self._custom.ok():
                c = {"line": tuple(CUSTOM["arm_line"]), "sleeve": tuple(CUSTOM["arm"]), "skin": tuple(CUSTOM["skin"])}
                hand_img = self._custom.hand()
            behind = not is_custom() or CUSTOM.get("behind")
            shl, shr = shoulders()
            arms = ((-1, sc["pl"], sc["lp"], shl), (1, sc["pr"], sc["rp"], shr))
            for side, paw, down, (sx, sy) in arms:
                if side > 0 and behind:
                    # 左を向いているので、マウスを持つ側（画面の左の手）は体のうしろ。
                    # その手をかいたあとで、机より上に出ている体と頭をもういちど上にのせる
                    top = int(self.P(DESK_FAR[2])) - int(self.P(dy))      # 体の絵の中で、机より上の部分
                    if top > 0:
                        part = body.crop((0, 0, body.width, min(top, body.height)))
                        im.paste(part, (0, M + int(self.P(dy))), part)
                        d = ImageDraw.Draw(im)
                sy += dy
                px, py = paw[0] / 2, paw[1] / 2
                ex, ey = sx + (px - sx) * 0.3, sy + (py - sy) * 0.3     # そでのおわり
                self.line(d, [(sx, sy), (px, py)], fill=c["line"], w=9.6)
                self.ell(d, sx, sy, 5.6, 5.6, c["line"], ol=None)
                self.line(d, [(ex, ey), (px, py)], fill=c["skin"], w=6)
                self.line(d, [(sx, sy), (ex, ey)], fill=c["sleeve"], w=7)
                self.ell(d, sx, sy, 4, 4, c["sleeve"], ol=None)
                if hand_img is not None:                 # 自作の手の画像
                    hx_, hy_ = self.P(px + self.ox) - hand_img.width / 2, self.P(py + self.oy + (1 if down else 0)) - hand_img.height / 2
                    im.paste(hand_img, (int(hx_), int(hy_)), hand_img)
                    d = ImageDraw.Draw(im)
                else:
                    self.ell(d, px, py + (1 if down else 0), 5.6, 4.2 if down else 5, c["skin"], ol=c["line"], w=1.6)

        if sc.get("edit"):
            for it in self.layout:
                x0, y0, x1, y1 = self.item_rect(it)
                col = (230, 60, 90) if it is sc.get("held") else (60, 120, 230)
                for a_, b_ in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                    n = max(1, int(math.hypot(b_[0] - a_[0], b_[1] - a_[1]) / 3))
                    for i in range(0, n, 2):
                        p = (a_[0] + (b_[0] - a_[0]) * i / n, a_[1] + (b_[1] - a_[1]) * i / n)
                        q = (a_[0] + (b_[0] - a_[0]) * (i + 1) / n, a_[1] + (b_[1] - a_[1]) * (i + 1) / n)
                        self.line(d, [p, q], fill=col, w=1.2)
            d.text((self.P(4), self.P(2 + TOP_M)), "もようがえ中", font=self.font_j, fill=(230, 60, 90))

        self.ox, self.oy = 0.0, 0.0
        small = im.resize((self.W, self.H), LANCZOS)
        alpha = small.getchannel("A").point(lambda a: 255 if a >= 110 else 0)
        out = Image.new("RGB", small.size, KEY)
        out.paste(small.convert("RGB"), mask=alpha)
        return out


# ============================================================
#  Windows まわり
# ============================================================
def set_dpi_aware():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_dpi_scale():
    try:
        return ctypes.windll.user32.GetDpiForSystem() / 96.0
    except Exception:
        return 1.0


class _RECT(ctypes.Structure):
    _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long), ("r", ctypes.c_long), ("b", ctypes.c_long)]


class _MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", _RECT), ("rcWork", _RECT), ("dwFlags", ctypes.c_ulong)]


class _PT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def monitor_workarea(x, y, fallback):
    """(x, y) がのっている（いちばん近い）モニターの、タスクバーをのぞいた範囲"""
    try:
        u = ctypes.windll.user32
        u.MonitorFromPoint.restype = ctypes.c_void_p
        h = u.MonitorFromPoint(_PT(int(x), int(y)), 2)          # 2 = いちばん近いモニター
        mi = _MONITORINFO()
        mi.cbSize = ctypes.sizeof(_MONITORINFO)
        if h and u.GetMonitorInfoW(ctypes.c_void_p(h), ctypes.byref(mi)):
            w = mi.rcWork
            if w.r > w.l and w.b > w.t:
                return w.l, w.t, w.r, w.b
    except Exception:
        pass
    return fallback


def get_workarea(root):
    try:
        class RECT(ctypes.Structure):
            _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long),
                        ("r", ctypes.c_long), ("b", ctypes.c_long)]
        r = RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0)
        if r.r > r.l and r.b > r.t:
            return r.l, r.t, r.r, r.b
    except Exception:
        pass
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight() - 48


try:
    _GAKS = ctypes.windll.user32.GetAsyncKeyState
except Exception:
    _GAKS = None


def is_down(vk):
    return bool(_GAKS and _GAKS(vk) & 0x8000)


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def cursor_pos():
    p = _POINT()
    try:
        ctypes.windll.user32.GetCursorPos(ctypes.byref(p))
    except Exception:
        return None
    return p.x, p.y


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ============================================================
#  ペット
# ============================================================
class Pet:
    def __init__(self, app, char="person"):
        global CURRENT_CHAR
        self.app = app
        self.char = CURRENT_CHAR = char
        art = app.art
        self.W, self.H = art.W, art.H
        self.win = tk.Toplevel(app.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", bool(app.cfg["topmost"]))
        self.win.config(bg=KEY_HEX)
        self.win.attributes("-transparentcolor", KEY_HEX)
        self.label = tk.Label(self.win, bg=KEY_HEX, bd=0, highlightthickness=0, cursor="hand2")
        self.label.pack()

        l, t, r, b = app.workarea
        self.x = float(random.randint(l, max(l, r - self.W)))
        self.y = float(t)
        self.vx, self.vy = random.uniform(-3, 3), 0.0
        self.state = "fall"
        self.timer = 0
        self.tick = 0
        self.sleep_start = 0.0
        self.pl, self.pr = list(rest_pos()[0]), list(rest_pos()[1])
        self.hold_l = self.hold_r = 0.0
        self.key_l = self.key_r = None
        self.shown = None
        self.photo = None
        self.pos = None
        self.press = None
        self.held = None
        self.trail = []

        self.label.bind("<ButtonPress-1>", self.on_press)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<ButtonRelease-1>", self.on_release)
        self.label.bind("<Button-3>", self.on_menu)

        self.label.bind("<Double-Button-1>", lambda e: app.open_settings())

        m = tk.Menu(self.win, tearoff=0)
        m.add_command(label="設定…（ダブルクリックでも開けます）", command=app.open_settings)
        m.add_checkbutton(label="もようがえ（小物やキャラを動かす）", variable=app.edit_var,
                          command=app.edit_changed)
        add = tk.Menu(m, tearoff=0)

        def fill_add():
            add.delete(0, "end")
            for group, gname in (("chara", "キャラ"), ("wa", "和風"), ("lab", "研究室")):
                sm = tk.Menu(add, tearoff=0)
                for kind, d_ in Art.ITEM_DEFS.items():
                    if d_[5] == group:
                        sm.add_command(label=d_[0], command=lambda k=kind: app.add_item(k))
                if sm.index("end") is not None:
                    add.add_cascade(label=gname, menu=sm)
        add.config(postcommand=fill_add)
        fill_add()
        m.add_cascade(label="小物・キャラを出す", menu=add)
        m.add_separator()
        m.add_command(label="ねる", command=self.go_sleep)
        m.add_command(label="ジャンプ", command=lambda: self.set_state("happy", 24))
        m.add_separator()
        cm = tk.Menu(m, tearoff=0)
        self.char_var = tk.StringVar(value=self.char)
        for key, label in CHAR_NAMES.items():
            cm.add_radiobutton(label=label, value=key, variable=self.char_var,
                               command=lambda: app.set_pet_char(self, self.char_var.get()))
        m.add_cascade(label="この子のキャラ", menu=cm)
        call = tk.Menu(m, tearoff=0)
        for key, label in CHAR_NAMES.items():
            call.add_command(label=label, command=lambda k=key: app.add_pet(k))
        m.add_cascade(label="もう1人よぶ", menu=call)
        m.add_separator()
        m.add_command(label="この子をしまう", command=self.close)
        m.add_command(label="ぜんぶ終了", command=app.quit)
        self.menu = m
        self.render()

    @property
    def workarea(self):
        """このペットがいるモニターの範囲（2画面でも、いる画面の上で動く）"""
        return monitor_workarea(self.x + self.W / 2, self.y + self.H / 2, self.app.workarea)

    @property
    def ground(self):
        return self.workarea[3] - self.H

    def set_state(self, s, timer=0):
        if self.state == "drag":
            return
        self.state, self.timer, self.tick = s, timer, 0

    def go_sleep(self):
        self.set_state("sleep")
        self.sleep_start = time.time()

    # ---- マウス操作（ペットをつかむ） ----
    def logical(self, e):
        s = self.app.art.scale
        return e.x / s, e.y / s - TOP_M

    def on_press(self, e):
        self.held = None
        if self.app.edit_var.get():
            lx, ly = self.logical(e)
            it = self.app.art.item_at(lx, ly)
            if it is not None:                     # 小物をつかむ
                self.held = (it, it["x"] - lx, it["y"] - ly)
                self.app.layout_dirty = True
                return
        self.press = (e.x_root, e.y_root, e.x_root - self.x, e.y_root - self.y)
        self.trail = [(time.time(), e.x_root, e.y_root)]

    def on_drag(self, e):
        if self.held:
            it, ox, oy = self.held
            lx, ly = self.logical(e)
            it["x"] = round(clamp(lx + ox, 4, UW - 4), 1)
            it["y"] = round(clamp(ly + oy, 70, DESK_NEAR[2] - 1), 1)
            self.app.layout_dirty = True
            return
        if not self.press:
            return
        px, py, ox, oy = self.press
        if self.app.cfg["locked"]:
            return
        if self.state != "drag" and abs(e.x_root - px) + abs(e.y_root - py) > 5:
            self.state, self.tick = "drag", 0
        if self.state == "drag":
            self.x, self.y = e.x_root - ox, e.y_root - oy
            self.trail.append((time.time(), e.x_root, e.y_root))
            self.trail = self.trail[-6:]

    def on_release(self, e):
        if self.held:
            self.held = None
            save_layout(self.app.art)
            self.app.layout_dirty = True
            return
        if self.press is None:
            return
        if self.state == "drag":
            t0, x0, y0 = self.trail[0]
            dt = max(time.time() - t0, 1e-3)
            self.vx = clamp((e.x_root - x0) / dt / 30, -40, 40)
            self.vy = clamp((e.y_root - y0) / dt / 30, -40, 40)
            self.state, self.tick = "fall", 0
        elif self.state != "fall":
            self.set_state("happy", 24)
        self.press = None

    def on_menu(self, e):
        menu = self.menu
        if self.app.edit_var.get():
            it = self.app.art.item_at(*self.logical(e))
            if it is not None:                     # もようがえ中に小物を右クリック → しまう
                menu = tk.Menu(self.win, tearoff=0)
                menu.add_command(label=f"「{Art.ITEM_DEFS[it['type']][0]}」をしまう",
                                 command=lambda: self.app.remove_item(it))
                menu.add_command(label="もようがえをおわる", command=lambda: self.app.edit_var.set(False))
        try:
            menu.tk_popup(e.x_root, e.y_root)
        finally:
            menu.grab_release()

    # ---- 毎フレーム ----
    def update(self):
        global CURRENT_CHAR
        CURRENT_CHAR = self.char
        app = self.app
        now = time.time()
        self.tick += 1
        l, t, r, b = self.workarea
        right = r - self.W
        s = self.state

        if s == "fall":
            self.vy = min(self.vy + 1.1, 32)
            self.x += self.vx
            self.y += self.vy
            self.vx *= 0.99
            if self.x < l:
                self.x, self.vx = l, -self.vx * 0.5
            elif self.x > right:
                self.x, self.vx = right, -self.vx * 0.5
            if self.y < t:
                self.y, self.vy = t, 0
            if self.y >= self.ground:
                self.y, self.vx, self.vy = self.ground, 0, 0
                self.state = "idle"
                self.set_state("happy", 24)
        elif s != "drag":
            if self.y < self.ground - 1:
                self.state, self.vy = "fall", 0
            self.y = min(self.y, self.ground)
            active = now - app.last_input < 1.5
            if s == "sleep":
                if app.last_input > self.sleep_start:
                    self.set_state("work")
            elif s == "happy":
                self.timer -= 1
                if self.timer <= 0:
                    self.set_state("idle")
            else:
                want = "work" if active else "idle"
                if want != s:
                    self.set_state(want)
                if want == "idle" and now - app.last_input > app.cfg["sleep_min"] * 60 and random.random() < 0.003:
                    self.go_sleep()

        self.move_paws(now)
        self.render()

    def move_paws(self, now):
        app = self.app
        for idx in app.new_presses:
            cx, cy = key_center(idx)
            if cx < KB_MID:
                self.pl = [cx, cy]
                self.hold_l, self.key_l = now + 0.45, idx
            else:
                self.pr = [cx, cy]
                self.hold_r, self.key_r = now + 0.45, idx

        if self.state == "happy":
            tl, tr = (CX - 48, 62), (CX + 48, 62)
        elif self.state in ("drag", "fall"):
            tl, tr = (CX - 50, 70), (CX + 50, 70)
        else:
            # 画面左の手（＝もちまるの右手）がマウス担当
            # キーを押していないときは手を体の横にもどす
            rl, rr = rest_pos()
            tr = self.pr if now < self.hold_r else rr
            if now < self.hold_l:
                tl = self.pl
            elif app.mouse_var.get() and now - app.last_mouse < 1.5 and self.state != "sleep":
                tl = (MOUSE_C[0] + app.moff[0] + 1, MOUSE_C[1] + app.moff[1] * 0.6 - 3)
            else:
                tl = rl
        f = 0.55
        self.pl = [self.pl[0] + (tl[0] - self.pl[0]) * f, self.pl[1] + (tl[1] - self.pl[1]) * f]
        self.pr = [self.pr[0] + (tr[0] - self.pr[0]) * f, self.pr[1] + (tr[1] - self.pr[1]) * f]

    def scene(self):
        app = self.app
        now = time.time()
        s = self.state
        breath = sway = 0
        z = None
        dy = 0
        fx = 0
        if s == "idle":
            breath = [0, 1, 2, 1][(self.tick // 10) % 4]
            sway = [0, 2, 0, -2][(self.tick // 10) % 4]
            eyes = "blink" if self.tick % 100 < 4 else "open"
        elif s == "work":
            eyes = "focus"
            if app.last_mouse > app.last_key:
                fx = -3     # マウスのほうを見る
        elif s == "sleep":
            breath = [0, 1, 2, 1][(self.tick // 16) % 4]
            z = (self.tick // 16) % 4
            eyes = "sleep"
        elif s == "happy":
            dy = -round(14 * math.sin(math.pi * (24 - self.timer) / 24))
            eyes = "happy"
        elif s == "drag":
            eyes = "squint"
            sway = [0, 2, 0, -2][(self.tick // 4) % 4]
        else:
            eyes = "wide"

        lp = self.key_l is not None and now < self.hold_l - 0.3 or (
            self.key_l in app.down_idx and now < self.hold_l)
        rp = self.key_r is not None and now < self.hold_r - 0.3 or (
            self.key_r in app.down_idx and now < self.hold_r)
        on_mouse = abs(self.pl[0] - MOUSE_C[0]) < 14
        if on_mouse and (app.lb or app.rb):
            lp = True
        return {
            "eyes": eyes, "fx": fx, "breath": breath, "sway": sway, "z": z, "dy": dy,
            "pl": (round(self.pl[0] * 2), round(self.pl[1] * 2)),
            "pr": (round(self.pr[0] * 2), round(self.pr[1] * 2)),
            "lp": bool(lp), "rp": bool(rp),
            "pressed": app.highlight,
            "moff": (round(app.moff[0]), round(app.moff[1])),
            "lb": app.lb, "rb": app.rb,
            "flap": (self.tick // (5 if s == "sleep" else 3)) % 8 if is_person() else 0,
            "edit": app.edit_var.get(), "held": self.held[0] if self.held else None,
            "ver": app.layout_ver,
        }

    def render(self):
        sc = self.scene()
        key = tuple(sorted((k, v if not isinstance(v, (set, frozenset, dict)) else
                            (id(v) if isinstance(v, dict) else tuple(sorted(v))))
                           for k, v in sc.items()))
        if key != self.shown:
            self.photo = ImageTk.PhotoImage(self.app.art.compose(sc))
            self.label.config(image=self.photo)
            self.shown = key
        pos = (int(self.x), int(self.y))
        if pos != self.pos:
            self.win.geometry(f"{self.W}x{self.H}+{pos[0]}+{pos[1]}")
            self.pos = pos

    def close(self):
        self.win.destroy()
        if self in self.app.pets:
            self.app.pets.remove(self)
        if not self.app.pets:
            self.app.quit()
            return
        self.app.save_chars()


class App:
    def __init__(self, n=1):
        set_dpi_aware()
        self.root = tk.Tk()
        self.root.withdraw()
        self.cfg = load_app_settings()
        HAND.update(self.cfg.get("hand") or {})
        self.dpi = max(1.0, get_dpi_scale())
        self.art = Art(self.dpi * self.cfg["size"] / 100)
        self.workarea = get_workarea(self.root)
        self.typing_var = tk.BooleanVar(value=self.cfg["typing"])
        self.mouse_var = tk.BooleanVar(value=self.cfg["mouse"])
        self.typing_var.trace_add("write", lambda *a: self.set_cfg("typing", self.typing_var.get()))
        self.mouse_var.trace_add("write", lambda *a: self.set_cfg("mouse", self.mouse_var.get()))
        self.settings = None
        self.last_key = self.last_mouse = 0.0
        self.prev_down = set()
        self.down_idx = set()
        self.key_time = {}
        self.new_presses = []
        self.highlight = frozenset()
        self.cursor = cursor_pos()
        self.moff = [0.0, 0.0]
        self.lb = self.rb = False
        self.edit_var = tk.BooleanVar(value=False)
        self.theme_var = tk.StringVar(value=self.art.theme)
        self.layout_dirty = False
        self.layout_ver = 0
        self.pets = []
        chars = [c for c in (self.cfg.get("chars") or []) if c in CHAR_NAMES] or ["person"]
        chars += ["person"] * (n - len(chars))
        for c in chars:
            self.add_pet(c, save=False)
        if self.cfg["pos"] and self.pets:              # 前に置いていた場所から始める
            p = self.pets[0]
            sx, sy = self.cfg["pos"][0], self.cfg["pos"][1]
            l, t, r, b = monitor_workarea(sx + p.W / 2, sy + p.H / 2, self.workarea)   # その場所のモニター
            p.x, p.y = float(clamp(sx, l, max(l, r - p.W))), float(sy)
            p.y, p.vx, p.state = p.ground, 0.0, "idle"
        self.loop_count = 0
        self.root.after(33, self.loop)

    @property
    def last_input(self):
        return max(self.last_key, self.last_mouse)

    def add_pet(self, char="person", save=True):
        self.pets.append(Pet(self, char))
        if save:
            self.save_chars()
        if self.settings and self.settings.win.winfo_exists():
            self.settings.fill_chars()

    def save_chars(self):
        self.set_cfg("chars", [p.char for p in self.pets])

    def set_pet_char(self, pet, char):
        """このペットのキャラを変える"""
        global CURRENT_CHAR
        pet.char = CURRENT_CHAR = char
        pet.char_var.set(char)
        pet.pl, pet.pr = list(rest_pos()[0]), list(rest_pos()[1])
        pet.shown = None
        self.save_chars()
        if self.settings and self.settings.win.winfo_exists():
            self.settings.fill_chars()

    # ---- 設定 ----
    def set_cfg(self, key, value):
        self.cfg[key] = value
        save_app_settings(self.cfg)

    def open_settings(self):
        if self.settings and self.settings.win.winfo_exists():
            self.settings.win.deiconify()
            self.settings.win.lift()
            return
        self.settings = SettingsWindow(self)

    def set_topmost(self, on):
        self.set_cfg("topmost", bool(on))
        for p in self.pets:
            p.win.attributes("-topmost", bool(on))

    def set_size(self, pct):
        """大きさを変える（ペットをつくりなおす）"""
        pct = int(clamp(pct, 50, 200))
        if pct == self.cfg["size"]:
            return
        self.set_cfg("size", pct)
        old = [(p.x + p.W / 2, p.y + p.H) for p in self.pets]
        chars = [p.char for p in self.pets]
        for p in list(self.pets):
            p.win.destroy()
        self.pets = []
        if self.art in ART_INSTANCES:
            ART_INSTANCES.remove(self.art)
        theme, layout = self.art.theme, self.art.layout
        self.art = Art(self.dpi * pct / 100)
        self.art.theme, self.art.layout = theme, layout
        self.art.rebuild()
        for i, o in enumerate(old or [None]):
            self.add_pet(chars[i] if i < len(chars) else "person", save=False)
            p = self.pets[-1]
            if o is not None:
                cxp, bottom = o
                l, t, r, b = monitor_workarea(cxp, bottom - 2, self.workarea)
                p.x, p.y = float(clamp(cxp - p.W / 2, l, max(l, r - p.W))), float(bottom - p.H)
                p.y, p.vx, p.state = p.ground, 0.0, "idle"

    # ---- 自作キャラ ----
    def open_chara_editor(self):
        if getattr(self, "chara_ed", None) and self.chara_ed.win.winfo_exists():
            self.chara_ed.win.lift()
            return
        self.chara_ed = CharaEditor(self)

    def set_hand(self, key, value):
        global CURRENT_CHAR
        HAND[key] = value
        self.set_cfg("hand", dict(HAND))
        for p in self.pets:
            CURRENT_CHAR = p.char
            p.pl, p.pr = list(rest_pos()[0]), list(rest_pos()[1])
        self.redraw_all()

    def set_character(self, kind):
        """1人目のキャラを変える"""
        if self.pets:
            self.set_pet_char(self.pets[0], kind)

    # ---- もようがえ ----
    def edit_changed(self):
        self.layout_dirty = True

    def add_item(self, kind):
        it = Art.default_item(kind)
        if any(i["type"] == kind and abs(i["x"] - it["x"]) < 2 and abs(i["y"] - it["y"]) < 2
               for i in self.art.layout):
            it["x"], it["y"] = 232.0, 100.0          # 同じ場所にもうあれば、机の右のあいているところへ
        self.art.layout.append(it)
        save_layout(self.art)
        self.edit_var.set(True)
        self.layout_dirty = True

    def remove_item(self, it):
        if it in self.art.layout:
            self.art.layout.remove(it)
            save_layout(self.art)
            self.layout_dirty = True

    def set_theme(self, theme=None):
        """机のテーマを変える（小物もそのテーマのはじめの配置になる）"""
        theme = theme or self.theme_var.get()
        self.art.theme = theme
        self.art.layout[:] = Art.default_layout(theme)
        save_layout(self.art)
        self.layout_dirty = True

    def reset_layout(self):
        self.art.layout[:] = Art.default_layout(self.art.theme)
        save_layout(self.art)
        self.layout_dirty = True

    def redraw_all(self):
        self.layout_ver += 1
        for p in self.pets:
            p.shown = None

    # ---- ねこのみため ----
    def design_changed(self):
        global CUSTOM
        CUSTOM = jisaku.load_chara()
        for a in ART_INSTANCES:
            a._body.clear()
            a._custom = None
        self.layout_dirty = True                 # いすの向きもキャラに合わせてかきなおす
        self.redraw_all()
        global CURRENT_CHAR
        for p in self.pets:
            CURRENT_CHAR = p.char
            p.pl, p.pr = list(rest_pos()[0]), list(rest_pos()[1])

    def poll(self):
        now = time.time()
        self.new_presses = []
        # キーボード：押されている位置だけを見る（記録はしない）
        if self.typing_var.get():
            down = {vk for vk in WATCH_VKS if is_down(vk)}
            for vk in down - self.prev_down:
                idx = VK2IDX[vk]
                self.key_time[idx] = now
                self.new_presses.append(idx)
                self.last_key = now
            self.prev_down = down
            self.down_idx = {VK2IDX[v] for v in down}
            self.highlight = frozenset(self.down_idx | {i for i, t in self.key_time.items()
                                                        if now - t < 0.12})
        else:
            self.prev_down, self.down_idx, self.highlight = set(), set(), frozenset()

        # マウス
        cur = cursor_pos()
        tx = ty = 0.0
        if self.mouse_var.get():
            grabbing = any(p.press for p in self.pets)
            if cur and self.cursor and not grabbing:
                dx, dy = cur[0] - self.cursor[0], cur[1] - self.cursor[1]
                if abs(dx) + abs(dy) > 2:
                    self.last_mouse = now
                    # 向かい合っているので、もちまるから見て同じ方向＝画面上では上下左右が逆
                    tx, ty = clamp(-dx / 3, -10, 10), clamp(-dy / 4, -5, 5)
            self.lb, self.rb = is_down(0x01), is_down(0x02)
            if (self.lb or self.rb) and not grabbing:
                self.last_mouse = now
        else:
            self.lb = self.rb = False
        self.cursor = cur
        self.moff = [self.moff[0] * 0.5 + tx * 0.5, self.moff[1] * 0.5 + ty * 0.5]

    def loop(self):
        self.loop_count += 1
        if self.loop_count % 60 == 0:
            self.workarea = get_workarea(self.root)
        self.poll()
        if self.layout_dirty:
            self.layout_dirty = False
            self.art.rebuild()
            self.redraw_all()
        for p in list(self.pets):
            p.update()
        if self.loop_count % 150 == 0 and self.pets:      # 置いた場所をおぼえておく
            pos = [int(self.pets[0].x), int(self.pets[0].y)]
            if pos != self.cfg["pos"]:
                self.set_cfg("pos", pos)
        self.root.after(33, self.loop)

    def quit(self):
        if self.pets:
            self.set_cfg("pos", [int(self.pets[0].x), int(self.pets[0].y)])
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ============================================================
#  設定画面（ダブルクリック／右クリック →「設定…」）
# ============================================================
class SettingsWindow:
    def __init__(self, app):
        self.app = app
        w = self.win = tk.Toplevel(app.root)
        w.title("デスクトップペットの設定")
        w.attributes("-topmost", True)
        w.resizable(False, False)
        nb = ttk.Notebook(w)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        pad = dict(padx=8, pady=4)

        # ---- 表示 ----
        t = ttk.Frame(nb)
        nb.add(t, text="表示")
        ttk.Label(t, text="大きさ").grid(row=0, column=0, sticky="w", **pad)
        self.size = tk.IntVar(value=app.cfg["size"])
        self.size_lbl = ttk.Label(t, width=6)
        sc = ttk.Scale(t, from_=50, to=200, orient="horizontal", length=200, variable=self.size,
                       command=lambda v: self.size_lbl.config(text=f"{int(float(v))}%"))
        sc.grid(row=0, column=1, **pad)
        sc.bind("<ButtonRelease-1>", lambda e: app.set_size(self.size.get()))
        self.size_lbl.grid(row=0, column=2, sticky="w")
        self.size_lbl.config(text=f"{app.cfg['size']}%")
        self.topmost = tk.BooleanVar(value=app.cfg["topmost"])
        ttk.Checkbutton(t, text="いつもほかのウィンドウより手前に表示", variable=self.topmost,
                        command=lambda: app.set_topmost(self.topmost.get())).grid(row=1, column=0, columnspan=3, sticky="w", **pad)
        self.locked = tk.BooleanVar(value=app.cfg["locked"])
        ttk.Checkbutton(t, text="その場に固定する（ドラッグで動かない）", variable=self.locked,
                        command=lambda: app.set_cfg("locked", self.locked.get())).grid(row=2, column=0, columnspan=3, sticky="w", **pad)
        self.auto = tk.BooleanVar(value=autostart_on())
        ttk.Checkbutton(t, text="パソコンを起動したら、自動でペットも起動する", variable=self.auto,
                        command=lambda: set_autostart(self.auto.get())).grid(row=3, column=0, columnspan=3, sticky="w", **pad)

        # ---- 動き ----
        t = ttk.Frame(nb)
        nb.add(t, text="動き")
        ttk.Checkbutton(t, text="キーボードに反応して、同じ場所のキーをおす", variable=app.typing_var).grid(
            row=0, column=0, columnspan=3, sticky="w", **pad)
        ttk.Checkbutton(t, text="マウスに反応して、マウスを動かす", variable=app.mouse_var).grid(
            row=1, column=0, columnspan=3, sticky="w", **pad)
        ttk.Label(t, text="なにもしないと寝るまで").grid(row=2, column=0, sticky="w", **pad)
        self.sleep = tk.IntVar(value=app.cfg["sleep_min"])
        sp = ttk.Spinbox(t, from_=1, to=60, width=5, textvariable=self.sleep,
                         command=lambda: app.set_cfg("sleep_min", int(self.sleep.get())))
        sp.grid(row=2, column=1, sticky="w")
        sp.bind("<FocusOut>", lambda e: self._sleep_typed())
        sp.bind("<Return>", lambda e: self._sleep_typed())
        ttk.Label(t, text="分くらい").grid(row=2, column=2, sticky="w")
        bar = ttk.Frame(t)
        bar.grid(row=3, column=0, columnspan=3, sticky="w", **pad)
        ttk.Button(bar, text="いま寝かせる", command=lambda: [p.go_sleep() for p in app.pets]).pack(side="left", padx=2)
        ttk.Button(bar, text="ジャンプさせる",
                   command=lambda: [p.set_state("happy", 24) for p in app.pets]).pack(side="left", padx=2)

        # ---- 机 ----
        t = ttk.Frame(nb)
        nb.add(t, text="机")
        ttk.Label(t, text="机のテーマ").grid(row=0, column=0, sticky="w", **pad)
        for j, (key, th) in enumerate(DESK_THEMES.items()):
            ttk.Radiobutton(t, text=th["name"], value=key, variable=app.theme_var,
                            command=app.set_theme).grid(row=0, column=1 + j, sticky="w")
        ttk.Checkbutton(t, text="もようがえ（ペットの上で小物をドラッグして動かす）", variable=app.edit_var,
                        command=app.edit_changed).grid(row=1, column=0, columnspan=4, sticky="w", **pad)
        ttk.Label(t, text="小物・キャラを出す").grid(row=2, column=0, sticky="w", **pad)
        self.pick = ttk.Combobox(t, state="readonly", width=22, postcommand=self.fill_pick)
        self.fill_pick()
        self.pick.current(0)
        self.pick.grid(row=2, column=1, columnspan=2, sticky="w")
        ttk.Button(t, text="出す", command=lambda: app.add_item(self.kinds[self.pick.current()])).grid(
            row=2, column=3, sticky="w", padx=4)
        ttk.Label(t, text="しまうときは、もようがえ中に小物を右クリック", foreground="#666").grid(
            row=3, column=0, columnspan=4, sticky="w", **pad)
        ttk.Button(t, text="配置をはじめにもどす", command=app.reset_layout).grid(row=4, column=0, sticky="w", **pad)

        # ---- キャラ ----
        t = ttk.Frame(nb)
        nb.add(t, text="キャラ")
        self.chars_box = ttk.LabelFrame(t, text="ペットとキャラ")
        self.chars_box.grid(row=0, column=0, columnspan=4, sticky="we", **pad)
        self.fill_chars()
        bar = ttk.Frame(t)
        bar.grid(row=1, column=0, columnspan=4, sticky="w", **pad)
        ttk.Label(bar, text="もう1人よぶ：").pack(side="left")
        for key, label in CHAR_NAMES.items():
            ttk.Button(bar, text=label, command=lambda k=key: app.add_pet(k)).pack(side="left", padx=2)
        ttk.Button(t, text="自作キャラを作る…", command=app.open_chara_editor).grid(row=2, column=0, sticky="w", **pad)
        hf = ttk.LabelFrame(t, text="手の位置")
        hf.grid(row=3, column=0, columnspan=4, sticky="we", **pad)
        self.hand = {}
        for i, (key, label) in enumerate((("sh_x", "肩のはば（広く →）"), ("sh_y", "肩の高さ（下へ →）"),
                                          ("rest_x", "休めている手のはば（広く →）"), ("rest_y", "休めている手の高さ（下へ →）"))):
            ttk.Label(hf, text=label).grid(row=i, column=0, sticky="w", padx=6, pady=2)
            v = tk.DoubleVar(value=HAND[key])
            lbl = ttk.Label(hf, width=4, text=str(int(HAND[key])))
            ttk.Scale(hf, from_=-20, to=20, orient="horizontal", length=170, variable=v,
                      command=lambda val, k=key, l=lbl: (l.config(text=str(round(float(val)))),
                                                         app.set_hand(k, round(float(val))))).grid(row=i, column=1)
            lbl.grid(row=i, column=2, sticky="w")
            self.hand[key] = v
        ttk.Button(hf, text="手の位置をもとにもどす", command=self.reset_hand).grid(row=4, column=0, sticky="w", padx=6, pady=4)


        bot = ttk.Frame(w)
        bot.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(bot, text="ペットをぜんぶ終了", command=app.quit).pack(side="left")
        ttk.Button(bot, text="とじる", command=w.destroy).pack(side="right")

    GROUPS = {"chara": "キャラ", "wa": "和風", "lab": "研究室"}

    def fill_chars(self):
        """ペットごとに、キャラをえらぶ行"""
        for w_ in self.chars_box.winfo_children():
            w_.destroy()
        self.char_vars = []
        for i, p in enumerate(self.app.pets):
            ttk.Label(self.chars_box, text=f"{i + 1}人目").grid(row=i, column=0, sticky="w", padx=6, pady=2)
            v = tk.StringVar(value=p.char)
            for j, (key, label) in enumerate(CHAR_NAMES.items()):
                ttk.Radiobutton(self.chars_box, text=label, value=key, variable=v,
                                command=lambda p=p, v=v: self.app.set_pet_char(p, v.get())).grid(row=i, column=1 + j, sticky="w")
            ttk.Button(self.chars_box, text="しまう", width=6,
                       command=lambda p=p: (p.close(), self.fill_chars())).grid(row=i, column=4, padx=6)
            self.char_vars.append(v)

    def fill_pick(self):
        self.kinds = [k for k in Art.ITEM_DEFS]
        self.pick.config(values=[f"{Art.ITEM_DEFS[k][0]}（{self.GROUPS[Art.ITEM_DEFS[k][5]]}）" for k in self.kinds])
        if self.pick.current() < 0 and self.kinds:
            self.pick.current(0)

    def reset_hand(self):
        for key, v in self.hand.items():
            v.set(0)
            self.app.set_hand(key, 0)

    def _sleep_typed(self):
        try:
            v = int(clamp(int(self.sleep.get()), 1, 60))
        except (ValueError, tk.TclError):
            v = self.app.cfg["sleep_min"]
        self.sleep.set(v)
        self.app.set_cfg("sleep_min", v)


# ============================================================
#  自作キャラを作る画面
# ============================================================
class CharaEditor:
    CANVAS = 340

    def __init__(self, app):
        self.app = app
        self.c = jisaku.load_chara()
        w = self.win = tk.Toplevel(app.root)
        w.title("自作キャラを作る")
        w.attributes("-topmost", True)
        w.resizable(False, False)
        pad = dict(padx=6, pady=2)

        left = ttk.Frame(w)
        left.grid(row=0, column=0, sticky="n", padx=8, pady=8)
        ttk.Label(left, text="① パーツの画像をえらぶ", font=("", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
        self.part_lbl = {}
        for i, (part, label, need) in enumerate(jisaku.PARTS):
            ttk.Label(left, text=label.split("…")[0].strip() + ("（必須）" if need else "")).grid(
                row=1 + i, column=0, sticky="w", **pad)
            ttk.Button(left, text="えらぶ…", command=lambda p=part: self.pick_part(p)).grid(row=1 + i, column=1, **pad)
            lb = ttk.Label(left, width=14, foreground="#555")
            lb.grid(row=1 + i, column=2, sticky="w")
            self.part_lbl[part] = lb
        ttk.Label(left, text="※ ゆれるパーツと「目をとじた頭」は、頭と同じ大きさの画像に、\n"
                             "　 同じ位置でかいてください（重ねて使います）", foreground="#777").grid(
            row=7, column=0, columnspan=3, sticky="w", **pad)

        ttk.Label(left, text="② 点を決める（えらんでから、右の絵をクリック）", font=("", 10, "bold")).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(10, 2))
        self.point = tk.StringVar(value=jisaku.POINTS[0][0])
        self.point_lbl = {}
        for i, (key, part, label) in enumerate(jisaku.POINTS):
            ttk.Radiobutton(left, text=label, value=key, variable=self.point, command=self.show).grid(
                row=9 + i, column=0, columnspan=2, sticky="w", **pad)
            lb = ttk.Label(left, width=8)
            lb.grid(row=9 + i, column=2, sticky="w")
            self.point_lbl[key] = lb

        ttk.Label(left, text="③ 大きさ・色", font=("", 10, "bold")).grid(row=15, column=0, columnspan=3, sticky="w", pady=(10, 2))
        self.sliders = {}
        for i, (key, label, lo, hi) in enumerate((("scale", "大きさ", 0.03, 0.4), ("neck_y", "首の高さ（下へ）", 30, 75),
                                                  ("swing", "ゆれる角度", 0, 90))):
            ttk.Label(left, text=label).grid(row=16 + i, column=0, sticky="w", **pad)
            v = tk.DoubleVar(value=self.c[key])
            sc = ttk.Scale(left, from_=lo, to=hi, orient="horizontal", length=160, variable=v)
            sc.grid(row=16 + i, column=1, columnspan=2, sticky="w")
            sc.bind("<ButtonRelease-1>", lambda e, k=key: self.set_value(k, self.sliders[k].get()))
            self.sliders[key] = v
        cbar = ttk.Frame(left)
        cbar.grid(row=19, column=0, columnspan=3, sticky="w", **pad)
        self.swatch = {}
        for key, label in (("arm", "腕（そで）"), ("skin", "手・はだ"), ("arm_line", "ふちの線")):
            b = tk.Button(cbar, text=label, width=9, relief="groove", command=lambda k=key: self.pick_color(k))
            b.pack(side="left", padx=2)
            self.swatch[key] = b
        self.behind = tk.BooleanVar(value=bool(self.c.get("behind")))
        ttk.Checkbutton(left, text="横向きのキャラ（マウスを持つ手を体のうしろに）", variable=self.behind,
                        command=lambda: self.set_value("behind", self.behind.get())).grid(
            row=20, column=0, columnspan=3, sticky="w", **pad)

        right = ttk.Frame(w)
        right.grid(row=0, column=1, sticky="n", padx=8, pady=8)
        self.cv = tk.Canvas(right, width=self.CANVAS, height=self.CANVAS, bg="#e8ecf2", highlightthickness=1,
                            highlightbackground="#aab", cursor="crosshair")
        self.cv.pack()
        self.cv.bind("<Button-1>", self.click)
        self.cv_info = ttk.Label(right, foreground="#555")
        self.cv_info.pack(anchor="w", pady=4)
        self.status = ttk.Label(right, foreground="#b03030", wraplength=self.CANVAS, justify="left")
        self.status.pack(anchor="w", pady=4)
        bar = ttk.Frame(right)
        bar.pack(fill="x", pady=6)
        ttk.Button(bar, text="このキャラを使う", command=self.use).pack(side="left")
        ttk.Button(bar, text="とじる", command=w.destroy).pack(side="right")
        self._photo = None
        self.refresh()

    # ---- 表示 ----
    def refresh(self):
        for part, lb in self.part_lbl.items():
            lb.config(text=self.c["parts"].get(part) and "✓ えらんだ" or "（なし）")
        for key, lb in self.point_lbl.items():
            lb.config(text="✓" if key in self.c["points"] else "まだ", foreground="#2a7" if key in self.c["points"] else "#c33")
        for key, b in self.swatch.items():
            col = "#%02x%02x%02x" % tuple(self.c[key])
            b.config(bg=col, activebackground=col, fg="white" if sum(self.c[key]) < 380 else "black")
        miss = jisaku.missing(self.c)
        self.status.config(text=("まだ足りないもの：" + "、".join(miss)) if miss else "準備OK！「このキャラを使う」で動きます",
                           foreground="#b03030" if miss else "#2a7a3a")
        self.show()

    def show(self):
        key = self.point.get()
        part = next(p for k, p, l in jisaku.POINTS if k == key)
        self.cv.delete("all")
        path = jisaku.part_path(self.c, part)
        if not path:
            self.cv.create_text(self.CANVAS / 2, self.CANVAS / 2, text="この点を決めるには、\n先にパーツの画像をえらんでください",
                                fill="#667", justify="center")
            self.cv_info.config(text="")
            return
        im = jisaku.cutout(path)
        f = self.CANVAS / max(im.width, im.height)
        self.f = f
        bg = Image.new("RGBA", (int(im.width * f), int(im.height * f)), (232, 236, 242, 255))
        bg.alpha_composite(im.resize(bg.size, LANCZOS))
        self._photo = ImageTk.PhotoImage(bg)
        self.cv.create_image(0, 0, anchor="nw", image=self._photo)
        for k, p, label in jisaku.POINTS:
            if p == part and k in self.c["points"]:
                x, y = self.c["points"][k][0] * f, self.c["points"][k][1] * f
                col = "#e03050" if k == key else "#3070d0"
                self.cv.create_oval(x - 6, y - 6, x + 6, y + 6, outline=col, width=3)
                self.cv.create_line(x - 10, y, x + 10, y, fill=col)
                self.cv.create_line(x, y - 10, x, y + 10, fill=col)
        self.cv_info.config(text="クリックで「" + next(l for k, p, l in jisaku.POINTS if k == key) + "」を決める")

    # ---- 操作 ----
    def pick_part(self, part):
        path = filedialog.askopenfilename(parent=self.win, title="画像をえらぶ",
                                          filetypes=[("画像", "*.png *.webp *.jpg *.jpeg *.gif"), ("すべて", "*.*")])
        if not path:
            return
        try:
            jisaku.cutout(path)
        except Exception as ex:
            messagebox.showerror("自作キャラ", f"画像を読めませんでした：{ex}", parent=self.win)
            return
        jisaku.set_part(self.c, part, path)
        for k, p, l in jisaku.POINTS:              # その画像の上で決める点があれば、そこを開く
            if p == part and k not in self.c["points"]:
                self.point.set(k)
                break
        self.changed()

    def click(self, e):
        key = self.point.get()
        part = next(p for k, p, l in jisaku.POINTS if k == key)
        if not jisaku.part_path(self.c, part):
            return
        self.c["points"][key] = [int(e.x / self.f), int(e.y / self.f)]
        keys = [k for k, p, l in jisaku.POINTS]
        for k in keys[keys.index(key) + 1:] + keys[:keys.index(key)]:   # つぎの「まだ」の点へ
            p = next(pp for kk, pp, l in jisaku.POINTS if kk == k)
            if k not in self.c["points"] and jisaku.part_path(self.c, p):
                self.point.set(k)
                break
        self.changed()

    def set_value(self, key, value):
        self.c[key] = round(value, 3) if isinstance(value, float) else value
        self.changed()

    def pick_color(self, key):
        res = colorchooser.askcolor(color="#%02x%02x%02x" % tuple(self.c[key]), parent=self.win, title="色をえらぶ")
        if res and res[0]:
            self.c[key] = [int(v) for v in res[0]]
            self.changed()

    def changed(self):
        jisaku.save_chara(self.c)
        self.refresh()
        self.app.design_changed()

    def use(self):
        miss = jisaku.missing(self.c)
        if miss:
            messagebox.showinfo("自作キャラ", "まだ足りないものがあります：\n" + "\n".join(miss), parent=self.win)
            return
        jisaku.save_chara(self.c)
        self.app.set_character("custom")



def preview(path):
    art = Art(float(os.environ.get("PET_PREVIEW_SCALE", "1.0")))
    base = {"eyes": "focus", "fx": 0, "breath": 0, "sway": 0, "z": None, "dy": 0,
            "pl": tuple(round(v * 2) for v in rest_pos()[0]),
            "pr": tuple(round(v * 2) for v in rest_pos()[1]),
            "lp": False, "rp": False, "pressed": frozenset(), "moff": (0, 0), "lb": False, "rb": False}
    q = VK2IDX[ord("Q")]
    ent = VK2IDX[0x0D]
    sp = VK2IDX[0x20]
    scenes = [
        dict(base, eyes="open"),
        dict(base, pr=tuple(round(v * 2) for v in key_center(q)), rp=True, pressed=frozenset([q])),
        dict(base, pl=tuple(round(v * 2) for v in key_center(ent)), lp=True, pressed=frozenset([ent])),
        dict(base, fx=-3, pl=((MOUSE_C[0] - 8) * 2, (MOUSE_C[1] - 3) * 2), moff=(-9, 0), lb=True, lp=True),
        dict(base, pr=tuple(round(v * 2) for v in key_center(sp)), rp=True, pressed=frozenset([sp])),
        dict(base, eyes="sleep", z=1, breath=2),
    ]
    sheet = Image.new("RGB", (art.W * 3, art.H * 2), (220, 230, 240))
    for i, sc in enumerate(scenes):
        im = art.compose(sc)
        px = im.load()
        for yy in range(im.height):
            for xx in range(im.width):
                if px[xx, yy] == KEY:
                    px[xx, yy] = (220, 230, 240)
        sheet.paste(im, ((i % 3) * art.W, (i // 3) * art.H))
    sheet.save(path)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        preview(sys.argv[2])
    else:
        n = 1
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            n = max(1, min(10, int(sys.argv[1])))
        app = App(n)
        if os.environ.get("PET_AUTOQUIT"):
            app.root.after(int(os.environ["PET_AUTOQUIT"]), app.quit)
        app.run()
