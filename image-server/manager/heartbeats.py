# coding=utf-8
"""
本程序实现从服务的心跳机制
"""
import random
import string
import sys
import requests
import threading
from socket import *
sys.path.append('..')
from etc.sys_set import PRIVATE_REGISTRY_PORT, IMAGE_SERVICE_PORT_VAR
import time

from manager.tools import md5_salt
sys.path.append('..')
from etc.sys_set import SERVICE_HOST_VAR
from etc.sys_set import HEARTBEAT_PORT_VAR
from etc.sys_set import HARBOR_URL
from etc.core_var import PATTERN_HOST_OBJ


class SlaveHeartbeats(threading.Thread):

    def run(self):
        """ 向指定节点发送心跳信号

        :return:
        """
        while True:
            if not isinstance(SERVICE_HOST_VAR, str):
                raise KeyError('Host error.The host must be a string')
            if not isinstance(HEARTBEAT_PORT_VAR, int):
                raise KeyError('Port error.The port must be a integer')
            if PATTERN_HOST_OBJ.match(SERVICE_HOST_VAR) is None:
                raise KeyError('Host error.The host may be like "127.0.0.1"')
            try:
                # 检测私有镜像服务是否在线
                if self.check_server():
                    s = socket(AF_INET, SOCK_DGRAM)
                    s.connect((SERVICE_HOST_VAR, HEARTBEAT_PORT_VAR))
                else:
                    time.sleep(2)
                    continue
            except gaierror, e:
                print "Address-related error connecting to server: %s" % e
                sys.exit(1)
            except error, e:
                print "Connection error: %s" % e
                sys.exit(1)
            # message = random.choice(string.ascii_letters) * random.randint(1, 10)
            message = 'image'
            try:
                encryption_message = md5_salt(message)
                s.sendall(message + '%' + encryption_message)
                s.close()
            except error, e:
                print "Error sending data: %s" % e
                s.close()
                sys.exit(1)
            time.sleep(2)

    @staticmethod
    def check_server():
        """ 检查私有仓库及镜像响应服务运行状态

        :return:bool值
        """
        status = False
        # 检测官方私有仓库(已停用)
        # registry_url = 'http://127.0.0.1:' + str(PRIVATE_REGISTRY_PORT)
        # 检测harbor仓库
        registry_url = HARBOR_URL
        response_url = 'http://127.0.0.1:' + str(IMAGE_SERVICE_PORT_VAR) + '/healthy/'
        try:
            rg_obj = requests.get(registry_url)
            rs_obj = requests.get(response_url)
            if rg_obj.status_code == 200 and rs_obj.status_code == 200:
                status = True
        except requests.ConnectionError:
            pass
        return status
