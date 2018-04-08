# coding=utf-8

# ----------------------------系统配置---------------------------- #
# !本机IP
THE_MACHINE_IP = '0.0.0.0'

# ---------------------------主服务镜像服务--------------------------#
# ！主服务与镜像服务通信端口
IMAGE_SERVICE_PORT_VAR = 14000

# ---------------------------镜像下载服务--------------------------- #
# !镜像服务与从节点通信端口(以废弃)
SLAVE_UPLOAD_PORT = 13000
# !私有镜像仓库监听端口
PRIVATE_REGISTRY_PORT = 16000

# ----------------------------心跳服务--------------------------- #
# !主服务心跳通信端口
HEARTBEAT_PORT_VAR = 10000
# !主服务所在IP
SERVICE_HOST_VAR = '127.0.0.1'
