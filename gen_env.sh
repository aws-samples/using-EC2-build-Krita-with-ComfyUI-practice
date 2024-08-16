#!/bin/bash

# 打包好的comfyui ubuntu的 AMI ID, 请务必替换成我们自己的AMI ID, 此处需要注意不同机型的AMI有可能不适配,请一定一定要使用指定机型的AMI
EC2_AMI_ID='ami-0cc6595684751bb4f'
# EC2 key pair name, 请务必替换成我们自己的EC2 Key Name
EC2_KEY_NAME='west'
# EC2 实例类型, 默认为: g6.2xlarge
EC2_INSTANCE_TYPE='g6.2xlarge'
# DynamoDB Table 名称, 用户分配的ComfyUI服务器信息, 默认为: user-comfyui-servers
USER_COMFYUI_SERVERS_TABLE='user-comfyui-servers'
# DynamoDB Table 名称, Custom Nodes信息, 默认为: comfyui_custom_nodes
COMFYUI_CUSTOM_NODES_TABLE='comfyui_custom_nodes'
# 指定自己的VPC CIDR
VPC_CIDR='10.0.0.0/16'

echo "EC2_AMI_ID=${EC2_AMI_ID}" > .env
echo "EC2_KEY_NAME=${EC2_KEY_NAME}" >> .env
echo "EC2_INSTANCE_TYPE=${EC2_INSTANCE_TYPE}" >> .env
echo "USER_COMFYUI_SERVERS_TABLE=${USER_COMFYUI_SERVERS_TABLE}" >> .env
echo "COMFYUI_CUSTOM_NODES_TABLE=${COMFYUI_CUSTOM_NODES_TABLE}" >> .env
echo "VPC_CIDR=${VPC_CIDR}" >> .env