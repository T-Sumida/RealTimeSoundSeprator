# coding:utf-8

import numpy as np
import copy


class Separator(object):
    def __init__(self, col, row, k):
        """コンストラクタ

        Arguments:
            col {int} -- 列数
            row {int} -- 行数
            k {int} -- 因子数
        """
        self.timber = {}
        self.algorithm = self.is_divergence
        self.k = k + 1
        self.row = row
        self.col = col
        self.dictionary = np.random.random_sample([col, self.k])
        self.activation = np.random.random_sample([self.k, row])

    def set_dictionary(self, data, k, name=None):
        """辞書行列を登録する

        Arguments:
            data {numpy.array} -- 登録するデータ
            k {int} -- 辞書のインデックス

        Keyword Arguments:
            name {str} -- 辞書の名前 (default: {None})

        Returns:
            bool -- 成功の可否
        """
        if k >= self.k:
            return False
        self.dictionary[:, k] = np.array(data, np.float32)
        if name is None:
            self.timber[k] = "timber:"+str(k)
        else:
            self.timber[k] = name
        return True

    def add_dictionary(self, data, name=None):
        """辞書にデータを追加する

        Arguments:
            data {numpy.array} -- 追加する辞書データ

        Keyword Arguments:
            name {str} -- 辞書の名前 (default: {None})
        """
        self.k += 1
        new_dict = np.random.random_sample([self.col, self.k])
        new_dict[:, 0:self.k-2] = self.dictionary[:, 0:self.k-2]
        new_dict[:, -1] = self.dictionary[:, -1]
        self.dictionary = new_dict
        self.dictionary[:, self.k-2] = np.array(data, np.float32)
        self.activation = np.random.random_sample([self.k, self.row])
        if name is None:
            self.timber[self.k-2] = "timber:"+str(self.k-1)
        else:
            self.timber[self.k-2] = name

    def separate(self, data, iter=10):
        """音源分離を行う

        Arguments:
            data {numpy.array} -- ターゲットデータ

        Keyword Arguments:
            iter {int} -- イテレーション回数 (default: {10})

        Returns:
            numpy.array -- 励起行列
        """
        data = data.reshape(self.col, 1)
        self.algorithm(data, iter)
        return self.activation

    def get_timber(self):
        """辞書名を返す

        Returns:
            list -- 辞書名
        """
        return self.timber

    def is_divergence(self, data, iter):
        """IS-divergence用のアルゴリズム

        Arguments:
            data {numpy.array} -- ターゲットデータ
            iter {int} -- イテレーション回数
        """
        for _ in range(iter):
            try:
                approx = np.dot(self.dictionary, self.activation)
                wt = np.ones([1, self.k], np.float32)
                w1 = data/approx
                w2 = np.transpose(self.dictionary)/sum(np.transpose(approx[:]))

                wh = np.dot(w2, w1)
                wt[:] = sum(np.transpose(w2[:]))
                wt = np.transpose(wt)

                wt[wt == 0.0] = 1.0e-5
                bias = wh/wt

                self.activation = self.activation * np.sqrt(bias)

                approx = np.dot(self.dictionary, self.activation)
                w1 = data/approx
                w2 = self.activation/sum(approx[:])

                wh = np.dot(w1,np.transpose(w2))
                wt = sum(np.transpose(w2[:]))
                wt[wt == 0.0] = 1.0e-5

                bias = wh/wt
                self.dictionary[:, self.k-1] = self.dictionary[:, self.k-1] * bias[:, self.k-1]

                if np.sum(approx) > np.sum(data):
                    self.activation *= np.sum(data)/np.sum(approx)
                # self.dictionary[:, self.k-1] /= sum(self.dictionary[:, self.k-1])
            except:
                self.activation = np.random.random_sample([self.k, self.row])

    def euc_divergence(self, data, iter):
        """EUC-divergence用のアルゴリズム

        Arguments:
            data {numpy.array} -- ターゲットデータ
            iter {int} -- イテレーション回数
        """
        for _ in range(iter):
            try:
                approx = np.dot(self.dictionary, self.activation)
                wh = np.dot(np.transpose(self.dictionary) , data)
                wt = np.dot(np.transpose(self.dictionary) , approx)

                wt[wt == 0.0] = 1.0e-5
                bias = wh/wt

                self.activation = self.activation * bias

                approx = np.dot(self.dictionary,self.activation)
                wh = np.dot(data,np.transpose(self.activation))
                wt = np.dot(approx,np.transpose(self.activation))
                wt[wt == 0.0] = 1.0e-5

                bias = wh/wt
                self.dictionary[:, self.k-1] = self.dictionary[:, self.k-1] * bias[:, self.k-1]
                self.dictionary[:, self.k-1] /= sum(self.dictionary[:, self.k-1])
            except:
                self.activation = np.random.random_sample([self.k, self.row])

    def kl_divergence(self, data, iter):
        """KL-divergence用のアルゴリズム

        Arguments:
            data {numpy.array} -- ターゲットデータ
            iter {int} -- イテレーション回数
        """
        for _ in range(iter):
            try:
                approx = np.dot(self.dictionary, self.activation)
                w = data/approx
                wh = np.dot(np.transpose(self.dictionary), w)

                wt = np.ones([1, self.k], dtype=np.float32)
                wt[:] = np.sum(self.dictionary[:, :])
                wt = np.transpose(wt)
                wt[wt == 0.0] = 1.0e-5
                bias = wh/wt
                self.activation = self.activation * bias

                approx = np.dot(self.dictionary, self.activation)
                w = data/approx
                wh = np.dot(w,np.transpose(self.activation))

                wt = np.ones([self.k,1],np.float32)
                wt = np.sum(np.transpose(self.activation[:]))
                wt = np.transpose(wt)
                wt[wt == 0.0] = 1.0e-5
                bias = wh/wt
                self.dictionary[:, self.k-1] = self.dictionary[:, self.k-1] * bias[:, self.k-1]
                if np.sum(approx) > np.sum(data):
                    self.activation *= np.sum(data)/np.sum(approx)
            except:
                self.activation = np.random.random_sample([self.k, self.row])

