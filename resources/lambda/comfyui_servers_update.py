import boto3
import os
from comfyui_servers_dbutils import update_comfyui_server_info

comfyui_servers_table = os.environ.get('USER_COMFYUI_SERVERS_TABLE')
comfyui_server_port = os.environ.get('COMFYUI_SERVER_PORT')
ec2_name_prefix = os.environ.get('EC2_NAME_PREFIX')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(comfyui_servers_table)
ec2_client = boto3.client('ec2')

def lambda_handler(event, context):
    print(event)
    instance_id = event['detail']['instance-id']
    state = event['detail']['state']
    # 获取实例的信息
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    print(response)
    # 提取实例的标签
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    # 查找 Name 标签
    name_tag = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), None)
    if name_tag and name_tag.startswith(ec2_name_prefix):
        username = name_tag.replace(ec2_name_prefix, '')
        if state == 'running':
            public_ip = response['Reservations'][0]['Instances'][0].get('PublicIpAddress')
            private_ip = response['Reservations'][0]['Instances'][0].get('PrivateIpAddress')
            server_info = f"{public_ip}:{comfyui_server_port}"
            update_comfyui_server_info(username=username, instance_id=instance_id, status=state, server_info=server_info, private_ip=private_ip)
        elif state == 'stopped' or state == 'stopping':
            update_comfyui_server_info(username=username, instance_id=instance_id, status=state, server_info="", private_ip='')
        else:
            raise Exception(f"Not support status: {state}")
    else:
        print(f'Not comfyui instance: {instance_id}')