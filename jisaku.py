"""
自作の画像を使う：小物・キャラの追加と、自作のメインキャラ（頭・体・手などのパーツ）

  custom/                 … 追加した画像（コピーしておく）
  custom/custom.json      … 追加した小物・キャラの一覧
  custom/chara/           … 自作メインキャラのパーツ画像
  custom/chara/chara.json … パーツの「点」（首のつけねなど）や大きさ

画像は PNG（背景すきとおり）がいちばんきれい。まっ白な背景なら自動でぬきます。
"""
import json
import os
import shutil
import time

from PIL import Image, ImageChops, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CDIR = os.path.join(HERE, "custom")
REG = os.path.join(CDIR, "custom.json")
CHARA_DIR = os.path.join(CDIR, "chara")
CHARA_JSON = os.path.join(CHARA_DIR, "chara.json")

LANCZOS = getattr(Image, "Resampling", Image).LANCZOS
BICUBIC = getattr(Image, "Resampling", Image).BICUBIC


# ============================================================
#  画像の読みこみ（白い背景をぬく）
# ============================================================
def cutout(path):
    """RGBA で読む。すきとおりのない画像は、まわりのまっ白をすきとおらせる"""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        if im.getchannel("A").getextrema()[0] < 250:
            return im
    rgb = im.convert("RGB")
    w, h = rgb.size
    for c in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if min(rgb.getpixel(c)) >= 225:
            ImageDraw.floodfill(rgb, c, (255, 0, 255), thresh=30)
    mask = ImageChops.difference(rgb, Image.new("RGB", rgb.size, (255, 0, 255))).convert("L").point(
        lambda v: 255 if v > 0 else 0)
    out = Image.open(path).convert("RGBA")
    out.putalpha(mask)
    return out


def _copy_in(src, folder, stem):
    os.makedirs(folder, exist_ok=True)
    ext = os.path.splitext(src)[1].lower() or ".png"
    dst = os.path.join(folder, stem + ext)
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    return os.path.basename(dst)


# ============================================================
#  小物・キャラ（机の上やうしろに置くもの）
# ============================================================
def load_items():
    try:
        with open(REG, encoding="utf-8") as f:
            return [e for e in json.load(f) if os.path.exists(os.path.join(CDIR, e["file"]))]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def save_items(items):
    os.makedirs(CDIR, exist_ok=True)
    with open(REG, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)


def add_item(src, name, kind, height):
    """画像をコピーして登録する。kind: "item"（机の上の小物） / "chara"（机の奥からのぞけるキャラ）"""
    items = load_items()
    iid = "c%d" % int(time.time() * 1000)
    entry = {"id": iid, "name": name, "kind": kind, "height": int(height),
             "file": _copy_in(src, CDIR, iid)}
    items.append(entry)
    save_items(items)
    return entry


def remove_item(iid):
    items = load_items()
    for e in items:
        if e["id"] == iid:
            try:
                os.remove(os.path.join(CDIR, e["file"]))
            except OSError:
                pass
    save_items([e for e in items if e["id"] != iid])


def set_item_height(iid, height):
    items = load_items()
    for e in items:
        if e["id"] == iid:
            e["height"] = int(height)
    save_items(items)


def item_sprite(entry, k):
    """小物の画像を、高さ entry["height"]（ペットの絵の px）にしたもの と 足もと（下のまんなか）の x"""
    im = cutout(os.path.join(CDIR, entry["file"]))
    bb = im.getchannel("A").getbbox() or (0, 0, im.width, im.height)
    im = im.crop(bb)
    sc = entry["height"] * k / max(1, im.height)
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), LANCZOS)
    return im, im.width / 2


# ============================================================
#  自作のメインキャラ
# ============================================================
PARTS = [  # (名前, 説明, 必要か)
    ("head", "頭（目をあけている）", True),
    ("head_closed", "頭（目をとじている）… まばたき・ねるとき用。なくてもOK", False),
    ("antenna", "ゆれるパーツ（触角・しっぽ・リボンなど）… 頭と同じ大きさの画像に、その位置でかく", False),
    ("body", "体（首から下）", True),
    ("hand", "手 … 腕の先につく。なければ丸い手", False),
]
POINTS = [  # (名前, どの画像の上で, 説明)
    ("head_neck", "head", "頭：首のつけね（ここを中心にかしげる）"),
    ("antenna_base", "antenna", "ゆれるパーツ：つけね（ここを中心にゆれる）"),
    ("body_neck", "body", "体：首のつけね（頭をつける場所）"),
    ("body_sh_l", "body", "体：画面の左の肩（腕が出る場所）"),
    ("body_sh_r", "body", "体：画面の右の肩"),
]
DEFAULT_CHARA = {"parts": {}, "points": {}, "scale": 0.12, "neck_y": 57,
                 "arm": [40, 40, 46], "arm_line": [30, 30, 34], "skin": [240, 224, 210],
                 "sleeve_len": 0.3, "behind": False, "swing": 30}


