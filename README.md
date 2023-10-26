# python-senpai

このリポジトリは以下のアプリケーションを含みます
 - video_to_keypoints.py: YOLOv8とMediaPipe Holisticによる姿勢推定とその結果をPKLファイルに保存するアプリ。
 - keypoints_to_figure.py: 上記がアプリが出力したPKLファイルのデータをグラフ描画するアプリ

## スクリプト

### グラフ描画
以下の動画([YouTube](https://youtu.be/FYrrFdX6A7s?si=FpTq_ExCCWz0PumD))で、アプリケーションの機能や構造を説明をしているので併せてご覧ください。
<p align="center">
<a href="https://youtu.be/FYrrFdX6A7s?si=FpTq_ExCCWz0PumD"><img src="http://img.youtube.com/vi/FYrrFdX6A7s/mqdefault.jpg" width="300"></a>
</p>

 - [keypoints_to_figure.py](src/keyoints_to_figure.py): グラフ描画アプリ(下のラッパー)
 - [trajectory_plotter.py](src/trajectory_plotter.py): PKLファイルのデータのグラフ描画

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
 - [yolo_plotter.py](src/yolo_plotter.py): PKLファイルを読み込んで推論結果を時系列グラフにプロット
