# coding:utf-8

import glob
import time
import concurrent.futures as conf
import numpy as np

from audio_controller import AudioController
from separator import Separator
from osc import OscClient

# 録音時間
TIME = 3

# OSCの送信頻度[sec]
OSC_FREQ = 0.1

OSC_TIMBER_ADDR = "/timber_size"
OSC_RESULT_ADDR = "/sep_data"


class RealTimeAudioSeparator(object):
    def __init__(self, chunk=1024):
        """コンストラクタ

        Keyword Arguments:
            chunk {int} -- バッファサイズ (default: {1024})
        """
        self.chunk = chunk
        self.ac = AudioController()
        self.buffer = np.zeros((self.chunk), dtype=np.float32)
        self.window_func = np.hamming(self.chunk)
        self.osc = OscClient("localhost", 5000)
        self.separate_results = None
        self.timbers = None
        self.separate_flag = True
        self.sep_thread = None
        self.osc_thread = None

    def calc_spectrum(self, data):
        """スペクトルを計算する

        Arguments:
            data {numpy.array} -- 入力データ

        Returns:
            numpy.array -- スペクトル
        """
        self.buffer[:self.chunk//2] = self.buffer[self.chunk//2:]
        self.buffer[self.chunk//2:] = data

        F = np.fft.fft(self.buffer * self.window_func)
        amp = np.abs(F)[:self.chunk//2]
        return amp/np.sum(amp)

    def setup(self):
        """初期設定を行う"""
        files = glob.glob("./audio/*")
        if len(files) == 0:
            print("audioディレクトリにwavファイルを置いてください")
            exit(1)
        self.separator = Separator(self.chunk//2, 1, len(files))
        for i, f in enumerate(files):
            name = f.split("/")[-1].split('.')[0]
            data, ch, fs = self.ac.read_wav(f)
            spectrum = np.zeros((self.chunk//2), dtype=np.float32)

            for j in range(0, len(data), self.chunk//2):
                amp = self.calc_spectrum(data[j:j+self.chunk//2])
                spectrum += amp
            self.separator.set_dictionary(spectrum/j, i, name=name)

    def run(self):
        """処理を開始する"""
        print("======================= RUN =======================")
        self.ac.setup_stream(chunck=self.chunk//2)

        with conf.ThreadPoolExecutor(max_workers=2) as executor:
            self.start_separate(executor)
            while True:
                print("> ", end="")
                line = input()
                if line == 'a':
                    self.stop_separate(executor)
                    self.add_timber()
                    self.start_separate(executor)
                elif line == 'c':
                    self.stop_separate(executor)
                    self.change_timber()
                    self.start_separate(executor)
                elif line == 'q':
                    self.stop_separate(executor)
                    break
                elif line == 's':
                    self.print_timber_list()
                elif line == 'h':
                    print('\'a\' is add timber.')
                    print('\'c\' is change timber.')
                    print('\'s\' is show timber list.')
                    print('\'q\' is shutdown application.')
            self.ac.close_stream()

    def print_countdown(self):
        """録音時のカウントダウンを表示する"""
        print('please input audio {}[sec]!!!'.format(TIME))
        print('============3============')
        time.sleep(1)
        print('============2============')
        time.sleep(1)
        print('============1============')
        time.sleep(1)
        print('RECORD!!')

    def print_timber_list(self):
        """現在の音色のリストを表示する"""
        timbers = self.separator.get_timber()
        for k, v in timbers.items():
            print("Timber:{} : {}".format(k, v))

    def add_timber(self):
        """音色を追加する"""
        self.print_countdown()
        spectrum = self.record()
        self.separator.add_dictionary(spectrum)
        print("finish add")

    def change_timber(self):
        """登録してある音色を変更する"""
        timber_index = -1
        timber_name = None
        while True:
            print('Please input [timber_index,timber_name] to change. (cancel is [q] key)')
            self.print_timber_list()
            print("> ", end="")
            line = input()
            if len(line.split(",")) != 2 and line != 'q':
                continue
            if line == 'q':
                return
            if not line.split(",")[0].isdecimal():
                continue
            timber_index, timber_name = int(line.split(",")[0]), line.split(",")[1]
            if (timber_index > len(self.separator.get_timber()) - 1) or (timber_index < 0):
                print('[error] index out of range.')
                continue
            break

        self.print_countdown()
        spectrum = self.record()
        self.separator.set_dictionary(spectrum, timber_index, name=timber_name)
        print('finish change')

    def record(self):
        """録音する

        Returns:
            numpy.array -- スペクトル
        """
        counter = 0
        it = 0
        spectrum = np.zeros((self.chunk//2), dtype=np.float32)
        self.ac.clear_buffer()
        self.ac.start_stream()
        while counter < TIME:
            if self.ac.q.__len__() > 0:
                data = self.ac.q.popleft()
                spectrum += self.calc_spectrum(data)
                counter += self.ac.chunk / self.ac.rate
                it += 1
        self.ac.stop_stream()
        return spectrum / it

    def start_separate(self, executor):
        """スレッド処理を開始する

        Arguments:
            executor {conf.ThreadPoolExecutor} -- confインスタンス
        """
        self.timbers = self.separator.get_timber()
        if "noise" not in list(self.timbers.values()):
            self.timbers[len(self.timbers)] = "noise"
        msg = [len(self.timbers)]
        msg.extend([v for v in self.timbers.values()])
        self.osc.send(OSC_TIMBER_ADDR, msg)
        self.ac.clear_buffer()
        self.ac.start_stream()
        self.separate_flag = True
        self.sep_thread = executor.submit(self.separate_sound)
        self.osc_thread = executor.submit(self.send_result)

    def stop_separate(self, executor):
        """スレッド処理を停止する

        Arguments:
            executor {conf.ThreadPoolExecutor} -- confインスタンス
        """
        self.separate_flag = False
        self.sep_thread.result()
        self.sep_thread = None
        self.osc_thread.result()
        self.osc_thread = None
        self.ac.clear_buffer()
        self.ac.stop_stream()

    def separate_sound(self):
        """音源分離を行う"""
        while self.separate_flag:
            if self.ac.q.__len__() > 0:
                data = self.ac.q.popleft()
                spectrum = self.calc_spectrum(data)
                self.separate_results = self.separator.separate(spectrum)

    def send_result(self):
        """音源分離の結果を送信する"""
        while self.separate_flag:
            response = []
            if self.separate_results is None:
                continue
            if self.separate_results.shape[0] != len(self.timbers):
                continue
            for i, _ in enumerate(self.timbers.values()):
                response.append(self.separate_results[i][0])
            self.osc.send(OSC_RESULT_ADDR, response)
            time.sleep(OSC_FREQ)


if __name__ == "__main__":
    rtas = RealTimeAudioSeparator()
    rtas.setup()
    rtas.run()
