#!coding: utf-8
""" 操作教师服务镜像

"""
import os
import sys
import requests
import docker
import json
from docker.errors import ImageNotFound
sys.path.append('..')
from etc.core_var import TMP_DIR
from etc.sys_set import SLAVE_UPLOAD_PORT
from etc.sys_set import PRIVATE_REGISTRY_PORT
from etc.sys_set import THE_MACHINE_IP


class Image(object):
    """ 获取镜像服务器镜像列表, 向请求节点发送镜像

    """
    def __init__(self):
        """ 初始化客户端

        """
        self.client = docker.from_env()

    def get_image_list(self, _all=False):
        """ 获取镜像列表

        :parameter _all: 是否显示构建层镜像.默认为False
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
        for image_ in self.client.images.list(all=_all):
            image_ = self.client.images.get(image_.short_id)
            for tag in image_.tags:
                images_info.append({
                    'id': image_.id,
                    'short_id': image_.short_id,
                    'tag': tag,
                    # 此处去掉毫秒s
                    'created': image_.attrs.get('Created').split('.')[0],
                    'size': str(round(float(image_.attrs.get('Size')) / 1024 / 1024, 2)) + 'M',
                    'os': image_.attrs.get('Os')
                })
        return {'message': images_info, 'status': exec_status}

    def download(self, to_host, image_name):
        """ 下载文件到指定节点

        :param to_host:
        :param image_name:
        :return:
        """
        # try:
        #     image_obj = self.client.images.get(image_name)
        # except ImageNotFound:
        #     return {'message': 'image name not found, please check again', 'status': False}
        # 转移路径符号
        file_name = image_name.replace('/', '_').replace(':', '-') + '.tar'
        tmp_path = os.path.join(TMP_DIR, file_name)
        os.system('docker save >' + tmp_path + ' ' + image_name)
        # try:
        #     resp = image_obj.save()
        #     with open(tmp_path, 'w') as f:
        #         for stream in resp.stream():
        #             f.write(stream)
        # except APIError:
        #     return {'message': 'save image error', 'status': False}
        # 校验路径
        if not os.path.exists(tmp_path):
            return {'message': 'save image error', 'status': False}
        # 流式上传
        request_url = 'http://' + str(to_host) + ':' + str(SLAVE_UPLOAD_PORT)
        print request_url
        try:
            # headers = {'Content-Type': 'application/x-tar'}
            files = {
                'file': (image_name, open(tmp_path, 'rb'), 'application/x-tar')
            }
            requests.post(request_url, files=files)
            return {'message': 'send image success', 'status': True}
        except requests.ConnectionError:
            return {'message': 'host error', 'status': False}


class ImageRegistry(object):

    def __init__(self):
        self.root_path = 'http://' + THE_MACHINE_IP + ':' + str(PRIVATE_REGISTRY_PORT) + '/v2/'

    def __str__(self):
        return 'Private registry'

    def get_image_list(self):
        """ 返回私有镜像仓库镜像列表

        :return:
        """
        info = {'message': [], 'status': False}
        image_list = []
        rq_repository_url = self.root_path + '_catalog/'
        rq_tag_url = self.root_path + '{repository}/tags/list/'
        rq_repository_obj = requests.get(rq_repository_url)
        repository_list = json.loads(rq_repository_obj.text)
        for repository in repository_list['repositories']:
            rq_tag_obj = requests.get(rq_tag_url.format(repository=repository))
            for tag in json.loads(rq_tag_obj.text)['tags']:
                image_list.append({'repository': repository, 'tag': tag})
        info.update({'status': True})
        info['message'] = image_list
        return info
