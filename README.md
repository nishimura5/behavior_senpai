# python-senpai

Readme in English is [here](README-en.md)

python-senpaiは、行動分析と行動観察を行うためのアプリケーションです。また、開発を通じてPythonでのコーディングやデータ解析を学ぶためのプロジェクトです。Pythonの基礎(if文やfor文、リスト内包表記、classあたりを指します)を習得した方が、実用的なアプリケーションの開発に挑戦するための足掛かりにできるよう構成しています。とりわけ以下のライブラリの使用方法について学習することができます。

 - PandasのMultiIndex
 - Matplotlibでの時系列データ描画
 - OpenCV(cv2)のVideoCapture

## Requirement

python-senpaiはWindows11(22H2)上の[Rye](https://rye-up.com)で構築したPython環境で開発と動作確認をおこなっています。使用しているライブラリ等については[pyproject.toml](pyproject.toml)等を参照してください。

現在、macOS上のRyeで環境構築して実行するとmatplotlib.backends.backend_tkaggのimportに失敗することを確認しています。そこで、backend_tkaggのimportに失敗したとき用の分岐を設けています。本件が該当するコードは[trajectory_plotter.py](src/trajectory_plotter.py)と[recurrence_plotter.py](src/recurrence_plotter.py)です。

## Usage

ryeを使用する場合はこのリポジトリをclone後に以下を実行することで環境構築が実行されます。CUDAを有効にする場合は事前に[pyproject.toml](pyproject.toml)内のコメントアウトを外してください。

```
rye sync
```

pipでインストールできるライブラリのみを使用しているので、rye以外の方法（Anacondaなど）でも環境を構築することが可能です。

環境構築後は[launcher.py](src/launcher.py)を実行することでアプリケーションが起動します。

```
python src/launcher.py
or
rye run launcher
```

MediaPipe(YOLOも？)による推論を複数の動画ファイルに対して連続実行すると、2回目以降にメモリアクセス違反でクラッシュしてしまう現象を確認しているため、[detector_proc.py](src/detector_proc.py)をsubprocessで実行する方式としています。

## Applications

このプロジェクトでは、以下の独立したアプリケーションをlauncher.pyが呼び出す構成になっています。
 - [video_to_keypoints.py](src/video_to_keypoints.py)
 - [keypoints_to_mp4.py](src/keypoints_to_mp4.py)
 - [keypoints_to_trajplot.py](src/keypoints_to_trajplot.py)
 - [keypoints_to_recuplot.py](src/keypoints_to_recuplot.py)
 - [scene_table.py](src/scene_table.py)

### グラフ描画
以下の動画([YouTube](https://youtu.be/c38UHrECGJA?si=k946YKvBmVXjrG8v))で、アプリケーションの機能や構造を説明をしているので併せてご覧ください。
<p align="center">
<a href="https://youtu.be/c38UHrECGJA?si=k946YKvBmVXjrG8v"><img src="http://img.youtube.com/vi/c38UHrECGJA/mqdefault.jpg" width="300"></a>
</p>

 - [keypoints_to_figure.py](src/keypoints_to_figure.py): グラフ描画アプリ(下のラッパー)
 - [trajectory_plotter.py](src/trajectory_plotter.py): PKLファイルのデータのグラフ描画
 - [keypoints_proc.py](src/keypoints_proc.py): 時系列座標データに対する諸計算

### 姿勢推定
以下の動画([YouTube](https://youtu.be/hE8ZoA8gETU?si=iDzTC7EPSqV6PfcA))で、アプリケーションの機能や構造を説明をしているので併せてご覧ください。
<p align="center">
<a href="https://youtu.be/hE8ZoA8gETU?si=iDzTC7EPSqV6PfcA"><img src="http://img.youtube.com/vi/hE8ZoA8gETU/mqdefault.jpg" width="300"></a>
</p>

 - [video_to_keypoints.py](src/video_to_keypoints.py): 姿勢推定アプリ(下のラッパー)
 - [yolo_detector.py](src/yolo_detector.py): YOLOv8による推論
 - [mediapipe_detector.py](src/mediapipe_detector.py): MediaPipe Holisticによる推論
 - [windows_and_mac.py](src/windows_and_mac.py): 動画ファイルやフォルダを開く(WindowsとMacを想定)
 - [roi_cap.py](src/roi_cap.py): ROI機能

### その他
 - [mediapipe_drawer.py](src/mediapipe_drawer.py): PKLファイルを読み込んでMediaPipe Holisticの推論結果を動画に描画
 - [yolo_drawer.py](src/yolo_drawer.py): PKLファイルを読み込んでYOLOv8の推論結果を動画に描画
