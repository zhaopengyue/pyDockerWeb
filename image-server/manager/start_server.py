# coding=utf-8
import log
from heartbeats import start_heartbeats
from response import start_response

_logger = log.Logging('start')
_logger.set_file('start.txt')

if __name__ == '__main__':
    # 启动心跳服务
    start_heartbeats()
    # 响应服务
    try:
        start_response()
    except KeyboardInterrupt:
        _logger.write('服务已停止', level='info')
