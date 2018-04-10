# coding=utf-8
import sys
import datetime
from flask import Flask, url_for
from flask_restful import Api
from flask_restful import Resource
from flask_restful import reqparse
from image import Image
from image import ImageRegistry
from image import ImageHarbor
sys.path.append('..')
from etc.sys_set import IMAGE_SERVICE_PORT_VAR
from etc.sys_set import THE_MACHINE_IP
from etc.sys_set import HARBOR_URL


_image = Image()
_image_registry = ImageRegistry()
APP = Flask(__name__)
API = Api(APP)


class ImageResponse(Resource):

    def __init__(self):
        super(ImageResponse, self).__init__()
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('to_host', type=str)
        self.reqparse.add_argument('image_name', type=str)

    def get(self):
        message = _image.get_image_list()
        message.update(
            {'url': url_for('images', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
        return message

    def post(self):
        args = self.reqparse.parse_args()
        to_host = args.get('to_host')
        image_name = args.get('image_name')
        message = _image.download(to_host, image_name)
        message.update(
            {'url': url_for('images', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
        return message


class ImageRegistryResponse(Resource):

    def __init__(self):
        super(ImageRegistryResponse, self).__init__()
        self.reqparse = reqparse.RequestParser()

    def get(self):
        message = _image_registry.get_image_list()
        message.update(
            {'url': url_for('images_registry', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
        return message


class ImageHarborResponse(Resource):

    def __init__(self):
        super(ImageHarborResponse, self).__init__()
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('username', type=str)
        self.reqparse.add_argument('password', type=str)
        self.reqparse.add_argument('cacert', type=str)
        self.reqparse.add_argument('insecure', type=str)

    def get(self):
        image_harbor = ImageHarbor(HARBOR_URL)
        message = image_harbor.get_all_repositories()
        message.update(
            {'url': url_for('images_registry', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
        return message

    def post(self):
        args = self.reqparse.parse_args()
        username = args.get('username')
        password = args.get('password')
        cacert = args.get('cacert')
        insecure = args.get('insecure')
        image_harbor = ImageHarbor(HARBOR_URL, username, password, cacert=cacert, insecure=insecure)
        # 登录
        image_harbor.authenticate()
        message = image_harbor.get_all_repositories()
        message.update(
            {'url': url_for('images_registry', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
        # 注销
        image_harbor.unauthenticate()
        return message


@APP.route('/healthy/')
def check_healthy():
    return 'ok'


API.add_resource(ImageResponse, '/image_server/', endpoint='images')
API.add_resource(ImageRegistryResponse, '/image_registry_server/', endpoint='images_registry')
API.add_resource(ImageHarborResponse, '/image_harbor_server/', endpoint='images_harbor')


def start_response():
    """启动响应服务

    :return:
    """
    print '镜像服务器运行中...'
    APP.run(port=IMAGE_SERVICE_PORT_VAR, host=THE_MACHINE_IP)

