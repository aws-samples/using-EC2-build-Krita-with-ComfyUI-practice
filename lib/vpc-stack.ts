import {NestedStack} from "aws-cdk-lib";
import {Construct} from "constructs";
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export class VPCStack extends NestedStack {

    public readonly vpcId: string;
    public readonly comfyUISecurityGroup: ec2.SecurityGroup;
    public readonly pubSubnetID: string;

    /**
     *
     * @param {Construct} scope
     * @param {string} id
     * @param {StackProps=} props
     */
    constructor(scope: Construct, id: string, props?: cdk.NestedStackProps) {
        super(scope, id, props);
        // 创建 VPC
        const vpc = new ec2.Vpc(this, 'comfyui_vpc', {
            maxAzs: 2, // 使用两个可用区
            subnetConfiguration: [
                {
                    cidrMask: 24,
                    name: 'PublicSubnet1',
                    subnetType: ec2.SubnetType.PUBLIC,
                },
                {
                    cidrMask: 24,
                    name: 'PublicSubnet2',
                    subnetType: ec2.SubnetType.PUBLIC,
                },
            ],
        });

        const publicSubnets = vpc.selectSubnets({
            subnetType: ec2.SubnetType.PUBLIC,
        });
        this.pubSubnetID = publicSubnets.subnets[0].subnetId;

        this.comfyUISecurityGroup = new ec2.SecurityGroup(this, 'ComfyUISecurityGroup', {
            vpc,
            allowAllOutbound: true, // 允许所有出站流量
        });
      
        // 添加入站规则，允许 SSH（端口 22）和 8848 端口的流量
        this.comfyUISecurityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), 'Allow SSH access');
        this.comfyUISecurityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(8848), 'Allow access to port 8848');
        
        this.vpcId = vpc.vpcId
    }

}