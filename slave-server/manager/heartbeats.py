# coding=utf-8
"""
本程序实现从服务的心跳机制
"""
import random
import string
import sys
import os
import threading
from socket import *
import time
import requests
import log
from manager.tools import md5_salt
sys.path.append('..')
from etc.sys_set import SERVICE_HOST_VAR
from etc.sys_set import SLAVE_SERVICE_PORT_VAR
from etc.sys_set import HEARTBEAT_PORT_VAR
from etc.core_var import PATTERN_HOST_OBJ


_logger = log.Logging('heartbeat')
_logger.set_file('heartbeat.txt')


class SlaveHeartbeats(threading.Thread):

    def __init__(self):
        super(SlaveHeartbeats, self).__init__()
        self.signal = True

    def set_kill(self):
        self.signal = False

    @staticmethod
    def get_hostname():
        """ 获取主机hostname

        :return:
        """
        os_sys = os.name
        if os_sys == 'nt':
            hostname = os.getenv('computername')
            return hostname
        elif os_sys == 'posix':
            host = os.popen('hostname')
            try:
                hostname = host.read().split('\n')[0]
                if not hostname:
                    hostname = 'UnKnow'
                return hostname
            finally:
                host.close()
        else:
            return 'UnKnow'

    def run(self):
        """ 向指定节点发送心跳信号

        :return:
        """
        while self.signal:
            if not isinstance(SERVICE_HOST_VAR, str):
                raise KeyError('Host error.The host must be a string')
            if not isinstance(HEARTBEAT_PORT_VAR, int):
                raise KeyError('Port error.The port must be a integer')
            if PATTERN_HOST_OBJ.match(SERVICE_HOST_VAR) is None:
                raise KeyError('Host error.The host may be like "127.0.0.1"')
            try:
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
            hostname = self.get_hostname()
            message = 'slave|{hostname}|{cluster_id}'.format(hostname=hostname, cluster_id=SERVICE_HOST_VAR)
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
        """ 检查从节点响应服务运行状态

        :return:
        """
        status = False
        response_url = 'http://127.0.0.1:' + str(SLAVE_SERVICE_PORT_VAR) + '/healthy/'
        try:
            rs_obj = requests.get(response_url)
            if rs_obj.status_code == 200:
                status = True
        except requests.ConnectionError:
            pass
        return status


def start_heartbeats():
    print '心跳服务运行中'
    _logger.write('心跳检测服务已启动', level='info')
    heartbeat = SlaveHeartbeats()
    heartbeat.setDaemon(True)
    heartbeat.start()
    print '心跳服务已启动'
