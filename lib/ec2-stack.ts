import {NestedStack, NestedStackProps} from "aws-cdk-lib";
import {Construct} from "constructs";
import * as cdk from "aws-cdk-lib";
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as efs from 'aws-cdk-lib/aws-efs';
import * as iam from "aws-cdk-lib/aws-iam";

export interface EC2StackProps extends NestedStackProps {
    vpc: ec2.Vpc,
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

        const filebroswerRole = new iam.Role(this, 'filebroswer-role', {
            roleName: `filebroswer-ec2-${cdk.Stack.of(this).region}`,
            assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName('CloudWatchFullAccess'),
                iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonElasticFileSystemClientReadWriteAccess'),
            ],
        });
        
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
            "yum update -y",
            "yum install -y amazon-efs-utils",
            "mkdir -p /data/filebrowser",
            "cd /data/filebrowser",
            "wget https://github.com/filebrowser/filebrowser/releases/download/v2.30.0/linux-amd64-filebrowser.tar.gz",
            "tar -xzf linux-amd64-filebrowser.tar.gz",
            "cp -a  filebrowser /usr/bin/filebrowser",
            "touch ./filebrowser.log",
            "cat > /data/filebrowser/filebrowser.json <<EOF",
            "{",
            "\"address\": \"0.0.0.0\",",
            "\"port\": 80,",
            "\"database\": \"/data/filebrowser/filebrowser.db\",",
            "\"log\": \"/data/filebrowser/filebrowser.log\",",
            "\"locale\": \"zh-cn\",",
            "\"username\": \"admin\",",
            "\"password\": \"admin\",",
            "\"root\": \"/\",",
            "\"scope\": \"/\"",
            "}",
            "EOF",
            "mkdir /home/ec2-user/EFS",
            `sudo mount -t efs -o tls,iam,accesspoint=${props.accessPointRoot.accessPointId} ${props.fileSystemId}:/ /home/ec2-user/EFS`,
            `echo "${props.fileSystemId}:/ /home/ec2-user/EFS efs _netdev,tls,iam,accesspoint=${props.accessPointRoot.accessPointId} 0 0" | sudo tee -a /etc/fstab;`,
            "filebrowser -d /data/filebrowser/filebrowser.db config init",
            "filebrowser -d /data/filebrowser/filebrowser.db config set --address 0.0.0.0",
            "filebrowser -d /data/filebrowser/filebrowser.db config set --locale zh-cn",
            "filebrowser -d /data/filebrowser/filebrowser.db config set --log /data/filebrowser/filebrowser.log",
            "filebrowser -d /data/filebrowser/filebrowser.db users add admin admin --perm.admin",
            "cat > /etc/systemd/system/filebrowser.service <<EOF",
            "[Unit]",
            "Description=filebrowser",
            "Documentation=https://filebrowser.org/",
            "After=network.target",
            "",
            "[Service]",
            "ExecStart=/data/filebrowser/filebrowser -c /data/filebrowser/filebrowser.json",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "EOF",
            "systemctl daemon-reload",
            "systemctl enable --now filebrowser",
            "systemctl status filebrowser"
        );

        const filebroswerEC2 = new ec2.Instance(this, 'FileBroswerInstance', {
            instanceName: 'File Browser Instance',
            instanceType: new ec2.InstanceType('t3.large'), // 选择实例类型
            machineImage: ec2.MachineImage.latestAmazonLinux2023(), // 使用最新的 Amazon Linux AMI
            vpc: props.vpc,
            securityGroup,
            vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC }, 
            role: filebroswerRole,
            blockDevices: [{
                deviceName: '/dev/xvda',
                volume: ec2.BlockDeviceVolume.ebs(100, {
                    volumeType: ec2.EbsDeviceVolumeType.GP3,
                }),
            }],
            userData: userData,
        });

        new cdk.CfnOutput(scope, 'File Broswer Instance IP:', { value: filebroswerEC2.instancePublicIp });

    }

    

}