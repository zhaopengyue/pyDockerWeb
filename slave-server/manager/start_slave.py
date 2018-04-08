#!coding: utf-8
"""
本程序负责启动从服务的心跳服务, 响应服务

"""
from responses import start_response
from heartbeats import SlaveHeartbeats
from log import Logging

_logger = Logging('start_slave')
_logger.set_file('start_slave.txt')


if __name__ == '__main__':
    # 启动心跳服务
    heartbeat = SlaveHeartbeats()
    heartbeat.setDaemon(True)
    try:
        heartbeat.start()
        print '心跳服务已启动'
        # 启动响应服务
        print '监听主服务通讯请求中...'
        start_response()
    except KeyboardInterrupt:
        heartbeat.set_kill()
        _logger.write('服务已停止', level='info')
        print 'Exited, OK'

