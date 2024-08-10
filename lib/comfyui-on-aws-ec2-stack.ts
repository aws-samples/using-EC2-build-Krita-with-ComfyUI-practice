import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {VPCStack} from "./vpc-stack"
import { DynamodbStack } from './dynamodb-stack';
import { LambdaStack } from './lambda-stack';
import {ApigatewayStack} from "./apigateway-stack";

export class ComfyuiOnAwsEc2Stack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const vpc = new VPCStack(this, "comfyui-vpc");

    const user_comfyui_servers_table = new DynamodbStack(this, "user_comfyui_servers_table");
    
    const lambdas = new LambdaStack(this, "comfyui_lambda_stack", {
      comfyUISecurityGroup: vpc.comfyUISecurityGroup,
      vpcId: vpc.vpcId,
      pubSubnetID: vpc.pubSubnetID,
      comfyuiInstanceProfile: vpc.comfyuiInstanceProfile,
    });
    
    const apiGatewayStack = new ApigatewayStack(this, 'apigateway-stack', {
      comfyuiServersPostFunc: lambdas.comfyuiServersPostFunc,
      comfyuiServersStopFunc: lambdas.comfyuiServersStopFunc,
      comfyuiServersGetFunc: lambdas.comfyuiServersGetFunc,
    });
    
    new cdk.CfnOutput(this, 'ComfyUI-VPC-ID', {
      value: vpc.vpcId,
      exportName: `${id}-VPC-ID`,
    });
  }
}
