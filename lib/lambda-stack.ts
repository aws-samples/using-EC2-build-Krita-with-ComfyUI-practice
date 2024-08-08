import {Duration, NestedStack, NestedStackProps} from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import {Construct} from 'constructs';
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Constants } from "./constants";

export interface LambdaStackProps extends NestedStackProps {
    
}

export class LambdaStack extends NestedStack {
    
    public readonly comfyuiServersPostFunc: lambda.IFunction;
    public readonly comfyuiServersStopFunc: lambda.IFunction;
    public readonly comfyuiServersGetFunc: lambda.IFunction;

    constructor(scope: Construct, id: string, props: LambdaStackProps) {
        super(scope, id, props);
        
        const comfyUILambdaRole = new iam.Role(this, 'comfyui-lambda-role', {
            roleName: `comfyui-lambda-${cdk.Stack.of(this).region}`,
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName('CloudWatchFullAccess'),
                iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonEC2FullAccess'),
                iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonDynamoDBFullAccess'),
            ],
        });

        const functionSettings : lambda.FunctionProps = {
            runtime: lambda.Runtime.PYTHON_3_11,
            memorySize: 1024,
            timeout: cdk.Duration.seconds(60),
            architecture: cdk.aws_lambda.Architecture.X86_64,
            logRetention: cdk.aws_logs.RetentionDays.ONE_WEEK,
            code: lambda.Code.fromAsset('resources/lambda'),
            role: comfyUILambdaRole,
            handler: '',
        }

        this.comfyuiServersPostFunc = new lambda.Function(this, 'ComfyUIServersPost', {
            ...functionSettings,
            functionName: 'ComfyUI-Servers-Post-Func',
            handler: 'comfyui-servers-post.lambda_handler',
            environment: {
                'EC2_AMI_ID': Constants.EC2_AMI_ID,
                'EC2_KEY_NAME': Constants.EC2_KEY_NAME,
                'EC2_INSTANCE_TYPE': Constants.EC2_INSTANCE_TYPE,
                'USER_COMFYUI_SERVERS_TABLE': Constants.USER_COMFYUI_SERVERS_TABLE,
            },
            
        });

        this.comfyuiServersStopFunc = new lambda.Function(this, 'ComfyUIServersStop', {
            runtime: lambda.Runtime.PYTHON_3_11,
            functionName: 'ComfyUI-Servers-Stop-Func',
            handler: 'comfyui-servers-stop.lambda_handler',
            memorySize: 1024,
            timeout: cdk.Duration.seconds(120),
            code: lambda.Code.fromAsset('resources/lambda'),
            architecture: cdk.aws_lambda.Architecture.X86_64,
            logRetention: cdk.aws_logs.RetentionDays.ONE_WEEK,
            role: comfyUILambdaRole,
            environment: {
                'USER_COMFYUI_SERVERS_TABLE': Constants.USER_COMFYUI_SERVERS_TABLE,
            },
        });

    }
}