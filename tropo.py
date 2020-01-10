import argparse
from troposphere import GetAtt, Join, Ref, Template, Output
from troposphere.awslambda import Function, Code, Permission, Content, LayerVersion
from troposphere.iam import Role, Policy
from troposphere.apigateway import RestApi, Method, Resource, MethodResponse
from troposphere.apigateway import Integration, IntegrationResponse
from troposphere.apigateway import Deployment, Stage, EndpointConfiguration

#
# Arguments
#

parser = argparse.ArgumentParser(
    description="Black White Troposhpere template generator")
parser.add_argument("-b", "--bucket", required=True,
                    help="S3 bucket where shared layer is stored")
parser.add_argument("-k", "--key", required=True,
                    help="The shared layer zip file")
parser.add_argument("-c", "--code", required=True,
                    help="The Lambda code file")
parser.add_argument("-r", "--region", required=True,
                    help="The AWS region")

args = parser.parse_args()


t = Template()

#
# Lambda
#

# Create a role for the lambda function
t.add_resource(Role(
    "LambdaExecutionRole",
    Path="/",
    Policies=[Policy(
        PolicyName="inline-policy",
        PolicyDocument={
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "*"
            }, {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": "*"
            }]
        })],
    AssumeRolePolicyDocument={
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "lambda.amazonaws.com",
                    "apigateway.amazonaws.com"  # important !
                ]
            }
        }]
    }))

# create the Lambda function
layer = t.add_resource(LayerVersion(
    "LambdaLayer",
    LayerName="black-white-troposphere-lambda-sharp",
    Content=Content(
        S3Bucket=args.bucket,
        S3Key=args.key  # update the name to update layer version
    )
))

# read Lambda code
code = open(args.code).read().strip().split("\n")

func = t.add_resource(Function(
    "Lambda",
    Code=Code(
        ZipFile=Join("\n", code)
    ),
    Handler="index.handler",
    Role=GetAtt("LambdaExecutionRole", "Arn"),
    Runtime="nodejs12.x",
    MemorySize=128,
    Timeout=50,
    Layers=[Ref(layer)]
))

#
# API Gateway
#

# create the Api Gateway
rest_api = t.add_resource(RestApi(
    "ApiGateway",
    Name="black-white-troposhpere-lambda-sharp",
    BinaryMediaTypes=["*/*"],  # very important
    EndpointConfiguration=EndpointConfiguration(
        Types=["REGIONAL"]
    )
))

# Create a resource to map the lambda function to
resource = t.add_resource(Resource(
    "ResourceConvert",
    RestApiId=Ref(rest_api),
    PathPart="convert",
    ParentId=GetAtt("ApiGateway", "RootResourceId"),
))

# create a Lambda API method for the Lambda resource
method = t.add_resource(Method(
    "MethodConvert",
    DependsOn="Lambda",  # The Lambda Ref
    RestApiId=Ref(rest_api),
    AuthorizationType="NONE",
    ResourceId=Ref(resource),
    HttpMethod="POST",
    Integration=Integration(
        Credentials=GetAtt("LambdaExecutionRole", "Arn"),
        Type="AWS_PROXY",
        IntegrationHttpMethod='POST',
        Uri=Join("", [
            "arn:aws:apigateway:" + args.region + ":lambda:path/2015-03-31/functions/",
            GetAtt("Lambda", "Arn"),
            "/invocations"
        ])
    ),
))

# allow the API Gateway to invoke Lambda
permission = t.add_resource(Permission(
    "Permission",
    Action="lambda:InvokeFunction",
    FunctionName=GetAtt("Lambda", "Arn"),
    Principal="apigateway.amazonaws.com",
    SourceArn=Join("", [
        "arn:aws:execute-api:" + args.region + ":",
        Ref("AWS::AccountId"),
        ":",
        Ref(rest_api),
        "/*/POST/convert"
    ])
))

#
# Deploy API Gateway
#

stage_name = 'dev'

deployment = t.add_resource(Deployment(
    "Deployment",
    DependsOn="MethodConvert",
    RestApiId=Ref(rest_api),
))

stage = t.add_resource(Stage(
    "Stage",
    StageName=stage_name,
    RestApiId=Ref(rest_api),
    DeploymentId=Ref(deployment)
))

# add the deployment endpoint as an output
t.add_output([
    Output(
        "ApiEndpoint",
        Value=Join("", [
            "https://",
            Ref(rest_api),
            ".execute-api." + args.region + ".amazonaws.com/",
            stage_name
        ]),
        Description="Endpoint for this stage of the api"
    ),
])

print(t.to_json())
