import boto3
import json
import os
from boto3.dynamodb.conditions import Key
from datetime import datetime

comfyui_servers_table = os.environ.get('USER_COMFYUI_SERVERS_TABLE')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(comfyui_servers_table)
ec2_client = boto3.client('ec2')

def lambda_handler(event, context):

    print(event)
    body = json.loads(event['body'])
    username = body.get('username','No body')
    group_name = body.get('group_name','No Group')
    result = query_by_username(username)
    
    if result:
        for item in result:
            stop_instance(item['instance_id'])
            update_status(username, item['instance_id'])
            return {
                "statusCode": 200,
                "body": json.dumps({"instance_id": item['instance_id'], "code": 200})
            }
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": f"No instance exists with username: {username}", "code": 400})
        }

def stop_instance(instance_id):
    try:
        response = ec2_client.stop_instances(InstanceIds=[instance_id])
        print(f'Successfully stopped instance: {instance_id}')
        return response
    except Exception as e:
        print(f'Error stopping instance: {e}')
        raise e

def query_by_username(username):
    try:
        response = table.query(
            KeyConditionExpression=Key('username').eq(username)  # 这里 'username' 是你的分区键名
        )
        items = response['Items']
        return items
    except Exception as e:
        print(f"Error querying items: {e}")
        return None

def update_status(username, instance_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        response = table.update_item(
            Key={
                'username': username,  # 分区键
                'instance_id': instance_id  # 排序键
            },
            UpdateExpression="SET #status = :stopped, #updated_at = :updated_at",  # 更新表达式
            ExpressionAttributeNames={
                '#status': 'status',  # 使用表达式属性名称来避免与保留字冲突
                '#updated_at': 'updated_at'
            },
            ExpressionAttributeValues={
                ':stopped': 'stopped',  # 新的状态值
                ':updated_at': now  # 当前时间
            },
            ReturnValues="UPDATED_NEW"  # 返回更新后的新值
        )
        print("UpdateItem succeeded:", response)
    except Exception as e:
        print(f"Error updating item: {e}")