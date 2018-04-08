#!coding: utf-8
"""
本程序封装了主从通信模块,即主服务向从服务发送操作请求
"""
import json
import sys
import re
import requests
import log
from requests.exceptions import ConnectionError
from tools import GlobalMap as Gl
sys.path.append('..')
from etc.sys_set import SLAVE_SERVICE_PORT_VAR
from etc.sys_set import IMAGE_SERVER_LIST


_root_url = 'http://{host}:{port}/{root_path}/{type_path}'
_logger = log.Logging('communication')
_logger.set_file('communication.txt')


class Container(object):
    """
    容器操作类
    """

    @staticmethod
    def get_all_containers(cluster_id):
        """获取容器列表,获取所有容器列表

        构建url请求,向指定从节点发送获取容器列表请求

        :param cluster_id: 要获取的集群ID
        :return:
        {
            "host1" : {
                "status": ,
                "refresh": ,请求回执, status为True时才可显示
                "url": ,    请求url, status为True时才可显示
                "message": [
                    {
                        message: {
                            'id': 容器id,
                            'short_id': 容器短id,
                            'status': 容器状态,
                            'running': 容器是否在运行,
                            'finishedAt': 容器退出时间,
                            'startedAt': 容器开始时间,
                            'created': 容器创建日期
                            'image': 容器依赖镜像,
                            'exit_time': 容器退出时间.
                        },
                        'status': bool
                    },...
                ]
            },
            "host2": {
                ...
            }, ...
        } or (部分节点无效时)
        {
            "host1": {
                "status": ,
                "message": error_reason
            },
            "host2": {
                ...
            }
        } or (集群不可用或未找到)
        {}
        """
        containers_dict = {}
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        cluster_all_id = Gl.get_value('CLUSTER_ALL_ID_VAR', [])
        cluster_all_info = Gl.get_value('CLUSTER_ALL_INFO_VAR', {})
        if cluster_id not in cluster_all_id:
            _logger.write('集群ID: \'' + cluster_id + '\'未找到', 'warn')
            return {}
        for node in cluster_all_info.get(cluster_id).get('node'):
            node_host = node.get('host')
            if node_host not in cluster_status or not cluster_status.get(node_host).get('status'):
                continue
            rq_url = _root_url.format(
                host=node_host,
                port=SLAVE_SERVICE_PORT_VAR,
                root_path='container',
                type_path='_all'
            )
            try:
                rq_obj = requests.get(rq_url)
                rq_result = json.loads(rq_obj.text)
            except ConnectionError:
                _logger.write(str(node_host) + '连接失败', 'warn')
                rq_result = {'message': str(node_host) + ' connect fail', 'status': False}
            containers_dict.update({node_host: rq_result})
        return containers_dict

    @staticmethod
    def get_container(host):
        """获取单个节点容器信息

        由于每个Host仅可属于一个集群,故只需提供Host而无需提供集群ID

        :param host: 要查询的节点Host
        :return:
        {
            "message":[
                {
                    message: {
                        'id': 容器id,
                        'short_id': 容器短id,
                        'status': 容器状态,
                        'paused': 容器是否暂停,
                        'running': 容器是否在运行,
                        'finishedAt': 容器退出时间,
                        'startedAt': 容器开始时间,
                        'created': 容器创建日期
                        'image': 容器依赖镜像,
                        'exit_time': 容器退出时间.
                    },
                },
                {
                    ...
                },...
            ],
            "status": bool,
            "refresh": ,
            "url":
        } or
        {
            "message": error_reason,
            "status":
        }
        """
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        cluster_all_hosts = Gl.get_value('CLUSTER_ALL_HOSTS_VAR', [])
        if host not in cluster_all_hosts:
            _logger.write('节点Host: \'' + host + '\'无效', level='warn')
            return {'message': 'host unavailable', 'status': False}
        if host not in cluster_status or not cluster_status.get(host).get('status'):
            return {'message': 'type error', 'status': False}
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='container',
            type_path='_all'
        )
        try:
            rq_obj = requests.get(rq_url)
            containers_list = json.loads(rq_obj.text)
        except ConnectionError:
            _logger.write(str(host) + '连接失败', 'warn')
            return {'message': 'node connect fail', 'status': False}
        return containers_list

    @staticmethod
    def operator_container(host, action_type, container_id_or_name, **kwargs):
        """ 操作容器

        包含容器的启动,停止,重命名,构建,log,重启等操作

        :param host: 节点ip
        :param container_id_or_name: .str
        :param action_type: 操作类型,值可以为 .str
                kill: 可附带参数
                            signal, .str(信号.默认值为None)
                start:
                stop: 可附带单数为
                            timeout, .int(默认值为10)
                restart: 可附带单数为
                            timeout, .int(默认值为10)
                rename: 必须附带参数
                            new_name .str(新的镜像名)
                pause:
                logs: 可附带参数为
                            stderr .bool(标准错误流.默认True);
                            stdout .bool(标准输出流.默认True);
                            timestamps .bool(是否输出时间.默认True)
                commit: 可选附带参数为
                            repository .str;
                            tag .str;
                            changes: .str;
                            author: .str;
                            message: .str
                remove: 可选附带参数为
                            v: .bool(是否删除数据卷 )
                            link: .bool(是否删除连接容器)
                            force: .bool(是否强制删除)
                unpause:
                start:
        :param kwargs 以上所列附带参数
        :return:
        {
            "message": ,  #请求结果.str
            "status": ,   #执行状态.bool
            "url": ,      #请求url.str
            "refresh":    #请求回执时间.str
        } or
        {
            "message": error_reason,.str
            "status": False.bool
        }
        """
        _allow_action = ['start', 'stop', 'restart', 'rename', 'logs', 'pause', 'commit', 'kill', 'remove', 'unpause']
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        if action_type not in _allow_action or host not in cluster_status or not cluster_status.get(host).get('status'):
            _logger.write('节点Host: \'' + str(host) + '\'无效或本Host不可用', level='warn')
            return {'message': 'host unavailable', 'status': False}
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='container',
            type_path=''
        )
        if 'type' in kwargs or 'container_id_or_name' in kwargs:
            return {'message': 'type error', 'status': False}
        rq_args = {'type': action_type, 'container_id_or_name': container_id_or_name}
        rq_args.update(kwargs)
        try:
            rq_obj = requests.post(rq_url, json=rq_args)
            exec_result = json.loads(rq_obj.text)
            return exec_result
        except ConnectionError:
            _logger.write(str(host) + '连接失败', 'warn')
            return {'message': 'host connect fail', 'status': False}

    @staticmethod
    def create_container_shell(host, cmd):
        """ 创建容器

        创建容器的命令行模式, 通过shell语句创建
        eg: docker create ***

        :param host: 执行节点
        :param cmd:
        :return:
        {
            "message": , error_reason or container_id
            "status": ,
            'url': ,
            'refresh':
        }
        """
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        if host not in cluster_status or not cluster_status.get(host).get('status'):
            _logger.write('节点Host: \'' + host + '\'无效或本Host不可用', level='warn')
            return {'message': 'host unavailable', 'status': False}
        pattern_cmd = '^docker\s+(run|create)\s+.*'
        if re.match(pattern_cmd, cmd) is None:
            _logger.write('执行出错: 命令不合法', level='warn')
            return {'message': 'illegal command', 'status': False}
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='container',
            type_path=''
        )
        rq_args = {'type': 'create_shell', 'shell_cmd': cmd}
        try:
            rq_obj = requests.post(rq_url, json=rq_args)
            exec_result = json.loads(rq_obj.text)
            return exec_result
        except ConnectionError:
            _logger.write(str(host) + '连接失败', 'warn')
            return {'message': 'host connect fail', 'status': False}

    # @staticmethod
    # def create_container_args(host, **args):
    #     """ 创建容器
    #
    #     创建容器的点选式模式,通过docker python api创建
    #
    #     :param host: 执行节点
    #     :param args:
    #     待定
    #     :return: container id or Node
    #     """
    #     pass


