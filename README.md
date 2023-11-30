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
```
or
```
rye run launcher
```

MediaPipe(YOLOも？)による推論を複数の動画ファイルに対して連続実行すると、2回目以降にメモリアクセス違反でクラッシュしてしまう現象を確認しているため、[detector_proc.py](src/detector_proc.py)をsubprocessで実行する方式としています。

## Applications

このプロジェクトでは、以下のそれぞれ独立したアプリケーションをlauncher.pyが呼び出す構成になっています。
 - [video_to_keypoints.py](src/video_to_keypoints.py)
 - [track_list.py](src/track_list.py)
 - [keypoints_to_band.py](src/keypoints_to_band.py)
 - [keypoints_to_mp4.py](src/keypoints_to_mp4.py)
 - [keypoints_to_trajplot.py](src/keypoints_to_trajplot.py)
 - [keypoints_to_recuplot.py](src/keypoints_to_recuplot.py)
 - [scene_table.py](src/scene_table.py)


