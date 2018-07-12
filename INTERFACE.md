### 消息返回基本格式
``` json 
{
    "message":  "具体执行结果值,失败时值为None(null),  相关类型",
    "statusCode": "执行状态码, int",
    "errMessage": "错误信息, 成功时为None(null)。 str"
}
```

### statusCode列表
 **状态码为1时，为便于遍历, 相关失败值会以`0`或`''`展示**
- 0 所有任务都已经执行成功
- 1 任务已经完成,但结果中存在执行不成功的结果。
- 2 任务执行出错
- 3 函数参数格式错误
- 4 url参数格式非法
- 5 集群ID不存在或不合法
- 6 普通节点不存在或节点不在线
- 7 镜像节点不存在或节点不在线

### 相关服务调用规则及详细返回格式
> 路径为 http://<主节点IP>:5000/url，以下仅说明url

#### 获取整个集群镜像信息
1. 通过集群ID(主节点IP)获取
	- method: `POST`
	- url: `/image/info/`
	- post参数: 
	``` json
    {
        "cluster_id": 主节点IP(str)
    }
    ```
	- return: 
	``` json
    {
        "statusCode": "状态码(str)",
        "message": [
            {
                "short_id": "镜像ID",
                "node": "节点IP",
                "tag": "镜像标签",
                "created": "创建时间",
                "size": "镜像大小",
                "os":	"镜像系统",
                "status": "镜像状态"
            },
            {}
        ],
    "errMessage": "错误信息"
    }
    ```
2. 通过IP数组获取
	- method: `POST`
	- url: `/image/info_list/`
	- post参数: 
	```
    {
        "hosts": [
            "192.168.1.1",
            "192.168.1.2"
        ]
    }
    ```
	- return: 
	``` json
    {
        "statusCode": "状态码(str)",
        "message": [
        	{
                "short_id": "镜像ID",
                "node": "节点IP",
                "tag": "镜像标签",
                "created": "创建时间",
                "size": "镜像大小",
                "os":	"镜像系统",
                "status": "镜像状态"
            },
            {}
        ],
        "errMessage": "错误信息"
   }
   ```
   
#### 批量删除镜像
1. 通过IP列表删除镜像
	- method: `POST`,
	- url: `/image/operator_list/`,
	- post参数:
	``` json
    {
        "hosts": [
            "192.168.1.1",
            "192.168.1.2"
        ],
        "action": "remove",
        "images": [
            "镜像名1",
            "镜像名2"
        ],
        "args": {
            "force": "是否强制删除(boolean)"
        }
    }
    ```
    - return:
    ``` json
    {
        "message": [
            {
                "host": "节点IP",
                "message": {
                    "message": "ok",
                    "statusCode": "错误码",
                    "errMessage": "错误信息"
                },
                "image": "镜像ID"
            },
            {}
        ],
        "statusCode": "错误码",
        "errMessage": "错误信息"
    }
    ```
    - 说明
    ```
    post请求中host与imageID是一致的，需保证镜像名必须在host上,故host可以重复。
    返回信息中可通过message中的host与image查看具体某个镜像的执行状态。message中的字典顺序与传入时的顺序相同。
    ```
    
#### 镜像服务器
1. 获取可用镜像服务器列表
	- method: `POST`或`GET`
	- url: `/node/alive_server_list/`
	- return: 
	``` json
    {
        "errMessage": "错误信息",
        "message": [
            "192.168.1.1",
            "192.168.1.2"
        ],
        "statusCode": "错误码"
    }
    ```
2. 获取镜像列表
	- method: `POST`,
	- url: `/node/image_harbor_registry/`
	- post参数: 
	```
    {
        "image_server": "镜像服务器IP"
    }
    ```
	- return
	```
    {
        "message": [
        	{
                "name": "镜像名",
                "description": "描述",
                "pull_count": "pull次数",
                "star_count": "star个数",
                "update_time": "最后更新时间"
            }
        ],
        "statusCode": "错误码",
        "errMessage": "错误信息"
    }
    ```
3. 批量下载镜像
	- method: `POST`
	- url: `/node/download_list/`
	- post参数: 
	```
    {
        "to_hosts": [
            "192.168.1.1",
            "192.168.1.2"
        ],
        "images": [
            "镜像1"，
            "镜像2"
        ]，
        "image_server": "镜像服务器IP"
    }
    ```
    - return
    ``` json
    {
    	"message": [
        	{
                "host": "192.168.1.1",
                "message": {
                    "message": "ok",
                    "statusCode": "错误码",
                    "errMessage": "错误信息"
                },
                "repository": "镜像1"
            },
            {}
        ],
        "statusCode": "错误码",
        "errMessage": "错误信息"
    }
    ```
    
#### 删除所选节点所有镜像
1. 删除所选节目镜像
	- method: `POST`
	- post参数: 
	```
    {
        "hosts": [
            "127.0.0.1"
        ]
    }
    ```
    - url: `/image/remove_all/`
    - return:
    ```
   {
    	"message": [
            {
                "host": "192.168.1.1",
                "message": {
                    "message": "ok",
                    "statusCode": "错误码",
                    "errMessage": "错误信息"
                }
            },
            {}
        ],
        "statusCode": "错误码",
        "errMessage": "错误信息"
    }
    ```

