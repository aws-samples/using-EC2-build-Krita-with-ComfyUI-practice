import boto3
import os
import json

table_name = os.environ.get('USER_COMFYUI_SERVERS_TABLE')

def lambda_handler(event, context):
    
    print(event)
    body = json.loads(event['body'])
    # 创建EC2资源对象
    dynamodb_client = boto3.client('dynamodb')

    try:
        response = dynamodb_client.get_item(
            TableName=table_name,
            Key={
                'username': {'S': body.get('username')}
            }
        )
        print(response['Item'])
    except Exception as e:
        print(f'Error stopping instance: {e}')
        raise e

    return {
        "statusCode": 200,
        "body": json.dumps(response['Item'])
    }