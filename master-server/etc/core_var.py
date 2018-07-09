#!coding=utf-8
"""
本文件存放系统核心变量，包含一些系统重要配置
`# ！`为系统核心项
"""
import os
import re
# ----------------------------相关路径配置---------------------------------- #
# ！项目基础路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ！配置文件路径
ETC_DIR = os.path.join(BASE_DIR, 'etc')
# !系统数据存储目录
DATA_DIR = os.path.join(BASE_DIR, 'data')
# !系统临时文件存储路径
TMP_DIR = os.path.join(BASE_DIR, 'tmp')
# !系统日志存放位置
LOG_DIR = os.path.join(BASE_DIR, 'log')
# !集群信息配置XML文件位置(以失效, 现在改用DHCP动态加入, 无需配置节点)
CLUSTER_XML_PATH = os.path.join(ETC_DIR, 'cluster_set.xml')
# !全局变量管理系统文件存放位置
GLOBAL_VAL_FILE_PATH = os.path.join(DATA_DIR, 'global_val.json')
# ------------------------------------------------------------------------ #

# ----------------------------全局变量配置---------------------------------- #
# # !集群节点IP集合：仅仅存放集群IP
# CLUSTER_ALL_HOSTS_VAR = set()
# # !集群ID集合：仅仅存放集群ID
# CLUSTER_ALL_ID_VAR = set()
# # !集群节点信息变量：存放集群IP，ID，集群描述
# CLUSTER_ALL_INFO_VAR = {}
# # !集群状态信息变量
# CLUSTER_STATUS_VAR = {}
# # !集群未占用ID列表
# CLUSTER_FREE_ID_VAR = set[]
# ！MD5加密校验64位salt
MD5_64_SALT = 'ruI1QfGEoSPna0fWvK-i6Iep3NgSnLZ19DWofxHD2X_2htrkVFFoW-FLdaILvSi7'
# IP匹配正则对象
PATTERN_HOST_VAR = '^(?:(?:1[0-9][0-9]\.)|(?:2[0-4][0-9]\.)|(?:25[0-5]\.)|(?:[1-9][0-9]\.)|(?:[0-9]\.))' \
                        '{3}(?:(?:1[0-9][0-9])|(?:2[0-4][0-9])|(?:25[0-5])|(?:[1-9][0-9])|(?:[0-9]))$'
PATTERN_HOST_OBJ = re.compile(PATTERN_HOST_VAR)
# ----------------------------------------------------------------------- #

# # ----------------------------文件互斥锁----------------------------------- #
# # ！集群状态信息变量全局互斥锁
# CLUSTER_STATUS_LOCK_OBJ = threading.Lock()
# # ！集群节点IP集合全局互斥锁
# CLUSTER_ALL_HOSTS_LOCK_OBJ = threading.Lock()
# # !集群ID集合全局互斥锁
# CLUSTER_ALL_ID_LOCK_OBJ = threading.Lock()
# # !集群节点信息变量全局互斥锁
# CLUSTER_ALL_INFO_LOCK_OBJ = threading.Lock()
# # ----------------------------------------------------------------------- #

