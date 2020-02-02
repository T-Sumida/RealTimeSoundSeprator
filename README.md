# RealTimeSoundSeprator
リアルタイム音源分離モック

# 概要
非負値行列因子分解（NMF：Non-negative Matrix Factorization）を用いたリアルタイム音源分離モック。

入力音に、事前に登録した音源 or プログラム実行中に追加した音色がどれだけ含まれているかを計算する。
その計算結果を 0.1sec 間隔でOSC送信する。

確認用の[可視化プログラム](visualizer/visualizer.pde)についてはProcessing3で作成。

# 環境構築
- MacOS Mojave 10.14.5
- python 3.7.0
```
$ git clone https://github.com/T-Sumida/RealTimeSoundSeprator.git
$ cd RealTimeSoundSeprator
$ pip install -r requirements.txt
```

# 使い方
## 実行方法
```
$ python realtime_audio_separator.py
```

## 実行中の操作
インタプリタで操作を行う。
### 音色追加コマンド ： a
コマンドを実行するとカウントダウンが開始し、「RECORD!」と出力されてから３秒間録音する。
録音した音源から新しい音色データを作成し、NMFに登録する。
```
$ python realtime_audio_separator.py
======================= RUN =======================
> a
please input audio 3[sec]!!!
============3============
============2============
============1============
RECORD!!
finish add
```

### 音色変更コマンド : c
現在登録されている音色を変更する。
コマンドを実行すると、現在登録されている音色が表示される。

続いて、```変更したい音色ID,新しい音色名```を入力し、aコマンドと同様に録音を開始する。
```
> c
Please input [timber_index,timber_name] to change. (cancel is [q] key)
Timber:0 : scratch
Timber:1 : voise
Timber:2 : clap
Timber:3 : noise
> 2,tip
please input audio 3[sec]!!!
============3============
============2============
============1============
RECORD!!
finish change
```

### 音色確認コマンド : s
現在登録する音色を表示する。

```
> s
Timber:0 : scratch
Timber:1 : voise
Timber:2 : clap
Timber:3 : timber:4
Timber:4 : noise
```

### 終了コマンド : q
アプリケーションを終了する。

```
> q
RealTimeSoundSeprator t_sumida$
```
### ヘルプコマンド : h
コマンドの説明を表示する。

```
> h
'a' is add timber.
'c' is change timber.
's' is show timber list.
'q' is shutdown application.
```


# License
Copyright © 2020 T_Sumida Distributed under the MIT License.
