import boto3
import os
import json
from dbutils import query_by_username, update_status, create_comfyui_servers_info

ami_id = os.environ.get('EC2_AMI_ID')
key_name = os.environ.get('EC2_KEY_NAME')
instance_type = os.environ.get('EC2_INSTANCE_TYPE')
security_group_id = os.environ.get('SECURITY_GROUP_ID')
pub_subnet_id = os.environ.get('PUB_SUBNET_ID')
resource_tag = os.environ.get('RESOURCE_TAG')
ec2_role_arn = os.environ.get('EC2_ROLE_ARN')
comfyui_server_port = os.environ.get('COMFYUI_SERVER_PORT')
access_point_global_id = os.environ.get('ACCESS_POINT_GLOBAL_ID')
access_point_groups_id = os.environ.get('ACCESS_POINT_GROUPS_ID')
file_system_id = os.environ.get('FILE_SYSTEM_ID')

ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')

def lambda_handler(event, context):
    
    print(event)
    body = json.loads(event['body'])
    username = body.get('username','No body')
    group_name = body.get('group_name','No Group')
    result = query_by_username(username)
    if result:
        print(f"Username:{username} already has a comfyui server")
        for item in result:
            instance_id = item['instance_id']
            start_instance(instance_id=instance_id)
            update_status(username=username, instance_id=instance_id, status='starting')
    else:
        print(f"Username:{username} doesn't have a comfyui server, now create a new one.")
        instances = create_instance(username=username, group_name=group_name)
        instance_id = instances[0].id

    return {
        "statusCode": 200,
        "body": json.dumps({"instance_id": instance_id, "code": 200})
    }

def create_instance(username, group_name):

    comfyui_home_dir = "/home/ubuntu/comfy/ComfyUI"
    # 定义用户数据脚本, !!!!!!!!下面的脚本需要根据我们使用的不同AMI,作出调整!!!!!!!
    user_data_script = f"""#!/bin/bash
    sudo apt-get update
    sudo apt-get -y install git binutils rustc cargo pkg-config libssl-dev
    git clone https://github.com/aws/efs-utils
    cd efs-utils
    ./build-deb.sh
    sudo apt-get -y install ./build/amazon-efs-utils*deb
    
    mkdir {comfyui_home_dir}/models/loras/global
    mkdir {comfyui_home_dir}/models/loras/groups
    chown ubuntu:ubuntu {comfyui_home_dir}/models/loras/global
    chown ubuntu:ubuntu {comfyui_home_dir}/models/loras/groups
    mount -t efs -o tls,iam,accesspoint={access_point_global_id} {file_system_id}:/ {comfyui_home_dir}/models/loras/global
    mount -t efs -o tls,iam,accesspoint={access_point_groups_id} {file_system_id}:/ {comfyui_home_dir}/models/loras/groups
    echo "{file_system_id} {comfyui_home_dir}/models/loras/global efs _netdev,tls,iam,accesspoint={access_point_global_id} 0 0" >> /etc/fstab
    echo "{file_system_id} {comfyui_home_dir}/models/loras/groups efs _netdev,tls,iam,accesspoint={access_point_groups_id} 0 0" >> /etc/fstab

    cat <<EOL > /etc/systemd/system/comfyui.service
    [Unit]
    Description=ComfyUI Service
    After=network.target

    [Service]
    User=ubuntu
    WorkingDirectory=/home/ubuntu
    ExecStart=/bin/bash -c 'source /home/ubuntu/venv/bin/activate && python3 {comfyui_home_dir}/main.py --listen 0.0.0.0 --port {comfyui_server_port}'
    Restart=always
    Environment=PATH=/home/ubuntu/venv/bin:\$PATH

    [Install]
    WantedBy=multi-user.target
    EOL
    systemctl daemon-reload
    systemctl start comfyui.service
    systemctl enable comfyui.service
    """
    
    try:
        # 创建EC2实例
        instances = ec2.create_instances(
            ImageId=ami_id,  # 替换为您需要的AMI ID
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_type,  # 替换为您需要的实例类型
            KeyName=key_name,  # 替换为您的密钥对名称
            UserData=user_data_script,
            SecurityGroupIds=[security_group_id],
            SubnetId=pub_subnet_id,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',  # 指定资源类型为 EC2 实例
                    'Tags': [
                        {
                            'Key': 'RESOURCE_TAG',  # 标签键
                            'Value': resource_tag  # 标签值
                        },
                        {
                            'Key': 'Name',  # 标签键
                            'Value': username  # 标签值
                        }
                    ]
                }
            ],
            IamInstanceProfile={
                'Arn': ec2_role_arn
            }
        )

        create_comfyui_servers_info(username=username, group_name=group_name, instance_id=instances[0].id)
    except Exception as e:
        print(f'Error stopping instance: {e}')
        raise e

    return instances

def start_instance(instance_id):
    try:
        response = ec2_client.start_instances(InstanceIds=[instance_id])
        print(f'Successfully stopped instance: {instance_id}')
        return response
    except Exception as e:
        print(f'Error stopping instance: {e}')
        raise e