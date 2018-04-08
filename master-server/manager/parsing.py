#!coding: utf-8
"""
本程序实现集群信息的读入,验证,组合
"""
import sys
import log
from tools import GlobalMap as Gl
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
sys.path.append('..')
from etc.core_var import CLUSTER_XML_PATH
from etc.core_var import PATTERN_HOST_OBJ
from etc.sys_set import IMAGE_SERVER_LIST

_logger = log.Logging('parsing')
_logger.set_file('parsing.txt')


class Parsing(object):

    def __init__(self):
        try:
            self.tree = ET.parse(CLUSTER_XML_PATH)
            _logger.write(CLUSTER_XML_PATH + ' 格式校验成功', level='info')
        except ET.ParseError:
            _logger.write(CLUSTER_XML_PATH + ' 格式错误', level='error')
            raise ET.ParseError(CLUSTER_XML_PATH + ' Invalid format')
        self.cluster_root = self.tree.getroot()

    def load(self):
        cluster = {}
        temp_cluster_all_id = []
        temp_cluster_all_hosts = []
        temp_cluster_all_hosts_name = []
        temp_cluster_num = 0
        temp_cluster_free_id = []
        try:
            _logger.write('开始读取文件配置', level='info')
            for cluster_info in self.cluster_root:
                temp_cluster_num += 1
                temp_cluster_id = cluster_info.find('host').text
                temp_cluster_all_id.append(str(temp_cluster_id))
                temp_cluster_free_id.append(str(temp_cluster_id))
                temp_cluster_describe = cluster_info.find('describe').text
                temp_cluster_server_port = cluster_info.find('port').text
                temp_cluster_nodes = []
                for cluster_node in cluster_info.findall('node'):
                    temp_cluster_node = {'host': cluster_node.find('host').text}
                    if PATTERN_HOST_OBJ.match(temp_cluster_node['host']) is None:
                        raise KeyError('Host error.The host may be like "127.0.0.1"')
                    temp_cluster_node['name'] = cluster_node.find('name').text
                    temp_cluster_node['account'] = cluster_node.find('account').text
                    temp_cluster_node['password'] = cluster_node.find('password').text
                    temp_cluster_node['server_path'] = cluster_node.find('server_path').text
                    if temp_cluster_node['host'] in temp_cluster_all_hosts:
                        _logger.write('Host必须唯一', level='error')
                        raise ValueError('host must be unique.')
                    else:
                        temp_cluster_all_hosts.append(temp_cluster_node['host'])
                    if temp_cluster_node['name'] in temp_cluster_all_hosts_name:
                        _logger.write('Host name 必须唯一', level='error')
                        raise ValueError('host name must be unique.')
                    temp_cluster_nodes.append(temp_cluster_node)
                cluster.update({temp_cluster_id: {'port': temp_cluster_server_port, 'describe': temp_cluster_describe, 'node': temp_cluster_nodes}})
            _logger.write('cluster_set.xml文件配置读取成功', level='info')
            # 读取教师服务器列表
            try:
                temp_all_image_server_host = []
                for image_server in IMAGE_SERVER_LIST:
                    image_server_host = image_server[0]
                    if PATTERN_HOST_OBJ.match(image_server_host) is None:
                        raise KeyError('Host error.The host may be like "127.0.0.1"')
                    temp_all_image_server_host.append(image_server[0])
            except IndexError:
                _logger.write('镜像服务器列表格式错误')
                raise ValueError('IMAGE_SERVER_LIST form is error')
        except AttributeError:
            _logger.write(CLUSTER_XML_PATH + ' 属性错误', level='error')
            raise AttributeError('File attribute error.')
        # 以下代码保证xml文件中只有一个集群,主服务在教师机时删除如下代码
        if temp_cluster_num != 1:
            _logger.write('仅可拥有一个集群.', level='error')
            raise ValueError('Error value. The number of clusters is allowed only 1.')
        _logger.write('开始写入文件', level='info')
        Gl.set_value('CLUSTER_ALL_HOSTS_VAR', temp_cluster_all_hosts)
        Gl.set_value('CLUSTER_ALL_ID_VAR', temp_cluster_all_id)
        Gl.set_value('CLUSTER_ALL_INFO_VAR', cluster)
        Gl.set_value('CLUSTER_FREE_ID_VAR', temp_cluster_free_id)
        Gl.set_value('ALL_IMAGE_SERVER_HOST_VAR', temp_all_image_server_host)
        _logger.write('文件写入完成', level='info')