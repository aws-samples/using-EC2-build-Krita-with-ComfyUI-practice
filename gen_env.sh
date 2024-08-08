#!/bin/bash

# 打包好的comfyui ubuntu的 AMI ID, 请务必替换成我们自己的AMI ID
EC2_AMI_ID='ami-0ae76e4bfde4d10f7'
# EC2 key pair name, 请务必替换成我们自己的EC2 Key Name
EC2_KEY_NAME='west'
# EC2 实例类型, 默认为: g6.2xlarge
EC2_INSTANCE_TYPE='g6.2xlarge'

# DynamoDB Table 名称, 默认为: user-comfyui-servers
USER_COMFYUI_SERVERS_TABLE='user-comfyui-servers'