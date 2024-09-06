## 使用Amazon EC2 来构建Comfy UI Servers
### 架构图
![Arch](arch.jpg "架构图") 
### 部署步骤
#### 生成环境变量, 请根据自身环境信息修改`gen_env.sh`后,执行脚本
```
sh gen_env.sh
```

### API说明
Invoke URL: 请在CloudFormation中查看API Gateway Stack的输出.
API Key: 请在CloudFormation中查看API Gateway Stack的输出中找到apikey的ARN,然后基于ARN找到apikey的值

#### 创建GPU EC2
```
URL: {{url}}/comfyui-servers
Method: POST
Header: 
    x-api-key: {{api-key}}
Post Body:
    {
        "username": # 用户名,
        "group_name": # 部门名称
        "server_idle_time": #服务器闲置时间
    }
Response:
成功:{
        "instance_id": "i-08a522c731994ee3b", # EC2 实例ID
        "code": 200 # 服务代码
    }
失败:
    {"message": "", "code": 400}
```
#### 停止GPU EC2
```
URL: {{url}}/comfyui-servers/stop
Method: PATCH
Header: 
    x-api-key: {{api-key}}
Post Body:
    {
        "username": # 用户名,
        "group_name": # 部门名称
    }
Response:
成功:{
        "instance_id": "i-08a522c731994ee3b", # EC2 实例ID
        "code": 200 # 响应代码
    }
失败:
    {"message": "", "code": 400}
```
#### 查询GPU EC2状态信息
```
URL: {{url}}/comfyui-servers?username=user40
Method: GET
Header: 
    x-api-key: {{api-key}}
queryParameter:
    username={{username}}
Response:
成功:{
        "code": 200, # 响应代码
        "server-info": {
            "updated_at": "2024-08-15 09:25:42", # 更新时间
            "created_at": "2024-08-11 15:38:58", # 创建时间
            "instance_id": "i-08a522c731994ee3b", # EC2 实例ID
            "status": "running", # EC2 状态, 主要包含: starting, running, stopping, stopped
            "comfyui_available": true/false, # true: comfyui服务可用, false: comfyui服务不可用
            "username": "user30", # 用户名
            "server_info": "18.237.77.160:8848", # 用户资源信息
            "group_name": "group1" # 部门信息
        }
    }
失败:
    {"message": "", "code": 400}
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

## Disclaimer
=============================Disclaimer========================================
The sample code or script or other assets are provided as Service Content (in the case that you are using Amazon Web Services China regions) or AWS Content (in the case that you are using Amazon Web Services regions outside Mainland China) (“Assets”) under the Customer Agreement or the relevant written agreement between you and the operator of the relevant Amazon Web Services region (whichever applies). You should not use the Assets in your production accounts, or on production or other critical data. You are responsible for testing, securing, and optimizing the Assets, as appropriate for production grade use based on your specific quality control practices and standards.  Deploying the Assets may incur charges for creating or using Amazon Web Services chargeable resources, such as running Amazon EC2 instances or using Amazon S3 storage.
示例代码或脚本或其他资料（“资料”）作为您与相关亚马逊云科技区域运营商之间的客户协议或相关书面协议（以适用者为准）下的“服务内容”（如果您使用亚马逊云科技中国区域）或“AWS 内容”（如果您使用中国大陆以外的亚马逊云科技区域）而提供给您。您不应在您的生产账户中使用“资料”，也不应将“资料”用于您的生产或其他关键数据。您负责根据您的特定质量控制实践和标准对“资料”进行测试、采取安全措施和优化，以适合生产级用途。部署“资料”可能会因创建或使用亚马逊云科技收费资源（例如运行Amazon EC2 实例或使用 Amazon S3 存储）而产生费用。
=============================End of disclaimer ===================================
