# coding:utf-8

from collections import deque

import numpy as np
import pyaudio
import wave


class AudioController(object):
    def __init__(self):
        """コンストラクタ"""
        self.q = deque()
        self.is_stream = False
        self.p = None
        self.stream = None

    def setup_stream(self, ch=1, rate=44100, chunck=1024):
        """ストリームをセットアップする

        Keyword Arguments:
            ch {int} -- チャンネル数 (default: {1})
            rate {int} -- サンプリングレート (default: {44100})
            chunck {int} -- 1フレームの点数 (default: {1024})
        """
        if self.p is not None:
            self.p.terminate()
        self.rate = rate
        self.chunk = chunck
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=ch,
            rate=rate,
            input=True,
            output=False,
            stream_callback=self.callback,
            frames_per_buffer=chunck
        )

    def read_wav(self, wav_path):
        """音源を読み込む

        Arguments:
            wav_path {str} -- 音源ファイルのパス

        Returns:
            [numpy.array, int, int] -- 波形データ, チャンネル数, サンプリング周波数
        """
        try:
            wf = wave.open(wav_path, 'r')
        except FileNotFoundError:
            print("[Error] No such file: " + wav_path)
            exit(1)

        buf = wf.readframes(-1)
        samplewidth = wf.getsampwidth()
        if samplewidth == 2:
            data = np.frombuffer(buf, dtype='int16')
        elif samplewidth == 4:
            data = np.frombuffer(buf, dtype='int32')
        ch = wf.getnchannels()
        fs = wf.getframerate()
        wf.close()
        return data, ch, fs

    def start_stream(self):
        """リアルテイムで音のバッファリングを開始する"""
        self.is_stream = True

    def stop_stream(self):
        """リアルテイムで音のバッファリングを停止する"""
        self.is_stream = False

    def clear_buffer(self):
        """溜まっているバッファを初期化する"""
        self.q.clear()

    def close_stream(self):
        """Pyaudioのストリームをクローズする"""
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def callback(self, in_data, frame_count, time_info, status):
        """音を受け取るコールバック

        Arguments:
            in_data {list} -- 音源データ
            frame_count {[type]} -- [description]
            time_info {[type]} -- [description]
            status {[type]} -- [description]

        Returns:
            [type] -- [description]
        """
        if self.is_stream:
            data = np.frombuffer(in_data, dtype='int16') / 32768.
            self.q.append(data)
        return None, pyaudio.paContinue
