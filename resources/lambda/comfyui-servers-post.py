import boto3
import os
import json

ami_id = os.environ.get('EC2_AMI_ID')
key_name = os.environ.get('EC2_KEY_NAME')
instance_type = os.environ.get('EC2_INSTANCE_TYPE')
security_group_id = os.environ.get('SECURITY_GROUP_ID')
pub_subnet_id = os.environ.get('PUB_SUBNET_ID')
resource_tag = os.environ.get('RESOURCE_TAG')
ec2_role_arn = os.environ.get('EC2_ROLE_ARN')

def lambda_handler(event, context):
    
    print(event)
    body = json.loads(event['body'])
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
                            'Value': body.get('username','No body') + '-comfyui'  # 标签值
                        }
                    ]
                }
            ],
            IamInstanceProfile={
                'Arn': ec2_role_arn
            }
        )
    except Exception as e:
        print(f'Error stopping instance: {e}')
        raise e

    return {
        "statusCode": 200,
        "body": json.dumps({"instance_id": instances[0].id, "code": 200})
    }