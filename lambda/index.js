const sharp = require("sharp")

exports.handler = function (event, context, callback) {

    sharp(Buffer.from(event.body, 'base64'))
        .grayscale()
        .toBuffer(function (err, data, info) {
            var response = {
                statusCode: 200,
                headers: { 'Content-Type': 'image/jpeg' },
                body: data.toString('base64'),
                isBase64Encoded: true
            }
            callback(null, response);
        })
}