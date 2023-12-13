# python-senpai

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
[scene_table]: https://github.com/nishimura5/python_senpai/blob/master/src/scene_table.py
[gui_parts]: https://github.com/nishimura5/python_senpai/blob/master/src/gui_parts.py
[print_track_file]: https://github.com/nishimura5/python_senpai/blob/master/src/samplecode/print_track_file.py

Readme in English is [here](README-en.md)

python-senpaiは、行動分析と行動観察を行うためのアプリケーションです。また、開発を通じてPythonでのコーディングやデータ解析を学ぶためのプロジェクトです。Pythonの基礎(if文やfor文、リスト内包表記、classあたりを指します)を習得した方が、実用的なアプリケーションの開発に挑戦するための足掛かりにできるよう構成しています。とりわけ以下のライブラリの使用方法について学習することができます。

 - PandasのMultiIndex
 - Matplotlibでの時系列データ描画
 - OpenCV(cv2)のVideoCapture

現在python-senpaiが対応している姿勢推定モデルは以下のとおりです。

 - YOLOv8
 - MediaPipe

## Requirement

python-senpaiはWindows11(22H2)上の[Rye](https://rye-up.com)で構築したPython環境で開発と動作確認をおこなっています。使用しているライブラリ等については[pyproject.toml][pyproject]等を参照してください。

macOSでの動作確認も行っていますが、tkinterのバックエンドに関連する不具合を確認しているため、動作が安定しない場合があります。たとえば、macOS上のRyeで環境構築して実行するとmatplotlib.backends.backend_tkaggのimportに失敗することを確認しています。この問題については、対策としてbackend_tkaggのimportに失敗したとき用の分岐を設けています。

## Usage

ryeを使用する場合はこのリポジトリをclone後に以下を実行することで環境構築が実行されます。CUDAを有効にする場合は事前に[pyproject.toml][pyproject]内の以下のコメントアウトを外してください。
```
[[tool.rye.sources]]
name = "torch"
url = "https://download.pytorch.org/whl/cu118"
type = "index"
```

mac環境ではtkaggが使用できない場合があるため、以下のコメントアウトを外してpyqt5をaddしてください。
```
"pyqt5>=5.15.10",
```

ryeを使用する場合は以下のコマンドで環境構築が完了します。

```
rye sync
```

pipでインストールできるライブラリのみを使用しているので、rye以外の方法（Anacondaなど）でも環境を構築することが可能です。

環境構築後は[launcher.py][launcher]を実行することでアプリケーションが起動します。

```
python src/launcher.py
```
or
```
rye run launcher
```

## Applications

このプロジェクトでは、以下のそれぞれ独立したアプリケーションをlauncher.pyが呼び出す構成になっています。
 - [app_detect.py][app_detect]
 - [app_track_list.py][app_track_list]
 - [app_member_edit.py][app_member_edit]
 - [app_make_mp4.py][app_make_mp4]
 - [app_trajplot.py][app_trajplot]
 - [app_area_filter.py][app_area_filter]
 - [app_calc_vector.py][app_calc_vector]
 - [app_recuplot.py][app_recuplot]
 - [scene_table.py][scene_table]

## Interface

### Track file

app_detect.pyで姿勢推定を行った結果としての時系列座標データは、Pickle化されたPandasのDataFrame型で保存されます。python-senpaiはこれをTrackファイルと呼んでいます。ファイル拡張子は'.pkl'です。

Trackファイルは3-level-multi-indexで時系列座標データを保持しています。indexの名称はlevel 0から順に'frame', 'member', 'keypoint'です。frameは0から始まる整数で、動画のフレーム番号と対応しています。memberとkeypointは姿勢推定モデルが検出したkeypointsのIDです。Trackファイルには必ず'x', 'y', 'timestamp'の3つのcolumnsが含まれています。姿勢推定モデルの仕様に応じて、そのほかに、'z'や'conf'といったcolumnsが含まれます。

Trackファイルに格納されたDataFrameのattrsプロパティには、元の動画ファイルのファイル名やそのフレームサイズ、姿勢推定に使用したモデルの名称等が記録されています。

Trackファイルを読み込み、attrsに記録された内容を確認するためのPythonコードは以下のとおりです。

```
trk_df = pd.read_pickle("path/to/track_file.pkl")
print(trk_df.attrs)
```

また[print_track_file.py][print_track_file]にはTrack fileを開くための基本的なサンプルコードを記述しています。

### Calculated track file

[app_calc_vector.py][app_calc_vector]や[app_area_filter][app_area_filter]で処理されたデータは、Track fileと同じくPickle化されたPandasのDataFrame型で保存されますが、データの構造が少し異なります。ファイル拡張子は'.pkl'です。

Calculated track fileは2-level-multi-indexでデータを保持しています。indexの名称はlevel 0から順に'frame', 'member'です。columnsの名称は計算の内容に準じますが、必ず'timestamp'が含まれています。

### Temporary file

アプリケーションの設定値や直近で読み込まれたTrack fileのパスは、Pickle化されたPythonのdictionary型で保存されます。ファイル名は'temp.pkl'です。このファイルが存在しない場合はアプリケーションが(初期値を用いて)自動生成します。したがって、設定値をクリアする等の目的で、ファイルを手動で削除(ゴミ箱に移動)することができます。
'temp.pkl'は[gui_parts.py][gui_parts]が管理しています。
