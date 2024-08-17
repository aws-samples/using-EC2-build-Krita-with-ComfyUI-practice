from datetime import datetime
import os
import boto3
from boto3.dynamodb.conditions import Key

custom_nodes_table = os.environ.get('COMFYUI_CUSTOM_NODES_TABLE')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(custom_nodes_table)

def get_custom_nodes_by_type(node_type):
    response = table.query(
        IndexName='node-type-index',
        KeyConditionExpression=Key('node_type').eq(node_type)
    )
    return response['Items']