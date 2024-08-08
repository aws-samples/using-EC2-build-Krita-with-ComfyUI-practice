import boto3

def lambda_handler(event, context):

    ec2_client = boto3.client('ec2')
    # 停止实例，替换为您的实例ID
    instance_id = 'i-1234567890abcdef0'
    try:
        response = ec2_client.stop_instances(InstanceIds=[instance_id])
        print(f'Successfully stopped instance: {instance_id}')
        return response
    except Exception as e:
        print(f'Error stopping instance: {e}')
        raise e