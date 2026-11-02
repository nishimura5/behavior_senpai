# dev170: フィルターの時間軸

Bandpassfilter、Highpassfilter、Lowpassfilter は、Mix/Norm の描画・CSV、Feature copy のすべてで対象 member の `timestamp`（ミリ秒）を使う。
Track の元の fps 属性や行番号からは推定せず、暗黙の 60 Hz は使用しない。

- シーンごとに `1000 / median(diff(timestamp))` で実効サンプリング周波数（Hz）を求める。
- 時刻は有限で、member 内で厳密な昇順であること。重複・逆行・欠測時刻は中止する。自動ソートはしない。
- 選択シーン内の全隣接間隔が中央値から **1% + 0.000001 ms** 以内であること。欠落フレーム、間引きで交互になる間隔、時刻の飛びは中止する。
- 選択シーン内の特徴量の欠測・無限値は中止する。`dropna()` による連結や補間は行わない。シーン外の特徴量欠測は許容し、出力は NaN にする。
- 分離したシーンは独立に処理する。重複・接触する時刻範囲は併合する。サンプルがない範囲はスキップするが、全範囲が空なら中止する。
- 各区間のサンプル数は Bandpassfilter で最低34、Highpassfilter / Lowpassfilter で最低19。非空の短い区間を黙って除外しない。
- カットオフは Nyquist 周波数（実効サンプリング周波数の半分）未満であること。エラーには必要なサンプル数や周波数、可能な範囲で特徴量名・member を表示する。

カットオフは従来通り、Bandpassfilter が 0.2–2 Hz、Highpassfilter が 0.2 Hz、Lowpassfilter が 0.4 Hz。
5次 Butterworth フィルターを二次セクション（SOS）で構成し、往復適用する。区間端はパディングの影響を受ける。

`feature_proc.calc(series, code, *, timestamps=None, sampling_frequency=None, scene_ranges=None)` の直接利用では、時刻がない場合に限り、呼び出し側が等間隔かつ連続した単一memberの信号であると保証し、`sampling_frequency`（Hz）を明示してよい。
時刻と周波数を両方渡した場合は1%以内の一致を検証する。時刻も明示周波数もない旧式呼び出しは、フィルターを使う場合に理由付きエラーとする。明示周波数だけではシーン選択できない。
フィルター以外の正規化・閾値処理・四則演算は従来の計算を維持する。

`thin_by_timestamp()` は各memberの先頭時刻を起点に固定幅の時間ビンで最初の時刻を残し、同じ時刻のキーポイントを一緒に保持する。
60→15 fps は約66.667 ms間隔となる。一方、30→20 fpsなどの不等間隔になる間引き結果は、上記条件を満たさなければフィルターでは中止する。間引き自体はリサンプリングやアンチエイリアス処理を行わない。

実データの時刻生成元は検出処理の `CAP_PROP_POS_MSEC`、DLC変換の `frame / fps * 1000`。
作業ツリーに実Trackはなく、実収録の揺れは未確認。整数ミリ秒への丸めなどで1%を超える揺れがあるデータは、このリリースでは安全側に倒して中止する。

Mix/Norm のフィルター失敗時は保存ボタンを無効にし、部分結果を破棄する。CSVは計算成功前には書き込まない。
Feature copy は先行修正の一時HDF5による更新を維持し、失敗した対象の既存ファイルはバイト単位で保持する。

検証: `python -X utf8 -m unittest discover -v -s tests`。
GUIのランチャーテストは子プロセスごとに実VideoCaptureを1回だけ生成する。今回のMix/NormテストはVideoCaptureを生成しない。
