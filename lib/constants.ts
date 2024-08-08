import * as dotenv from "dotenv";
dotenv.config();
export class Constants {

    public static readonly USER_COMFYUI_SERVERS_TABLE = process.env.USER_COMFYUI_SERVERS_TABLE ??'user-comfyui-servers'
    public static readonly EC2_AMI_ID = process.env.EC2_AMI_ID ??''
    public static readonly EC2_KEY_NAME = process.env.EC2_KEY_NAME ??''
    public static readonly EC2_INSTANCE_TYPE = process.env.EC2_KEY_NAME ??'g6.2xlarge'

}