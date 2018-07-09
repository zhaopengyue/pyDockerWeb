#!coding: utf-8
""" 操作教师服务镜像

"""
import sys
from urlparse import urlparse

import requests
import json
from requests.exceptions import SSLError
sys.path.append('..')


class ImageHarbor(object):
    """ 处理harbor请求

    """

    def __init__(self, harbor_url, username=None, password=None, api_version='v2', cacert=None, insecure=False, ):
        self.username = username
        self.password = password
        self.harbor_url = harbor_url
        self.api_version = api_version
        # Has no protocol, use http
        if not urlparse(harbor_url).scheme:
            self.harbor_url = 'http://' + harbor_url
        parsed_url = urlparse(self.harbor_url)
        self.protocol = parsed_url.scheme
        self.host = parsed_url.hostname
        self.port = parsed_url.port
        self.session_id = None
        self.user_agent = 'python-harborclient'
        # https
        if insecure:
            self.verify_cert = False
        else:
            if cacert:
                self.verify_cert = cacert
            else:
                self.verify_cert = True

    def unauthenticate(self):
        """注销harbor账户"""
        if not self.session_id:
            requests.get(
                '%s://%s/logout' % (self.protocol, self.host),
                cookies={'beegosessionID': self.session_id},
                verify=self.verify_cert
            )
            return True
        else:
            return False

    def authenticate(self):
        """登录harbor"""
        if not self.username or not self.password:
            return
        try:
            resp = requests.post(
                self.harbor_url + '/login',
                data={
                    'principal': self.username,
                    'password': self.password
                },
                verify=self.verify_cert
            )
            if resp.status_code == 200:
                self.session_id = resp.cookies.get('beegosessionID')
            if resp.status_code >= 400:
                pass
        except SSLError:
            pass

    def get_all_repositories(self):
        """ 返回所有公有镜像列表

        :return:
        """
        info = []
        # 未登录时
        if not self.session_id:
            # 请求所有公有镜像
            repositories = self.request('GET', '/repositories/top')
        else:
            repositories = self.request('GET', '/repositories/top', cookies={'beegosessionID': self.session_id})
        for repository in repositories:
            info.append({
                'name': repository.get('name'),
                'description': repository.get('description'),
                'pull_count': repository.get('pull_count'),
                'star_count': repository.get('star_count'),
                'update_time': repository.get('update_time')
            })
        return {'message': info, 'statusCode': 0, 'errMessage': None}

    def request(self, method, url, **kwargs):
        url = self.harbor_url + '/api' + url
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        kwargs['headers']['User-Agent'] = self.user_agent
        kwargs['headers']['Accept'] = 'application/json'
        kwargs['headers']['Content-Type'] = 'application/json'
        kwargs["headers"]['Harbor-API-Version'] = self.api_version
        resp = requests.request(method, url, verify=self.verify_cert, **kwargs)
        if resp.status_code >= 400:
            return []
        try:
            value = json.loads(resp.text)
        except ValueError:
            value = []
        return value
