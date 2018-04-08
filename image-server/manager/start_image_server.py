# coding=utf-8
import log
from heartbeats import SlaveHeartbeats
from response import start_response

_logger = log.Logging('start')
_logger.set_file('start.txt')

if __name__ == '__main__':
    # 启动心跳服务
    heartbeat = SlaveHeartbeats()
    heartbeat.setDaemon(True)
    heartbeat.start()
    print '心跳服务已启动'
    _logger.write('心跳服务已启动', level='info')
    start_response()
