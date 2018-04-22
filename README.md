# pyDockerWeb
## 项目简介
pyDockerWeb是一款由python，bootstrap等实现的一款docker综合管理Web平台。其主要包含如下功能：
- 支持集群节点的docker状态信息展示
- 支持在线对容器进行启动、删除等操作
- 支持在线对镜像进行tag、删除等操作
- 支持从私有镜像仓库（Harbor）下载镜像到指定节点
- 支持在线创建容器   

## 项目架构
pyDockerWeb主要有三部分构成:
- master-server：主服务。运行在集群的主节点上。负责响应前端web请求、监控所有节点服务状态（心跳方式）、向从节点发出执行命令请求、获取镜像服务器信息等
- slave-server：从服务。运行在集群的从节点（工作节点）上。负责响应主服务请求并反馈执行结果、报告本节点状态等
- image-server：镜像服务。运行在集群的镜像节点。负责获取私有镜像仓库信息、报告本节点状态等


## 项目截图
1. 主页
![](https://github.com/zhaopengyue/readMePicture/blob/master/pyDockerWeb/index.png?raw=true)
2. 容器页
![](https://github.com/zhaopengyue/readMePicture/blob/master/pyDockerWeb/container.png?raw=true)
3. 镜像页
![](https://github.com/zhaopengyue/readMePicture/blob/master/pyDockerWeb/image.png?raw=true)
4. 节点页
![](https://github.com/zhaopengyue/readMePicture/blob/master/pyDockerWeb/node.png?raw=true)

## 安装方式
见[INSTALL.md](https://github.com/zhaopengyue/pyDockerWeb/blob/master/INSTALL.md)
