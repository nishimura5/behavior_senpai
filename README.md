# Behavior Senpai

[pyproject]: https://github.com/nishimura5/python_senpai/blob/master/pyproject.toml
[launcher]: https://github.com/nishimura5/python_senpai/blob/master/src/launcher.py
[app_detect]: https://github.com/nishimura5/python_senpai/blob/master/src/app_detect.py
[app_track_list]: https://github.com/nishimura5/python_senpai/blob/master/src/app_track_list.py
[app_member_edit]: https://github.com/nishimura5/python_senpai/blob/master/src/app_member_edit.py
[app_make_mp4]: https://github.com/nishimura5/python_senpai/blob/master/src/app_make_mp4.py
[app_trajplot]: https://github.com/nishimura5/python_senpai/blob/master/src/app_trajplot.py
[app_area_filter]: https://github.com/nishimura5/python_senpai/blob/master/src/app_area_filter.py
[app_calc_vector]: https://github.com/nishimura5/python_senpai/blob/master/src/app_calc_vector.py
[app_recuplot]: https://github.com/nishimura5/python_senpai/blob/master/src/app_recuplot.py
[app_scene_table]: https://github.com/nishimura5/python_senpai/blob/master/src/app_scene_table.py
[gui_parts]: https://github.com/nishimura5/python_senpai/blob/master/src/gui_parts.py
[print_track_file]: https://github.com/nishimura5/python_senpai/blob/master/src/samplecode/print_track_file.py
[detector_proc]: https://github.com/nishimura5/python_senpai/blob/master/src/detector_proc.py

