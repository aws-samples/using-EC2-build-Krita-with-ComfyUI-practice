import * as dotenv from "dotenv";
dotenv.config();
export class Constants {

    public static readonly USER_COMFYUI_SERVERS_TABLE = process.env.USER_COMFYUI_SERVERS_TABLE ??'user-comfyui-servers'
    public static readonly COMFYUI_CUSTOM_NODES_TABLE = process.env.COMFYUI_CUSTOM_NODES_TABLE ??'comfyui_custom_nodes'
    public static readonly EC2_AMI_ID = process.env.EC2_AMI_ID ??''
    public static readonly EC2_KEY_NAME = process.env.EC2_KEY_NAME ??''
    public static readonly EC2_INSTANCE_TYPE = process.env.EC2_INSTANCE_TYPE ??'g6.2xlarge'
    public static readonly RESOURCE_TAG = "COMFYUI-SERVERS"
    public static readonly COMFYUI_SERVER_PORT = '8848'
    public static readonly VPC_CIDR = process.env.VPC_CIDR ??'10.0.0.0/16'
}