import {NestedStack, NestedStackProps} from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import {Construct} from 'constructs';
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Constants } from "./constants";
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as events from 'aws-cdk-lib/aws-events'
import * as targets from 'aws-cdk-lib/aws-events-targets'

export interface LambdaStackProps extends NestedStackProps {
    comfyUISecurityGroup: ec2.SecurityGroup,
    vpcId: string,
    pubSubnetID: string,
    comfyuiInstanceProfile: iam.CfnInstanceProfile,
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
                iam.ManagedPolicy.fromAwsManagedPolicyName('IAMFullAccess'),
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
        // 启动ComfyUI Servers
        this.comfyuiServersPostFunc = new lambda.Function(this, 'ComfyUIServersPost', {
            ...functionSettings,
            functionName: 'ComfyUI-Servers-Post-Func',
            handler: 'comfyui-servers-post.lambda_handler',
            environment: {
                'EC2_AMI_ID': Constants.EC2_AMI_ID,
                'EC2_KEY_NAME': Constants.EC2_KEY_NAME,
                'EC2_INSTANCE_TYPE': Constants.EC2_INSTANCE_TYPE,
                'USER_COMFYUI_SERVERS_TABLE': Constants.USER_COMFYUI_SERVERS_TABLE,
                'SECURITY_GROUP_ID': props.comfyUISecurityGroup.securityGroupId,
                'PUB_SUBNET_ID': props.pubSubnetID,
                'RESOURCE_TAG': Constants.RESOURCE_TAG,
                'EC2_ROLE_ARN': props.comfyuiInstanceProfile.attrArn,
                'COMFYUI_SERVER_PORT': Constants.COMFYUI_SERVER_PORT,
            },
            
        });

        // 停止ComfyUI Server
        this.comfyuiServersStopFunc = new lambda.Function(this, 'ComfyUIServersStop', {
            ...functionSettings,
            functionName: 'ComfyUI-Servers-Stop-Func',
            handler: 'comfyui-servers-stop.lambda_handler',
            environment: {
                'USER_COMFYUI_SERVERS_TABLE': Constants.USER_COMFYUI_SERVERS_TABLE,
            },
        });
        
        // 获取ComfyUI Servers信息
        this.comfyuiServersGetFunc = new lambda.Function(this, 'ComfyUIServersGet', {
            ...functionSettings,
            functionName: 'ComfyUI-Servers-Get-Func',
            handler: 'comfyui-servers-get.lambda_handler',
            environment: {
                'USER_COMFYUI_SERVERS_TABLE': Constants.USER_COMFYUI_SERVERS_TABLE,
            },
        });

        /**
         * 通过Event Bridge监听EC2的状态信息,并通过lambda来修改dynamodb中的记录状态
         */
        const comfyuiServersUpdateFunc = new lambda.Function(this, 'ComfyUIServersUpdate', {
            ...functionSettings,
            functionName: 'ComfyUI-Servers-Update-Func',
            handler: 'comfyui-servers-update.lambda_handler',
            environment: {
                'USER_COMFYUI_SERVERS_TABLE': Constants.USER_COMFYUI_SERVERS_TABLE,
                'COMFYUI_SERVER_PORT': Constants.COMFYUI_SERVER_PORT,
            },
        });

        comfyuiServersUpdateFunc.addPermission('AllowEventBridgeInvocation', {
            principal: new iam.ServicePrincipal('events.amazonaws.com'),
            action: 'lambda:InvokeFunction',
            sourceArn: `arn:aws:events:${this.region}:${this.account}:rule/*`, // Replace with your EventBridge rule ARN
        });

        const rule = new events.Rule(this, 'ComfyUI-Servers-States-Events', {
            ruleName: 'ComfyUI-Servers-States-Event',
            eventPattern: {
                source: ["aws.ec2"],
                detailType: ["EC2 Instance State-change Notification"],
                detail: {
                state: ["running", "stopped"]
                }
            }
        });
      
        // 将 Lambda 函数作为目标添加到规则中
        rule.addTarget(new targets.LambdaFunction(comfyuiServersUpdateFunc));
    
        cdk.Tags.of(this.comfyuiServersPostFunc).add('RESOURCE_TAG', Constants.RESOURCE_TAG);
        cdk.Tags.of(this.comfyuiServersStopFunc).add('RESOURCE_TAG', Constants.RESOURCE_TAG);
        cdk.Tags.of(this.comfyuiServersGetFunc).add('RESOURCE_TAG', Constants.RESOURCE_TAG);
        cdk.Tags.of(comfyuiServersUpdateFunc).add('RESOURCE_TAG', Constants.RESOURCE_TAG);
    }
}