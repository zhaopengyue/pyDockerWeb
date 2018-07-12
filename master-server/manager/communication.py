#!coding: utf-8
"""
本程序封装了主从通信模块,即主服务向从服务发送操作请求
"""
import json
import sys
import re
import requests
from requests.exceptions import ConnectionError

from manager.log import Logging
from manager.tools import GlobalMap as Gl
from etc.sys_set import SLAVE_SERVICE_PORT_VAR
from etc.sys_set import IMAGE_SERVER_PORT_VAR


_root_url = 'http://{host}:{port}/{root_path}/{type_path}'

# 日志文件配置
_logger = Logging('communication')
_logger.set_file('communication.log')


def format_result(func):
    """ 处理输出结果, 并标准化返回结果

    格式化前函数需要返回 statusCode, message, errMessage

    ***仅包装批量操作函数***
    格式化输出结果, 对函数数输出结果进行二次包装. 包装结果为
    {
        "statusCode": 执行结果状态码
        "message":    message 具体见接口文档
        "errMessage": errMessage
    }
    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        status_code, message, err_message = func(*args, **kwargs)
        if status_code == 0:
            err_message = None
        if status_code > 1:
            message = None
        return {
            'statusCode': status_code,
            'message': message,
            'err_message': err_message
        }
    return wrapper


def host_validation(func):
    """ 验证单个host是否合法

    :param func:
    :return:
    """
    def wrapper(host, *args, **kwargs):
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        cluster_all_hosts = Gl.get_value('CLUSTER_ALL_HOSTS_VAR', [])
        if host not in cluster_all_hosts or host not in cluster_status or not cluster_status.get(host).get('status'):
            err_message = u'节点Host: \'' + host + u'\'非法'
            _logger.write(err_message, level='warn')
            return {
                'statusCode': 6,
                'errMessage': err_message,
                'message': None
            }
        try:
            return func(host, *args, **kwargs)
        except ConnectionError, e:
            return {
                'statusCode': 6,
                'errMessage': '\'' + host + u'\'连接失败',
                'message': None
            }
    return wrapper


def hosts_validation(func):
    """ 验证host列表,筛选出可用host

    :param func:
    :return:
    """
    def wrapper(hosts, *args, **kwargs):
        if not isinstance(hosts, list):
            return {
                'errMessage': u'参数非法',
                'message': None,
                'statusCode': 3
            }
        status_code = 0
        err_message = ''
        available_hosts = hosts
        # cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        # cluster_all_hosts = Gl.get_value('CLUSTER_ALL_HOSTS_VAR', [])
        # available_hosts = []
        # for host in hosts:
        #     if host in cluster_all_hosts and host in cluster_status and cluster_status.get(host).get('status'):
        #         available_hosts.append(host)
        #     else:
        #         # 更新全局status_code为1
        #         status_code = 1

        if available_hosts.__len__() != 0:
            return func(available_hosts, *args, **kwargs)
        else:
            return {
                'statusCode': 6,
                'errMessage': u'列表中无可用节点',
                'message': None
            }
    return wrapper


class Container(object):
    """
    容器操作类
    """

    @staticmethod
    @format_result
    def get_all_containers(cluster_id):
        """ 获取容器列表,获取所有容器列表

        构建url请求,向指定从节点发送获取容器列表请求

        :param cluster_id: 要获取的集群ID
        :return:[
        {
            "host": host,    IP
            "message" : {
                "statusCode": 状态码,
                "refresh": ,请求回执,
                "url": ,    请求url,
                "errMessage": 错误信息
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
                        'statusCode': int
                        'errMessage': str
                    },...
                ]
            }
        }, {}...]
        """
        # 状态码
        status_code = 0
        containers_dict = []
        err_message = ''
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        _logger.write(cluster_status.__str__())
        cluster_all_id = Gl.get_value('CLUSTER_ALL_ID_VAR', [])
        _logger.write(cluster_all_id.__str__())
        cluster_all_info = Gl.get_value('CLUSTER_ALL_INFO_VAR', {})
        _logger.write(cluster_all_info.__str__())
        # 验证ID
        if cluster_id not in cluster_all_id:
            _logger.write(u'集群ID: \'' + cluster_id + u'\'未找到', 'warn')
            return 5, '', u'集群ID' + cluster_id + u'未找到'
        for node in cluster_all_info.get(cluster_id).get('node'):
            node_host = node.get('host')
            # 验证节点状态
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
                node_err_message = rq_result.get('errMessage')
                if node_err_message:
                    err_message = err_message + rq_result.get('errMessage') + '\n'
            except ConnectionError:
                # 连接失败, 该节点标记为失败
                node_status_code = 6
                _logger.write(str(node_host) + u'连接失败', 'warn')
                err_message = err_message + '\'' + str(node_host) + u'\'连接失败\n'
                rq_result = {
                    'message': None,
                    'statusCode': node_status_code,
                    'errMessage': err_message
                }
            # 存在失败情况
            if rq_result.get('statusCode') > 0:
                # 设置整体statusCode为1
                status_code = 1
            containers_dict.append({
                'host': node_host,
                'message': rq_result
            })
        return status_code, containers_dict, err_message

    @staticmethod
    @hosts_validation
    @format_result
    def get_all_containers_by_list(hosts):
        """ 通过IP列表获取容器信息

        :param hosts: IP 列表
        :return:
        [
        {
            "host": host,    IP
            "message" : {
                "statusCode": 状态码,
                "refresh": ,请求回执,
                "url": ,    请求url,
                "errMessage": 错误信息
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
                        'statusCode': int
                        'errMessage': str
                    },...
                ]
            }
        }, {}...]
        """
        # 状态码
        status_code = 0
        containers_dict = []
        err_message = ''
        for node in hosts:
            rq_url = _root_url.format(
                host=node,
                port=SLAVE_SERVICE_PORT_VAR,
                root_path='container',
                type_path='_all'
            )
            try:
                rq_obj = requests.get(rq_url)
                rq_result = json.loads(rq_obj.text)
                node_err_message = rq_result.get('errMessage')
                if node_err_message:
                    err_message = err_message + rq_result.get('errMessage') + '\n'
            except ConnectionError:
                # 连接失败, 该节点标记为失败
                node_status_code = 6
                _logger.write(str(node) + u'连接失败', 'warn')
                err_message = err_message + '\'' + str(node) + u'\'连接失败\n'
                rq_result = {
                    'message': None,
                    'statusCode': node_status_code,
                    'errMessage': err_message
                }
            # 存在失败情况
            if rq_result.get('statusCode') > 0:
                # 设置整体statusCode为1
                status_code = 1
            containers_dict.append({
                'host': node,
                'message': rq_result
            })
        return status_code, containers_dict, err_message

    @staticmethod
    @host_validation
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
            "statusCode": int,
            "refresh": ,
            "url":,
            "errMessage": str
        }
        """
        # 错误码
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='container',
            type_path='_all'
        )
        rq_obj = requests.get(rq_url)
        rq_result = json.loads(rq_obj.text)
        return rq_result

    @staticmethod
    @host_validation
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
                            new_name .str(新的容器名)
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
            "statusCode": ,   #状态码.int
            "url": ,      #请求url.str
            "refresh":    #请求回执时间.str
            "errMessage": #错误信息, str
        }
        """
        _allow_action = ['start', 'stop', 'restart', 'rename', 'logs', 'pause', 'commit', 'kill', 'remove', 'unpause']
        if action_type not in _allow_action:
            err_message = '\'' + action_type + u'\'不合法'
            _logger.write(err_message, level='warn')
            return {
                'statusCode': 3,
                'errMessage': err_message,
                'message': None
            }
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='container',
            type_path=''
        )
        if 'type' in kwargs or 'container_id_or_name' in kwargs:
            err_message = u'函数传参异常'
            return {
                'statusCode': 3,
                'errMessage': err_message,
                'message': None
            }
        rq_args = {'type': action_type, 'container_id_or_name': container_id_or_name}
        rq_args.update(kwargs)
        rq_obj = requests.post(rq_url, json=rq_args)
        rq_result = json.loads(rq_obj.text)
        return rq_result

    @staticmethod
    @hosts_validation
    @format_result
    def operator_container_by_hosts(hosts, action_type, containers, **kwargs):
        """ 通过IP 列表进行对节点进行批量操作

        由于批量操作, 故仅允许进行 kill, start, stop, restart, pause, unpause
        要求containers与hosts一一对应

        :param hosts 所要操作的IP列表
        :param action_type 动作类型
        :param containers 容器列表
        :return:
        """
        _allow_action = ['kill', 'start', 'stop', 'restart', 'pause', 'unpause']
        err_message = ''
        status_code = 0
        exec_result = []
        if action_type not in _allow_action:
            err_message = '\'' + action_type + u'\'不合法'
            _logger.write(err_message, level='warn')
            return {
                'statusCode': 3,
                'errMessage': err_message,
                'message': None
            }
        if hosts.__len__() != containers.__len__():
            err_message = u'节点表与容器id表不匹配'
            _logger.write(err_message, 'warn')
            return {
                'statusCode': 3,
                'errMessage': err_message,
                'message': None
            }
        if 'type' in kwargs or 'containers' in kwargs:
            err_message = u'函数传参异常'
            return {
                'statusCode': 3,
                'errMessage': err_message,
                'message': None
            }
        for index in xrange(hosts.__len__()):
            host = hosts[index]
            container = containers[index]
            rq_url = _root_url.format(
                host=host,
                port=SLAVE_SERVICE_PORT_VAR,
                root_path='container',
                type_path=''
            )
            rq_args = {'type': action_type, 'container_id_or_name': container}
            rq_args.update(kwargs)
            try:
                rq_obj = requests.get(rq_url)
                rq_result = json.loads(rq_obj.text)
                node_err_message = rq_result.get('errMessage')
                if node_err_message:
                    err_message = err_message + rq_result.get('errMessage') + '\n'
            except ConnectionError:
                # 连接失败, 该节点标记为失败
                node_status_code = 6
                node_err_message = host + u'连接失败'
                _logger.write(node_err_message, 'warn')
                err_message = err_message + node_err_message + '\n'
                rq_result = {
                    'message': None,
                    'statusCode': node_status_code,
                    'errMessage': node_err_message
                }
                # 存在失败情况
            if rq_result.get('statusCode') > 0:
                # 设置整体statusCode为1
                status_code = 1
            exec_result.append({
                'host': host,
                'message': rq_result,
                'container': container
            })
        return status_code, exec_result, err_message

    @staticmethod
    @host_validation
    def create_container_shell(host, cmd):
        """ 创建容器

        创建容器的命令行模式, 通过shell语句创建
        eg: docker create ***

        :param host: 执行节点
        :param cmd:
        :return:
        {
            "message": ,
            "statusCode": ,
            'url': ,
            'refresh':,
            'errMessage':
        }
        """
        pattern_cmd = '^docker\s+(run|create)\s+.*'
        if re.match(pattern_cmd, cmd) is None:
            err_message = u'执行出错: 命令不合法'
            _logger.write(err_message, level='warn')
            return {
                'message': None,
                'statusCode': 6,
                'errMessage': err_message
            }
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
            _logger.write(str(host) + u'连接失败', 'warn')
            return {'message': None, 'statusCode': 6, 'errMessage': str(host) + u'连接失败'}

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
    @format_result
    def get_all_images(cluster_id):
        """

        :param cluster_id: 集群ID
        :return:
        [
            {
                "host": host,
                "message": {
                    "statusCode": ,
                    "refresh": ,
                    "url": ,
                    "message": [
                        {
                            "message": {
                                'id': 镜像id,
                                'short_id': 镜像短id,
                                'tags': 镜像标签列表,
                                'created': 镜像创建日期,
                                'size': 镜像大小,
                                'os': 镜像系统
                            },
                            "statusCode": ,
                            "errMessage":
                        },
                        {}
                    ],
                    "errMessage":
                }
            }, {}, ...
        ]
        """
        images_list = []
        err_message = ''
        status_code = 0
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        cluster_all_id = Gl.get_value('CLUSTER_ALL_ID_VAR', [])
        cluster_all_info = Gl.get_value('CLUSTER_ALL_INFO_VAR', {})
        if cluster_id not in cluster_all_id:
            err_message = u'集群ID: \'' + str(cluster_id) + u'\'未找到'
            _logger.write(err_message, 'warn')
            return 5, '', err_message
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
                node_err_message = rq_result.get('errMessage')
                if node_err_message:
                    err_message = node_err_message + rq_result.get('errMessage') + '\n'
            except ConnectionError:
                # 连接失败, 该节点标记为失败
                node_status_code = 6
                _logger.write(str(node_host) + u'连接失败', 'warn')
                err_message = err_message + '\'' + str(node_host) + u'\'连接失败\n'
                rq_result = {
                    'message': None,
                    'statusCode': node_status_code,
                    'errMessage': err_message
                }
                # 存在失败情况
            if rq_result.get('statusCode') > 0:
                # 设置整体statusCode为1
                status_code = 1
            images_list.append({
                'host': node_host,
                'message': rq_result
            })
        return status_code, images_list, err_message

    @staticmethod
    @hosts_validation
    @format_result
    def get_all_images_by_list(hosts):
        """ 通过IP列表获取镜像列表

        :param hosts: IP列表
        :return:
        [
            {
                "host": host,
                "message": {
                    "statusCode": ,
                    "refresh": ,
                    "url": ,
                    "message": [
                        {
                            "message": {
                                'id': 镜像id,
                                'short_id': 镜像短id,
                                'tags': 镜像标签列表,
                                'created': 镜像创建日期,
                                'size': 镜像大小,
                                'os': 镜像系统
                            },
                            "statusCode": ,
                            "errMessage":
                        },
                        {}
                    ],
                    "errMessage":
                }
            }, {}, ...
        ]
        """
        err_message = ''
        status_code = 0
        images_list = []
        for host in hosts:
            rq_url = _root_url.format(
                host=host,
                port=SLAVE_SERVICE_PORT_VAR,
                root_path='image',
                type_path='_all'
            )
            try:
                rq_obj = requests.get(rq_url)
                rq_result = json.loads(rq_obj.text)
                node_err_message = rq_result.get('errMessage')
                if node_err_message:
                    err_message = err_message + rq_result.get('errMessage') + '\n'
            except ConnectionError:
                # 连接失败, 该节点标记为失败
                node_status_code = 6
                node_err_message = host + u'连接失败'
                _logger.write(str(host) + u'连接失败', 'warn')
                err_message = err_message + node_err_message + '\n'
                rq_result = {
                    'message': None,
                    'statusCode': node_status_code,
                    'errMessage': node_err_message
                }
                # 存在失败情况
            if rq_result.get('statusCode') > 0:
                # 设置整体statusCode为1
                status_code = 1
            images_list.append({
                'host': host,
                'message': rq_result
            })
        return status_code, images_list, err_message

    @staticmethod
    @host_validation
    def get_image(host):
        """获取单个节点容器信息

        由于每个Host仅可属于一个集群,故只需提供Host而无需提供集群ID

        :param host: 要查询的节点Host
        :return:
        {
            "message":{
                'id': 镜像id,
                'short_id': 镜像短id,
                'tags': 镜像标签列表,
                'created': 镜像创建日期,
                'size': 镜像大小,
                'os': 镜像系统
            },
            "statusCode": int.执行状态,
            "errMessage": str
        }
        """
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='image',
            type_path='_all'
        )
        rq_obj = requests.get(rq_url)
        images_info = json.loads(rq_obj.text)
        return images_info

    @staticmethod
    @host_validation
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
            "message":'ok',
            "statusCode": .bool(执行状态),
            "errMessage":
            "url": .str(请求url,status 为True时显示)
            "refresh": .str(请求回执时间 ,status为True时显示)
        }
        """
        _allow_action = ['remove', 'tag', 'search']
        if action_type not in _allow_action or 'type' in kwargs or 'image_id_or_name' in kwargs:
            err_message = u'函数传参异常'
            return {
                'statusCode': 3,
                'errMessage': err_message,
                'message': None
            }
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='image',
            type_path=''
        )
        rq_args = {'type': action_type, 'image_id_or_name': image_id_or_name}
        rq_args.update(kwargs)
        rq_obj = requests.post(rq_url, json=rq_args)
        exec_result = json.loads(rq_obj.text)
        return exec_result

    @staticmethod
    @hosts_validation
    @format_result
    def remove_all_images(hosts):
        """ 删除所有节点的所有镜像

        :param hosts: 节点IP列表
        :return: [
            {
                "host": "",
                "message": {
                    "message": "ok",
                    "statusCode": 0,
                    "errMessage": None
                }
            }, {}
        ]
        """
        err_message = ''
        status_code = 0
        exec_result = []
        for host in hosts:
            rq_url = _root_url.format(
                host=host,
                port=SLAVE_SERVICE_PORT_VAR,
                root_path='image',
                type_path=''
            )
            rq_args = {'type': 'remove_all', 'force': True}
            try:
                rq_obj = requests.post(rq_url, json=rq_args)
                rq_result = json.loads(rq_obj.text)
                node_err_message = rq_result.get('errMessage')
                if node_err_message:
                    err_message = err_message + rq_result.get('errMessage') + '\n'
            except ConnectionError:
                # 连接失败, 该节点标记为失败
                node_status_code = 6
                node_err_message = host + u'连接失败'
                _logger.write(node_err_message, 'warn')
                err_message = err_message + node_err_message + '\n'
                rq_result = {
                    'message': None,
                    'statusCode': node_status_code,
                    'errMessage': node_err_message
                }
                # 存在失败情况
            if rq_result.get('statusCode') > 0:
                # 设置整体statusCode为1
                status_code = 1
            exec_result.append({
                'host': host,
                'message': rq_result
            })
        return status_code, exec_result, err_message

    @staticmethod
    @hosts_validation
    @format_result
    def operator_images_by_list(hosts, action_type, images, **kwargs):
        """ 通过IP 列表进行对节点进行批量操作

        由于批量操作, 故仅允许进行 remove操作
        要求images与hosts一一对应

        :param hosts 所要操作的IP列表
        :param action_type 动作类型
        :param images 容器列表
        :return:
        """
        _allow_action = ['remove']
        err_message = ''
        status_code = 0
        exec_result = []
        if action_type not in _allow_action:
            err_message = '\'' + action_type + u'\'不合法'
            _logger.write(err_message, level='warn')
            return 3, None, err_message
        if hosts.__len__() != images.__len__():
            err_message = u'节点表与镜像id表不匹配'
            _logger.write(err_message, 'warn')
            return 3, None, err_message
        if 'type' in kwargs or 'images' in kwargs:
            err_message = u'函数传参异常'
            return 3, None, err_message
        for index in xrange(hosts.__len__()):
            host = hosts[index]
            image = images[index]
            rq_url = _root_url.format(
                host=host,
                port=SLAVE_SERVICE_PORT_VAR,
                root_path='image',
                type_path=''
            )
            rq_args = {'type': action_type, 'image_id_or_name': image}
            rq_args.update(kwargs)
            try:
                rq_obj = requests.post(rq_url, json=rq_args)
                rq_result = json.loads(rq_obj.text)
                node_err_message = rq_result.get('errMessage')
                if node_err_message:
                    err_message = err_message + rq_result.get('errMessage') + '\n'
            except ConnectionError:
                # 连接失败, 该节点标记为失败
                node_status_code = 6
                node_err_message = host + u'连接失败'
                _logger.write(node_err_message, 'warn')
                err_message = err_message + node_err_message + '\n'
                rq_result = {
                    'message': None,
                    'statusCode': node_status_code,
                    'errMessage': node_err_message
                }
                # 存在失败情况
            if rq_result.get('statusCode') > 0:
                # 设置整体statusCode为1
                status_code = 1
            exec_result.append({
                'host': host,
                'message': rq_result,
                'image': image
            })
        return status_code, exec_result, err_message

    @staticmethod
    @host_validation
    def download_image(download_to_host, image_server_host, repository):
        """ 下载镜像

        从远程镜像仓库下载镜像

        :param image_server_host: 镜像服务器ip
        :param download_to_host: 要下载镜像的节点
        :param repository: 所要下载的镜像名,包含镜像tag
        :return:
        {
            "message": ,
            "statusCode": ,
            "refresh": ,
            "url": ,
            "errMessage":
        }
        """
        # 验证image server状态
        image_server_status = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
        all_image_server_info_var = Gl.get_value('ALL_IMAGE_SERVER_INFO_VAR', {})
        if image_server_host not in image_server_status or not image_server_status.get(image_server_host).get('status'):
            _logger.write(u'镜像服务器Host: \'' + str(image_server_host) + u'\'无效或本Host不可用', level='warn')
            return {
                'statusCode': 7,
                'errMessage': u'镜像服务器Host: \'' + str(image_server_host) + u'\'无效或本Host不可用',
                'message': None
            }
        registry_server_port = all_image_server_info_var.get(image_server_host).get('registry_port')
        # 提取tag
        try:
            repository_tag = repository.split(':')[1]
        except IndexError:
            repository_tag = None
        # 拼接仓库名
        repository = image_server_host + ':' + str(registry_server_port) + '/' + repository.split(':')[0]
        print repository
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
        rq_obj = requests.post(rq_url, json=rq_args)
        exec_result = json.loads(rq_obj.text)
        return exec_result

    @staticmethod
    @hosts_validation
    @format_result
    def download_images_by_list(hosts, image_server_host, repositories):
        """ 从harbor仓库批量下载镜像

        :param hosts:
        :param image_server_host:
        :param repositories:
        :return:
        """
        if not isinstance(repositories, list):
            return {
                'statusCode': 3,
                'errMessage': '函数传参错误',
                'message': None
            }
        # 验证image server状态
        image_server_status = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
        all_image_server_info_var = Gl.get_value('ALL_IMAGE_SERVER_INFO_VAR', {})
        if image_server_host not in image_server_status or not image_server_status.get(image_server_host).get('status'):
            _logger.write(u'镜像服务器Host: \'' + str(image_server_host) + u'\'无效或本Host不可用', level='warn')
            return 7, None, u'镜像服务器Host: \'' + str(image_server_host) + u'\'无效或本Host不可用'
        registry_server_port = all_image_server_info_var.get(image_server_host).get('registry_port')
        download_status = []
        err_message = ''
        status_code = 0
        for host in hosts:
            for repository in repositories:
                # 提取tag
                try:
                    repository_tag = repository.split(':')[1]
                except IndexError:
                    repository_tag = None
                # 拼接仓库名
                repository = image_server_host + ':' + str(registry_server_port) + '/' + repository.split(':')[0]
                print repository
                rq_url = _root_url.format(
                    host=host,
                    port=SLAVE_SERVICE_PORT_VAR,
                    root_path='image',
                    type_path=''
                )
                rq_args = {
                    'repository': repository,
                    'tag': repository_tag,
                    'type': 'pull'
                }
                try:
                    rq_obj = requests.post(rq_url, json=rq_args)
                    rq_result = json.loads(rq_obj.text)
                    node_err_message = rq_result.get('errMessage')
                    if node_err_message:
                        err_message = err_message + rq_result.get('errMessage') + '\n'
                except ConnectionError:
                    # 连接失败, 该节点标记为失败
                    node_status_code = 6
                    node_err_message = host + u'连接失败'
                    _logger.write(host + u'连接失败', 'warn')
                    err_message = err_message + node_err_message + '\n'
                    rq_result = {
                        'message': None,
                        'statusCode': node_status_code,
                        'errMessage': node_err_message
                    }
                    # 存在失败情况
                if rq_result.get('statusCode') > 0:
                    # 设置整体statusCode为1
                    status_code = 1
                download_status.append({
                    'host': host,
                    'message': rq_result,
                    'repository': repository
                })
        return status_code, download_status, err_message

    @staticmethod
    def get_image_server_list():
        """ 返回镜像服务器列表

        :return:['image_server_host_1', 'image_server_host_2', ...]
        """
        all_image_server_host_var = Gl.get_value('ALL_IMAGE_SERVER_HOST_VAR', [])
        return {'message': all_image_server_host_var, 'statusCode': 0, 'errMessage': None}

    @staticmethod
    def get_alive_image_server_list():
        """ 返回可用的镜像服务器列表

        :return: ['alive_image_server_host_1', 'alive_image_server_host_2', ...]
        """
        info = []
        all_image_server_host_var = Gl.get_value('ALL_IMAGE_SERVER_HOST_VAR', [])
        image_server_status = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
        for image_server in all_image_server_host_var:
            if image_server not in image_server_status or not image_server_status.get(image_server).get('status'):
                continue
            info.append(image_server)
        if info.__len__() > 0:
            return {'message': info, 'statusCode': 0, 'errMessage': None}
        else:
            return {'message': None, 'statusCode': 7, 'errMessage': 'No mirror server is available.'}

    @staticmethod
    def get_image_server_harbor(image_server):
        """ 获取harbor镜像列表

        :param image_server: harbor镜像服务器地址
        :return:
        """
        image_server_status = Gl.get_value('IMAGE_SERVER_STATUS_VAR', {})
        if image_server not in image_server_status or not image_server_status.get(image_server).get('status'):
            _logger.write(u'镜像服务器Host: \'' + str(image_server) + u'\'无效或本Host不可用', level='warn')
            return {
                'errMessage': u'镜像服务器不可用',
                'statusCode': 7,
                'message': None
            }
        rq_url = _root_url.format(
            host=image_server,
            port=IMAGE_SERVER_PORT_VAR,
            root_path='image_harbor_server',
            type_path=''
        )
        rq_obj = requests.get(rq_url)
        exec_result = json.loads(rq_obj.text)
        return exec_result


