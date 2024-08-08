import {NestedStack} from "aws-cdk-lib";
import {Construct} from "constructs";
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export class VPCStack extends NestedStack {

    public readonly vpcId: string;

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
        
        this.vpcId = vpc.vpcId
    }

}