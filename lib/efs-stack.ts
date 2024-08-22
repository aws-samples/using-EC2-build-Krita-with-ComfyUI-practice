import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as efs from 'aws-cdk-lib/aws-efs';
import {NestedStack, NestedStackProps} from "aws-cdk-lib";
import * as cdk from 'aws-cdk-lib';

export interface EFSStackProps extends NestedStackProps {
    vpc: ec2.Vpc,
}

export class EFSStack extends NestedStack {

    public readonly accessPointModels: efs.AccessPoint;
    public readonly accessPointOutput: efs.AccessPoint;
    public readonly accessPointStartScript: efs.AccessPoint;
    public readonly accessPointRoot: efs.AccessPoint;
    public readonly fileSystemId: string;

    /**
     *
     * @param {Construct} scope
     * @param {string} id
     * @param {StackProps=} props
     */
    constructor(scope: Construct, id: string, props: EFSStackProps) {
        super(scope, id, props);
        // 创建安全组
        const vpc = props.vpc
        const securityGroup = new ec2.SecurityGroup(this, 'ComfyUIEfsSecurityGroup', {
            vpc,
            allowAllOutbound: true,
            securityGroupName: 'ComfyUIEfsSecurityGroup',
        });
  
        // 允许 NFS 连接
        securityGroup.addIngressRule(ec2.Peer.ipv4(vpc.vpcCidrBlock), ec2.Port.tcp(2049), 'Allow NFS Connections');
    
        // 创建 EFS 文件系统
        const fileSystem = new efs.FileSystem(this, 'ComfyUIEfsFileSystem', {
            fileSystemName: 'ComfyUI File System',
            vpc,
            securityGroup,
            encrypted: true, // 启用加密
            performanceMode: efs.PerformanceMode.GENERAL_PURPOSE, // 性能模式
            throughputMode: efs.ThroughputMode.ELASTIC, // 吞吐模式
        });
    
        this.accessPointModels = fileSystem.addAccessPoint('AccessPointModels', {
            path: '/models',
            createAcl: {
                ownerGid: '1000',
                ownerUid: '1000',
                permissions: '0755',
            },
            posixUser: {
                gid: '1000',
                uid: '1000',
                secondaryGids: ['1001'],
            },
        });
        
        this.accessPointOutput = fileSystem.addAccessPoint('AccessPointOutput', {
            path: '/output',
            createAcl: {
                ownerGid: '1000',
                ownerUid: '1000',
                permissions: '0755',
            },
            posixUser: {
                gid: '1000',
                uid: '1000',
                secondaryGids: ['1001'],
            },
        });

        this.accessPointStartScript = fileSystem.addAccessPoint('AccessPointStartScript', {
            path: '/start-script',
            createAcl: {
                ownerGid: '1000',
                ownerUid: '1000',
                permissions: '0755',
            },
            posixUser: {
                gid: '1000',
                uid: '1000',
                secondaryGids: ['1001'],
            },
        });

        this.accessPointRoot = fileSystem.addAccessPoint('AccessPointRoot', {
            path: '/',
            createAcl: {
                ownerGid: '0',
                ownerUid: '0',
                permissions: '0755',
            },
            posixUser: {
                gid: '0',
                uid: '0',
                secondaryGids: ['1001'],
            },
        });
        // 获取访问点的 ID
        this.fileSystemId = fileSystem.fileSystemId;

        new cdk.CfnOutput(scope, 'FileSystem ID', { value: this.fileSystemId });
        new cdk.CfnOutput(scope, 'AccessPoint Models ID', { value: this.accessPointModels.accessPointId });
        new cdk.CfnOutput(scope, 'AccessPoint Output ID', { value: this.accessPointOutput.accessPointId });
        new cdk.CfnOutput(scope, 'AccessPoint Start Script', { value: this.accessPointStartScript.accessPointId });
        new cdk.CfnOutput(scope, 'AccessPoint Root', { value: this.accessPointRoot.accessPointId });

    }

}