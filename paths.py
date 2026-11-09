"""
ファイルの場所

  - ふつうに python で動かすとき：どれもこのフォルダ
  - exe にしたとき：
      絵（hito.png など）       … exe の中（RES）
      設定・配置・自作の画像     … exe と同じフォルダ（APP）。はじめて起動したときに、exe の中の
                                    最初の設定をコピーする
"""
import os
import shutil
import sys

FROZEN = getattr(sys, "frozen", False)
_HERE = os.path.dirname(os.path.abspath(__file__))
RES = getattr(sys, "_MEIPASS", _HERE)
APP = os.path.dirname(os.path.abspath(sys.executable)) if FROZEN else _HERE


def res(name):
    """同梱の絵など（読むだけ）"""
    return os.path.join(RES, name)


def app(name):
    """設定や自作の画像（書きこむもの）"""
    return os.path.join(APP, name)


def first_run_copy():
    """exe のとき、はじめての起動で最初の机の配置を exe のとなりにコピー"""
    if not FROZEN:
        return
    for f in ("layout.json",):
        if not os.path.exists(app(f)) and os.path.exists(res(f)):
            try:
                shutil.copyfile(res(f), app(f))
            except OSError:
                pass


def launch_command():
    """自動起動に使うコマンド"""
    if FROZEN:
        return '@start "" "%s"' % os.path.abspath(sys.executable)
    return '@start "" pythonw "%s"' % os.path.join(_HERE, "desktop_pet.py")


first_run_copy()
