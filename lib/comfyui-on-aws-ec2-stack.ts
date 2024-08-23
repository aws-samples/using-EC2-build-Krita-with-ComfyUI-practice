import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {VPCStack} from "./vpc-stack"
import { DynamodbStack } from './dynamodb-stack';
import { LambdaStack } from './lambda-stack';
import {ApigatewayStack} from "./apigateway-stack";
import { EFSStack } from './efs-stack';
import { EC2Stack } from './ec2-stack';

export class ComfyuiOnAwsEc2Stack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const vpcStack = new VPCStack(this, "comfyui-vpc");

    const user_comfyui_servers_table = new DynamodbStack(this, "user_comfyui_servers_table");

    const efsStack = new EFSStack(this, "comfyui_efs_stack", {vpc: vpcStack.vpc})
    
    const lambdas = new LambdaStack(this, "comfyui_lambda_stack", {
      comfyUISecurityGroup: vpcStack.comfyUISecurityGroup,
      vpc: vpcStack.vpc,
      comfyuiInstanceProfile: vpcStack.comfyuiInstanceProfile,
      accessPointModels: efsStack.accessPointModels,
      accessPointOutput: efsStack.accessPointOutput,
      accessPointStartScript: efsStack.accessPointStartScript,
      accessPointRoot: efsStack.accessPointRoot,
      fileSystemId: efsStack.fileSystemId,
    });
    
    const apiGatewayStack = new ApigatewayStack(this, 'apigateway-stack', {
      comfyuiServersPostFunc: lambdas.comfyuiServersPostFunc,
      comfyuiServersStopFunc: lambdas.comfyuiServersStopFunc,
      comfyuiServersGetFunc: lambdas.comfyuiServersGetFunc,
      comfyuiCustomNodesFunc: lambdas.comfyuiCustomNodesFunc,
    });

    const ec2_stack = new EC2Stack(this, 'ec2-stack', {
      vpc: vpcStack.vpc,
      accessPointRoot: efsStack.accessPointRoot,
      fileSystemId: efsStack.fileSystemId,
    })
    
    new cdk.CfnOutput(this, 'ComfyUI-VPC-ID', {
      value: vpcStack.vpc.vpcId,
      exportName: `${id}-VPC-ID`,
    });
  }
}
