#!coding: utf-8
"""
本程序用于启动主服务的后台部分,包含解析文件服务,心跳服务

"""
import threading
from manager.response import start_web_server
from manager.heartbeat import start_heartbeats
from manager.tools import GlobalMap as Gl

# -------------------清理变量---------------- #
Gl.clean()
print '变量初始化完成'
# -------------------后台响应服务-------------#
thread = threading.Thread(target=start_web_server)
thread.setDaemon(True)
thread.start()
print '启动后台响应服务'
# ------------------------------------------#
# -------------------心跳服务---------------- #
start_heartbeats()
# ------------------------------------------ #
