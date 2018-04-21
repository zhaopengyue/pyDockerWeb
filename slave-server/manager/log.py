#!coding: utf-8
"""
本程序实现主服务的日志服务
"""
import logging
import sys
import os
from etc.core_var import LOG_DIR


class Logging(object):

    def __init__(self, log_name):
        self.logger = logging.getLogger(log_name)
        self.formatter = logging.Formatter('%(asctime)s %(levelname)-2s: %(message)s')
        self.logger.setLevel(logging.INFO)

    def set_file(self, path, mode='w+'):
        """ 设置文件路径

        设置要写入日志文件的相关参数

        :param path: 写入文件名
        :param mode: 文件打开模式.同open()的打开模式相同
        :return:
        """
        file_path = os.path.join(LOG_DIR, path)
        file_handler = logging.FileHandler(file_path, encoding='utf-8', mode=mode)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def write(self, info, level):
        """ 写入日志

        向指定文件中写入日志

        :param info: 写入日志内容
        :param level: 日志等级
        :return:
        """
        info = info.decode('utf-8')
        if level == 'info':
            self.logger.info(info)
        elif level == 'warn':
            self.logger.warn(info)
        elif level == 'error':
            self.logger.error(info)
        else:
            pass
