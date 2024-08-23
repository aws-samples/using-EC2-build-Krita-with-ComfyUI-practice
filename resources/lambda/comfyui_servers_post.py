import boto3
import os
import json
from comfyui_servers_dbutils import query_comfyui_servers_by_username, update_status, create_comfyui_servers_info
from custom_nodes_dbutils import get_custom_nodes_by_type

INSTANCE_GPU=[
    {'instance': 'g5', 'gpu': 'NVIDIA A10G', 'arch': 'Ampere'},
    {'instance': 'g6', 'gpu': 'NVIDIA L4', 'arch': 'Ada Lovelace'},
]

ami_id = os.environ.get('EC2_AMI_ID')
key_name = os.environ.get('EC2_KEY_NAME')
instance_type = os.environ.get('EC2_INSTANCE_TYPE')
security_group_id = os.environ.get('SECURITY_GROUP_ID')
pub_subnet_id = os.environ.get('PUB_SUBNET_ID')
resource_tag = os.environ.get('RESOURCE_TAG')
ec2_role_arn = os.environ.get('EC2_ROLE_ARN')
ec2_name_prefix = os.environ.get('EC2_NAME_PREFIX')
account_id = os.environ.get('ACCOUNT_ID')
region = os.environ.get('REGION')

# EFS
access_point_models_id = os.environ.get('ACCESS_POINT_MODELS_ID')
access_point_output_id = os.environ.get('ACCESS_POINT_OUTPUT_ID')
access_point_start_script_id = os.environ.get('ACCESS_POINT_START_SCRIPT_ID')
file_system_id = os.environ.get('FILE_SYSTEM_ID')
mount_path = os.environ.get('MOUNT_PATH')

ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')
cw = boto3.client('cloudwatch')
efs_client = boto3.client('efs')

ubuntu_home = '/home/ubuntu'
comfyui_home_dir = '/home/ubuntu/comfy/ComfyUI'
start_script_folder = 'start-script'
model_dirs = ['checkpoints', 'clip', 'clip_vision', 'configs', 'controlnet', 'diffusers', 'diffusion_models', 'embeddings', 'gligen', 'hypernetworks', 'inpaint', 'ipadapter', 'loras', 'mmdets', 'onnx', 'photomaker', 'sams', 'style_models', 'ultralytics', 'unet', 'upscale_models', 'vae', 'vae_approx']
def lambda_handler(event, context):
    
    print(event)
    body = json.loads(event['body'])
    username = body.get('username','No body')
    group_name = body.get('group_name','No Group')
    result = query_comfyui_servers_by_username(username)
    if result:
        print(f"Username:{username} already has a comfyui server")
        for item in result:
            instance_id = item['instance_id']
            if item['status'] == 'stopped':
                start_instance(instance_id=instance_id)
                update_status(username=username, instance_id=instance_id, status='starting')
            else:
                return {
                    "statusCode": 200,
                    "body": json.dumps({"message": f"Can not start instance_id: {instance_id}, current status:{item['status']}", "code": 400})
                }
    else:
        print(f"Username:{username} doesn't have a comfyui server, now create a new one.")
        instances = create_instance(username=username, group_name=group_name)
        instance_id = instances[0].id

    return {
        "statusCode": 200,
        "body": json.dumps({"instance_id": instance_id, "code": 200})
    }

