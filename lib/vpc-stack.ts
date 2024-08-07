import {NestedStack} from "aws-cdk-lib";
import {Construct} from "constructs";
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export class VPCStack extends NestedStack {
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
            {
                cidrMask: 24,
                name: 'PrivateSubnet1',
                subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
            },
            {
                cidrMask: 24,
                name: 'PrivateSubnet2',
                subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
            },
            ],
        });
    
        // 输出 VPC ID
        new cdk.CfnOutput(this, 'VpcId', {
            value: vpc.vpcId,
        });
    
        // 输出子网 ID
        vpc.publicSubnets.forEach((subnet, index) => {
            new cdk.CfnOutput(this, `PublicSubnet${index + 1}Id`, {
            value: subnet.subnetId,
            });
        });
    
        vpc.privateSubnets.forEach((subnet, index) => {
            new cdk.CfnOutput(this, `PrivateSubnet${index + 1}Id`, {
            value: subnet.subnetId,
            });
        });
    }

}