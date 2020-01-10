# the directory of his script file
dir="$(cd "$(dirname "$0")"; pwd)"

[[ ! -f "$dir/settings.sh" ]] \
    && echo "abort: settings.sh is missing" >&2 \
    && exit 1

cd "$dir"
source settings.sh

[[ -f "lambda/$SHARED_LAYER_ZIP" ]] \
    && echo "abort: $SHARED_LAYER_ZIP already exists" >&2 \
    && exit 1

[[ -z $(echo "$S3_BUCKET") ]] \
    && echo "abort: S3_BUCKET must be defined in settings.sh" >&2 \
    && exit 1

# install `node-prune` if not already installed
if [[ -z "$(which node-prune)" ]]; then
    sudo curl --silent \
        --fail \
        --location \
        https://install.goreleaser.com/github.com/tj/node-prune.sh \
        | sudo bash -s -- -b /usr/local/bin
fi

cd lambda

# create the shared package
npm install
node-prune
mkdir nodejs
mv node_modules nodejs/
zip $SHARED_LAYER_ZIP -r9 nodejs
mv nodejs/node_modules .
rm --force --dir --recursive nodejs

# upload the zip to s3 in a `layers` directory
[[ -n "$(aws s3 ls s3://$S3_BUCKET/layers/$SHARED_LAYER_ZIP)" ]] \
    && echo "abort: s3://$S3_BUCKET/layers/$SHARED_LAYER_ZIP already exists" >&2 \
    && exit 1

aws s3 cp $SHARED_LAYER_ZIP s3://$S3_BUCKET/layers/