![ScreenShot](https://www.design.kyushu-u.ac.jp/~eigo/Behavior%20Senpai%20_%20Python%20senpai_files/git_behavior_senpai_trajplot.png)

Behavior Senpai(ビヘイビア センパイ)は、定量的行動観察を行うためのアプリケーションです。ビデオカメラで撮影した人の行動をkeypoint検出AIを使用して時系列座標データ化し、その時系列座標データを用いて人の行動を定量的に分析することができます。

Behavior Senpaiは以下の3種類のAI画像処理フレームワーク/モデルを使った、動画ファイルに対するkeypoint検出を実現します。

 - YOLOv8 Pose
 - MediaPipe Holistic
 - RTMPose Body8-Halpe26 (MMPose)

## Requirement

Behavior SenpaiはWindows11(23H2)で開発と動作確認をおこなっています。

### CUDAを使用する場合

 - 空き容量: 10GB～
 - 搭載RAM: 16GB～
 - GPU: RTX2060～
 - [Rye](https://rye-up.com)
 - .NET 8.0
 - CUDA 12.1

### CUDAを使用しない場合

CUDA対応GPUを搭載していない場合はMediaPipe Holisticのみが使用可能です。

 - 空き容量: 8GB～
 - 搭載RAM: 16GB～
 - [Rye](https://rye-up.com)
 - .NET 8.0

## Usage

### Windows

BehaviorSenpai.exeを実行するとアプリケーションが起動します。CUDAを使用する場合は初回起動時に「Enable features using CUDA」にチェックを入れてから「OK」ボタンをクリックしてください。

### Mac

Macでは、RyeがダウンロードするCPythonではなく別途pyenv等でPythonをダウンロードまたはビルドし、手動でtoolchainに追加する必要があります。具体的な手順の一例としては

 - pyenv install 3.11.6
 - pyenv which python でpythonのpathを得る
 - .python-versionファイルを開き"pyenv@3.11.6"に書き換える
 - rye toolchain register --name=pyenv /path/to/pyenv/python3.11
 - rye fetch 3.11.6
 - git clone https://github.com/nishimura5/behavior_senpai.git
 - cd behavior_senpai
 - rye sync
 - . ./launcher.sh

で導入が完了します。

## Interface

### Track file

app_detect.pyでキーポイント検出を行った結果としての時系列座標データは、Pickle化されたPandasのDataFrame型で保存されます。Behavior SenpaiはこれをTrack fileと呼んでいます。ファイル拡張子は'.pkl'です。Track fileはキーポイント検出を行った動画ファイルと同じディレクトリに生成される'trk'フォルダに保存されます。

Track fileは3-level-multi-indexで時系列座標データを保持しています。indexの名称はlevel 0から順に'frame', 'member', 'keypoint'です。frameは0から始まる整数で、動画のフレーム番号と対応しています。memberとkeypointはモデルが検出したkeypointsのIDです。Track fileには必ず'x', 'y', 'timestamp'の3つのcolumnsが含まれています。x,yの単位はpx、timestampの単位はミリ秒です。

Track fileに格納されているDataFrameの例を以下に示します。なおcolumnsにはAIモデルの仕様に応じて、そのほかに、'z'や'conf'といったcolumnが含まれることがあります。

|  |  |  | x | y | timestamp |
| - | - | - | - | - | - |
| frame | member | keypoint |  |  |  |
| 0 | 1 | 0 | 1365.023560 | 634.258484 | 0.0 |
|  |  | 1 | 1383.346191 | 610.686951 | 0.0 |
|  |  | 2 | 1342.362061 | 621.434998 | 0.0 |
|  |  | ... | ... | ... | ... |
|  |  | 16 | 1417.897583 | 893.739258 | 0.0 |
|  | 2 | 0 | 2201.367920 | 846.174194 | 0.0 |
|  |  | 1 | 2270.834473 | 1034.986328 | 0.0 |
|  |  | ... | ... | ... | ... |
|  |  | 16 | 2328.100098 | 653.919312 | 0.0 |
| 1 | 1 | 0 | 1365.023560 | 634.258484 | 33.333333 |
|  |  | 1 | 1383.346191 | 610.686951 | 33.333333 |
|  |  | ... | ... | ... | ... |

### Calculated Track file

[app_calc_vector.py][app_calc_vector]や[app_area_filter][app_area_filter]で処理されたデータは、Track fileと同じくPickle化されたPandasのDataFrame型で保存されますが、データの構造が少し異なります。ファイル拡張子は'.pkl'です。

Calculated Track fileは2-level-multi-indexでデータを保持しています。indexの名称はlevel 0から順に'frame', 'member'です。columnsの名称は計算の内容に準じますが、必ず'timestamp'が含まれています。

### Attributes of Track file

Track fileやCalculated Track fileに格納されたDataFrameの[attrsプロパティ](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html)には、元の動画ファイルのファイル名やそのフレームサイズ、キーポイント検出に使用したAIモデルの名称等が記録されています。

Track fileを読み込み、attrsに記録された内容を確認するためのPythonコードは以下のとおりです。attrsプロパティはdictionary型です。

```
trk_df = pd.read_pickle("path/to/track_file.pkl")
print(trk_df.attrs)
```

主なattrsの内容は以下のとおりです。このほかにも適宜追加されます。

#### model

キーポイント検出に使用したAIモデルの名称が記録されています。attrsへの追加は[app_detector.py][app_detect]（[detector_proc.py][detector_proc]）で行われます。

 - YOLOv8 x-pose-p6
 - MediaPipe Holistic

#### frame_size

キーポイント検出を行った動画のフレームサイズがtuple型(width, height)で記録されています。単位はpxです。attrsへの追加は[app_detector.py][app_detect]（[detector_proc.py][detector_proc]）で行われます。

#### video_name

キーポイント検出を行った動画のファイル名が記録されています。attrsへの追加は[app_detector.py][app_detect]（[detector_proc.py][detector_proc]）で行われます。

#### next, prev

ビデオカメラで撮影した長時間の動画ファイルは、カメラの仕様で録画時に分割されることがあります。Track fileは動画ファイルと対になっているためTrack fileも分かれてしまいます。nextとprevは分かれているTrack fileの前後関係を記録するためのものです。attrsへの追加は[app_track_list.py][app_track_list]で行われます。

### Temporary file

アプリケーションの設定値や直近で読み込まれたTrack fileのパスは、Pickle化されたPythonのdictionary型で保存されます。ファイル名は'temp.pkl'です。このファイルが存在しない場合はアプリケーションが(初期値を用いて)自動生成します。したがって、設定値をクリアする等の目的で、ファイルを手動で削除(ゴミ箱に移動)することができます。
'temp.pkl'は[gui_parts.py][gui_parts]が管理しています。
