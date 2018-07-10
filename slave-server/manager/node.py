#!coding: utf-8
"""
本程序封装了系统信息获取,容器及镜像操作等相关方法
相关接口文档详见INTERFACE.md
"""
import os
import datetime
import docker
import re
from docker.errors import APIError
from docker.errors import NotFound
from docker.errors import ImageNotFound
from manager.log import Logging

# 声明日志输出对象
_log = Logging('node')
_log.set_file('node.log')


def format_error(func):
    """ 处理异常结果，标准化返回结果

    格式化输出errMessage,若errMessage为'', 则将其更改为Node, 同时对docker sdk抛出的异常进行处理

    :param func:
    :return:
    """

    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except (ImageNotFound, NotFound, APIError), e:
            return {'message': None, 'statusCode': 2, 'errMessage': e.response.json().get('message')}
        except Exception, e:
            return {'message': None, 'statusCode': 2, 'errMessage': e}
        status_code = result.get('statusCode', 0)
        # 状态码为0时将err_message更改为None
        if status_code == 0:
            err_message = None
            result['errMessage'] = err_message
        return result
    return wrapper


def parameter_validation(func):
    """函数的参数格式验证
       :return:
    """

    def wrapper(self, id_, *args, **kwargs):
        if not isinstance(id_, str):
            return {'message': None, 'statusCode': 3, 'errMessage': 'image id must be str'}
        if 'timeout' in kwargs:
            if not isinstance(kwargs.get('timeout'), int):
                return {'message': None, 'statusCode': 3, 'errMessage': 'timeout must be int'}
        if 'tag' in kwargs:
            if not isinstance(kwargs.get('tag'), int):
                return {'message': None, 'statusCode': 3, 'errMessage': 'tag must be int'}
        return func(self, id_, *args, **kwargs)
    return wrapper


class System(object):
    """
    获取CPU,内存,硬盘信息

    """
    @staticmethod
    @format_error
    def get_cpu_info():
        """获取本节点的CPU信息

        :return:CPU相关信息
        {
            'message':{
                'physical_cpu_num': 物理CPU个数
                'physical_cpu_core_num': 每个物理CPU核数,
                'processor_core_num': 逻辑CPU核数
                'all_cpu_core_num': 总核数 = 物理CPU个数 * 每个物理CPU核数
            },
            'statusCode': ,
            'errMessage':
        }
        """
        # 物理CPU个数
        physical_cpu_num_cmd = 'cat /proc/cpuinfo| grep "physical id"| sort| uniq| wc -l'
        # 查看每个物理CPU中core的个数(即核数)
        physical_cpu_core_num_cmd = 'cat /proc/cpuinfo| grep "cpu cores"|uniq |cut -d \':\' -f 2|sed \'s/^[ \t]*//g\''
        # 逻辑CPU核数
        processor_core_num_cmd = 'cat /proc/cpuinfo | grep \'processor\' | sort | uniq | wc -l'
        status_code = 0
        err_message = ''
        try:
            physical_cpu_num = os.popen(physical_cpu_num_cmd).read().split('\n')[0]
            if not physical_cpu_num:
                physical_cpu_num = 0
        except Exception:
            err_message += '物理cpu个数读取失败;'
            physical_cpu_num = 0
            status_code = 1
        try:
            physical_cpu_core_num = os.popen(physical_cpu_core_num_cmd).read().split('\n')[0]
            if not physical_cpu_core_num:
                physical_cpu_core_num = 0
        except Exception:
            physical_cpu_core_num = 0
            err_message += u'每个cpu核数读取失败;'
            status_code = 1
        try:
            processor_core_num = os.popen(processor_core_num_cmd).read().split('\n')[0]
            if not processor_core_num:
                processor_core_num = 0
        except Exception:
            err_message += u'逻辑cpu核数读取失败;'
            status_code = 1
            processor_core_num = 0
        cpu_info = {
            'physical_cpu_num': physical_cpu_num,
            'physical_cpu_core_num': physical_cpu_core_num,
            'processor_core_num': processor_core_num,
            'all_cpu_core_num': str(int(physical_cpu_num) * int(physical_cpu_core_num))
        }
        _log.write(cpu_info.__str__())
        return {'message': cpu_info, 'statusCode': status_code, 'errMessage': err_message}

    @staticmethod
    @format_error
    def get_mem_info():
        """ 获取内存信息

        :return:
        {
            message: {
                'total_mem':, 内存总量
                'free_mem': , 空闲内存量
                'active_mem': 使用内存量
                'cache/buffer_mem': 缓存量
            },
            'statusCode': ,
            'errorMessage':
        }
        """
        # 以下单位皆为kb
        # 内存总量,单位kb
        total_mem_cmd = "cat /proc/meminfo |grep MemTotal | awk '{print $2}'"
        # 空闲内存总量,单位kb
        free_mem_cmd = "cat /proc/meminfo |grep MemFree | awk '{print $2}'"
        # 使用内存总量,单位kb
        active_mem_cmd = "cat /proc/meminfo |grep Active | awk '{print $2}'"
        # cache/buff内存量, 单位kb
        cache_mem_cmd = "cat /proc/meminfo |grep Cached | awk 'NR == 1 {print $2}'"
        buffer_mem_cmd = "cat /proc/meminfo |grep Buffers | awk 'NR == 1 {print $2}'"
        status_code = 0
        err_message = ''
        try:
            total_mem = os.popen(total_mem_cmd).read().split('\n')[0]
            free_mem = os.popen(free_mem_cmd).read().split('\n')[0]
            active_mem = os.popen(active_mem_cmd).read().split('\n')[0]
            cache_mem = os.popen(cache_mem_cmd).read().split('\n')[0]
            buffer_mem = os.popen(buffer_mem_cmd).read().split('\n')[0]
            mem_info = {
                'total_mem': total_mem,
                'free_mem': free_mem,
                'active_mem': active_mem,
                'cache/buffer_mem': str(int(cache_mem) + int(buffer_mem))
            }
        except Exception:
            mem_info = None
            status_code = 2
            err_message = u'内存读取过程中失败'
        _log.write(mem_info.__str__())
        return {'message': mem_info, 'statusCode': status_code, 'errMessage': err_message}

    @staticmethod
    @format_error
    def get_disk_info():
        """ 获取磁盘信息

        单位为kb

        :return:
        (
            "message": {
                'available': 可用总量,
                'capacity': 总量
                'used': 已使用量
            },
            "statusCode": ,
            "errMessage": ,
        , )
        """
        dick_info = {}
        disk = os.statvfs("/")
        dick_info['available'] = disk.f_bsize * disk.f_bavail / 1024
        dick_info['capacity'] = disk.f_bsize * disk.f_blocks / 1024
        dick_info['used'] = disk.f_bsize * disk.f_bfree / 1024
        _log.write(dick_info.__str__())
        return {'message': dick_info, 'statusCode': 0}