def load_chara():
    c = json.loads(json.dumps(DEFAULT_CHARA))
    try:
        with open(CHARA_JSON, encoding="utf-8") as f:
            c.update(json.load(f))
    except (OSError, ValueError):
        pass
    return c


def save_chara(c):
    os.makedirs(CHARA_DIR, exist_ok=True)
    with open(CHARA_JSON, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)


def set_part(c, part, src):
    c["parts"][part] = _copy_in(src, CHARA_DIR, part)
    save_chara(c)


def part_path(c, part):
    f = c["parts"].get(part)
    p = os.path.join(CHARA_DIR, f) if f else None
    return p if p and os.path.exists(p) else None


def missing(c):
    """まだ足りないもの（日本語のリスト）"""
    out = []
    for part, label, need in PARTS:
        if need and not part_path(c, part):
            out.append(label.split("…")[0].strip() + " の画像")
    for key, part, label in POINTS:
        if part_path(c, part) and key not in c["points"]:
            out.append(label.split("（")[0])
    return out


def shoulders(c, cx, neck_y):
    """(左の肩, 右の肩) をペットの絵の座標で"""
    p, s = c["points"], c["scale"]
    if "body_neck" not in p:
        return (cx - 13, neck_y + 8), (cx + 21, neck_y + 8)
    nx, ny = p["body_neck"]
    out = []
    for key, dflt in (("body_sh_l", (cx - 13, neck_y + 8)), ("body_sh_r", (cx + 21, neck_y + 8))):
        if key in p:
            out.append((cx + (p[key][0] - nx) * s, neck_y + (p[key][1] - ny) * s))
        else:
            out.append(dflt)
    return tuple(out)


class CustomChara:
    """パーツの画像を、Live2D みたいに動かしてかく"""

    def __init__(self, c, k):
        self.c, self.k = c, k
        s = self.s = c["scale"] * k
        self.img = {}
        for part, label, need in PARTS:
            path = part_path(c, part)
            if path:
                im = cutout(path)
                self.img[part] = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), LANCZOS)

    def ok(self):
        return not missing(self.c)

    def render(self, art, im, cx, neck_y, eyes, fx, breath, sway, flap=0):
        import math
        import hito
        if not self.ok():
            return
        eye, ang, bob, flutter = hito.Hito.pose(eyes, fx, breath, sway)
        p, s, k = self.c["points"], self.s, self.k
        lift = breath * 0.3 * k
        # 体：首のつけねが (cx, neck_y) にくるように
        bx, by = p["body_neck"]
        body = self.img["body"]
        im.paste(body, (int(cx * k - bx * s), int(neck_y * k - by * s - lift)), body)
        # 頭：ゆれるパーツをゆらしてから、首を中心にかしげる
        head = self.img["head_closed"] if (eye == "closed" and "head_closed" in self.img) else self.img["head"]
        head = head.copy()
        if "antenna" in self.img and "antenna_base" in p:
            ph = 2 * math.pi * flap / 8
            amp = 0.3 if eyes == "sleep" else 1.0
            a = flutter * 0.5 + self.c.get("swing", 30) * amp * (1 - math.cos(ph)) / 2 - self.c.get("swing", 30) / 2
            ant = self.img["antenna"].rotate(a, resample=BICUBIC, center=(p["antenna_base"][0] * s, p["antenna_base"][1] * s))
            if ant.size != head.size:
                pad = Image.new("RGBA", head.size, (0, 0, 0, 0))
                pad.paste(ant, (0, 0), ant)
                ant = pad
            head.alpha_composite(ant)
        hx, hy = p["head_neck"]
        head = head.rotate(ang, resample=BICUBIC, center=(hx * s, hy * s))
        im.paste(head, (int(cx * k - hx * s), int(neck_y * k - hy * s - lift + bob * k)), head)

    def hand(self):
        return self.img.get("hand")
