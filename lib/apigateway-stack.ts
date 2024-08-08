import {
    NestedStack,
    aws_apigateway as _apigateway,
    Duration, NestedStackProps
} from "aws-cdk-lib";
import {Construct} from "constructs";
import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";

export interface APIGatewayProps extends NestedStackProps {
    comfyuiServersPostFunc: lambda.IFunction,
    comfyuiServersStopFunc: lambda.IFunction,
}

export class ApigatewayStack extends NestedStack {

    constructor(scope: Construct, id: string, props: APIGatewayProps) {
        super(scope, id, props);

        const stageName = 'prod';
        const comfyUIServersAPI = new _apigateway.RestApi(this, 'COMFYUI-SERVERS-API', {
            restApiName: 'COMFYUI-SERVERS-API',
            retainDeployments: false,
            deploy: true,
            deployOptions: {
                stageName: stageName,
                cacheClusterEnabled: true,
                cacheClusterSize: '0.5',
                cacheTtl: Duration.minutes(1),
                throttlingBurstLimit: 100,
                throttlingRateLimit: 1000
            },
            endpointTypes: [
                _apigateway.EndpointType.EDGE
            ],
        });

        const apiKey = new _apigateway.ApiKey(this, 'COMFYUI-SERVERS-API-KEY', {
            apiKeyName: 'COMFYUI-SERVERS-API-KEY',
            enabled: true,
            description: 'COMFYUI-SERVERS-API-KEY'
        });

        const usagePlan = comfyUIServersAPI.addUsagePlan('ComfyUI-API-Key-UsagePlan', {
            name: 'ComfyUI-API-Key-UsagePlan',
            throttle: {
                burstLimit: 10,
                rateLimit: 100
            },
            quota: {
                limit: 1000,
                offset: 0,
                period: _apigateway.Period.DAY
            },
            apiStages: [
                {
                    api: comfyUIServersAPI,
                    stage: comfyUIServersAPI.deploymentStage,
                }
            ]
        });
        usagePlan.addApiKey(apiKey)

        const comfyuiServersRootPath = comfyUIServersAPI.root.addResource('comfyui-servers', {
            defaultMethodOptions: {
                apiKeyRequired: true
            }
        });
        comfyuiServersRootPath.addMethod('POST', new _apigateway.LambdaIntegration(props.comfyuiServersPostFunc));
    }
}