#!coding: utf-8
"""
本程序负责启动从服务的心跳服务, 响应服务

"""
from manager.responses import start_response
from manager.heartbeats import start_heartbeats
from manager.log import Logging


_logger = Logging('start_slave')
_logger.set_file('start.txt')


if __name__ == '__main__':
    # 启动心跳服务
    start_heartbeats()
    # 响应服务
    try:
        start_response()
    except KeyboardInterrupt:
        _logger.write('服务已停止', level='info')
        print 'Exited, OK'
