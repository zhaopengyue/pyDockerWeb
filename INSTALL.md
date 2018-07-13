## 集群部署指南

### 部署注意事项
1. harbor私有仓库建议部署在一台单独的，采用x86架构的PC机上。
2. 本系统必须在各节点docker启动后运行，负责会出错。
3. 以下安装过程以debian类型系统为例
4. 开发环境中python版本为python2.7.11,请安装合适的python保证运行环境正确
5. 为避免python环境污染，请按条件选择安装使用virtualenv。若使用了virtualenv，则需要在`作为一个服务`中添加source语句和指定python路径
   
### 集群各服务搭建
> 包含[项目](https://github.com/zhaopengyue/pyDockerWeb)中的'master-server, slave-server, image-server'三部分  

1. 安装集群各服务 
将项目中的三个文件夹分别放置于对应的节点主目录下，并将该文件夹加入PYTHONPATH。部署说明如下：
 - master-server: 部署在主节点, 无需配置；
 - slave-server：部署在从节点, 需要配置；
 - image-server：部署在镜像节点，与Harbor部署于同一节点，需要配置。   
2. 配置集群各服务  
 - 将各个节点的相关文件夹加入PYTHONPATH。以master-server为例,slave-server与image-server同此操作:  
``` shell
# 假设master-server位置： /home/username/
vim /etc/profile
# 文件末尾追加一行
export PYTHONPATH=$PYTHONPATH:/home/username/master-server
```
 - 配置python库(以master-server为例,slave-server与image-server同此操作)
 ```
 cd master-server
 pip install -r requirements.txt
 ```
 - slave-server配置  
``` shell
 cd slave-server/etc  
 vim sys_set.py
 # 修改以下项为主节点IP
 SERVICE_HOST_VAR = 'your master server ip'
```
 - image-server配置
``` shell
 cd image-server/etc
 vim sys_set.py
 # 修改以下项为主节点IP
 SERVICE_HOST_VAR = 'your master server ip'
 # 修改如下项为Harbor仓库连接，Harbor搭建之后会讲述。
 # 务必保证该链接其他节点访问。
 HARBOR_URL = 'http://10.42.0.10:17000'
 ```
3. 启动服务（以master-server为例）
``` shell
cd master-server
python manager/start_server.py &
```

### Harbor搭建
> 以下基于离线安装包安装，参考自https://blog.csdn.net/aixiaoyang168/article/details/73549898

1. 下载harbor：`wget https://storage.googleapis.com/harbor-releases/release-1.4.0/harbor-offline-installer-v1.4.0.tgz`
2. 配置harbor  
解压缩之后，目录下会生成harbor.conf文件，该文件就是Harbor的配置文件。 主要配置以下项  
<b>注意'hostname'配置需要与第二步`image-server`中的`HARBOR_URL`相同。</b>
``` shell
## Configuration file of Harbor
# hostname设置访问地址，可以使用ip、域名，不可以设置为127.0.0.1或localhost
# 请不要使用10000，8080，80, 5000, 11000, 14000, 15000端口。
hostname = 10.42.0.1:8088
# 访问协议，默认是http，也可以设置https，如果设置https，则nginx ssl需要设置on
ui_url_protocol = http
# 启动Harbor后，管理员UI登录的密码，默认是Harbor12345
harbor_admin_password = Harbor12345
```  
此外还需要修改docker-compose.yml，找到如下部分，将如上hostname中的端口映射至容器80端口
```
proxy:
    image: vmware/nginx-photon:v1.4.0-rc2
    container_name: nginx
    restart: always
    volumes:
      - ./common/config/nginx:/etc/nginx:z
    networks:
      - harbor
    ports:
      - 17000:80
      - 443:443
      - 4443:4443
```
3. 安装harbor：harbor主目录下执行`sudo ./install.sh`。安装过程中会加载若干镜像。
4. 安装完成后harbor便已经启动。启动后会运行若干容器。
5. 验证：访问`hostname`标记的主机，如下结果表示安装成功。  
![](https://img-blog.csdn.net/20170621153931923?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvYWl4aWFveWFuZzE2OA==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

### 修改docker
由于harbor仓库采用http通信, 而docker 1.12之后版本基于http协议下载镜像时会报错(提示不支持http), 故需将docker配置作如下修改(针对使用apt安装的docker)  
请将以下IP及端口修改为harbor仓库的IP及端口  
<b>该操作需要应用于所有从节点(工作节点)</b>
``` bash
sudo cat > /etc/docker/daemon.json << EOF
{"graph": "/var/lib/docker", "insecure-registries":["10.42.0.1:17000"]}
```

### 作为一个服务
> 为便于服务运行，故给服务部署自启，自启动服务使用systemctl部署。

集群各服务开机自启配置(以master-server为例，slave-server和image-server同此)
``` shell
sudo vim /etc/systemd/system/pyDockerMaster.service
# 文件中添加如下项--------------------------------
$ cat /etc/systemd/system/pyDockerMaster.service 
[Unit]
Description=pyDockerWeb master server
After=docker.target
[Service]
Type=simple
WorkingDirectory=/home/pirate
ExecStart=/bin/bash -c "source /etc/profile;/usr/bin/python /home/pirate/master-server/manager/start_server.py"
Restart=always
[Install]
WantedBy=multi-user.target
# -------------------------------------------------------
# 开启服务
sudo systemctl start pyDockerMaster.service
# 添加开机自启动
sudo systemctl enable pyDockerMaster.service
```
以上服务安装完成并启动成功后，访问`http://<your_master_node_ip>:8080`，如下结果表示系统安装成功。
![](https://github.com/zhaopengyue/readMePicture/blob/master/pyDockerWeb/index.png?raw=true)