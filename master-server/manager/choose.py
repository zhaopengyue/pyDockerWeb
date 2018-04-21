#!coding: utf-8
"""
本程序实现集群的选取分配及注销
"""
import threading
from manager.tools import GlobalMap as Gl
from manager.log import Logging

_logger = Logging('choose')
_logger.set_file('choose.txt', mode='a')


class Choose(object):

    _choose_lock = threading.Lock()

    @staticmethod
    def choose_free_cluster():
        """选择集群

        返回一个空闲集群id及其下属的所有节点信息(host, username, password)
        本方法为原子方法,同时仅允许一个线程操作本方法

        :return: 字典形式：{'cluster_id': '', 'node': [{'host': '', 'account': '', 'password': '', 'name': ''}], 'describe': ''} or None
        """
        Choose._choose_lock.acquire()
        cluster_all_info = Gl.get_value('CLUSTER_ALL_INFO_VAR', {})
        cluster_free_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
        cluster = {}
        try:
            cluster_id = cluster_free_id.pop()
            cluster['cluster_id'] = cluster_id
            cluster['node'] = cluster_all_info.get(cluster_id).get('node')
            cluster['describe'] = cluster_all_info.get(cluster_id).get('describe')
            _logger.write('集群选择成功.集群ID: ', level='info')
        except IndexError:
            cluster = None
            _logger.write('集群选择失败: 无空闲集群', level='warn')
        Gl.set_value('CLUSTER_FREE_ID_VAR', cluster_free_id)
        Choose._choose_lock.release()
        return cluster

    @staticmethod
    def add_free_cluster(cluster_id):
        """标记集群为空闲

        将指定集群标记为空闲

        :param cluster_id: 集群ID
        :return: Boolean：标记执行状态
        """
        cluster_all_id = Gl.get_value('CLUSTER_ALL_ID_VAR', [])
        cluster_free_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
        bool_status = True
        if cluster_id in cluster_free_id:
            _logger.write('集群标记失败: 该集群已空闲', level='warn')
            bool_status = False
        if cluster_id not in cluster_all_id:
            _logger.write('集群标记失败: 集群ID不存在', level='warn')
            bool_status = False
        if bool_status:
            cluster_free_id.append(cluster_id)
            Gl.set_value('CLUSTER_FREE_ID_VAR', cluster_free_id)
        return bool_status