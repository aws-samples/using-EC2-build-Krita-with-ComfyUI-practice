import boto3
import os
import json
from dbutils import query_by_username, update_status, create_comfyui_servers_info

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
access_point_groups_id = os.environ.get('ACCESS_POINT_GROUPS_ID')
file_system_id = os.environ.get('FILE_SYSTEM_ID')
account_id = os.environ.get('ACCOUNT_ID')
region = os.environ.get('REGION')

ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')
cw = boto3.client('cloudwatch')

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
    user_data_script = f"""#!/bin/bash
    echo "user data"
    su - ubuntu
    mkdir {comfyui_home_dir}/models/loras/global
    mkdir {comfyui_home_dir}/models/loras/groups
    sudo mount -t efs -o tls,iam,accesspoint={access_point_global_id} {file_system_id}:/ {comfyui_home_dir}/models/loras/global
    sudo mount -t efs -o tls,iam,accesspoint={access_point_groups_id} {file_system_id}:/ {comfyui_home_dir}/models/loras/groups
    sudo echo "{file_system_id} {comfyui_home_dir}/models/loras/global efs _netdev,tls,iam,accesspoint={access_point_global_id} 0 0" >> /etc/fstab
    sudo echo "{file_system_id} {comfyui_home_dir}/models/loras/groups efs _netdev,tls,iam,accesspoint={access_point_groups_id} 0 0" >> /etc/fstab
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