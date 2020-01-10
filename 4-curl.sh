# the directory of his script file
dir="$(cd "$(dirname "$0")"; pwd)"

[[ ! -f "$dir/settings.sh" ]] \
    && echo "abort: settings.sh is missing" >&2 \
    && exit 1

cd "$dir"
source settings.sh

URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query Stacks[0].Outputs[0].OutputValue \
    --output text)

echo "curl: $URL/convert"
curl $URL/convert \
    --header "Content-Type: image/png" \
    --data-binary @bird.jpg \
    --output bird-grey.jpg