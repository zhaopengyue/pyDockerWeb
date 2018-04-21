#!coding: utf-8
"""
本程序封装了系统信息获取,容器及镜像操作等相关方法
"""
import os
import sys
import datetime
import docker
import re
from docker.errors import APIError
from docker.errors import NotFound
from docker.errors import ImageNotFound


class System(object):
    """
    获取CPU,内存,硬盘信息

    """
    @staticmethod
    def get_cpu_info():
        """获取本节点的CPU信息

        :return:CPU相关信息
        {'message':{
                'physical_cpu_num': 物理CPU个数
                'physical_cpu_core_num': 每个物理CPU核数,
                'processor_core_num': 逻辑CPU核数
                'all_cpu_core': 总核数 = 物理CPU个数 * 每个物理CPU核数
            },
        'status': bool
        } or
        {
        'message':None
        'status': bool
        }
        """
        # 物理CPU个数
        physical_cpu_num_cmd = 'cat /proc/cpuinfo| grep "physical id"| sort| uniq| wc -l'
        # 查看每个物理CPU中core的个数(即核数)
        physical_cpu_core_num_cmd = 'cat /proc/cpuinfo| grep "cpu cores"|uniq |cut -d \':\' -f 2|sed \'s/^[ \t]*//g\''
        # 逻辑CPU核数
        processor_core_num_cmd = 'cat /proc/cpuinfo | grep \'processor\' | sort | uniq | wc -l'
        try:
            physical_cpu_num = os.popen(physical_cpu_num_cmd).read().split('\n')[0]
            if not physical_cpu_num:
                physical_cpu_num = 0
        except Exception:
            physical_cpu_num = 0
        try:
            physical_cpu_core_num = os.popen(physical_cpu_core_num_cmd).read().split('\n')[0]
            if not physical_cpu_core_num:
                physical_cpu_core_num = 0
        except Exception:
            physical_cpu_core_num = 0
        try:
            processor_core_num = os.popen(processor_core_num_cmd).read().split('\n')[0]
            if not processor_core_num:
                processor_core_num = 0
        except Exception:
            processor_core_num = 0
        cpu_info = {
            'physical_cpu_num': physical_cpu_num,
            'physical_cpu_core_num': physical_cpu_core_num,
            'processor_core_num': processor_core_num,
            'all_cpu_core': str(int(physical_cpu_num) * int(physical_cpu_core_num))
        }
        return {'message': cpu_info, 'status': True}

    @staticmethod
    def get_mem_info():
        """ 获取内存信息

        :return:
        {
            message: {
                'total_mem':, 内存总量
                'free_mem': , 空闲内存量
                'active_mem': 使用内存量
                cache/buffer_mem: 缓存量
            },
            'status': bool
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
        except Exception, e:
            mem_info = None
        if mem_info:
            status = True
        else:
            status = False
        return {'message': mem_info, 'status': status}

    @staticmethod
    def get_disk_info():
        """ 获取磁盘信息

        单位为kb

        :return:
        ({
            'available': 可用总量,
            'capacity': 总量
            'used': 已使用量
        }, )
        """
        dick_info = {}
        disk = os.statvfs("/")
        dick_info['available'] = disk.f_bsize * disk.f_bavail / 1024
        dick_info['capacity'] = disk.f_bsize * disk.f_blocks / 1024
        dick_info['used'] = disk.f_bsize * disk.f_bfree / 1024
        return {'message': dick_info, 'status': True}


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

    def get_list(self):
        """ 获取容器列表

        获取所有容器,包含未运行容器和正在运行容器

        :return:
        {
        "message":[{
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
            'status': bool
            },...
            ],
        "status": bool
        }
        """
        containers_info = []
        exec_status = True
        for container in self.client.containers.list(all=True):
            # 此处忽略毫秒
            exec_result = self.get_info(str(container.id))
            if not exec_result.get('status'):
                exec_status = False
            containers_info.append(exec_result)
        return {'message': containers_info, 'status': exec_status}

    def get_info(self, container_id_or_name):
        """ 获取单个容器信息

        :param container_id_or_name: 容器名或ID
        :return:
        {
            message: {
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
            'status': bool
        }
        """
        if not isinstance(container_id_or_name, str):
            message = 'container_id_or_name must be str'
            return {'message': message, 'status': False}
        try:
            container = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'container id or name: ' + container_id_or_name + ' not found'
            return {'message': message, 'status': False}

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
            'id': container.id,
            'short_id': container.short_id,
            'status': container.status,
            'running': container.attrs.get('State').get('Running'),
            'paused': container.attrs.get('State').get('Paused'),
            'finishedAt': finished_at,
            'startedAt': started_at,
            'created': container.attrs['Created'],
            'image': container.attrs.get('Config').get('Image'),
            'name': container.attrs.get('Name'),
            'exit_time': self._get_exit_time(container.status, finished__time, started_time)
        }
        return {'message': container_info, 'status': True}

    def _get_exit_time(self, status, end_time, start_time):
        """ 获取容器退出到现在的时间

        :type status: 容器状态
        :type old_time: datetime obj
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

    def kill(self, container_id_or_name, signal=None):
        """ 杀死容器或向容器发送信号

        类似于`docker kill`

        :param container_id_or_name: 容器. str
        :param signal: 要发送的信号.默认值为None(即SIGKILL). str or int
        :return: 执行状态信息
        """
        if not isinstance(container_id_or_name, str):
            message = 'container_id_or_name must be str'
            return {'message': message, 'status': False}
        try:
            container_obj = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'container id or name: ' + container_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            container_obj.kill(signal)
        except APIError, e:
            print e
            message = 'kill fail'
            return {'message': message, 'status': False}
        return {'message': 'ok', 'status': True}

    def start(self, container_id_or_name):
        """ 启动容器

        类似`docker start`

        :param container_id_or_name: 容器id或名字. str
        :return: 执行状态
        """
        if not isinstance(container_id_or_name, str):
            message = 'container_id_or_name must be str'
            return {'message': message, 'status': False}
        try:
            container_obj = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'container id or name: ' + container_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            container_obj.start()
        except APIError, e:
            print e
            message = 'start fail'
            return {'message': message, 'status': False}
        return {'message': 'ok', 'status': True}

    def stop(self, container_id_or_name, timeout=10):
        """ 停止容器

        类似`docker stop`

        :param timeout: 停止容器时的超时时间.若超时时间内容器未停止,则杀死容器.
        :param container_id_or_name: 容器id或名字. str
        :return: 执行状态. bool
        """
        if not isinstance(container_id_or_name, str):
            message = 'container_id_or_name must be str'
            return {'message': message, 'status': False}
        try:
            container_obj = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'container id or name: ' + container_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            container_obj.stop(timeout=timeout)
        except APIError, e:
            print e
            message = 'stop fail'
            return {'message': message, 'status': False}
        return {'message': 'ok', 'status': True}

    def restart(self, container_id_or_name, timeout=10):
        """ 停止容器

        类似`docker restart`

        :param timeout: 停止容器时的超时时间.若超时时间内容器未停止,则杀死容器.
        :param container_id_or_name: 容器id或名字. str
        :return: 执行状态. bool
        """
        if not isinstance(container_id_or_name, str):
            message = 'container_id_or_name must be str'
            return {
                'message': message,
                'status': False
            }
        if not isinstance(timeout, int):
            message = 'timeout must be str'
            return {
                'message': message,
                'status': False
            }
        try:
            container_obj = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'container id or name: ' + container_id_or_name + ' not found'
            return {
                'message': message,
                'status': False
            }
        try:
            container_obj.restart(timeout=timeout)
        except APIError, e:
            print e
            message = 'restart fail'
            return {'message': message, 'status': False}
        return {'message': 'ok', 'status': True}

    def rename(self, container_id_or_name, new_name):
        """ 重命名容器

        类似于`docker rename`

        :param container_id_or_name: 容器id或名字. str
        :param new_name: 新的容器名. str
        :return: 执行状态. bool
        """
        if not isinstance(container_id_or_name, str) or not isinstance(new_name, str):
            message = 'container_id_or_name and new_name must be str'
            return {'message': message, 'status': False}
        try:
            container_obj = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'Container id or name: ' + container_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            container_obj.rename(new_name)
        except APIError, e:
            print e
            return {'message': 'rename fail', 'status': False}
        return {'message': 'ok', 'status': True}

    def pause(self, container_id_or_name):
        """ 启动容器

        类似`docker pause`

        :param container_id_or_name: 容器id或名字. str
        :return: 执行状态. bool
        """
        if not isinstance(container_id_or_name, str):
            message = 'container_id_or_name  must be str'
            return {'message': message, 'status': False}
        try:
            container_obj = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'container id or name: ' + container_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            container_obj.pause()
        except APIError, e:
            print e
            return {'message': 'pause fail', 'status': False}
        return {'message': 'ok', 'status': True}

    def unpause(self, container_id_or_name):
        """ 启动容器

        类似`docker unpause`

        :param container_id_or_name: 容器id或名字. str
        :return: 执行状态. bool
        """
        if not isinstance(container_id_or_name, str):
            message = 'container_id_or_name  must be str'
            return {'message': message, 'status': False}
        try:
            container_obj = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'container id or name: ' + container_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            container_obj.unpause()
        except APIError, e:
            print e
            return {'message': 'unpause fail', 'status': False}
        return {'message': 'ok', 'status': True}

    def logs(self, container_id_or_name, **kwargs):
        """ 获取容器日志

        获取日志输出,暂时不涉及流式输出,类似于`docker logs`

        :parameter : stdout: 获取标准输出流. bool
                     stderr: 获取标准错误流 bool
                     timestamps: 展示时间戳 bool
        :return:
        """
        if not isinstance(container_id_or_name, str):
            message = 'container_id_or_name  must be str'
            return {'message': message, 'status': False}
        try:
            container_obj = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'container id or name: ' + container_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            info = container_obj.logs(**kwargs)
        except APIError, e:
            print e
            return {'message': 'log fail', 'status': False}
        return {'message': info, 'status': True}

    def commit(self, container_id_or_name, repository=None, tag=None, **kwargs):
        """ 构建一个容器为镜像

        类似于`docker commit`

        :param container_id_or_name: 容器名或id. str
        :param tag: The tag to push. str
        :param repository: The repository to push the image to. str
        :parameter message: A commit message. str
                   author: The name of the author. str
                   changes: Dockerfile instructions to apply while committing. str
        :return: 执行状态.
        {
            "message": ,
            "status"
        }
        """
        if not isinstance(repository, str) or not isinstance(tag, str) or not isinstance(container_id_or_name, str):
            message = 'repository and tag and container_id_or_name must be str'
            return {'message': message, 'status': False}
        try:
            container_obj = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'container id or name: ' + container_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            container_obj.commit(repository=repository, tag=tag, **kwargs)
        except APIError, e:
            print e
            return {'message': 'commit fail', 'status': False}
        return {'message': 'ok', 'status': True}

    def remove(self, container_id_or_name, **kwargs):
        """ 删除容器, 类似于

        docker rm ``

        :param container_id_or_name: 容器id或名字 .str
        :param kwargs: v: 是否删除数据卷 .bool
                       link: 是否删除连接容器 .bool
                       force: 是否强制删除 .bool
        :return:
        """
        try:
            container_obj = self.client.containers.get(container_id_or_name)
        except NotFound, e:
            print e
            message = 'container id or name: ' + container_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            container_obj.remove(**kwargs)
        except APIError, e:
            print e
            return {'message': 'remove fail', 'status': False}
        return {'message': 'ok', 'status': True}

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
            return {'message': 'illegal command', 'status': False}
        read_obj = os.popen(cmd)
        container = read_obj.read()
        if not container:
            return {'message': 'create error. please check again', 'status': False}
        container_id = container.split('\n')[0]
        # 检测是否创建成功
        status = True
        try:
            self.client.containers.get(container_id)
        except NotFound:
            status = False
        if status:
            return {'message': container_id, 'status': status}
        else:
            return {'message': 'create fail', 'status': status}


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
                } or err_reason,
            "status": bool.执行状态
            },...
            ],
        "status": bool
        }
        """
        images_info = []
        exec_status = True
        for image in self.client.images.list(all=all_):
            image_info = self.get_info(str(image.id))
            if not image_info.get('status'):
                exec_status = False
            images_info.append(image_info)
        return {'message': images_info, 'status': exec_status}

    def get_info(self, image_id_or_name):
        """ 获取单个镜像信息

        :type image_id_or_name: 镜像名或镜像id, 使用镜像名时必须指名版本号
        :return:
        {
            "message":{
                'id': 镜像id,
                'short_id': 镜像短id,
                'tags': 镜像标签列表,
                'created': 镜像创建日期,
                'size': 镜像大小,
                'os': 镜像系统
            } or err_reason,
            "status": bool.执行状态
        }
        """
        if not isinstance(image_id_or_name, str):
            message = 'image_id_or_name must be str'
            return {'message': message, 'status': False}
        try:
            image = self.client.images.get(image_id_or_name)
        except ImageNotFound, e:
            print e
            message = 'image id or name: ' + image_id_or_name + ' not found'
            return {'message': message, 'status': False}
        image_info = {
            'id': image.id,
            'short_id': image.short_id,
            'tags': image.tags,
            # 此处去掉毫秒s
            'created': image.attrs.get('Created').split('.')[0],
            'size': image.attrs.get('Size'),
            'os': image.attrs.get('Os')
        }
        return {'message': image_info, 'status': True}

    def remove(self, image_id_or_name, force=False):
        """ 删除镜像

        类似与`docker rmi`

        :param image_id_or_name: 镜像的名字或id. `str`.建议使用id.
        :param force: 是否强制删除. `Boolean` .默认为False
        :return:
        {
            "message": str,
            "status": bool.执行状态
        }
        """
        if not isinstance(image_id_or_name, str):
            message = 'image_id_or_name must be str'
            return {'message': message, 'status': False}
        try:
            # 确认是否存在
            self.client.images.get(image_id_or_name)
        except ImageNotFound, e:
            print e
            message = 'image id or name: ' + image_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            noprune = False
            if force:
                noprune = True
            self.client.images.remove(image=image_id_or_name, force=force, noprune=noprune)
        except APIError, e:
            # 需要强制删除
            print e
            return {'message': 'remove fail', 'status': False}
        return {'message': 'ok', 'status': True}

    def remove_list(self, repositories, force=False):
        """ 删除镜像列表中的镜像

        :param repositories: 镜像的名字或id列表. `list[]`
        :param force: 是否强制删除. `Boolean`. 默认为False
        :return:
        {
        'message': [
                {image_id_name: {'message': ,'status': }}
            ],
        'status': bool    # 有一个执行错误则标记为False
        }
        """
        if not isinstance(repositories, list) or not isinstance(force, bool):
            message = 'repositories must be list and force must be bool'
            return {'message': message, 'status': False}
        remove_status = []
        exec_status = True
        for image in repositories:
            exec_result = self.remove(image, force)
            if not exec_result.get('status'):
                exec_status = False
            remove_status.append({image: exec_result})
        return {'message': remove_status, 'status': exec_status}

    def pull(self, repository, tag='latest'):
        """ 下载远程镜像到本地

        :param repository: 下载的镜像名字. `str`
        :param tag: 下载镜像标签.默认为latest. `str`
        :return:
        {
        "message": str,
        "status": bool.执行状态
        }
        """
        if not isinstance(repository, str) or not isinstance(tag, str):
            message = 'repository and tag must be str'
            return {'message': message, 'status': False}
        try:
            print repository, tag
            self.client.images.pull(repository, tag=tag)
        except APIError, e:
            print e
            return {'message': 'pull fail', 'status': False}
        return {'message': 'ok', 'status': True}

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
            return {'message': 'repositories must be list'}
        exec_status = True
        for repository in repositories:
            exec_result = self.pull(repository.get('repository'), repository.get('tag', 'latest'))
            if not exec_result.get('status'):
                exec_status = False
            pull_status.append({repository: exec_result})
        return {'message': pull_status, 'status': exec_status}

    def search(self, *args, **kwargs):
        """ 查询

        Search for IMAGE_OBJ on Docker Hub. Similar to the docker search command.

        :return:
        {
        "message": [],
        "status": bool.执行状态
        }
        """
        try:
            return {'message': self.client.images.search(*args, **kwargs), 'status': True}
        except APIError, e:
            print e
            return {'message': 'search fail', 'status': False}

    def tag(self, image_id_or_name, repository, tag=None, **kwargs):
        """ 修改镜像名

        :param image_id_or_name: 要修改的镜像名或id.使用镜像名时需要指名tag. str
        :param repository: 新的镜像名. str
        :param tag: tag标签. 默认为None
        :param kwargs: force: 是否强制修改. str
        :return: 执行状态.
        {
        "message": str,
        "status": bool.执行状态
        }
        """
        if not isinstance(image_id_or_name, str) or not isinstance(repository, str):
            message = 'image_id_or_name and repository must be str'
            return {'message': message, 'status': False}
        try:
            # 确认是否存在
            image_obj = self.client.images.get(image_id_or_name)
        except ImageNotFound, e:
            print e
            message = 'image id or name: ' + image_id_or_name + ' not found'
            return {'message': message, 'status': False}
        try:
            image_obj.tag(repository, tag, **kwargs)
        except APIError, e:
            print e
            return {'message': 'tag fail', 'status': False}
        return {'message': 'ok', 'status': True}