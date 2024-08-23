import boto3
import json
import socket
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
        server_info = items[0]
        if server_info['status'] == 'running' and server_info['server_info']:
            server_info['comfyui_avaiable'] = is_port_open(server_info['server_info'].split(':')[0], int(server_info['server_info'].split(':')[1]))
        else:
            server_info['comfyui_avaiable'] = False
        return {
            "statusCode": 200,
            "body": json.dumps({"code":200, "server-info":server_info})
        }
    else:
        return {
            "statusCode": 200,
            "body": json.dumps({"code":400, "message": f"No server info with username: {username}"})
        }

def is_port_open(ip, port, timeout=2):
    """
    检查指定的IP和端口是否开放
    :param ip: 目标IP地址
    :param port: 目标端口
    :param timeout: 超时时间（秒）
    :return: True 如果端口开放，False 如果端口未开放
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
    except (socket.timeout, ConnectionRefusedError):
        return False
    finally:
        sock.close()
    return True