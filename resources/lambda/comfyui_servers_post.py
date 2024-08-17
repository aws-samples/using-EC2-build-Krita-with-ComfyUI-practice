import boto3
import os
import json
from comfyui_servers_dbutils import query_comfyui_servers_by_username, update_status, create_comfyui_servers_info
from custom_nodes_dbutils import get_custom_nodes_by_type

INSTANCE_GPU=[
    {'instance': 'g5', 'gpu': 'NVIDIA A10G', 'arch': 'Ampere'},
    {'instance': 'g6', 'gpu': 'NVIDIA L4', 'arch': 'Ada Lovelace'},
]

ami_id = os.environ.get('EC2_AMI_ID')
key_name = os.environ.get('EC2_KEY_NAME')
instance_type = os.environ.get('EC2_INSTANCE_TYPE')
security_group_id = os.environ.get('SECURITY_GROUP_ID')
pub_subnet_id = os.environ.get('PUB_SUBNET_ID')
resource_tag = os.environ.get('RESOURCE_TAG')
ec2_role_arn = os.environ.get('EC2_ROLE_ARN')
comfyui_server_port = os.environ.get('COMFYUI_SERVER_PORT')
access_point_global_id = os.environ.get('ACCESS_POINT_GLOBAL_ID')
access_point_output_id = os.environ.get('ACCESS_POINT_OUTPUT_ID')
file_system_id = os.environ.get('FILE_SYSTEM_ID')
account_id = os.environ.get('ACCOUNT_ID')
region = os.environ.get('REGION')

ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')
cw = boto3.client('cloudwatch')
efs_client = boto3.client('efs')

def lambda_handler(event, context):
    
    print(event)
    body = json.loads(event['body'])
    username = body.get('username','No body')
    group_name = body.get('group_name','No Group')
    result = query_comfyui_servers_by_username(username)
    if result:
        print(f"Username:{username} already has a comfyui server")
        for item in result:
            instance_id = item['instance_id']
            if item['status'] == 'stopped':
                start_instance(instance_id=instance_id)
                update_status(username=username, instance_id=instance_id, status='starting')
            else:
                return {
                    "statusCode": 200,
                    "body": json.dumps({"message": f"Can not start instance_id: {instance_id}, current status:{item['status']}", "code": 400})
                }
    else:
        print(f"Username:{username} doesn't have a comfyui server, now create a new one.")
        instances = create_instance(username=username, group_name=group_name)
        instance_id = instances[0].id

    return {
        "statusCode": 200,
        "body": json.dumps({"instance_id": instance_id, "code": 200})
    }