class System(object):
    """
    系统信息获取类
    """

    @staticmethod
    @format_result
    def get_all_system(cluster_id, type_):
        """ 获取系统信息列表

        构建url请求,向指定从节点发送获取系统信息列表请求

        :param type_: 信息类型. 值类型为mem, disk, cpu
        :param cluster_id: 要获取的集群ID
        :return:
        [
            {
                "host": host    IP
                "message": {
                    'message': {
        #由具体值定       'total_mem':, 内存总量
                        'free_mem': , 空闲内存量
                        'active_mem': 使用内存量
                        'cache/buffer_mem': 缓存量
                    },
                    'statusCode': ,
                    'errorMessage':
                },
                "errMessage": ,
                "statusCode": ,
                "refresh":,
                "url":
            }
        ]
        """
        system_info_list = []
        status_code = 0
        err_message = ''
        _allow_type = ['mem', 'disk', 'cpu']
        if type_ not in _allow_type:
            return 3, '', u'函数传参错误'
        cluster_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
        cluster_all_id = Gl.get_value('CLUSTER_ALL_ID_VAR', [])
        cluster_all_info = Gl.get_value('CLUSTER_ALL_INFO_VAR', {})
        if cluster_id not in cluster_all_id:
            _logger.write(u'集群ID: \'' + cluster_id.__str__() + u'\'未找到', 'warn')
            return 5, '', u'集群ID' + cluster_id.__str__() + u'未找到'
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
                node_err_message = rq_result.get('errMessage')
                if node_err_message:
                    err_message = err_message + rq_result.get('errMessage') + '\n'
            except ConnectionError:
                # 连接失败, 该节点标记为失败
                node_status_code = 6
                node_err_message = node_host + u'连接失败'
                _logger.write(node_err_message, 'warn')
                err_message = err_message + node_err_message + '\n'
                rq_result = {
                    'message': None,
                    'statusCode': node_status_code,
                    'errMessage': node_err_message
                }
                # 存在失败情况
            if rq_result.get('statusCode') > 0:
                # 设置整体statusCode为1
                status_code = 1
            system_info_list.append({
                'host': node_host,
                'message': rq_result
            })
        return status_code, system_info_list, err_message

    @staticmethod
    @host_validation
    def get_system(host, type_):
        """获取单个节点系统信息

        由于每个Host仅可属于一个集群,故只需提供Host而无需提供集群ID

        :param host: 要查询的节点Host
        :param type_: 查询种类
        :return: [] or None
        """
        _allow_type = ['mem', 'disk', 'cpu']
        if type_ not in _allow_type:
            return {'errMessage': u'函数参数异常', 'statusCode': 3, 'message': None}
        rq_url = _root_url.format(
            host=host,
            port=SLAVE_SERVICE_PORT_VAR,
            root_path='system',
            type_path=''
        )
        rq_args = {'type': type_}
        rq_obj = requests.get(rq_url, params=rq_args)
        system_list = json.loads(rq_obj.text)
        return system_list