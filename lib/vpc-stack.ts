import {NestedStack} from "aws-cdk-lib";
import {Construct} from "constructs";
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from "aws-cdk-lib/aws-iam";

export class VPCStack extends NestedStack {

    public readonly vpc: ec2.Vpc;
    public readonly comfyUISecurityGroup: ec2.SecurityGroup;
    public readonly pubSubnetID: string;
    public readonly comfyuiInstanceProfile: iam.CfnInstanceProfile;

    /**
     *
     * @param {Construct} scope
     * @param {string} id
     * @param {StackProps=} props
     */
    constructor(scope: Construct, id: string, props?: cdk.NestedStackProps) {
        super(scope, id, props);
        // 创建 VPC
        this.vpc = new ec2.Vpc(this, 'comfyui_vpc', {
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
        cdk.Tags.of(this.vpc).add('Name', 'ComfyUI-VPC');

        const publicSubnets = this.vpc.selectSubnets({
            subnetType: ec2.SubnetType.PUBLIC,
        });
        this.pubSubnetID = publicSubnets.subnets[0].subnetId;

        this.comfyUISecurityGroup = new ec2.SecurityGroup(this, 'ComfyUISecurityGroup', {
            vpc: this.vpc,
            allowAllOutbound: true, // 允许所有出站流量
        });
      
        // 添加入站规则，允许 SSH（端口 22）和 8848 端口的流量
        this.comfyUISecurityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), 'Allow SSH access');
        this.comfyUISecurityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(8848), 'Allow access to port 8848');

        const comfyuiEC2Role = new iam.Role(this, 'ComfyuiEC2Role', {
            roleName: `comfyui-ec2-role--${cdk.Stack.of(this).region}`,
            assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName('CloudWatchFullAccess'),
                iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3FullAccess'),
                iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonElasticFileSystemClientReadWriteAccess'),
            ]
        });

        this.comfyuiInstanceProfile = new iam.CfnInstanceProfile(this, 'ComfyUIInstanceProfile', {
            instanceProfileName: 'ComfyUI-Instance-Profile',
            roles: [comfyuiEC2Role.roleName],
        });

        const dynamoDbEndpoint = new ec2.GatewayVpcEndpoint(this, 
            'DynamoDbEndpoint', {
                vpc: this.vpc,
                service: ec2.GatewayVpcEndpointAwsService.DYNAMODB,
            }
        );
    }

}