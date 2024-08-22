#!/bin/bash
yum update -y
yum install -y amazon-efs-utils
mkdir -p /data/filebrowser