class Image(object):
    """
    镜像操作类
    """

    @staticmethod
    def get_all_images(cluster_id):
        """

        :param cluster_id: 集群ID
        :return:
        {
            "host1" : {
                "status": ,
                "refresh": ,
                "url": ,
                "message": [
                    {
                        "message":{
                            'id': 镜像id,
                            'short_id': 镜像短id,
                            'tags': 镜像标签列表,
                            'created': 镜像创建日期,
                            'size': 镜像大小,
                            'os': 镜像系统
                        } or err_reason,
                    },...
                ]
            },
            "host2": {
                ...
            }, ...
        } or
        {
            "host1": {
                "status":,
                "message": error_reason,
            },
            "host2": {
                "status":,
                "message": error_reason
            },
            ...
        } or
        {

        }
        """
        images_dict = {}
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        cluster_all_id = Gl.get_value('CLUSTER_ALL_ID_VAR', [])
        cluster_all_info = Gl.get_value('CLUSTER_ALL_INFO_VAR', {})
        if cluster_id not in cluster_all_id:
            _logger.write('集群ID: \'' + cluster_id + '\'未找到', 'warn')
            return {'message': 'node unavailable', 'status': False}
        for node in cluster_all_info.get(cluster_id).get('node'):
            node_host = node.get('host')
            if node_host not in cluster_status or not cluster_status.get(node_host).get('status'):
                continue
            rq_url = _root_url.format(
                host=node_host,
                port=SLAVE_SERVICE_PORT_VAR,
                root_path='image',
                type_path='_all'
            )
            try:
                rq_obj = requests.get(rq_url)
                rq_result = json.loads(rq_obj.text)
            except ConnectionError:
                _logger.write(str(node_host) + '连接失败', 'warn')
                rq_result = {'message': 'node connect fail', 'status': False}
            images_dict.update({node_host: rq_result})
        return images_dict

    @staticmethod
    def get_image(host):
        """获取单个节点容器信息

        由于每个Host仅可属于一个集群,故只需提供Host而无需提供集群ID

        :param host: 要查询的节点Host
        :return:
        {
        "message":[{
            "message":{
                    'id': 镜像id,
                    'short_id': 镜像短id,
                    'tags': 镜像标签列表,
                    'created': 镜像创建日期,
                    'size': 镜像大小,
                    'os': 镜像系统
                } or err_reason,
            "status": bool.执行状态
            },...
            ],
        "status": bool
        }
        """
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        cluster_all_hosts = Gl.get_value('CLUSTER_ALL_HOSTS_VAR', [])
        if host not in cluster_all_hosts:
            _logger.write('节点Host: \'' + host + '\'无效', level='warn')
            return {'message': 'node unavailable', 'status': False}
        if host not in cluster_status or not cluster_status.get(host).get('status'):
            return {'message': 'node unavailable', 'status': False}
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='image',
            type_path='_all'
        )
        try:
            rq_obj = requests.get(rq_url)
            images_info = json.loads(rq_obj.text)
        except ConnectionError:
            _logger.write(str(host) + '连接失败', 'warn')
            return {'message': 'node connect fail', 'status': False}
        return images_info

    @staticmethod
    def operator_image(host, action_type, image_id_or_name, **kwargs):
        """ 操作镜像

        包含镜像的删除, 查询, tag

        :param image_id_or_name: 镜像id或镜像名 .str
        :param action_type: 操作类型.允许值为remove, tag, search .str
                    remove: 可附加变量为
                            force .bool(是否强制删除.默认值为False)
                    search:
                    tag: 可附加变量为
                            repository .str(表示镜像名);
                            tag .str(表示版本,默认值None);
                            force .bool(表示是否强制更改,默认值None)
        :param host: 节点ip
        :param kwargs: 以上可附加变量
        :return:
        {
            "message":'ok' or err_reason,
            "status": .bool(执行状态)
            "url": .str(请求url,status 为True时显示)
            "refresh": .str(请求回执时间 ,status为True时显示)
        }
        """
        _allow_action = ['remove', 'tag', 'search']
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        if action_type not in _allow_action or host not in cluster_status or not cluster_status.get(host).get('status'):
            _logger.write('节点Host: \'' + host + '\'无效或本Host不可用', level='warn')
            return {'message': 'node unavailable', 'status': False}
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='image',
            type_path=''
        )
        if 'type' in kwargs or 'image_id_or_name' in kwargs:
            return {'message': 'type error', 'status': False}
        rq_args = {'type': action_type, 'image_id_or_name': image_id_or_name}
        rq_args.update(kwargs)
        try:
            rq_obj = requests.post(rq_url, json=rq_args)
            exec_result = json.loads(rq_obj.text)
            return exec_result
        except ConnectionError:
            _logger.write(str(host) + '连接失败', 'warn')
            return {'message': 'connect fail', 'status': False}

    @staticmethod
    def download_image(download_to_host, image_server_host, repository):
        """ 下载镜像

        从远程镜像仓库下载镜像

        :param image_server_host: 镜像服务器ip
        :param download_to_host: 要下载镜像的节点
        :param repository: 所要下载的镜像名,包含镜像tag
        :return:
        {
            "message": ,
            "status": ,
            "refresh": ,
            "url":
        } or
        {
            "message": ,
            "status":
        }
        """
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        image_server_status = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
        image_server_port = None
        if download_to_host not in cluster_status or not cluster_status.get(download_to_host).get('status'):
            _logger.write('节点Host: \'' + str(download_to_host) + '\'无效或本Host不可用', level='warn')
            return {'message': 'node unavailable', 'status': False}
        if image_server_host not in image_server_status or not image_server_status.get(image_server_host).get('status'):
            _logger.write('镜像服务器Host: \'' + str(image_server_host) + '\'无效或本Host不可用', level='warn')
            return {'message': 'image server unavailable', 'status': False}
        for server in IMAGE_SERVER_LIST:
            if server[0] == image_server_host:
                image_server_port = server[1]
        if not image_server_port:
            return {'message': 'image server not found', 'status': False}
        # 提取tag
        try:
            repository_tag = repository.split(':')[1]
        except IndexError:
            repository_tag = None
        # 拼接仓库名
        repository = image_server_host + ':' + str(image_server_port) + '/' + repository
        rq_url = _root_url.format(
            host=download_to_host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='image',
            type_path=''
        )
        rq_args = {
            'repository': repository,
            'tag':  repository_tag,
            'type': 'pull'
        }
        try:
            rq_obj = requests.post(rq_url, json=rq_args)
            exec_result = json.loads(rq_obj.text)
        except ConnectionError:
            _logger.write(str(download_to_host) + '连接失败', 'warn')
            exec_result = {'message': 'host connect fail', 'status': False}
        return exec_result

    @staticmethod
    def get_image_server_list():
        """ 返回镜像服务器列表

        :return:
        """
        return {'message': IMAGE_SERVER_LIST, 'status': True}

    @staticmethod
    def get_alive_image_server_list():
        info = []
        image_server_status = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
        for image_server in IMAGE_SERVER_LIST:
            if image_server[0] not in image_server_status or not image_server_status.get(image_server[0]).get('status'):
                continue
            info.append(image_server)
        if info.__len__() > 0:
            return {'message': info, 'status': True}
        else:
            return {'message': info, 'status': False}


    @staticmethod
    def get_image_server(image_server):
        """ 获取镜像服务器所在节点的镜像列表

        :param image_server:  镜像服务器IP
        :return:
        """
        image_server_port = None
        image_server_status = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
        if image_server not in image_server_status or not image_server_status.get(image_server).get('status'):
            _logger.write('镜像服务器Host: \'' + str(image_server) + '\'无效或本Host不可用', level='warn')
            return {'message': 'image server unavailable', 'status': False}
        for server in IMAGE_SERVER_LIST:
            if server[0] == image_server:
                image_server_port = server[1]
        if image_server_port is None:
            return {'message': 'image server not allowed', 'status': False}
        rq_url = _root_url.format(
            host=image_server,
            port=image_server_port,
            root_path='image_server',
            type_path=''
        )
        try:
            rq_obj = requests.get(rq_url)
            exec_result = json.loads(rq_obj.text)
        except ConnectionError:
            _logger.write(str(image_server) + '连接失败', 'warn')
            exec_result = {'message': 'image server connect fail', 'status': False}
        return exec_result

    @staticmethod
    def get_image_server_registry(image_server):
        """ 获取镜像镜像服务器所在节点的私有仓库

        :param image_server:
        :return:
        """
        image_server_port = None
        image_server_status = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
        if image_server not in image_server_status or not image_server_status.get(image_server).get('status'):
            _logger.write('镜像服务器Host: \'' + str(image_server) + '\'无效或本Host不可用', level='warn')
            return {'message': 'image server unavailable', 'status': False}
        for server in IMAGE_SERVER_LIST:
            if server[0] == image_server:
                image_server_port = server[2]
        if image_server_port is None:
            return {'message': 'image server not allowed', 'status': False}
        rq_url = _root_url.format(
            host=image_server,
            port=image_server_port,
            root_path='image_registry_server',
            type_path=''
        )
        try:
            rq_obj = requests.get(rq_url)
            exec_result = json.loads(rq_obj.text)
        except ConnectionError:
            _logger.write(str(image_server) + '连接失败', 'warn')
            exec_result = {'message': 'image server connect fail', 'status': False}
        return exec_result

    @staticmethod
    def download_image_tar(image_server, download_to_host, repository):
        """ 下载镜像

        从远程镜像仓库下载镜像  -- 文件方式

        :param image_server: 镜像服务器地址
        :param download_to_host: 要下载镜像的节点
        :param repository: 所要下载的镜像名(包含tag)
        :return:

        """
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        if download_to_host not in cluster_status or not cluster_status.get(download_to_host).get('status'):
            _logger.write('节点Host: \'' + download_to_host + '\'无效或本Host不可用', level='warn')
            return {'message': 'node unavailable', 'status': False}
        image_server_status = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
        if image_server not in image_server_status or not image_server_status.get(image_server).get('status'):
            _logger.write('镜像服务器Host: \'' + str(image_server) + '\'无效或本Host不可用', level='warn')
            return {'message': 'image server unavailable', 'status': False}
        image_server_port = None
        for server in IMAGE_SERVER_LIST:
            if server[0] == image_server:
                image_server_port = server[1]
        if image_server_port is None:
            return {'message': 'image server not allowed', 'status': False}
        rq_url = _root_url.format(
            host=image_server,
            port=image_server_port,
            root_path='image_server',
            type_path=''
        )
        rq_args = {
            'to_host': download_to_host,
            'image_name': repository
        }
        try:
            rq_obj = requests.post(rq_url, json=rq_args)
            exec_result = json.loads(rq_obj.text)
        except ConnectionError:
            _logger.write(str(download_to_host) + '连接失败', 'warn')
            exec_result = {'message': 'host connect fail', 'status': False}
        return exec_result


