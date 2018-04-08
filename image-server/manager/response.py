# coding=utf-8
import sys
import datetime
from flask import Flask, url_for
from flask_restful import Api
from flask_restful import Resource
from flask_restful import reqparse
from image import Image
from image import ImageRegistry
sys.path.append('..')
from etc.sys_set import IMAGE_SERVICE_PORT_VAR
from etc.sys_set import THE_MACHINE_IP


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
        print args
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


API.add_resource(ImageResponse, '/image_server/', endpoint='images')
API.add_resource(ImageRegistryResponse, '/image_registry_server/', endpoint='images_registry')


def start_response():
    """启动响应服务

    :return:
    """
    print '镜像服务器运行中...'
    APP.run(port=IMAGE_SERVICE_PORT_VAR, host=THE_MACHINE_IP)

