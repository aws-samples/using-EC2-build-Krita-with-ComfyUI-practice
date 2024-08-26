import boto3
import json
import os
from comfyui_servers_dbutils import update_status, query_comfyui_servers_by_username

comfyui_servers_table = os.environ.get('USER_COMFYUI_SERVERS_TABLE')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(comfyui_servers_table)
ec2_client = boto3.client('ec2')

def lambda_handler(event, context):

    print(event)
    body = json.loads(event['body'])
    username = body.get('username','No body')
    group_name = body.get('group_name','No Group')
    result = query_comfyui_servers_by_username(username)
    
    if result:
        for item in result:
            stop_instance(item['instance_id'])
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