# デスクトップペット

デスクトップの下で、キャラクターが机に向かってキーボードを打ったりマウスを動かしたりする、Windows 用のデスクトップペットです。

- 本物のキーボードで押したキーと**同じ位置**のキーを押します（押したキーは光ります。何を打ったかは記録・保存しません）
- カーソルを動かすと、マウスを動かします。クリックするとボタンが光ります
- しばらく何もしないと寝ます。クリックでジャンプ、ドラッグでつかんで動かせます
- 2画面でも、好きなモニターに置けます

## 動かし方

必要なもの：Windows、Python 3、[Pillow](https://pypi.org/project/pillow/)

```bash
pip install pillow
```

```bash
pythonw desktop_pet.py
```

`start_pet.bat` をダブルクリックしても起動できます（黒い窓は出ません）。

## exe にする

Python が入っていないパソコンでも動く `DesktopPet.exe` を作れます。

```bash
pip install pyinstaller
```

```bash
python -m PyInstaller --noconfirm --onefile --noconsole --name DesktopPet --icon icon.ico --add-data "hito.png;." --add-data "fudeneko.png;." --add-data "layout.json;." desktop_pet.py
```

`dist\DesktopPet.exe` ができます。好きなフォルダに置いてダブルクリックで起動します。
設定・配置・自作キャラの画像は、exe と同じフォルダに保存されます（はじめての起動で最初の設定がコピーされます）。

## 使い方

| 操作 | できること |
| --- | --- |
| ダブルクリック | 設定画面をひらく |
| 右クリック | メニュー（もようがえ、小物を出す、ねる、終了 など） |
| ドラッグ | つかんで動かす（もようがえ中は小物を動かす） |

設定画面のタブ：

- **表示**：大きさ、いつも手前に表示、その場に固定、パソコン起動時に自動で起動
- **動き**：キーボード・マウスへの反応、寝るまでの時間
- **机**：机のテーマ（和風／研究室）、もようがえ、小物を出す
- **キャラ**：ペットごとのキャラ（ひと／自作キャラ）、もう1人よぶ、自作キャラを作る、手の位置

## ファイル

| ファイル | 中身 |
| --- | --- |
| `desktop_pet.py` | 本体（ウィンドウ、机・キーボード・マウス、動き、設定画面） |
| `hito.py` | ひと（`hito.png`）をパーツに分けて Live2D 風に動かす |
| `jisaku.py` | 自作キャラ（頭・体・手などのパーツの画像を動かす） |
| `paths.py` | ファイルの場所（ふつうに動かすときと exe のときのちがい） |
| `icon.ico` | exe のアイコン |
| `hito.png`, `fudeneko.png` | キャラクターの絵 |
| `layout.json` | 机の上の配置とテーマ |
| `custom/chara/` | 自作キャラのパーツ画像（作ったときにできる） |

`app_settings.json`（大きさや置いた場所など、パソコンごとの設定）は自動で作られます。

## 見た目だけ確かめる

```bash
python desktop_pet.py --preview preview.png
```
