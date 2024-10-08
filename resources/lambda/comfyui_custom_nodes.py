from datetime import datetime
import os
import boto3
import json
import uuid
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

custom_nodes_table = os.environ.get('COMFYUI_CUSTOM_NODES_TABLE')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(custom_nodes_table)

def lambda_handler(event, context):
    print(event)
    if event['httpMethod'] == 'POST':
        return create_custom_nodes(event)
    elif event['httpMethod'] == 'PATCH':
        return update_custom_nodes(event)
    elif event['httpMethod'] == 'GET':
        return get_custom_nodes(event)
    elif event['httpMethod'] == 'DELETE':
        return delete_custom_nodes(event)
    else:
        return build_response(400, json.dumps({'code': 500, 'message': f'Not support method:{event['httpMethod']}'}))

def create_custom_nodes(event):
    body = json.loads(event['body'])
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        item = {
            "id": str(uuid.uuid1()),
            "node_name": body.get("node_name"),
            "node_type": body.get("node_type"),
            "group_name": body.get("group_name"),
            "repo_url": body.get("repo_url"),
            "extra_parameter": body.get("extra_parameter"),
            "status": body.get("status"),
            "creator": body.get("creator"),
            'created_at': now,
            'updated_at': now,
        }
        table.put_item(Item=item)
        return build_response(200, json.dumps({'code': 200, 'item': item}))
    except Exception as e:
        print(f'Error creating custom nodes: {e}')
        return build_response(500, json.dumps(e))
                              
def update_custom_nodes(event):
    if not event['pathParameters']:
        return build_response(400, json.dumps({'code': 400, 'message': 'customer node id is mandatory'}))

    body = json.loads(event['body'])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        response = table.update_item(
            Key={
                'id': event['pathParameters']["id"]
            },
            UpdateExpression="SET #node_name = :node_name,#node_type = :node_type,#group_name = :group_name,#status =:status, #repo_url = :repo_url, #updated_at = :updated_at, #extra_parameter = :extra_parameter",  # 更新表达式
            ExpressionAttributeNames={
                '#status': 'status',  # 使用表达式属性名称来避免与保留字冲突
                '#updated_at': 'updated_at',
                '#node_name': 'node_name',
                '#node_type': 'node_type',
                '#group_name': 'group_name',
                '#extra_parameter': 'extra_parameter',
                '#repo_url': 'repo_url',
            },
            ExpressionAttributeValues={
                ':status': body.get("status"),  # 新的状态值
                ':updated_at': now,  # 当前时间
                ':node_name': body.get("node_name"),
                ':node_type': body.get("node_type"),
                ':group_name': body.get("group_name"),
                ':extra_parameter': body.get("extra_parameter", ""),
                ':repo_url': body.get("repo_url"),
            },
            ReturnValues="ALL_NEW"  # 返回更新后的新值
        )
        print("UpdateItem succeeded:", response)
        return build_response(200, json.dumps({'code': 200, 'item': response['Attributes']}))
    except Exception as e:
        print(f"Error updating item: {e}")
        return build_response(500, json.dumps(e))

def get_custom_nodes(event):
    if event['pathParameters'] and event['pathParameters']['id']:
        response = table.query(
            KeyConditionExpression=Key('id').eq(event['pathParameters']['id'])
        )
        items = response['Items']
        return build_response(200, json.dumps({'code': 200, 'item': items[0]}))
    else:
        response = table.query(
            IndexName='node-type-index',  # 替换为您的GSI名称
            KeyConditionExpression=Key('node_type').eq(event['queryStringParameters']['node_type'])
        )
        print(response)
        return build_response(200, json.dumps({'code': 200, 'items': response['Items']}))

def delete_custom_nodes(event):
    if event['pathParameters'] and event['pathParameters']['id']:
        try:
            response = table.delete_item(
                Key={
                    'id': event['pathParameters']['id']
                },
                ConditionExpression='attribute_exists(id)'
            )
            return build_response(200, json.dumps({'code': 200, 'response': response}))
        except ClientError as e:
            if e.response['Error']['Code'] == "ConditionalCheckFailedException":
                return build_response(404, json.dumps({'code': 404, 'response': f"item not found with id: {event['pathParameters']['id']}"}))
            else:
                print("Unexpected error: %s" % e)
    else:
        return build_response(400, json.dumps({'code': 400, 'message':'parameter id is mandatory' }))
def build_response(statusCode, body):
    return {
        'statusCode': statusCode,
        'body': body
    }