def create_instance(username, group_name):
    # Get Global Custom Nodes
    repo_list = get_custom_nodes_by_type('global')
    # Convert repo_list to a string for the user data script
    repo_clone_commands = "\n".join([
        f"""
        if [ ! -d {comfyui_home_dir}/custom_nodes/{repo['repo_url'].split('/')[-1].replace('.git', '')} ]; then
            git clone {repo['repo_url']} {comfyui_home_dir}/custom_nodes/{repo['repo_url'].split('/')[-1].replace('.git', '')} &&
            if [ -f {comfyui_home_dir}/custom_nodes/{repo['repo_url'].split('/')[-1].replace('.git', '')}/requirements.txt ]; then
                source /home/ubuntu/venv/bin/activate && pip install -r {comfyui_home_dir}/custom_nodes/{repo['repo_url'].split('/')[-1].replace('.git', '')}/requirements.txt;
            fi
        else
            echo "Repository {repo['repo_url']} already cloned."
        fi
        """
        for repo in repo_list
    ])
    print(repo_clone_commands)

    # User Data Script
    output_dir = f'{comfyui_home_dir}/output'
    user_output_dir = f'{output_dir}/{group_name}/{username}'
    ec2_start_script_dir = f'{ubuntu_home}/{start_script_folder}'

    check_efs_directory_and_produce_mount_cmd(username=username, group_name=group_name)

    user_data_script = f"""#!/bin/bash
    echo "---------user data start-----------"
    # Mount EFS
    if [ ! -d "{ec2_start_script_dir}" ]; then
        mkdir -p {ec2_start_script_dir}
    fi
    mount -t efs -o tls,iam,accesspoint={access_point_start_script_id} {file_system_id}:/{username} {ec2_start_script_dir}
    echo "{file_system_id}:/{username} {ec2_start_script_dir} efs _netdev,tls,iam,accesspoint={access_point_start_script_id} 0 0" >> /etc/fstab
    chmod +x {ec2_start_script_dir}/mount.sh
    bash {ec2_start_script_dir}/mount.sh
    
    # Create User Output Dir
    if [ ! -d "{user_output_dir}" ]; then
        mkdir -p {user_output_dir}
    fi

    # Custom Nodes Clone
    {repo_clone_commands}
    sudo chown -R ubuntu:ubuntu {comfyui_home_dir}/custom_nodes/*

    # Set Comfyui as system service
    sudo cat << EOF > /etc/systemd/system/comfyui.service
    [Unit]
    Description=ComfyUI Service
    After=network.target

    [Service]
    User=ubuntu
    WorkingDirectory=/home/ubuntu/comfy/ComfyUI
    ExecStart=/home/ubuntu/venv/bin/python3 main.py --listen 0.0.0.0 --port 8848 --output-directory {user_output_dir}
    Restart=always

    [Install]
    WantedBy=multi-user.target
EOF

    # start comfyui as system service
    sudo systemctl daemon-reload
    sudo systemctl enable comfyui.service
    sudo systemctl start comfyui.service
    echo "---------user data end-----------"
    """
    
    try:
        # 创建EC2实例
        instances = ec2.create_instances(
            ImageId=ami_id,  # 替换为您需要的AMI ID
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_type,  # 替换为您需要的实例类型
            KeyName=key_name,  # 替换为您的密钥对名称
            UserData=user_data_script,
            SecurityGroupIds=[security_group_id],
            SubnetId=pub_subnet_id,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',  # 指定资源类型为 EC2 实例
                    'Tags': [
                        {
                            'Key': 'RESOURCE_TAG',  # 标签键
                            'Value': resource_tag  # 标签值
                        },
                        {
                            'Key': 'Name',  # 标签键
                            'Value': f'{ec2_name_prefix}{username}'  # 标签值
                        }
                    ]
                }
            ],
            IamInstanceProfile={
                'Arn': ec2_role_arn
            }
        )

        instance_id=instances[0].id
        gpu_info = next((item for item in INSTANCE_GPU if item['instance'] == instance_type[:2]), None)
        # 添加告警,一旦GPU使用过低超过30分钟, 直接Stop

        cw.put_metric_alarm(
            AlarmName=f'GPUUtilizationLow-{instance_id}',
            ComparisonOperator='LessThanThreshold',
            EvaluationPeriods=30,
            MetricName='nvidia_smi_utilization_gpu',
            Namespace='CWAgent',
            Period=60,
            Statistic='Maximum',
            Threshold=1.0,
            ActionsEnabled=True,
            AlarmActions=[f'arn:aws:swf:{region}:{account_id}:action/actions/AWS_EC2.InstanceId.Stop/1.0'],
            AlarmDescription='Alarm when GPU utilization is low for 30 minutes',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                },
                {
                    'Name': 'name', 
                    'Value': gpu_info['gpu']
                },
                {
                    'Name': 'index', 
                    'Value': '0'
                },
                {
                    'Name': 'arch', 
                    'Value': gpu_info['arch']
                }
            ]
        )
        create_comfyui_servers_info(username=username, group_name=group_name, instance_id=instance_id)
    except Exception as e:
        print(f'Error stopping instance: {e}')
        raise e

    return instances

