# python-senpai

Readme in English is [here](README-en.md)

python-senpaiは、行動分析と行動観察を行うためのアプリケーションです。また、開発を通じてPythonでのコーディングやデータ解析を学ぶためのプロジェクトです。Pythonの基礎(if文やfor文、リスト内包表記、classあたりを指します)を習得した方が、実用的なアプリケーションの開発に挑戦するための足掛かりにできるよう構成しています。とりわけ以下のライブラリの使用方法について学習することができます。

 - PandasのMultiIndex
 - Matplotlibでの時系列データ描画
 - OpenCV(cv2)のVideoCapture

現在python-senpaiが対応している姿勢推定モデルは以下のとおりです。

 - YOLOv8
 - MediaPipe

## Requirement

python-senpaiはWindows11(22H2)上の[Rye](https://rye-up.com)で構築したPython環境で開発と動作確認をおこなっています。使用しているライブラリ等については[pyproject.toml](pyproject.toml)等を参照してください。

macOSでの動作確認も行っていますが、tkinterのバックエンドに関連する不具合を確認しているため、動作が安定しない場合があります。たとえば、macOS上のRyeで環境構築して実行するとmatplotlib.backends.backend_tkaggのimportに失敗することを確認しています。この問題については、対策としてbackend_tkaggのimportに失敗したとき用の分岐を設けています。

## Usage

ryeを使用する場合はこのリポジトリをclone後に以下を実行することで環境構築が実行されます。CUDAを有効にする場合は事前に[pyproject.toml](pyproject.toml)内の以下のコメントアウトを外してください。
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

環境構築後は[launcher.py](src/launcher.py)を実行することでアプリケーションが起動します。

```
python src/launcher.py
```
or
```
rye run launcher
```

## Applications

このプロジェクトでは、以下のそれぞれ独立したアプリケーションをlauncher.pyが呼び出す構成になっています。
 - [video_to_keypoints.py](src/video_to_keypoints.py)
 - [track_list.py](src/track_list.py)
 - [keypoints_to_band.py](src/keypoints_to_band.py)
 - [keypoints_to_mp4.py](src/keypoints_to_mp4.py)
 - [keypoints_to_trajplot.py](src/keypoints_to_trajplot.py)
 - [keypoints_to_vector.py](src/keypoints_to_vector.py)
 - [keypoints_to_recuplot.py](src/keypoints_to_recuplot.py)
 - [scene_table.py](src/scene_table.py)

## Interface

### Track file

video_to_keypoints.pyで姿勢推定を行った結果としての時系列座標データは、Pickle化されたPandasのDataFrame型で保存されます。python-senpaiはこれをTrackファイルと呼んでいます。ファイル拡張子は'.pkl'です。

Trackファイルは3-level-multi-indexで時系列座標データを保持しています。indexの名称はlevel 0から順に'frame', 'member', 'keypoint'です。frameは0から始まる整数で、動画のフレーム番号と対応しています。memberとkeypointは姿勢推定モデルが検出したkeypointsのIDです。Trackファイルには必ず'x', 'y', 'timestamp'の3つのcolumnsが含まれています。姿勢推定モデルの仕様に応じて、そのほかに、'z'や'conf'といったcolumnsが含まれます。

Trackファイルに格納されたDataFrameのattrsプロパティには、元の動画ファイルのファイル名やそのフレームサイズ、姿勢推定に使用したモデルの名称等が記録されています。

Trackファイルを読み込み、attrsに記録された内容を確認するためのPythonコードは以下のとおりです。

```
trk_df = pd.read_pickle("path/to/track_file.pkl")
print(trk_df.attrs)
```

### Calculated track file

[keypoints_to_vector.py](src/keypoints_to_vector.py)で処理されたデータは、Track fileと同じくPickle化されたPandasのDataFrame型で保存されますが、データの構造が少し異なります。ファイル拡張子は'.pkl'です。

Calculated track fileは2-level-multi-indexでデータを保持しています。indexの名称はlevel 0から順に'frame', 'member'です。columnsの名称は計算の内容に準じますが、必ず'timestamp'が含まれています。

### Temporary file

アプリケーションの設定値や直近で読み込まれたTrack fileのパスは、Pickle化されたPythonのdictionary型で保存されます。ファイル名は'temp.pkl'です。このファイルが存在しない場合はアプリケーションが(初期値を用いて)自動生成します。したがって、設定値をクリアする等の目的で、ファイルを手動で削除(ゴミ箱に移動)することができます。