class System(object):
    """
    系统信息获取类
    """

    @staticmethod
    def get_all_system(cluster_id, type_):
        """ 获取系统信息列表

        构建url请求,向指定从节点发送获取系统信息列表请求

        :param type_: 信息类型. 值类型为mem, disk, cpu
        :param cluster_id: 要获取的集群ID
        :return: [] or None
        """
        system_info_list = {}
        _allow_type = ['mem', 'disk', 'cpu']
        if type_ not in _allow_type:
            return {'message': 'type error', 'status': False}
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        cluster_all_id = Gl.get_value('CLUSTER_ALL_ID_VAR', [])
        cluster_all_info = Gl.get_value('CLUSTER_ALL_INFO_VAR', {})
        if cluster_id not in cluster_all_id:
            _logger.write('集群ID: \'' + cluster_id + '\'未找到', 'warn')
            return {}
        for node in cluster_all_info.get(cluster_id).get('node'):
            node_host = node.get('host')
            if node_host not in cluster_status or not cluster_status.get(node_host).get('status'):
                continue
            rq_url = _root_url.format(
                host=node_host,
                port=SLAVE_SERVICE_PORT_VAR,
                root_path='system',
                type_path=''
            )
            try:
                params = {
                    'type': type_
                }
                rq_obj = requests.get(rq_url, params=params)
                rq_result = json.loads(rq_obj.text)
            except ConnectionError:
                _logger.write(str(node_host) + '连接失败', 'warn')
                rq_result = {'message': 'node connect error', 'status': False}
            system_info_list.update({node_host: rq_result})
        return system_info_list

    @staticmethod
    def get_system(host, type_):
        """获取单个节点系统信息

        由于每个Host仅可属于一个集群,故只需提供Host而无需提供集群ID

        :param host: 要查询的节点Host
        :param type_: 查询种类
        :return: [] or None
        """
        system_list = None
        _allow_type = ['mem', 'disk', 'cpu']
        if type_ not in _allow_type:
            return {'message': 'type error', 'status': False}
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        cluster_all_hosts = Gl.get_value('CLUSTER_ALL_HOSTS_VAR', [])
        if host not in cluster_all_hosts:
            _logger.write('节点Host: \'' + host + '\'无效', level='warn')
            return {'message': 'host not found', 'status': False}
        if host not in cluster_status or not cluster_status.get(host).get('status'):
            return {'message': 'host unavailable', 'status': False}
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='system',
            type_path=''
        )
        rq_args = {'type': type_}
        try:
            rq_obj = requests.get(rq_url, params=rq_args)
            system_list = json.loads(rq_obj.text)
        except ConnectionError:
            _logger.write(str(host) + '连接失败', 'warn')
            system_list = {'message': 'host connect fail', 'status': False}
        return system_list