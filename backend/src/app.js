const config = require("./config");
const fs = require("fs");
const https = require('https');
const cors = require("cors");
const self_signed_option = {
    key: fs.readFileSync("cert/server.key"),
    cert: fs.readFileSync("cert/server.cert")
}

const app_self = require("./routes/self");
const app_allow = require("./routes/allowed_http");
const app_allows = require("./routes/allowed_https");
const app_block = require("./routes/blocked_http");
const app_blocks = require("./routes/blocked_https");
const app = require("./routes/self");

app_self.use(cors())
app_allow.use(cors())
app_allows.use(cors())
app_block.use(cors())
app_blocks.use(cors())

app_self.listen(config.ports.self, () => {
    console.log(`Listening 'self' on port ${config.ports.self}`);
});

app_allow.listen(config.ports.allowed_http, () => {
    console.log(`Listening 'allowed_http' on port ${config.ports.allowed_http}`);
});

app_block.listen(config.ports.blocked_http, () => {
    console.log(`Listening 'blocked_http' on port ${config.ports.blocked_http}`);
});

https.createServer(self_signed_option, app_allows).listen(config.ports.allowed_https, () => {
    console.log(`Listening 'allowed_https' with ssl context on port ${config.ports.allowed_https}`);
});

https.createServer(self_signed_option, app_blocks).listen(config.ports.blocked_https, () => {
    console.log(`Listening 'allowed_https' with ssl context on port ${config.ports.blocked_https}`);
});