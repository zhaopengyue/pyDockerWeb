## 集群部署指南
<b>集群部署包含如下部分：</b>
> * DHCP服务的安装与配置 
> * 集群各服务的安装与配置
> * nginx的安装与配置
> * harbor私有仓库的安装与配置
> * 各服务的开机自启动

### 部署注意事项
1. 由于本系统采用DHCP，各个节点采用动态加入机制，整个集群只有DHCP服务节点的IP固定。为便于部署及访问，建议将nginx服务，DHCP服务及主服务部署在同一个节点上。
2. harbor私有仓库建议部署在一台单独的，采用x86架构的PC机上。
3. 本系统必须在各节点docker启动后运行，负责会出错。
3. 以下安装过程以debian类型系统为例
   
### DHCP服务的安装与配置
> DHCP服务采用dhcp3 server  

1. 安装DHCP：`sudo apt-get install isc-dhcp-server`
2. 配置DHCP：DHCP服务配置文件位于`/etc/dhcp/dhcpd.conf`，DHCP网卡配置文件位于`/etc/default/isc-dhcp-server` <br>
<b>若你有多块网卡，你需要在网卡配置文件中指定网卡名</b>
``` shell
sudo vim /etc/dhcp/dhcpd.conf
# 文件中编辑
subnet 192.168.0.0 netmask 255.255.255.0 {  #网段及掩码
  range 192.168.0.2 192.168.0.253;		#分配范围
  option routers 192.168.0.1;		
  option subnet-mask 255.255.255.0;
  option broadcast-address 192.168.0.255;
  option domain-name-servers 192.168.0.1;
  option ntp-servers 192.168.0.1;
  option netbios-name-servers 192.168.0.1;
  option netbios-node-type 8;
}
```    
3. 启动DHCP服务： `sudo service isc-dhcp-server restart`
4. 验证DHCP服务： `sudo netstat -uap`
![](https://img-blog.csdn.net/20161105123723002)  
有dhcpd表示运行成功

### 集群各服务搭建
> 包含[项目](https://github.com/zhaopengyue/pyDockerWeb)中的'master-server, slave-server, image-server'三部分  

1. 安装集群各服务 
将项目中的三个文件夹分别放置于对应的节点主目录下，并将该文件夹加入PYTHONPATH。部署说明如下：
 - master-server: 部署在主节点, 无需配置；
 - slave-server：部署在从节点, 需要配置；
 - image-server：部署在镜像节点，与Harbor不属于统一节点，需要配置。   
2. 配置集群各服务  
 - 将各个节点的相关文件夹加入PYTHONPATH。以master-server为例:  
``` shell
# master-server位置： /home/username/
vim /etc/profile
# 文件末尾追加一行
export PYTHONPATH=$PYTHONPATH:/home/username/master-server
```
 - 配置python库(以master-server为例)
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

### Nginx服务搭建
> 注意： 只需在主节点搭建  

1. 安装说明参考如下链接  
 https://www.cnblogs.com/EasonJim/p/7806879.html
2. 配置nginx（只列出需要修改的必要项）
``` conf
server {
        listen       8080;		# web监听端口
        server_name  localhost;		# 域名
        #charset koi8-r;
        #access_log  logs/host.access.log  main;
        # web静态文件根目录。位于master-server/web_file文件夹中
        root <your_master_server_path>/web_file;
        location / {
        	# index目录。位于master-server/web_file/produceion
            root <your_master_server_path>/web_file/production;
            index  index.html index.htm;
        }
        location /vendors {
            index  index.html index.htm;
        }
        location /src {
            index  index.html index.htm;
        }
        location /build {
            index  index.html index.htm;
        }
        
        location /apis {
            rewrite  ^/apis/(.*)$ /$1 break;
            proxy_pass   http://localhost:5000;
        }

        error_page  404              /page_404.html;

        # redirect server error pages to the static page /50x.html
        #
        error_page   500 502 503 504  /page_50x.html;
        location = /page_50x.html {
        		# 出错目录位于master-server/web_file/produceion
                root <your_master_server_path>/web_file/production;
        }
     }
```
3. 启动nginx：`sudo <your_nginx_install_path>/sbin/nginx`

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
3. 安装harbor：harbor主目录下执行`sudo ./install.sh`。安装过程中会加载若干镜像。
4. 安装完成后harbor便已经启动。启动后会运行若干容器。
5. 验证：访问`hostname`标记的主机，如下结果表示安装成功。  
![](https://img-blog.csdn.net/20170621153931923?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvYWl4aWFveWFuZzE2OA==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

### 集群持久运行
> 为便于服务运行，故给服务部署自启，自启动服务使用systemctl部署。

1. nginx服务自启动配置		
```
sudo vim /etc/systemd/system/pyDockerNginx.service
# 文件中添加如下项---------------------
[Unit]
Description=pyDockerWeb nginx web server
After=network.target remote-fs.target nss-lookup.target
[Service]
Type=forking
ExecStart=/bin/bash -c "/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/nginx.conf"
ExecReload=/bin/bash -c "/usr/local/nginx/sbin/nginx -s reload"
ExecStop=/bin/bash -c "/usr/local/nginx/sbin/nginx -s stop"
[Install]
WantedBy=multi-user.target
# -----------------------------------
# 开启服务
sudo systemctl start pyDockerNginx.service
# 添加开机自启动
sudo systemctl enable pyDockerNginx.service
```
2. 集群各服务开机自启配置(以master-server为例)
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