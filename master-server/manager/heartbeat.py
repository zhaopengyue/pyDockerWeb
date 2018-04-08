#!coding: utf-8
"""
本程序实现主服务的心跳服务器
心跳包由从服务在每个轮训后上传，主服务通过心跳包定时检测从服务状态并将其标记。采用UDP通信
"""
import sys
import socket
import threading
import time
import log
sys.path.append('..')
from tools import GlobalMap as Gl
from tools import md5_salt
from etc.sys_set import HEARTBEAT_PORT_VAR
from etc.sys_set import HEARTBEAT_TIMEOUT_VAR
from etc.sys_set import SERVICE_HOST_VAR
from etc.core_var import PATTERN_HOST_OBJ


_logger = log.Logging('heartbeat')
_logger.set_file('heartbeat.txt')


class Receive(threading.Thread):
    """接收类
    该类负责接收从服务发送的心跳请求并跟新状态信息,支持并发访问
    """
    def __init__(self, host, port):
        super(Receive, self).__init__()
        if not isinstance(host, str):
            raise KeyError('Host error.The host must be a string')
        if not isinstance(port, int):
            raise KeyError('Port error.The port must be a integer')
        if PATTERN_HOST_OBJ.match(host) is not None:
            self.host = host
        else:
            raise KeyError('Host error.The host may be like "127.0.0.1"')
        self.port = port
        # 设置UDP通信
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        self.sock.bind((self.host, self.port))
        _logger.write('心跳检测服务已启动', level='info')
        try:
            while True:
                key, address = self.sock.recvfrom(1024)
                receive_time = time.time()
                cluster_status_var = Gl.get_value('CLUSTER_STATUS_VAR', {})
                image_server_status_var = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
                # 若地址不在配置文件中,则该心跳无效,忽略请求
                if address[0] not in Gl.get_value('CLUSTER_ALL_HOSTS_VAR', []) \
                        and address[0] not in Gl.get_value('ALL_IMAGE_SERVER_HOST_VAR', []):
                    pass
                else:
                    type_ = key.split('%')[0]
                    if type_ != 'slave' and type_ != 'image':
                        continue
                    if not self._check_key(key):
                        continue
                    if type_ == 'slave':
                        if address[0] in cluster_status_var:
                            cluster_status_var[address[0]].update({'time': receive_time, 'status': True})
                        else:
                            cluster_status_var.update({address[0]: {'status': True, 'time': receive_time}})
                    else:
                        if address[0] in image_server_status_var:
                            image_server_status_var.get(address[0]).update({'time': receive_time, 'status': True})
                        else:
                            image_server_status_var.update({address[0]: {'status': True, 'time': receive_time}})
                Gl.set_value('CLUSTER_STATUS_VAR', cluster_status_var)
                Gl.set_value('IMAGE_SERVER_STATUS_VAR', image_server_status_var)
        finally:
            self.sock.close()

    def _check_key(self, message):
        if '%' not in message:
            return False
        if md5_salt(message.split('%')[0]) != message.split('%')[1]:
            return False
        return True


class Heartbeats(object):
    """心跳类

    负责定时检测所有节点并标记该节点状态
    """

    @staticmethod
    def check_timeout():
        while True:
            now_time = time.time()
            cluster_all_host_var = Gl.get_value('CLUSTER_ALL_HOSTS_VAR', [])
            cluster_status_var = Gl.get_value('CLUSTER_STATUS_VAR', {})
            image_server_status_var = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
            all_image_server_host = Gl.get_value('ALL_IMAGE_SERVER_HOST_VAR', [])
            if not cluster_all_host_var:
                raise ValueError('Value error.CLUSTER_ALL_HOSTS_VAR is not allowed to be empty.')
            for host in cluster_all_host_var:
                if host not in cluster_status_var:
                    cluster_status_var.update({host: {'status': False, 'time': 0}})
                else:
                    last_time = cluster_status_var.get(host).get('time')
                    if now_time - last_time > HEARTBEAT_TIMEOUT_VAR:
                        cluster_status_var.update({host: {'status': False, 'time': last_time}})
            if not all_image_server_host:
                raise ValueError('Value error.ALL_IMAGE_SERVER_HOST_VAR is not allowed to be empty.')
            for host in all_image_server_host:
                if host not in image_server_status_var:
                    image_server_status_var.update({host: {'status': False, 'time': 0}})
                else:
                    last_time = image_server_status_var.get(host).get('time')
                    if now_time - last_time > HEARTBEAT_TIMEOUT_VAR:
                        image_server_status_var.update({host: {'status': False, 'time': last_time}})
            Gl.set_value('IMAGE_SERVER_STATUS_VAR', image_server_status_var)
            Gl.set_value('CLUSTER_STATUS_VAR', cluster_status_var)
            # _logger.write('检查结果:' + cluster_status_var.__str__(), level='info')
            time.sleep(2)


def start_heartbeats():
    print '心跳服务运行中...'
    num_receivers = len(Gl.get_value('CLUSTER_ALL_HOSTS_VAR', [])) + len(Gl.get_value('ALL_IMAGE_SERVER_HOST_VAR', []))
    receivers = []
    for i in range(num_receivers):
        receiver = Receive(host=SERVICE_HOST_VAR, port=HEARTBEAT_PORT_VAR)
        receiver.setDaemon(True)
        receiver.start()
        receivers.append(receiver)
    try:
        Heartbeats.check_timeout()
    except KeyboardInterrupt:
        _logger.write('服务已停止', level='info')
        print 'Exited, OK'