def start_instance(instance_id):
    try:
        response = ec2_client.start_instances(InstanceIds=[instance_id])
        print(f'Successfully stopped instance: {instance_id}')
        return response
    except Exception as e:
        print(f'Error stopping instance: {e}')
        raise e
    
def check_create_directory(directory):
    """检查目录是否存在，如果不存在则创建目录。"""
    if not os.path.exists(directory):  
        os.makedirs(directory)  

def check_efs_directory_and_produce_mount_cmd(group_name, username):

    start_script_dir = os.path.join(mount_path, start_script_folder, username)
    check_create_directory(start_script_dir)

    """检查EFS目录并生成挂载命令。"""
    mount_cmd = ['#!/bin/bash']  # 使用列表来更有效地构建挂载命令

    for dir_name in model_dirs:
        # 拼接完整路径
        efs_paths = {
            'global': os.path.join(mount_path, 'models', dir_name, 'global'),
            'group': os.path.join(mount_path, 'models', dir_name, 'groups', group_name),
            'user': os.path.join(mount_path, 'models', dir_name, 'users', username)
        }

        # 检查并创建EFS路径
        for path in efs_paths.values():
            check_create_directory(path)

        # 拼接EC2路径
        ec2_paths = {
            'global': os.path.join(comfyui_home_dir, 'models', dir_name, 'global'),
            'group': os.path.join(comfyui_home_dir, 'models', dir_name, 'group'),
            'user': os.path.join(comfyui_home_dir, 'models', dir_name, 'user')
        }

        # 生成挂载命令
        for key in ec2_paths:
            ec2_path = ec2_paths[key]
            mount_cmd.append(f'''
        if [ ! -d "{ec2_path}" ]; then
            mkdir -p {ec2_path};
        fi
            ''')

        mount_cmd.append(f'''
        sudo mount -t efs -o tls,iam,accesspoint={access_point_models_id} {file_system_id}:/{dir_name}/global {ec2_paths['global']};
        sudo mount -t efs -o tls,iam,accesspoint={access_point_models_id} {file_system_id}:/{dir_name}/groups/{group_name} {ec2_paths['group']};
        sudo mount -t efs -o tls,iam,accesspoint={access_point_models_id} {file_system_id}:/{dir_name}/users/{username} {ec2_paths['user']};
        echo "{file_system_id}:/{dir_name}/global {ec2_paths['global']} efs _netdev,tls,iam,accesspoint={access_point_models_id} 0 0" | sudo tee -a /etc/fstab;
        echo "{file_system_id}:/{dir_name}/groups/{group_name} {ec2_paths['group']} efs _netdev,tls,iam,accesspoint={access_point_models_id} 0 0" | sudo tee -a /etc/fstab;
        echo "{file_system_id}:/{dir_name}/users/{username} {ec2_paths['user']} efs _netdev,tls,iam,accesspoint={access_point_models_id} 0 0" | sudo tee -a /etc/fstab;
        ''')
    
    # 处理不同用户挂载所属Group目录逻辑
    ec2_group_output_path = os.path.join(comfyui_home_dir, 'output', group_name)
    efs_group_output_path = os.path.join(mount_path, 'output', group_name)
    check_create_directory(efs_group_output_path)
    mount_cmd.append(f'''
    if [ ! -d "{ec2_group_output_path}" ]; then
        mkdir -p {ec2_group_output_path};
    fi
    ''')

    mount_cmd.append(f'''
    sudo mount -t efs -o tls,iam,accesspoint={access_point_output_id} {file_system_id}:/{group_name} {ec2_group_output_path}
    echo "{file_system_id}:/{group_name} {ec2_group_output_path} efs _netdev,tls,iam,accesspoint={access_point_output_id} 0 0" | sudo tee -a /etc/fstab;
    ''')

    with open(os.path.join(start_script_dir, f'mount.sh'), 'w') as f:
        f.write(''.join(mount_cmd))
    print(f'Mount command has been written to {os.path.join(start_script_dir, f"mount.sh")}')