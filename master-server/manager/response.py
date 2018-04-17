# coding=utf-8
"""
本程序为学生端web界面的后台

"""
import sys

from flask import Flask, request, jsonify
from log import Logging
from tools import GlobalMap as Gl
from communication import Image
from communication import Container
from communication import System
sys.path.append('..')
from etc.sys_set import WEB_RESPONSE_HOST, WEB_RESPONSE_PORT

app = Flask(__name__)
# 镜像操作实例
_image = Image()
# 容器操作实例
_container = Container()
# 系统信息获取实例
_system = System()
# 日志操作实例
_logger = Logging('web_flask')
_logger.set_file('web_flask.txt')


@app.route('/')
def hello_world():
    return 'Hello World!'


def get_node_num(cluster_id):
    """  获取指定集群的节点个数

    :param cluster_id: 集群IP
    :return: 集群个数(int)
    """
    return Gl.get_value('CLUSTER_ALL_INFO_VAR', {}).get(cluster_id, {}).get('node').__len__()


@app.route('/index/top/', methods=['POST', 'OPTION', 'GET'])
def index_top():
    """ 处理index页面顶端请求

    请求方式: POST
    请求携带参数: cluster_id: 集群主服务IP(集群ID)

    :return:
    {
        'message': {
            'cpu': 逻辑cpu个数
            'disk': 所有节点硬盘之和,单位G
            'mem': 所有节点内存之和,单位G
            'task': 所有节点容器之和,单位个
            'image': 所有节点镜像个数之和,单位个
            'node': 节点个数之和,单位个
        },
        'status': 执行状态
    }
    """
    args = request.get_json()
    cluster_id = args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('index_top: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    cpu_info = _system.get_all_system(cluster_id, type_='cpu')
    disk_info = _system.get_all_system(cluster_id, type_='disk')
    mem_info = _system.get_all_system(cluster_id, type_='mem')
    total_cpu = 0
    total_disk = 0
    total_mem = 0
    total_container = 0
    total_image = 0
    total_node = 0
    for _, value in cpu_info.items():
        total_cpu += int(value.get('message').get('processor_core_num'))
    for _, value in disk_info.items():
        total_disk += float(value.get('message').get('capacity')) / 1024 / 1024
    for _, value in mem_info.items():
        total_mem += float(value.get('message').get('total_mem')) / 1024 / 1024
    nodes = Gl.get_value('CLUSTER_ALL_INFO_VAR', {}).get(cluster_id, {})
    nodes_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
    for node in nodes.get('node'):
        total_node += 1
        temp_host = node.get('host')
        temp_node_status = nodes_status.get(temp_host).get('status')
        # 若节点在线
        if temp_node_status:
            temp_node_container = _container.get_container(temp_host)
            temp_node_container_status = temp_node_container.get('status')
            # 若获取信息成功
            if temp_node_container_status:
                total_container += temp_node_container.get('message').__len__()
            temp_node_image = _image.get_image(temp_host)
            if temp_node_image.get('status'):
                total_image += _image.get_image(temp_host).get('message', []).__len__()
    return jsonify({
        'message': {
            'cpu': total_cpu,
            'disk': round(total_disk, 2),
            'mem': round(total_mem, 2),
            'task': total_container,
            'image': total_image,
            'node': total_node
        },
        'status': True
    })


@app.route('/index/node/', methods=['POST'])
def index_node():
    """ 处理index页面节点统计页请求

    请求方式: POST
    请求携带参数: cluster_id: 集群主服务IP(集群ID)

    :return:
    {
        "message": [
            temp_name,  节点名
            temp_host,  节点IP
            temp_container_info, 节点容器信息,格式如10(5 Running, 2 Pause, 3 Stop)
            temp_node_image_num, 节点镜像个数
            temp_node_cpu_num,  节点cpu逻辑个数
            temp_mem_info,   节点内存信息,格式如123M/1.2G
            temp_node_status, 节点是否连接,格式为html
        ]
    }
    """
    args = request.get_json()
    cluster_id = args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('index_node: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    nodes = Gl.get_value('CLUSTER_ALL_INFO_VAR', {}).get(cluster_id, {})
    info = {'message': [], 'status': False}
    nodes_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
    for node in nodes.get('node'):
        temp_host = node.get('host')
        temp_name = node.get('name')
        temp_pause_num = 0
        temp_stop_num = 0
        temp_running_num = 0
        temp_container_num = 0
        temp_node_active_mem = 0
        temp_node_total_mem = 0
        temp_node_image_num = 0
        temp_node_cpu_num = 0
        temp_node_status = nodes_status.get(temp_host).get('status')
        # 若节点在线
        if temp_node_status:
            temp_node_container = _container.get_container(temp_host)
            temp_node_container_status = temp_node_container.get('status')
            # 若获取信息成功
            if temp_node_container_status:
                for container in temp_node_container.get('message'):
                    temp_container_num += 1
                    if container.get('message').get('running'):
                        temp_running_num += 1
                        continue
                    if container.get('message').get('paused'):
                        temp_pause_num += 1
                        continue
                    temp_stop_num += 1
            temp_node_image = _image.get_image(temp_host)
            if temp_node_image.get('status'):
                temp_node_image_num = _image.get_image(temp_host).get('message', []).__len__()
            else:
                temp_node_image_num = 0
            temp_node_cpu = _system.get_system(temp_host, type_='cpu')
            if temp_node_cpu.get('status'):
                temp_node_cpu_num = temp_node_cpu.get('message').get('processor_core_num')
            else:
                temp_node_cpu_num = 0
            temp_node_mem = _system.get_system(temp_host, type_='mem')
            if temp_node_mem.get('status'):
                temp_node_active_mem = round(float(temp_node_mem.get('message').get('active_mem')) / 1024, 2)
                temp_node_total_mem = round(float(temp_node_mem.get('message').get('total_mem')) / 1024 / 1024, 2)
            else:
                temp_node_active_mem = 0
                temp_node_total_mem = 0
        temp_container_info = '{total}({running} Running, {paused} Pause, {stop} Stop)'.format(
            total=temp_container_num,
            running=temp_running_num,
            paused=temp_pause_num,
            stop=temp_stop_num
        )
        temp_mem_info = '{active}M/{total}G'.format(
            active=temp_node_active_mem,
            total=temp_node_total_mem
        )
        if temp_node_status:
            temp_node_status = '<span class="label label-success">success</span>'
        else:
            temp_node_status = '<span class="label label-danger">dangers</span>'
        node_dic = [temp_name, temp_host, temp_container_info, temp_node_image_num, temp_node_cpu_num, temp_mem_info, temp_node_status]
        info.get('message').append(node_dic)
    info.update({'status': True})
    return jsonify(info)


@app.route('/container/info/', methods=['POST'])
def container_info():
    """ 获取执行集群所有容器的信息

    请求方式: POST
    请求携带参数: cluster_id

    :return:
    {
        "message": [
            {
                'short_id':
                'node': ,
                'name': ,
                'image':,
                'exit_time': ,
                'create': ,
                'status':
            }
        ],
        "status":
    }
    """
    # cluster_id = '127.0.0.1'
    args = request.get_json()
    cluster_id = args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('container_info: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    container_info = _container.get_all_containers(cluster_id)
    info = []
    for host, value in container_info.items():
        if not value.get('status'):
            continue
        for container in value.get('message'):
            if container.get('message').get('paused'):
                status = '<span class="label label-warning">&nbsp;&nbsp;paused&nbsp;&nbsp;</span>'
            elif container.get('message').get('running'):
                status = '<span class="label label-success">running</span>'
            else:
                status = '<span class="label label-danger">&nbsp;&nbsp;exited&nbsp;&nbsp;</span>'
            info.append({
                'short_id': container.get('message').get('short_id'),
                'node': node_address_name(cluster_id, host),
                'name': container.get('message').get('name'),
                'image': container.get('message').get('image'),
                'exit_time': container.get('message').get('exit_time'),
                'create': container.get('message').get('created'),
                'status': status
            })
    return jsonify({'message': info, 'status': True})


@app.route('/container/operator/', methods=['POST'])
def container_op():
    """ 操作指定容器

    请求方式: POST
    请求携带参数: cluster_id 集群主服务IP
                action: 操作类型(str)
                container_id: 容器名或容器id(str)

    :return:
    {
        "message": 执行结果
        "status": 执行状态
    }
    """
    rq_args = request.get_json()
    cluster_id = rq_args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('container_op: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    host_name = rq_args.get('node')
    # type_为元祖,原因未知
    type_ = rq_args.get('action'),
    container_id = rq_args.get('container_id')
    args = rq_args.get('args')
    host = node_name_address(cluster_id, host_name)
    if not host:
        _logger.write(str(host_name) + ' not found', level='error')
        return jsonify({'message': str(host_name) + ' not found', 'status': False})
    result = _container.operator_container(host, action_type=type_[0], container_id_or_name=container_id, **args)
    return jsonify(result)


@app.route('/container/create/', methods=['POST'])
def container_create():
    """ 创建容器

    请求方式: POST
    请求携带参数: cluster_id: 集群id
                node: 节点name
                cmd: 创建命令

    :return:
    {
        "message": 容器id或执行节点
        "status": 执行状态
    }
    """
    rq_args = request.get_json()
    cluster_id = rq_args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('container_create: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    host_name = rq_args.get('node')
    create_cmd = rq_args.get('cmd')
    host = node_name_address(cluster_id, host_name)
    if not host:
        _logger.write(str(host_name) + ' not found', level='error')
        return jsonify({'message': str(host_name) + ' not found', 'status': False})
    result = _container.create_container_shell(host, create_cmd)
    return jsonify(result)


@app.route('/image/info/', methods=['GET', 'POST'])
def image_info():
    """ 获取集群镜像信息

    请求方式: POST
    请求携带参数: cluster_id: 集群id

    :return:
    {
        "message": [
            'short_id':
            'node':
            'tag':
            'created':
            'size':
            'os':
            'status':
        ],
        ...
    }
    """
    args = request.get_json()
    cluster_id = args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('image_info: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    images_info = _image.get_all_images(cluster_id)
    info = []
    image_use_list = set()
    container_info = _container.get_all_containers(cluster_id)
    for host, value in container_info.items():
        if not value.get('status'):
            continue
        for container in value.get('message'):
            container_image = container.get('message').get('image')
            if ':' not in container_image:
                container_image += ':latest'
            image_use_list.add(container_image)
    for host, value in images_info.items():
        node = node_address_name(cluster_id, host)
        if not value.get('status'):
            continue
        for image in value.get('message'):
            short_id = image.get('message').get('short_id')
            created = image.get('message').get('created')
            size = str(round(float(image.get('message').get('size')) / 1024 / 1024, 2)) + ' M'
            os_ = image.get('message').get('os')
            for tag in image.get('message').get('tags'):
                if tag in image_use_list:
                    status = '<span class="label label-danger">&nbsp;&nbsp;Using&nbsp;&nbsp;</span>'
                else:
                    status = '<span class="label label-success">&nbsp;&nbsp;NoUse&nbsp;&nbsp;</span>'
                info.append({
                    'short_id': short_id,
                    'node': node,
                    'tag': tag,
                    'created': created,
                    'size': size,
                    'os': os_,
                    'status': status
                })
    return jsonify({'message': info, 'status': True})


@app.route('/image/operator/', methods=['POST'])
def image_operator():
    """ 镜像相关操作

    请求携带参数: cluster_id 集群主服务IP
                action: 操作类型(str)
                image_id: 镜像名或镜像id(str)

    :return:
    {
        "message": 执行结果
        "status": 执行状态
    }

    :return:
    """
    rq_args = request.get_json()
    cluster_id = rq_args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('image_operator: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    host_name = rq_args.get('node')
    # type_为元祖,原因未知
    type_ = rq_args.get('action'),
    image_id = rq_args.get('image_id')
    args = rq_args.get('args')
    host = node_name_address(cluster_id, host_name)
    if not host:
        _logger.write(str(host_name) + ' not found', level='error')
        return jsonify({'message': str(host_name) + ' not found', 'status': False})
    result = _image.operator_image(host, type_[0], image_id, **args)
    return jsonify(result)


def node_address_name(cluster_id, address):
    """ 将节点ip转化为节点name

    :param cluster_id:
    :param address:
    :return:
    """
    nodes = Gl.get_value('CLUSTER_ALL_INFO_VAR', {}).get(cluster_id, {}).get('node')
    for node in nodes:
        if address == node['host']:
            return node['name']
    return None


def node_name_address(cluster_id, name):
    """ 将节点name转化为节点IP

    :param cluster_id:
    :param name:
    :return:
    """
    nodes = Gl.get_value('CLUSTER_ALL_INFO_VAR', {}).get(cluster_id, {}).get('node')
    for node in nodes:
        if name == node['name']:
            return node['host']
    return None


@app.route('/common/node/', methods=['POST'])
def common_node():
    """ 返回节点名及状态

    请求方式: POST
    请求携带参数: cluster_id: 集群id

    :return:
    {
        "message": [
            {
                "host": , 节点IP
                "name":  节点名
            }
        ],
        "status": 执行状态
    }
    """
    rq_args = request.get_json()
    cluster_id = rq_args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('common_node: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    nodes = Gl.get_value('CLUSTER_ALL_INFO_VAR', {}).get(cluster_id, {})
    nodes_status = Gl.get_value('CLUSTER_STATUS_VAR', {})
    info = []
    for node in nodes.get('node'):
        info.append({
            'host': node.get('host'),
            'name': node.get('name'),
            'status': nodes_status.get(node.get('host')).get('status')
        })
    return jsonify({'message': info, 'status': True})


@app.route('/node/mem/', methods=['POST'])
def node_mem():
    """ 获取内存信息

    请求方式: POST
    请求携带参数: cluster_id
                node: 节点名

    :return:
    {
        message: {
            "message": {
                'total_mem':, 内存总量
                'free_mem': , 空闲内存量
                'active_mem': 使用内存量
                'cache/buffer_mem': 缓存量
            },
            "status":
        },
        'status': bool
    }
    """

    rq_args = request.get_json()
    cluster_id = rq_args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('node_mem: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    host_name = rq_args.get('node')
    host = node_name_address(str(cluster_id), str(host_name))
    if not host:
        _logger.write(str(host_name) + ' not found', level='error')
        return jsonify({'message': str(host_name) + ' not found', 'status': False})
    result = System.get_system(str(host), 'mem')
    return jsonify({'message': result, 'status': True})


@app.route('/node/disk/', methods=['POST'])
def node_disk():
    """ 获取硬盘信息

    请求方式: POST
    请求携带参数: cluster_id
                node: 节点名

    :return:
    """
    rq_args = request.get_json()
    cluster_id = rq_args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('node_disk: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    host_name = rq_args.get('node')
    host = node_name_address(str(cluster_id), str(host_name))
    if not host:
        _logger.write(str(host_name) + ' not found', level='error')
        return jsonify({'message': str(host_name) + ' not found', 'status': False})
    result = System.get_system(str(host), 'disk')
    return jsonify({'message': result, 'status': True})


@app.route('/node/container/', methods=['POST'])
def node_container():
    """ 返回节点容器统计信息

    请求方式: POST
    请求携带参数: cluster_id
                node: 节点名

    :return:
    """
    rq_args = request.get_json()
    cluster_id = rq_args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('node_container: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    host_name = rq_args.get('node')
    host = node_name_address(str(cluster_id), str(host_name))
    if not host:
        _logger.write(str(host_name) + ' not found', level='error')
        return jsonify({'message': str(host_name) + ' not found', 'status': False})
    containers = _container.get_container(host)
    if not containers.get('status'):
        return jsonify({'message': 'host status error', 'status': False})
    container_info = {'created': 0, 'exited': 0, 'paused': 0, 'running': 0, 'restarting': 0}
    for container in containers.get('message'):
        container_status = container.get('message').get('status')
        if container_status in container_info:
            container_info[container_status] += 1
        else:
            container_info[container_status] = 1
    return jsonify({'message': container_info, 'status': True})


@app.route('/node/image_harbor_registry/', methods=['POST'])
def node_image_server_harbor():
    """ 返回镜像服务器私有仓库harbor列表

        该方法仅支持harbor

        请求方式: POST
        请求携带参数: cluster_id
                    image_server: 私有镜像仓库ip

    :return:
    """
    rq_args = request.get_json()
    cluster_id = rq_args.get('cluster_id')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('node_image_server_harbor: ' + str(cluster_id) + ' is illegal or not found node in cluster')
        return jsonify({'message': str(cluster_id) + '集群IP不合法或无加入节点'})
    image_server = rq_args.get('image_server')
    if not image_server:
        _logger.write('node_image_server_registry: ' + str(image_server) + ' is illegal')
        return jsonify({'message': 'image server is error', 'status': False})
    info = _image.get_image_server_harbor(image_server)
    return jsonify({'message': info, 'status': True})


@app.route('/node/download/', methods=['POST'])
def node_download():
    """ 镜像下载服务的镜像仓库方式
    请求方式: POST
    请求携带参数: cluster_id
                image_server: 私有镜像仓库ip
    :return:
    """
    rq_args = request.get_json()
    cluster_id = rq_args.get('cluster_id')
    to_host = rq_args.get('to_host')
    image_name = rq_args.get('image_name')
    image_server = rq_args.get('image_server')
    all_cluster_id = Gl.get_value('CLUSTER_FREE_ID_VAR', [])
    if cluster_id not in all_cluster_id:
        _logger.write('node_download: ' + str(cluster_id) + ' is illegal')
        return jsonify({'message': str(cluster_id) + ' is illegal'})
    if not image_server:
        _logger.write('node_download: ' + str(image_server) + ' is illegal')
        return jsonify({'message': 'image server is error', 'status': False})
    host = node_name_address(cluster_id, to_host)
    if not host:
        _logger.write(str(to_host) + ' not found', level='error')
        return jsonify({'message': str(to_host) + ' not found', 'status': False})
    message = _image.download_image(str(host), str(image_server), str(image_name))
    return jsonify({'message': message, 'status': True})


@app.route('/node/alive_server_list/', methods=['POST', 'GET'])
def get_alive_server_list():
    """ 返回可用的镜像服务器列表

    :return:
    """
    message = Image.get_alive_image_server_list()
    if message.get('status'):
        return jsonify({'message': message, 'status': True})
    else:
        return jsonify({'message': 'No mirror server is available.', 'status': False})


def start_web_server():
    app.run(host=WEB_RESPONSE_HOST, port=WEB_RESPONSE_PORT)

