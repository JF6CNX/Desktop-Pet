"""
ひと（hito.png の絵）を、Live2D みたいにパーツごとに動かす

  hito.png をパーツに切り分けて使う：
    - 触角（1本）     … つけねを中心に、上と下をいったりきたり
    - 頭（髪・顔・耳）   … 首を中心にかしげる／うなずく、上下にゆれる、まばたき
    - 体                 … 息にあわせて少しのびちぢみ
  腕と、机の下の足は desktop_pet.py 側でかく（キーを打つ手を動かすため）。

座標はすべて hito.png の上のピクセル（800×800）。
"""
import math
import os

from PIL import Image, ImageChops, ImageDraw

import paths
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = paths.res("hito.png")

SF = 0.16                   # 絵の 1px → ペットの絵の何 px か（大きさ）
HEAD_SCALE = 1.2            # 頭だけの大きさ（2.5頭身にするため、体より大きめ）
BODY_WIDE = 2.0             # 体の横はばを何倍にするか（ふとさ）
NECK = (400, 480)         # 首（頭がまわる中心）
KNOT = (194, 318)         # 触角のつけね（ここを中心にゆれる）
ANTENNA = [(48, 300), (100, 287), (160, 285), (192, 298), (198, 310), (198, 326), (178, 340), (140, 334), (55, 326)]
ANTENNA_LOW = [(198, 322), (198, 392), (186, 402), (150, 432), (100, 458), (66, 452), (58, 424), (118, 362), (166, 327), (186, 318)]  # 絵の2本目（動きの表現なので消す）
SWING = 50                # 触角がゆれる角度（上の位置から下の位置まで）
BODY_CX = 425             # 体のまんなか（ここを中心に太くする）
EYE = (452, 350)          # 目の点
CUT_Y = 610               # これより下（ひざ・足）は机にかくれるので使わない

SKIN = (238, 223, 209)
LINE = (72, 72, 74)       # ふちの線
SHIRT = (34, 34, 40)      # 黒いTシャツ
PANTS = (112, 112, 114)   # ズボン
SHOES = (36, 36, 40)      # くつ

LANCZOS = getattr(Image, "Resampling", Image).LANCZOS
BICUBIC = getattr(Image, "Resampling", Image).BICUBIC


def _load():
    im = Image.open(SRC).convert("RGBA")
    # 白い背景をすきとおらせる（まわりからぬりつぶし）
    w, h = im.size
    rgb = im.convert("RGB")
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        ImageDraw.floodfill(rgb, corner, (255, 0, 255), thresh=40)
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, (255, 0, 255)))
    mask = diff.convert("L").point(lambda v: 255 if v > 0 else 0)
    im.putalpha(mask)
    # 絵の中の「ゆれている線」は、本当にゆらすのでけす
    ImageDraw.Draw(im).rectangle([48, 333, 100, 412], fill=(0, 0, 0, 0))
    return im


def _poly_mask(size, pts):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


