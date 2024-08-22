import {NestedStack, NestedStackProps} from "aws-cdk-lib";
import {Construct} from "constructs";
import * as cdk from "aws-cdk-lib";
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as efs from 'aws-cdk-lib/aws-efs';
import { Constants } from "./constants";

export interface EC2StackProps extends NestedStackProps {
    vpc: ec2.Vpc,
    pubSubnetID: string,
    accessPointRoot: efs.AccessPoint,
    fileSystemId: string,
}

export class EC2Stack extends NestedStack {

     /**
     *
     * @param {Construct} scope
     * @param {string} id
     * @param {StackProps=} props
     */
     constructor(scope: Construct, id: string, props: EC2StackProps) {
        super(scope, id, props);
        
        const securityGroup = new ec2.SecurityGroup(this, 'file-broswer-server-sg', {
            vpc: props.vpc,
            description: 'File Broswer Security Group',
            allowAllOutbound: true   // 允许所有出站流量
        });
        // 允许 SSH 访问
        securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), 'allow ssh access');
        securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'allow http access');


        const userData = ec2.UserData.forLinux();
        userData.addCommands(
            'yum update -y', // 更新软件包
            'yum install -y amazon-efs-utils', // 安装 驱动
            'mkdir -p /data/filebrowser', 
            'cd /data/filebrowser',
            'wget https://github.com/filebrowser/filebrowser/releases/download/v2.30.0/linux-amd64-filebrowser.tar.gz',
            'tar -xzf linux-amd64-filebrowser.tar.gz',
            'cp -a  filebrowser /usr/bin/filebrowser',
            'touch ./filebrowser.log', // 创建日志文件
            'cat > /data/filebrowser/filebrowser.json <<EOF', // 创建配置文件
            '{',
            '"address": "0.0.0.0",',
            '"port": 80,',
            '"database": "/data/filebrowser/filebrowser.db",',
            '"log": "/data/filebrowser/filebrowser.log",',
            '"locale": "zh-cn",',
            '"username": "admin",',
            '"password": "admin",',
            '"root": "/",',
            '"scope": "/"',
            '}',
            'EOF',
            'mkdir /home/ec2-user/EFS',
            'sudo mount -t efs -o tls,iam,accesspoint={access_point_id} {file_system_id}:/ /home/ec2-user/EFS',
            'filebrowser -d /data/filebrowser/filebrowser.db config init', // 初始化配置
            'filebrowser -d /data/filebrowser/filebrowser.db config set --address 0.0.0.0', // 设置地址
            'filebrowser -d /data/filebrowser/filebrowser.db config set --locale zh-cn', // 设置语言
            'filebrowser -d /data/filebrowser/filebrowser.db config set --log /data/filebrowser/filebrowser.log', // 设置日志
            'filebrowser -d /data/filebrowser/filebrowser.db users add admin admin --perm.admin' // 添加管理员用户
        );

        const filebroswer = new ec2.Instance(this, 'MyInstance', {
            instanceType: new ec2.InstanceType('t3.large'), // 选择实例类型
            machineImage: ec2.MachineImage.latestAmazonLinux2023(), // 使用最新的 Amazon Linux AMI
            vpc: props.vpc,
            securityGroup,
            vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC }, 
        });


    }

    

}