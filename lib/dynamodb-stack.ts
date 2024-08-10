import {NestedStack, RemovalPolicy} from "aws-cdk-lib";
import {Construct} from "constructs";
import * as cdk from "aws-cdk-lib";
import { Constants } from "./constants";
import { AttributeType, Table, } from "aws-cdk-lib/aws-dynamodb";

export class DynamodbStack extends NestedStack {

    /**
     *
     * @param {Construct} scope
     * @param {string} id
     * @param {StackProps=} props
     */
    constructor(scope: Construct, id: string, props?: cdk.NestedStackProps) {
        super(scope, id, props);

        const user_comfyui_servers_table = new Table(this, "user-comfyui-servers", {
            tableName: Constants.USER_COMFYUI_SERVERS_TABLE,
            partitionKey: {
                name: "username",
                type: AttributeType.STRING,
            },
            sortKey: {
                name: "instance_id",  // 设置排序键为 instance_id
                type: AttributeType.STRING,  // 确保类型与实际数据匹配
            },
            pointInTimeRecovery: true,
            removalPolicy: RemovalPolicy.DESTROY, // NOT recommended for production code
        });

        const readScaling = user_comfyui_servers_table.autoScaleReadCapacity({
            minCapacity: 1,
            maxCapacity: 10,
        });

        readScaling.scaleOnUtilization({
            targetUtilizationPercent: 65,
        });

        const writeScaling = user_comfyui_servers_table.autoScaleWriteCapacity({
            minCapacity: 1,
            maxCapacity: 10,
        });

        writeScaling.scaleOnUtilization({
            targetUtilizationPercent: 65,
        });
    }
}