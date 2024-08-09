import boto3
import os

ami_id = os.environ.get('EC2_AMI_ID')
key_name = os.environ.get('EC2_KEY_NAME')
instance_type = os.environ.get('EC2_INSTANCE_TYPE')
security_group_id = os.environ.get('SECURITY_GROUP_ID')
pub_subnet_id = os.environ.get('PUB_SUBNET_ID')

def lambda_handler(event, context):
    # 创建EC2资源对象
    ec2 = boto3.resource('ec2')

    # 定义用户数据脚本, !!!!!!!!下面的脚本需要根据我们使用的不同AMI,作出调整!!!!!!!
    user_data_script = """#!/bin/bash
    source /home/ubuntu/venv/bin/activate
    python3 /home/ubuntu/comfy/ComfyUI/main.py --listen 0.0.0.0 --port 8848
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
            SubnetId=pub_subnet_id
        )
    except Exception as e:
        print(f'Error stopping instance: {e}')
        raise e

    # 打印实例ID
    for instance in instances:
        print(f'Created instance with ID: {instance.id}')