class Containers(object):
    """

    容器操作相关类

    """

    def __init__(self):
        """ 初始化客户端环境

        """
        self.client = docker.from_env()
        try:
            self.client.version()
        except APIError, e:
            print e

    @format_error
    def get_list(self):
        """ 获取容器列表

        获取所有容器,包含未运行容器和正在运行容器

        :return:
        {
        "message":[{
            "message": {
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
            'status': bool
            },...
            ],
        "statusCode": int,
        "errMessage": ,
        }
        """
        containers_info = []
        status_code = 0
        err_message = ''
        for container in self.client.containers.list(all=True):
            # 此处忽略毫秒
            exec_result = self.get_info(str(container.id))
            if exec_result.get('statusCode') != 0:
                status_code = 1
                err_message = container.id + u'信息获取失败;'
            containers_info.append(exec_result)
        _log.write(containers_info.__str__())
        _log.write(str(status_code))
        _log.write(err_message)
        return {'message': containers_info, 'statusCode': status_code, 'errMessage': err_message}

    @parameter_validation
    @format_error
    def get_info(self, id_):
        """ 获取单个容器信息

        :param id_: 容器名或ID
        :return:
        {
            "message": {
                'id': 容器id,
                'short_id': 容器短id,
                'status': 容器状态,
                'running': 容器是否在运行,
                'paused': 容器是否暂停,
                'finishedAt': 容器退出时间,
                'startedAt': 容器开始时间,
                'created': 容器创建日期
                'image': 容器依赖镜像,
                'exit_time': 容器退出时间.
            },
            'statusCode':
            ‘errMessage’:
        }
        """
        # if not isinstance(id_, str):
        #     return {'message': None, 'statusCode': 2, 'errMessage': 'id_ must be str'}
        container = self.client.containers.get(id_)

        started_at = container.attrs.get('State').get('StartedAt').split('.')[0]
        finished_at = container.attrs.get('State').get('FinishedAt').split('.')[0]
        try:
            started_time = datetime.datetime.strptime(started_at, '%Y-%m-%dT%X')
        except ValueError:
            started_time = datetime.datetime.strptime(started_at, '%Y-%m-%dT%XZ')
        try:
            finished__time = datetime.datetime.strptime(finished_at, '%Y-%m-%dT%X')
        except ValueError:
            finished__time = datetime.datetime.strptime(finished_at, '%Y-%m-%dT%XZ')
        # runtime = (finished__time - started_time).seconds
        container_info = {
            'id_': container.id,
            'short_id': container.short_id,
            'status': container.status,
            'running': container.attrs.get('State').get('Running'),
            'paused': container.attrs.get('State').get('Paused'),
            'finishedAt': finished_at,
            'startedAt': started_at,
            'created': container.attrs['Created'],
            'image': container.attrs.get('Config').get('Image'),
            'name': container.attrs.get('Name'),
            'exit_time': Containers._get_exit_time(container.status, finished__time, started_time)
        }
        return {'message': container_info, 'statusCode': 0}

    @staticmethod
    def _get_exit_time(status, end_time, start_time):
        """ 获取容器退出到现在的时间

        :type status: 容器状态
        :return:
        """
        date_now = datetime.datetime.now()
        if status == 'running':
            date_delta = date_now - start_time
        else:
            date_delta = date_now - end_time
        # eg: 1 months ago
        if date_delta.days > 30:
            date = '%d months ago' % (date_delta.days / 30)
        # eg: 24 days ago
        elif date_delta.days >= 2:
            date = '%d days ago' % date_delta.days
        # eg: Yesterday
        elif date_delta.days >= 1:
            date = 'Yesterday'
        # eg: 5 hours ago
        elif date_delta.seconds > 60 * 60:
            date = '%d hours ago' % (date_delta.seconds / 3600)
        # eg: 30 minutes ago
        elif date_delta.seconds > 60:
            date = '%d minutes ago' % (date_delta.seconds / 60)
        # eg: 49 seconds ago
        else:
            date = '%d seconds ago' % date_delta.seconds
        if status == 'exited' or status == 'restarting':
            date = status + ' ' + date
        elif status == 'running':
            date = 'up ' + date
        else:
            date = status
        return date

    @parameter_validation
    @format_error
    def kill(self, id_, signal=None):
        """ 杀死容器或向容器发送信号

        类似于`docker kill`

        :param id_: 容器. str
        :param signal: 要发送的信号.默认值为None(即SIGKILL). str or int
        :return: 执行状态信息
        """
        container_obj = self.client.containers.get(id_)
        container_obj.kill(signal)
        return {'message': 'ok', 'statusCode': 0}

    @parameter_validation
    @format_error
    def start(self, id_):
        """ 启动容器

        类似`docker start`

        :param id_: 容器id或名字. str
        :return: 执行状态
        """
        container_obj = self.client.containers.get(id_)
        container_obj.start()
        return {'message': 'ok', 'statusCode': 0}

    @parameter_validation
    @format_error
    def stop(self, id_, timeout=10):
        """ 停止容器

        类似`docker stop`

        :param timeout: 停止容器时的超时时间.若超时时间内容器未停止,则杀死容器.
        :param id_: 容器id或名字. str
        :return:
        """
        container_obj = self.client.containers.get(id_)
        container_obj.stop(timeout=timeout)
        return {'message': 'ok', 'statusCode': 0}

    @parameter_validation
    @format_error
    def restart(self, id_, timeout=10):
        """ 停止容器

        类似`docker restart`

        :param timeout: 停止容器时的超时时间.若超时时间内容器未停止,则杀死容器.
        :param id_: 容器id或名字. str
        :return:
        """
        container_obj = self.client.containers.get(id_)
        container_obj.restart(timeout=timeout)
        return {'message': 'ok', 'statusCode': 0}

    @parameter_validation
    @format_error
    def rename(self, id_, new_name):
        """ 重命名容器

        类似于`docker rename`

        :param id_: 容器id或名字. str
        :param new_name: 新的容器名. str
        :return: 执行状态. bool
        """
        if not isinstance(new_name, str):
            return {'message': None, 'statusCode': 3, 'errMessage': 'new_name must be str'}
        container_obj = self.client.containers.get(id_)
        container_obj.rename(new_name)
        return {'message': 'ok', 'statusCode': 0}

    @parameter_validation
    @format_error
    def pause(self, id_):
        """ 启动容器

        类似`docker pause`

        :param id_: 容器id或名字. str
        :return:
        """
        container_obj = self.client.containers.get(id_)
        container_obj.pause()
        return {'message': 'ok', 'statusCode': 0}

    @parameter_validation
    @format_error
    def unpause(self, id_):
        """ 启动容器

        类似`docker unpause`

        :param id_: 容器id或名字. str
        :return:
        """
        container_obj = self.client.containers.get(id_)
        container_obj.unpause()
        return {'message': 'ok', 'statusCode': 0}

    @parameter_validation
    @format_error
    def logs(self, id_, **kwargs):
        """ 获取容器日志

        获取日志输出,暂时不涉及流式输出,类似于`docker logs`

        :parameter : stdout: 获取标准输出流. bool
                     stderr: 获取标准错误流 bool
                     timestamps: 展示时间戳 bool
        :return:
        """
        container_obj = self.client.containers.get(id_)
        info = container_obj.logs(**kwargs)
        return {'message': info, 'statusCode': 0}

    @parameter_validation
    @format_error
    def commit(self, id_, repository=None, tag=None, **kwargs):
        """ 构建一个容器为镜像

        类似于`docker commit`

        :param id_: 容器名或id. str
        :param tag: The tag to push. str
        :param repository: The repository to push the image to. str
        :parameter message: A commit message. str
                   author: The name of the author. str
                   changes: Dockerfile instructions to apply while committing. str
        :return:
        """
        if not isinstance(repository, str) or not isinstance(tag, str):
            return {'message': None, 'statusCode': 3, 'errMessage': 'repository and tag and id_ must be str'}
        container_obj = self.client.containers.get(id_)
        container_obj.commit(repository=repository, tag=tag, **kwargs)
        return {'message': 'ok', 'statusCode': 0}

    @parameter_validation
    @format_error
    def remove(self, id_, **kwargs):
        """ 删除容器, 类似于

        docker rm ``

        :param id_: 容器id或名字 .str
        :param kwargs: v: 是否删除数据卷 .bool
                       link: 是否删除连接容器 .bool
                       force: 是否强制删除 .bool
        :return:
        """
        container_obj = self.client.containers.get(id_)
        container_obj.remove(**kwargs)
        return {'message': 'ok', 'statusCode': 0}

    @format_error
    def create_shell(self, cmd):
        """
        创建容器的shell命令方式

        eg: docker create ******

        :param cmd:
        :return:
        {
            "message": , error_reason or container_id
            "status":
        }
        """
        pattern_cmd = '^docker\s+(run|start|create)\s+.*'
        if re.match(pattern_cmd, cmd) is None:
            return {'message': None, 'statusCode': 3, 'errMessage': 'illegal command'}
        read_obj = os.popen(cmd)
        container = read_obj.read()
        if not container:
            return {'message': None, 'statusCode': 2, 'errMessage': 'create error. please check again'}
        container_id = container.split('\n')[0]
        _log.write(str(container_id))
        # 检测是否创建成功
        status = True
        try:
            self.client.containers.get(container_id)
        except NotFound:
            status = False
        if status:
            return {'message': 'ok', 'statusCode': 0}
        else:
            return {'message': None, 'statusCode': 2, 'errMessage': 'UnKnow error'}