def create_instance(username, group_name):
    comfyui_home_dir = '/home/ubuntu/comfy/ComfyUI'

    # Get Global Custom Nodes
    repo_list = get_custom_nodes_by_type('global')
    # Convert repo_list to a string for the user data script
    repo_clone_commands = "\n".join([f"git clone {repo['repo_url']} {comfyui_home_dir}/custom_nodes/{repo['repo_url'].split('/')[-1]}" for repo in repo_list])
    print(repo_clone_commands)

     # EFS directory Check
    access_point_user_directory=f'/models/users/{username}'
    access_point_group_directory=f'/models/groups/{group_name}'
    exists,user_access_point_id = check_access_point_for_directory(file_system_id, access_point_user_directory)
    if not exists:
        user_access_point_id = create_access_point(file_system_id, access_point_user_directory, username)['AccessPointId']
        
    exists,group_access_point_id = check_access_point_for_directory(file_system_id, access_point_group_directory)
    if not exists:
        group_access_point_id = create_access_point(file_system_id, access_point_group_directory, group_name)['AccessPointId']
    print(f'Current user_access_point_id: {user_access_point_id}, group_access_point_id: {group_access_point_id}')

    # User Data Script
    models_global_dir = f'{comfyui_home_dir}/models/loras/global'
    models_group_dir = f'{comfyui_home_dir}/models/loras/group'
    models_user_dir = f'{comfyui_home_dir}/models/loras/user'
    user_output_dir = f'{comfyui_home_dir}/output'

    user_data_script = f"""#!/bin/bash
    echo "user data"
    su - ubuntu
    # Set current username to file
    echo "{username}" > /home/ubuntu/username

    # Mount EFS
    if [ ! -d "{models_global_dir}" ]; then
        mkdir {models_global_dir}
    fi
    if [ ! -d "{models_group_dir}" ]; then
        mkdir {models_group_dir}
    fi
    if [ ! -d "{models_user_dir}" ]; then
        mkdir {models_user_dir}
    fi
    sudo mount -t efs -o tls,iam,accesspoint={access_point_global_id} {file_system_id}:/ {models_global_dir}
    sudo mount -t efs -o tls,iam,accesspoint={group_access_point_id} {file_system_id}:/ {models_group_dir}
    sudo mount -t efs -o tls,iam,accesspoint={user_access_point_id} {file_system_id}:/ {models_user_dir}
    sudo mount -t efs -o tls,iam,accesspoint={access_point_output_id} {file_system_id}:/ {user_output_dir}
    sudo echo "{file_system_id} {models_global_dir} efs _netdev,tls,iam,accesspoint={access_point_global_id} 0 0" >> /etc/fstab
    sudo echo "{file_system_id} {models_group_dir} efs _netdev,tls,iam,accesspoint={group_access_point_id} 0 0" >> /etc/fstab
    sudo echo "{file_system_id} {models_user_dir} efs _netdev,tls,iam,accesspoint={user_access_point_id} 0 0" >> /etc/fstab
    sudo echo "{file_system_id} {user_output_dir} efs _netdev,tls,iam,accesspoint={access_point_output_id} 0 0" >> /etc/fstab

    # Custom Nodes Clone
    {repo_clone_commands}
    sudo chown -R ubuntu:ubuntu {comfyui_home_dir}/custom_nodes/*
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

        instance_id=instances[0].id
        gpu_info = next((item for item in INSTANCE_GPU if item['instance'] == instance_type[:2]), None)
        # 添加告警,一旦GPU使用过低超过30分钟, 直接Stop

        cw.put_metric_alarm(
            AlarmName=f'GPUUtilizationLow-{instance_id}',
            ComparisonOperator='LessThanThreshold',
            EvaluationPeriods=30,
            MetricName='nvidia_smi_utilization_gpu',
            Namespace='CWAgent',
            Period=60,
            Statistic='Maximum',
            Threshold=1.0,
            ActionsEnabled=True,
            AlarmActions=[f'arn:aws:swf:{region}:{account_id}:action/actions/AWS_EC2.InstanceId.Stop/1.0'],
            AlarmDescription='Alarm when GPU utilization is low for 30 minutes',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                },
                {
                    'Name': 'name', 
                    'Value': gpu_info['gpu']
                },
                {
                    'Name': 'index', 
                    'Value': '0'
                },
                {
                    'Name': 'arch', 
                    'Value': gpu_info['arch']
                }
            ]
        )
        create_comfyui_servers_info(username=username, group_name=group_name, instance_id=instance_id)
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

def check_access_point_for_directory(file_system_id, target_directory):

    # 获取指定文件系统的所有 Access Points
    response = efs_client.describe_access_points(FileSystemId=file_system_id)

    # 遍历所有 Access Points
    for access_point in response['AccessPoints']:
        # 获取根目录路径
        root_directory = access_point['RootDirectory']['Path']
        
        # 检查目标目录是否与 Access Point 的根目录匹配
        if root_directory == target_directory:
            print(f"Access Point ID: {access_point['AccessPointId']} exists for directory: {target_directory}")
            return True,access_point['AccessPointId']

    print(f"No Access Point found for directory: {target_directory}")
    return False,'0'

def create_access_point(file_system_id, root_directory_path, name):
    # 创建 Access Point
    response = efs_client.create_access_point(
        ClientToken=f'unique-client-token-{name}',  # 确保这是唯一的
        FileSystemId=file_system_id,
        PosixUser={
            'Uid': 1000,  # POSIX 用户 ID
            'Gid': 1000,  # POSIX 组 ID
            'SecondaryGids': [1001]  # 可选的附加组 ID
        },
        RootDirectory={
            'Path': root_directory_path,  # 根目录路径
            'CreationInfo': {
                'OwnerUid': 1000,  # 根目录所有者 UID
                'OwnerGid': 1000,  # 根目录所有者 GID
                'Permissions': '0755'  # 根目录权限，例如 '750'
            }
        },
        Tags=[
            {
                'Key': 'Name',
                'Value': f'AccessPoint-{name}'  # 自定义标签
            }
        ]
    )
    return response