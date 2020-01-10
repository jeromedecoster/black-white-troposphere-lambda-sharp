# the directory of his script file
dir="$(cd "$(dirname "$0")"; pwd)"

[[ ! -f "$dir/settings.sh" ]] \
    && echo "abort: settings.sh is missing" >&2 \
    && exit 1

cd "$dir"
source settings.sh

echo 'docker run troposphere'
docker run \
    --volume $PWD:/tmp \
    troposphere python /tmp/tropo.py \
    --bucket $S3_BUCKET \
    --key layers/$SHARED_LAYER_ZIP \
    --code /tmp/lambda/index.js \
    --region $AWS_REGION \
    > cloudformation.json

STACK_ID=$(aws cloudformation list-stacks \
    --stack-status-filter CREATE_COMPLETE \
    --query "StackSummaries[?StackName=='$STACK_NAME'].[StackId]" \
    --output text)

if [[ -z "$STACK_ID" ]]; then
    # stack need to be created
    echo 'cloudformation create-stack'
    aws cloudformation create-stack \
    	--capabilities CAPABILITY_IAM \
    	--stack-name $STACK_NAME \
    	--template-body file://cloudformation.json

    echo 'cloudformation wait stack-create-complete'
    aws cloudformation wait stack-create-complete \
        --stack-name $STACK_NAME
    
else
    # stack can be updated
    echo 'cloudformation update-stack'
    aws cloudformation update-stack \
    	--capabilities CAPABILITY_IAM \
    	--stack-name $STACK_NAME \
    	--template-body file://cloudformation.json

    echo 'cloudformation wait stack-update-complete'
    aws cloudformation wait stack-update-complete \
        --stack-name $STACK_NAME
fi