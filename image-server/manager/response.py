# coding=utf-8
import sys
import datetime
from flask import Flask, url_for
from flask_restful import Api
from flask_restful import Resource
from flask_restful import reqparse
from image import ImageHarbor
sys.path.append('..')
from etc.sys_set import IMAGE_SERVICE_PORT_VAR
from etc.sys_set import THE_MACHINE_IP
from etc.sys_set import HARBOR_URL


APP = Flask(__name__)
API = Api(APP)


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
            {'url': url_for('images_harbor', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
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
            {'url': url_for('images_harbor', _external=True), 'refresh': datetime.datetime.now().strftime('%c')})
        # 注销
        image_harbor.unauthenticate()
        return message


@APP.route('/healthy/')
def check_healthy():
    return 'ok'


API.add_resource(ImageHarborResponse, '/image_harbor_server/', endpoint='images_harbor')


def start_response():
    """启动响应服务

    :return:
    """
    APP.run(port=IMAGE_SERVICE_PORT_VAR, host=THE_MACHINE_IP)

