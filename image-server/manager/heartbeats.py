# coding=utf-8
"""
本程序实现从服务的心跳机制
"""
import random
import string
import sys
import threading
from socket import *

import time

from manager.tools import md5_salt
sys.path.append('..')
from etc.sys_set import SERVICE_HOST_VAR
from etc.sys_set import HEARTBEAT_PORT_VAR
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
                s = socket(AF_INET, SOCK_DGRAM)
                s.connect((SERVICE_HOST_VAR, HEARTBEAT_PORT_VAR))
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