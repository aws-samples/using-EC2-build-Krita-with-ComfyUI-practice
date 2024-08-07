import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {VPCStack} from "./vpc-stack"

export class ComfyuiOnAwsEc2Stack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const vpc = new VPCStack(this, "comfyui-vpc");
    // The code that defines your stack goes here

    // example resource
    // const queue = new sqs.Queue(this, 'ComfyuiOnAwsEc2Queue', {
    //   visibilityTimeout: cdk.Duration.seconds(300)
    // });
  }
}
