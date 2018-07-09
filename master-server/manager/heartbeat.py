#!coding: utf-8
"""
本程序实现主服务的心跳服务器
心跳包由从服务在每个轮训后上传，主服务通过心跳包定时检测从服务状态并将其标记。采用UDP通信
"""
import socket
import threading
import time
import choose
from manager import log
from manager.tools import GlobalMap as Gl
from manager.tools import md5_salt
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
                host = address[0]
                # 集群所有从节点IP列表
                cluster_all_host_var = Gl.get_value('CLUSTER_ALL_HOSTS_VAR', [])
                # 集群所有镜像服务器列表
                all_image_server_host_var = Gl.get_value('ALL_IMAGE_SERVER_HOST_VAR', [])
                # 集群从节点信息列表
                cluster_all_info_var = Gl.get_value('CLUSTER_ALL_INFO_VAR', {})
                # 集群镜像服务器信息列表
                all_image_server_info_var = Gl.get_value('ALL_IMAGE_SERVER_INFO_VAR', {})
                # 从节点状态字典
                cluster_status_var = Gl.get_value('CLUSTER_STATUS_VAR', {})
                # 镜像服务器字典
                image_server_status_var = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
                # 集群ID列表
                cluster_all_id = Gl.get_value('CLUSTER_ALL_ID_VAR', [])
                # 集群空闲ID列表
                cluster_free_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
                try:
                    type_, hostname, cluster_id_or_registry_server_port = key.split('%')[0].split('|')
                    print hostname
                    hostname += '({host_end})'.format(host_end=host.split('.')[-1])
                except ValueError:
                    continue
                # 检查节点类型
                if type_ != 'slave' and type_ != 'image':
                    continue
                # 检查密钥是否正确
                if not self._check_key(key):
                    continue
                if type_ == 'slave':
                    # 如果是新加入的机器
                    if host not in cluster_all_host_var:
                        # 修改集群配置相关项目
                        cluster_all_host_var.append(host)
                        # 检查节点所发送的集群id是否存在, 不存在时创建新集群
                        if cluster_id_or_registry_server_port in cluster_all_info_var:
                            if 'node' in cluster_all_info_var[cluster_id_or_registry_server_port]:
                                cluster_all_info_var[cluster_id_or_registry_server_port]['node'].append({
                                    'name': hostname,
                                    'host': host
                                })
                            else:
                                cluster_all_info_var[cluster_id_or_registry_server_port].update({
                                    'node': [{
                                        'name': hostname,
                                        'host': host
                                    }]
                                })
                        else:
                            cluster_all_info_var.update({
                                cluster_id_or_registry_server_port: {'node': [{'name': hostname, 'host': host}]}
                            })
                            cluster_all_id.append(cluster_id_or_registry_server_port)
                            cluster_free_id.append(cluster_id_or_registry_server_port)
                    # 修改节点状态
                    if host in cluster_status_var:
                        cluster_status_var[host].update({'time': receive_time, 'status': True})
                    else:
                        cluster_status_var.update({host: {'status': True, 'time': receive_time}})
                elif type_ == 'image':
                    # 若为新加入的镜像服务器, 修改相关信息
                    if host not in all_image_server_host_var:
                        all_image_server_host_var.append(host)
                        all_image_server_info_var.update({host: {'registry_port': cluster_id_or_registry_server_port}})
                    # 修改节点状态
                    if host in image_server_status_var:
                        image_server_status_var[host].update({'time': receive_time, 'status': True})
                    else:
                        image_server_status_var.update({host: {'status': True, 'time': receive_time}})
                else:
                    pass
                # 写入数据
                Gl.set_value('CLUSTER_STATUS_VAR', cluster_status_var)
                Gl.set_value('IMAGE_SERVER_STATUS_VAR', image_server_status_var)
                Gl.set_value('CLUSTER_ALL_HOSTS_VAR', cluster_all_host_var)
                Gl.set_value('ALL_IMAGE_SERVER_HOST_VAR', all_image_server_host_var)
                Gl.set_value('CLUSTER_ALL_INFO_VAR', cluster_all_info_var)
                Gl.set_value('CLUSTER_FREE_ID_VAR', cluster_free_id)
                Gl.set_value('CLUSTER_ALL_ID_VAR', cluster_all_id)
                Gl.set_value('ALL_IMAGE_SERVER_INFO_VAR', all_image_server_info_var)
        finally:
            self.sock.close()

    @staticmethod
    def _check_key(message):
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
            # if not cluster_all_host_var:
            #     raise ValueError('Value error.CLUSTER_ALL_HOSTS_VAR is not allowed to be empty.')
            for host in cluster_all_host_var:
                if host not in cluster_status_var:
                    cluster_status_var.update({host: {'status': False, 'time': 0}})
                else:
                    last_time = cluster_status_var.get(host).get('time')
                    if now_time - last_time > HEARTBEAT_TIMEOUT_VAR:
                        cluster_status_var.update({host: {'status': False, 'time': last_time}})
            # if not all_image_server_host:
            #     raise ValueError('Value error.ALL_IMAGE_SERVER_HOST_VAR is not allowed to be empty.')
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
    # +1防止两者皆为0
    num_receivers = len(Gl.get_value('CLUSTER_ALL_HOSTS_VAR', [])) + len(Gl.get_value('ALL_IMAGE_SERVER_HOST_VAR', [])) + 1
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
