from datetime import datetime
import os
import boto3
from boto3.dynamodb.conditions import Key

comfyui_servers_table = os.environ.get('USER_COMFYUI_SERVERS_TABLE')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(comfyui_servers_table)

def update_status(username, instance_id, status):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        response = table.update_item(
            Key={
                'username': username,  # 分区键
                'instance_id': instance_id  # 排序键
            },
            UpdateExpression="SET #status = :status, #updated_at = :updated_at",  # 更新表达式
            ExpressionAttributeNames={
                '#status': 'status',  # 使用表达式属性名称来避免与保留字冲突
                '#updated_at': 'updated_at'
            },
            ExpressionAttributeValues={
                ':status': status,  # 新的状态值
                ':updated_at': now  # 当前时间
            },
            ReturnValues="UPDATED_NEW"  # 返回更新后的新值
        )
        print("UpdateItem succeeded:", response)
    except Exception as e:
        print(f"Error updating item: {e}")

def query_comfyui_servers_by_username(username):
    try:
        response = table.query(
            KeyConditionExpression=Key('username').eq(username)  # 这里 'username' 是你的分区键名
        )
        items = response['Items']
        return items
    except Exception as e:
        print(f"Error querying items: {e}")
        return None

def create_comfyui_servers_info(username, group_name, instance_id):
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        item = {
                'username': username,
                'group_name': group_name,
                'instance_id': instance_id,
                'status': 'creating',
                'created_at': now,
                'updated_at': now,
        }
        table.put_item(Item=item)
    except Exception as e:
        print(f'Error stopping instance: {e}')
        raise e

def update_comfyui_server_info(username, instance_id, status, server_info):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        response = table.update_item(
            Key={
                'username': username,  # 分区键
                'instance_id': instance_id  # 排序键
            },
            UpdateExpression="SET #status = :status,#server_info = :server_info, #updated_at = :updated_at",  # 更新表达式
            ExpressionAttributeNames={
                '#status': 'status',  # 使用表达式属性名称来避免与保留字冲突
                '#updated_at': 'updated_at',
                '#server_info': 'server_info',
            },
            ExpressionAttributeValues={
                ':status': status,  # 新的状态值
                ':updated_at': now,  # 当前时间
                ':server_info': server_info
            },
            ReturnValues="UPDATED_NEW"  # 返回更新后的新值
        )
        print("UpdateItem succeeded:", response)
    except Exception as e:
        print(f"Error updating item: {e}")