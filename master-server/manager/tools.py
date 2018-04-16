#!coding: utf-8
"""
本文件包含一些常用工具函数
"""
import hashlib
import sys
import os
import base64
import math
import json
import threading
sys.path.append('..')
from etc.core_var import MD5_64_SALT
from etc.core_var import GLOBAL_VAL_FILE_PATH


def md5_salt(message):
    """对传如的message加salt处理
    :param message: 要加密的字符串
    :return:
    """
    message_len = len(message)
    md5 = hashlib.md5()
    if message_len >= 2:
        message_end = message[:message_len/2] + MD5_64_SALT[32:] + message[message_len/2:] + MD5_64_SALT[:32]
    else:
        message_end = message + MD5_64_SALT
    md5.update(message_end)
    return md5.hexdigest()


def mk_salt(width):
    """生成指定位数salt
    :param width: 生成位数
    :return:
    """
    return base64.b64encode(os.urandom(int(math.ceil(0.75 * width))), '-_')[width]


class GlobalMap(object):
    """全局可读写变量管理器,依赖文件

    """

    _global_map_lock = threading.Lock()

    @staticmethod
    def set_value(key, value):
        """添加和设置变量值

        :param key: 变量名
        :param value: 变量值
        :return:
        """
        # if not os.path.exists(GLOBAL_VAL_FILE_PATH):
        #     raise ValueError(GLOBAL_VAL_FILE_PATH + ' is not found.')
        if isinstance(key, dict):
            raise TypeError('unhashable type: dict')
        if isinstance(value, set):
            raise TypeError('unhashable type: set')
        if isinstance(key, list):
            raise TypeError('unhashable type: list')
        GlobalMap._global_map_lock.acquire()
        _global_map = {}
        # 以追加方式读取文件, 若不存在则创建空文件
        with open(GLOBAL_VAL_FILE_PATH, 'a+') as fp:
            try:
                _global_map = json.load(fp, encoding='utf-8')
            except ValueError:
                pass
        _global_map.update({key: value})
        with open(GLOBAL_VAL_FILE_PATH, 'w') as fp:
            json.dump(_global_map, fp)
        GlobalMap._global_map_lock.release()

    @staticmethod
    def get_value(key, default_type):
        """获取指定变量的值

        :param default_type: 返回的默认类型.
        :param key: 变量名
        :return:
        """
        if not os.path.exists(GLOBAL_VAL_FILE_PATH):
            raise ValueError(GLOBAL_VAL_FILE_PATH + ' is not found.')
        if isinstance(key, dict):
            raise TypeError('unhashable type: dict')
        if isinstance(key, list):
            raise TypeError('unhashable type: list')
        GlobalMap._global_map_lock.acquire()
        _global_map = {}
        with open(GLOBAL_VAL_FILE_PATH) as fp:
            try:
                _global_map = json.load(fp, encoding='utf-8')
            except ValueError, e:
                print e
        GlobalMap._global_map_lock.release()
        if not _global_map.get(key):
            return default_type
        return _global_map.get(key)

    @staticmethod
    def del_value(key):
        """删除指定变量

        :param key: 要删除的变量名
        :return:
        """
        if not os.path.exists(GLOBAL_VAL_FILE_PATH):
            raise ValueError(GLOBAL_VAL_FILE_PATH + ' is not found.')
        if isinstance(key, dict):
            raise TypeError('unhashable type: dict')
        if isinstance(key, list):
            raise TypeError('unhashable type: list')
        GlobalMap._global_map_lock.acquire()
        _global_map = {}
        with open(GLOBAL_VAL_FILE_PATH) as fp:
            try:
                _global_map = json.load(fp, encoding='utf-8')
            except ValueError, e:
                print e
        if key not in _global_map:
            GlobalMap._global_map_lock.release()
            return False
        _global_map.pop(key)
        with open(GLOBAL_VAL_FILE_PATH, 'w') as fp:
            json.dump(_global_map, fp)
        GlobalMap._global_map_lock.release()
        return False

    @staticmethod
    def clean():
        """清除所有变量

        """
        if not os.path.exists(GLOBAL_VAL_FILE_PATH):
            raise ValueError(GLOBAL_VAL_FILE_PATH + ' is not found.')
        GlobalMap._global_map_lock.acquire()
        with open(GLOBAL_VAL_FILE_PATH, 'w') as fp:
            fp.truncate()
        GlobalMap._global_map_lock.release()