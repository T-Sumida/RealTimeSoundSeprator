# coding:utf-8

from pythonosc import udp_client

class OscClient:
    def __init__(self, ip, port):
        """コンストラクタ

        Arguments:
            ip {str} -- 宛先のIP
            port {int} -- 宛先のPORT
        """
        self.client = udp_client.SimpleUDPClient(
            ip, port
        )

    def send(self, addr, value):
        """送信する

        Arguments:
            value {list} -- 送信したい値
        """
        self.client.send_message(addr, value)
