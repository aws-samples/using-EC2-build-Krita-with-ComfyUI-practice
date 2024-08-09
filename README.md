# 使用Amazon EC2 来构建Comfy UI Servers

### 部署步骤
#### 生成环境变量, 请根据自身环境信息修改`gen_env.sh`后,执行脚本
```
sh gen_env.sh
```

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `npx cdk deploy`  deploy this stack to your default AWS account/region
* `npx cdk diff`    compare deployed stack with current state
* `npx cdk synth`   emits the synthesized CloudFormation template
