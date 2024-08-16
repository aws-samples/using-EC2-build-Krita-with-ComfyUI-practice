import boto3
import json
from comfyui_servers_dbutils import query_comfyui_servers_by_username

def lambda_handler(event, context):
    
    print(event)
    username = event.get('queryStringParameters', {}).get('username')
    if username:
        print(f"username: {username}")
    else:
        raise Exception("parameter username is mandantory~!")
    items = query_comfyui_servers_by_username(username=username)
    if items:
        return {
            "statusCode": 200,
            "body": json.dumps({"code":200, "server-info":items[0]})
        }
    else:
        return {
            "statusCode": 200,
            "body": json.dumps({"code":400, "message": f"No server info with username: {username}"})
        }