# the directory of his script file
dir="$(cd "$(dirname "$0")"; pwd)"

cd "$dir"
source settings.sh

rm --force --recursive lambda/node_modules
rm --force --recursive lambda/$SHARED_LAYER_ZIP

echo 'cloudformation delete-stack'
aws cloudformation delete-stack \
    --stack-name $STACK_NAME

echo 'cloudformation wait stack-delete-complete'
aws cloudformation wait stack-delete-complete \
    --stack-name $STACK_NAME