class Images(object):
    """

    镜像相关类

    """

    def __init__(self):
        """ 初始化客户端环境

        """
        self.client = docker.from_env()
        try:
            self.client.version()
        except APIError, e:
            print e

    def get_list(self, all_=True):
        """ 获取镜像列表

        :parameter all_: 是否显示构建层镜像.默认为False
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
                },
            "statusCode": ,
            "errMessage":
            },...
            ],
        "statusCode": int,
        "errMessage":
        }
        """
        images_info = []
        status_code = 0
        err_message = ''
        for image in self.client.images.list(all=all_):
            image_info = self.get_info(str(image.id))
            if image_info.get('statusCode') != 0:
                status_code = 1
                err_message = image.id + u'获取信息失败'
            images_info.append(image_info)
        return {'message': images_info, 'statusCode': status_code, 'errMessage': err_message}

    @parameter_validation
    @format_error
    def get_info(self, id_):
        """ 获取单个镜像信息

        :type id_: 镜像名或镜像id, 使用镜像名时必须指名版本号
        :return:
        {
            "message":{
                'id': 镜像id,
                'short_id': 镜像短id,
                'tags': 镜像标签列表,
                'created': 镜像创建日期,
                'size': 镜像大小,
                'os': 镜像系统
            } ,
            'statusCode':,
            'errMessage':,
        }
        """
        image = self.client.images.get(id_)
        image_info = {
            'id_': image.id,
            'short_id': image.short_id,
            'tags': image.tags,
            # 此处去掉毫秒s
            'created': image.attrs.get('Created').split('.')[0],
            'size': image.attrs.get('Size'),
            'os': image.attrs.get('Os')
        }
        return {'message': image_info, 'statusCode': 0}

    @parameter_validation
    @format_error
    def remove(self, id_, force=False):
        """ 删除镜像

        类似与`docker rmi`

        :param id_: 镜像的名字或id. `str`.建议使用id.
        :param force: 是否强制删除. `Boolean` .默认为False
        :return:
        {
            "message": str,
            "statusCode": int.执行状态
            "errMessage"
        }
        """
        noprune = False
        if force:
            noprune = True
        self.client.images.remove(image=id_, force=force, noprune=noprune)
        return {'message': 'ok', 'statusCode': 0}

    @format_error
    def remove_all(self, force=True):
        """ 一次性删除本节点所有镜像

        类似于```docker rmi `docker images -q` ```

        :param force: 是否强制删除 默认为true
        :return:
        """
        for image in self.client.images.list(all=True):
            image_id = str(image.id)
            self.remove(image_id, force)
        return {'message': 'ok', 'statusCode': 0}

    @format_error
    def remove_list(self, repositories, force=False):
        """ 删除镜像列表中的镜像

        :param repositories: 镜像的名字或id列表. `list[]`
        :param force: 是否强制删除. `Boolean`. 默认为False
        :return:
        {
            'message': [
                {image_id_name: {'message': ,'statusCode': }}
            ],
        'statusCode': int    # 有一个执行错误则标记为False
        }
        """
        if not isinstance(repositories, list) or not isinstance(force, bool):
            return {'message': None, 'statusCode': 3, 'errMessage': 'repositories must be list and force must be bool'}
        remove_status = []
        status_code = 0
        err_message = ''
        for image in repositories:
            exec_result = self.remove(image, force)
            if 0 != exec_result.get('statusCode'):
                status_code = 1
                err_message = image.id + u'删除失败;'
            remove_status.append({image: exec_result})
        return {'message': remove_status, 'statusCode': status_code, 'errMessage': err_message}

    @format_error
    def pull(self, repository, tag='latest'):
        """ 下载远程镜像到本地

        :param repository: 下载的镜像名字. `str`
        :param tag: 下载镜像标签.默认为latest. `str`
        :return:
        {
        "message": str,
        "statusCode": int.执行状态,
        "errMessage":
        }
        """
        if not isinstance(repository, str) or not isinstance(tag, str):
            return {'message': None, 'statusCode': 3, 'errMessage': 'repository and tag must be str'}
        self.client.images.pull(repository, tag=tag)
        return {'message': 'ok', 'statusCode': 0}

    @format_error
    def pull_list(self, repositories):
        """ 下载多个镜像到本地

        必须指名版本(tag)

        :param repositories: 下载的镜像名列表. [{'repository': ,'tag': },...]
        :return: pull状态列表
        {
        'message': [
                {repository: {'message': ,'status': }}
            ],
        'status': bool    # 有一个执行错误则标记为False
        }
        """
        pull_status = []
        if not isinstance(repositories, list):
            return {'errMessage': 'repositories must be list', 'message': None, 'statusCode': 3}
        status_code = 0
        err_message = ''
        for repository in repositories:
            exec_result = self.pull(repository.get('repository'), repository.get('tag', 'latest'))
            if exec_result.get('statusCode') != 0:
                status_code = 1
                err_message = repository.get('repository') + ':' + repository.get('tag', 'latest')
            pull_status.append({repository: exec_result})
        return {'message': pull_status, 'statusCode': status_code, 'errMessage': err_message}

    @format_error
    def search(self, *args, **kwargs):
        """ 查询

        Search for IMAGE_OBJ on Docker Hub. Similar to the docker search command.

        :return:
        {
        "message": [],
        "status": bool.执行状态
        }
        """
        return {'message': self.client.images.search(*args, **kwargs), 'statusCode': 0}

    @parameter_validation
    @format_error
    def tag(self, id_, repository, tag=None, **kwargs):
        """ 修改镜像名

        :param id_: 要修改的镜像名或id.使用镜像名时需要指名tag. str
        :param repository: 新的镜像名. str
        :param tag: tag标签. 默认为None
        :param kwargs: force: 是否强制修改. str
        :return: 执行状态.
        {
        "message": str,
        "status": bool.执行状态
        }
        """
        image_obj = self.client.images.get(id_)
        if not isinstance(repository, str):
            return {'message': None, 'statusCode': 3, 'errMessage': 'repository must be str'}
        image_obj.tag(repository, tag, **kwargs)
        return {'message': 'ok', 'statusCode': 0}