class Hito:
    def __init__(self, k):
        """k: ペットの絵の 1px が、かく画像の何 px か"""
        self.k = k
        src = _load()
        size = src.size
        up_m = _poly_mask(size, ANTENNA)                                             # 触角（1本）
        low_m = _poly_mask(size, ANTENNA_LOW)
        low_m = ImageChops.lighter(low_m, _poly_mask(size, [(52, 327), (82, 327), (82, 340), (52, 340)]))  # ゆれ線ののこり
        head_m = _poly_mask(size, [(0, 0), (800, 0), (800, 520), (506, 520), (506, 480), (0, 480)])
        head_m = ImageChops.subtract(ImageChops.subtract(head_m, up_m), low_m)
        body_m = _poly_mask(size, [(0, 480), (506, 480), (506, 520), (800, 520), (800, CUT_Y), (336, CUT_Y), (336, 570), (0, 570)])  # 左下のひざ・くつは使わない

        def part(m):
            p = Image.new("RGBA", size, (0, 0, 0, 0))
            p.paste(src, (0, 0), ImageChops.multiply(src.getchannel("A"), m))
            return p

        self.s = s = SF * k
        tw, th = max(1, int(size[0] * s)), max(1, int(size[1] * s))
        self.hs = hs = s * HEAD_SCALE
        hw_, hh_ = max(1, int(size[0] * hs)), max(1, int(size[1] * hs))
        self.antenna = part(up_m).resize((hw_, hh_), LANCZOS)
        body = part(body_m)
        # 絵の体の中にある「ひざの上の腕と手」は、腕を別にかくのでいらない → シャツの黒でぬる
        bd = ImageDraw.Draw(body)
        bd.polygon([(364, 498), (418, 490), (470, 522), (486, 562), (491, 612), (352, 612), (352, 586), (357, 540)],
                   fill=SHIRT + (255,))
        bd.line([(352, 530), (344, 586), (344, 612)], fill=LINE + (255,), width=11)       # 左のふちの線
        self.body = body.resize((int(tw * BODY_WIDE), th), LANCZOS)
        head = part(head_m)
        # 触角を切りとったところの、顔の左のふちの線をかきなおす
        ImageDraw.Draw(head).line([(195, 306), (194, 380), (192, 446)], fill=LINE + (255,), width=10)
        self.heads = {}
        for kind in ("open", "closed", "wide"):
            h = head.copy()
            d = ImageDraw.Draw(h)
            ex, ey = EYE
            d.ellipse([ex - 10, ey - 10, ex + 10, ey + 10], fill=SKIN + (255,))   # 目をいったん消す
            if kind == "open":
                d.ellipse([ex - 6, ey - 6, ex + 6, ey + 6], fill=(60, 58, 58, 255))
            elif kind == "wide":
                d.ellipse([ex - 8.5, ey - 8.5, ex + 8.5, ey + 8.5], fill=(60, 58, 58, 255))
            else:                                                                  # とじた目
                d.line([(ex - 9, ey + 1), (ex + 8, ey + 1)], fill=(60, 58, 58, 255), width=5)
            self.heads[kind] = h.resize((hw_, hh_), LANCZOS)
        self._cache = {}

    # ---- 動き ----
    @staticmethod
    def pose(eyes, fx, breath, sway):
        """表情（eyes）→ (目, 頭のかたむき[度, +で前にうなずく], 頭の上下, はちまきの角度)"""
        bob = (breath - 1) * 0.35
        flutter = sway * 4.0
        if eyes == "focus":           # キーボードを見る
            return "open", 1 + (-fx) * 0.3, bob, flutter
        if eyes == "sleep":
            return "closed", 9, bob, flutter * 0.5
        if eyes in ("blink",):
            return "closed", 0, bob, flutter
        if eyes == "happy":
            return "open", -3, bob, 12
        if eyes == "squint":          # つままれている
            return "closed", -7, bob, flutter * 2
        if eyes == "wide":            # おちている
            return "wide", -4, bob, -10
        return "open", 0, bob, flutter

    def render(self, art, im, cx, neck_y, eyes, fx, breath, sway, flap=0):
        """im（ペットの絵）に、首が (cx, neck_y) にくるように人をかく。flap: 触角のゆれの位相（0〜7）"""
        eye, ang, bob, flutter = self.pose(eyes, fx, breath, sway)
        amp = 0.3 if eyes == "sleep" else 1.0
        ph = 2 * math.pi * flap / 8
        a_ant = flutter * 0.5 + SWING * amp * (1 - math.cos(ph)) / 2   # 上の位置 ⇔ 下の位置 をいったりきたり
        s, k = self.s, self.k
        # 体：まっすぐ（左右対称）な黒いシャツの体。息を吸うと少し上へのびる
        lift = breath * 0.3 * k
        if art is not None:
            d = ImageDraw.Draw(im)
            self.lower_body(art, d, cx, neck_y)
            self.torso(art, d, cx, neck_y, breath * 0.3)
        # 頭：はちまきをゆらしてから、首を中心にかしげる
        head = self.heads[eye].copy()
        hs = self.hs
        knot = (KNOT[0] * hs, KNOT[1] * hs)
        head.alpha_composite(self.antenna.rotate(a_ant, resample=BICUBIC, center=knot))
        head = head.rotate(ang, resample=BICUBIC, center=(NECK[0] * hs, NECK[1] * hs))
        im.alpha_composite(head, (int(cx * k - NECK[0] * hs), int(neck_y * k - NECK[1] * hs - lift + bob * k)))

    def torso(self, art, d, cx, neck_y, up):
        tcx = cx + (BODY_CX - NECK[0]) * SF
        hw = 80 * SF * BODY_WIDE - 2
        yb = neck_y + (CUT_Y - NECK[1]) * SF
        art.rrect(d, (cx - 4, neck_y - 5 - up, cx + 4, neck_y + 4), 1.5, SKIN, ol=LINE, w=1.4)        # 首
        art.rrect(d, (tcx - hw, neck_y + 1 - up, tcx + hw, yb + 2), 9, SHIRT, ol=LINE, w=1.8)       # 体
        art.arc(d, cx, neck_y + 0.5 - up, 4.6, 20, 160, fill=LINE, w=1.2)                           # えりぐり

    def lower_body(self, art, d, cx, neck_y):
        """絵の体の下につづく、シャツのすそ・ズボン・足。
        ふだんは机にかくれていて、ジャンプしたときだけ見える"""
        tcx = cx + (BODY_CX - NECK[0]) * SF                  # 体のまんなか
        hw = 80 * SF * BODY_WIDE - 2                          # 体のはばの半分
        yb = neck_y + (CUT_Y - NECK[1]) * SF                  # 絵の体の下のはし
        # 足：こちら向きに座っている形。ひざが少し外にひらいて、すねは下へ、くつのつま先は外がわ。
        # 机の下（すき間）からひざから下が見える
        for side in (-1, 1):
            hip = (tcx + side * hw * 0.38, yb + 9)
            knee = (tcx + side * hw * 0.6, 120)              # 2.5頭身なので、足は短め
            ankle = (tcx + side * hw * 0.55, 131)
            art.line(d, [hip, knee, ankle], fill=LINE, w=11)
            art.line(d, [hip, knee, ankle], fill=PANTS, w=8.2)
            art.ell(d, ankle[0] + side * 2.5, ankle[1] + 2.4, 5.6, 3.2, SHOES, ol=LINE, w=1.4)
        art.rrect(d, (tcx - hw, yb + 1, tcx + hw, yb + 12), 5, PANTS, ol=LINE, w=1.6)   # ズボン
        art.rrect(d, (tcx - hw - 0.5, yb - 6, tcx + hw + 0.5, yb + 5), 4, SHIRT, ol=LINE, w=1.6)  # シャツのすそ

    def legs(self, art, d, cx):
        """机の下に見える足（ズボンとくつ。左を向いて座っている）"""
        for x0, x1 in ((cx - 6, cx - 12), (cx + 7, cx + 1)):
            art.line(d, [(x0, 128), (x1, 141)], fill=LINE, w=11)
            art.line(d, [(x0, 128), (x1, 141)], fill=PANTS, w=7.8)
            art.ell(d, x1 - 3, 143.5, 6.4, 3.4, SHOES, ol=LINE, w=1.4)


def arm_colors():
    return {"line": LINE, "sleeve": SHIRT, "skin": SKIN}
