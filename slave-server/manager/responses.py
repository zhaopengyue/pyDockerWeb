#!coding: utf-8
"""
本程序响应主服务请求执行
"""
import sys
import datetime
from flask import Flask, url_for, request, jsonify
from flask_restful import Api
from flask_restful import Resource
from flask_restful import reqparse
sys.path.append('..')
from node import Containers
from node import Images
from node import System
from etc.sys_set import SLAVE_SERVICE_PORT_VAR, THE_MACHINE_IP


APP = Flask(__name__)
API = Api(APP)
CONTAINER_OBJ = Containers()
IMAGE_OBJ = Images()


class Containers(Resource):
    """ 获取容器列表

    """
    @staticmethod
    def get():
        message = CONTAINER_OBJ.get_list()
        message.update(
            {'url': url_for('containers', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
        return message

    @staticmethod
    def post():
        message = CONTAINER_OBJ.get_list()
        message.update({'url': url_for('containers', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
        return message


class Container(Resource):
    """ 处理单个容器

    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('container_id_or_name', type=str, help='参数为容器ID或容器名')
        self.reqparse.add_argument('type', type=str)
        self.reqparse.add_argument('new_name', type=str)
        self.reqparse.add_argument('signal', type=str)
        self.reqparse.add_argument('timeout', type=int)
        self.reqparse.add_argument('stdout', type=str)
        self.reqparse.add_argument('stderr', type=str)
        self.reqparse.add_argument('timestamps', type=str)
        self.reqparse.add_argument('repository', type=str)
        self.reqparse.add_argument('tag', type=str)
        self.reqparse.add_argument('change', type=str)
        self.reqparse.add_argument('author', type=str)
        self.reqparse.add_argument('message', type=str)
        self.reqparse.add_argument('shell_cmd', type=str)
        self.reqparse.add_argument('v', type=bool)
        self.reqparse.add_argument('link', type=bool)
        self.reqparse.add_argument('force', type=bool)
        super(Container, self).__init__()

    def get(self):
        """ 获取容器信息

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
        "status": bool,
        "refresh": ,
        "url":
        }
        """
        args = self.reqparse.parse_args()
        container_id_or_name = args.get('container_id_or_name')
        message = CONTAINER_OBJ.get_info(container_id_or_name)
        message.update({'refresh': datetime.datetime.now().strftime('%c'), 'url': url_for('container', _external=True)})
        return message

    def post(self):
        """ 处理容器操作

        :return:
        """
        args = self.reqparse.parse_args()
        container_id_or_name = args.get('container_id_or_name')
        type_ = args.get('type')
        if type_ == 'kill':
            signal = args.get('signal', None)
            message = CONTAINER_OBJ.kill(container_id_or_name, signal)
        elif type_ == 'start':
            message = CONTAINER_OBJ.start(container_id_or_name)
        elif type_ == 'stop':
            timeout = args.get('timeout', 10)
            if not timeout:
                timeout = 10
            message = CONTAINER_OBJ.stop(container_id_or_name, timeout)
        elif type_ == 'restart':
            timeout = args.get('timeout', 10)
            if not timeout:
                timeout = 10
            message = CONTAINER_OBJ.restart(container_id_or_name, timeout)
        elif type_ == 'rename':
            new_name = args.get('new_name')
            message = CONTAINER_OBJ.rename(container_id_or_name, new_name)
        elif type_ == 'pause':
            message = CONTAINER_OBJ.pause(container_id_or_name)
        elif type_ == 'unpause':
            message = CONTAINER_OBJ.unpause(container_id_or_name)
        elif type_ == 'logs':
            log_stdout = args.get('stdout', True)
            log_stderr = args.get('stderr', True)
            log_time = args.get('timestamps', True)
            if not log_stderr:
                log_stderr = True
            if not log_time:
                log_time = True
            if not log_stdout:
                log_stdout = True
            message = CONTAINER_OBJ.logs(container_id_or_name, stdout=log_stdout, stderr=log_stderr, timestamps=log_time)
        elif type_ == 'commit':
            repository = args.get('repository', None)
            tag = args.get('tag', None)
            changes = args.get('changes', None)
            author = args.get('author', None)
            message_ = args.get('message', None)
            message = CONTAINER_OBJ.commit(container_id_or_name, repository, tag,
                                           changes=changes, author=author, message=message_)
        elif type_ == 'create_shell':
            shell_cmd = args.get('shell_cmd', '')
            message = CONTAINER_OBJ.create_shell(cmd=shell_cmd)
        elif type_ == 'remove':
            v = args.get('v', False)
            link = args.get('link', False)
            force = args.get('force', False)
            message = CONTAINER_OBJ.remove(container_id_or_name, v=v, link=link, force=force)
        else:
            message = {
                'message': 'container action type: \'' + type_ + '\' not found',
                'status': False
            }
        message.update({'refresh': datetime.datetime.now().strftime('%c'), 'url': url_for('container', _external=True)})
        return message


class Images(Resource):

    @staticmethod
    def get():
        message = IMAGE_OBJ.get_list()
        message.update(
            {'url': url_for('images', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
        return message

    @staticmethod
    def post():
        message = IMAGE_OBJ.get_list()
        message.update(
            {'url': url_for('images', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
        return message


class Image(Resource):
    """ 处理单个镜像

    """

    def __init__(self):
        super(Image, self).__init__()
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('image_id_or_name', type=str, help='参数为镜像ID或镜像名')
        self.reqparse.add_argument('type', type=str)
        self.reqparse.add_argument('force', type=bool, help='force must be bool')
        self.reqparse.add_argument('tag', type=str)
        self.reqparse.add_argument('repositories', type=list)
        self.reqparse.add_argument('repository', type=str)

    def get(self):
        args = self.reqparse.parse_args()
        image_id_or_name = args.get('image_id_or_name')
        message = IMAGE_OBJ.get_info(image_id_or_name)
        message.update({'refresh': datetime.datetime.now().strftime('%c'), 'url': url_for('image', _external=True)})
        return message

    def post(self):
        args = self.reqparse.parse_args()
        image_id_or_name = args.get('image_id_or_name')
        type_ = args.get('type')
        if type_ == 'remove':
            force = args.get('force', False)
            if not force:
                force = False
            message = IMAGE_OBJ.remove(image_id_or_name, force)
        # elif type_ == 'remove_list':
        #     images_list = args.get('repositories')
        #     force = args.get('force', False)
        #     if not force:
        #         force = False
        #     message = IMAGE_OBJ.remove_list(images_list, force)
        elif type_ == 'pull':
            repository = args.get('repository')
            tag = args.get('tag', 'latest')
            if not tag:
                tag = 'latest'
            message = IMAGE_OBJ.pull(repository, tag)
        # elif type_ == 'pull_list':
        #     repositories = args.get('repositories')
        #     message = IMAGE_OBJ.pull_list(repositories)
        elif type_ == 'search':
            repository = args.get('repository')
            message = IMAGE_OBJ.search(repository)
        elif type_ == 'tag':
            repository = args.get('repository')
            tag = args.get('tag', None)
            force = args.get('force', None)
            message = IMAGE_OBJ.tag(image_id_or_name, repository, tag, force=force)
        else:
            message = {
                'message': 'image action type: \'' + type_ + '\' not found',
                'status': False
            }
        message.update({'refresh': datetime.datetime.now().strftime('%c'), 'url': url_for('image', _external=True)})
        return message


class Sys(Resource):

    def __init__(self):
        super(Sys, self).__init__()
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('type', type=str, required=True, help='参数为系统信息类型(disk or mem or cpu)')

    def get(self):
        args = self.reqparse.parse_args()
        type_ = args.get('type')
        if type_ == 'mem':
            message = System.get_mem_info()
        elif type_ == 'disk':
            message = System.get_disk_info()
        elif type_ == 'cpu':
            message = System.get_cpu_info()
        else:
            message = {
                'message': 'system type: \'' + type_ + '\' not found',
                'status': False
            }
        message.update({'refresh': datetime.datetime.now().strftime('%c'), 'url': url_for('system', _external=True)})
        return message


@APP.route('/healthy/')
def check_healthy():
    return 'ok'


API.add_resource(Containers, '/container/_all/', endpoint='containers')
API.add_resource(Container, '/container/', endpoint='container')
API.add_resource(Images, '/image/_all/', endpoint='images')
API.add_resource(Image, '/image/', endpoint='image')
API.add_resource(Sys, '/system/', endpoint='system')


def start_response():
    """启动响应服务

    :return:
    """
    APP.run(port=SLAVE_SERVICE_PORT_VAR, host=THE_MACHINE_IP)
