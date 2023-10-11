# python-senpai

YOLOv8とMediaPipe Holisticの推論結果をPKLファイルに保存し、Pandasで読み込んでSeabornで時系列データとしてグラフ描画するまでの一部始終を動画にしました。AIによる追跡や姿勢推定の出力を時系列データとして記録することで、行動の定量化が可能となり、人の行動を条件間や個人間で比較することができるようになります。

## 動画

以下の動画([YouTube](https://youtu.be/3CYtbPIBzcI?si=NoCB__4hedZWYr4X))で、スクリプトのコーディングの一部始終を説明しているので併せてご覧ください。

<p align="center">
<a href="https://youtu.be/3CYtbPIBzcI?si=NoCB__4hedZWYr4X"><img src="https://i9.ytimg.com/vi_webp/3CYtbPIBzcI/maxresdefault.webp?v=65261c7e&sqp=CJzHmKkG&rs=AOn4CLDieDd1g-FOPfMLg92BPQjPBOcM3Q" width="500"></a>
</p>

## スクリプト

 - [mediapipe_detector.py](src/mediapipe_detector.py): MediaPipe Holisticによる推論結果をPKLファイルに出力
 - [mediapipe_drawer.py](src/mediapipe_drawer.py): PKLファイルを読み込んでMediaPipe Holisticの推論結果を動画に描画
 - [yolo_detector.py](src/yolo_detector.py): YOLOv8による推論結果をPKLファイルに出力
 - [yolo_drawer.py](src/yolo_drawer.py): PKLファイルを読み込んでYOLOv8の推論結果を動画に描画
 - [yolo_plotter.py](src/yolo_plotter.py): PKLファイルを読み込んで推論結果を時系列グラフにプロット
