#!coding: utf-8
"""
本程序负责轮训服务,获取当前节点信息保存并发送心跳包到主节点
"""
import threading
import time

import log
from heartbeats import SlaveHeartbeats
from node import Containers
from node import Images


class Rotating(threading.Thread):
    """
    轮训服务
    """

    def __init__(self):
        super(Rotating, self).__init__()
        self._logger = log.Logging('rotating')
        self._logger.set_file('rotating_info.txt')
        self.containers = Containers()
        self.images = Images()

    def run(self):
        while True:
            # Gl.clean()
            # Gl.set_value('refresh_time', datetime.datetime.now().strftime('%c'))
            # Gl.set_value('cpu_info', System.get_cpu_info())
            # Gl.set_value('mem_info', System.get_mem_info())
            # Gl.set_value('disk_info', System.get_disk_info())
            # Gl.set_value('container_list', self.containers.get_list())
            # Gl.set_value('image_list', self.images.get_list())
            SlaveHeartbeats().start()
            time.sleep(2)


Rotating().start()
