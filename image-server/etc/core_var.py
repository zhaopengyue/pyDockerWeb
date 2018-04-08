#!coding: utf-8
"""

本程序存放系统核心变量,包含系统核心配置

"""
import os


# ----------------------------相关路径配置---------------------------------- #
# ！项目基础路径
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ！配置文件路径
ETC_DIR = os.path.join(BASE_DIR, 'etc')
# !系统数据存储目录
DATA_DIR = os.path.join(BASE_DIR, 'data')
# !系统临时文件存储路径
TMP_DIR = os.path.join(BASE_DIR, 'tmp')
# !系统日志存放位置
LOG_DIR = os.path.join(BASE_DIR, 'log')
# !全局变量管理系统文件存放位置
GLOBAL_VAL_FILE_PATH = os.path.join(DATA_DIR, 'global_val.json')
# ------------------------------------------------------------------------ #

# ----------------------------全局变量配置---------------------------------- #
# ！MD5加密校验64位salt
MD5_64_SALT = 'ruI1QfGEoSPna0fWvK-i6Iep3NgSnLZ19DWofxHD2X_2htrkVFFoW-FLdaILvSi7'
# IP匹配正则对象
PATTERN_HOST_VAR = '^(?:(?:1[0-9][0-9]\.)|(?:2[0-4][0-9]\.)|(?:25[0-5]\.)|(?:[1-9][0-9]\.)|(?:[0-9]\.))' \
                        '{3}(?:(?:1[0-9][0-9])|(?:2[0-4][0-9])|(?:25[0-5])|(?:[1-9][0-9])|(?:[0-9]))$'
PATTERN_HOST_OBJ = re.compile(PATTERN_HOST_VAR)
# ----------------------------------------------------------------------- #
