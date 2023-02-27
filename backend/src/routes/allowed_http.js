const express = require('express');
const db = require("../src/db");
const app = express();

app.get("/", (req, res) => {
    res.send("Service is running");
})

app.get("/ping", (req, res) => {
    res.send("pong");
});

// route html
app.get(/\.html/, (req, res) => {
    let sign = parseInt(req.query.sign) || -1;
    let csp = parseInt(req.query.csp) || 0;
    if (sign != -1) {
        db.testReceive(req, sign, csp, (success) => {
            if(success) {
                console.log(`Received a request (html) - Test ID : ${sign} - CSP : ${csp} - Browser : ${req.query.browser}`);
            }
        });
    }
    res.sendFile("sample.html", { root: "./static" });
})

// route js
app.get(/\.js/, (req, res) => {
    let sign = parseInt(req.query.sign) || -1;
    let csp = parseInt(req.query.csp) || 0;
    if (sign != -1) {
        db.testReceive(req, sign, csp, (success) => {
            if(success) {
                console.log(`Received a request (js) - Test ID : ${sign} - CSP : ${csp} - Browser : ${req.query.browser}`);
            }
        });
    }
    res.sendFile("sample.js", { root: "./static" });
})

// route css
app.get(/\.css/, (req, res) => {
    let sign = parseInt(req.query.sign) || -1;
    let csp = parseInt(req.query.csp) || 0;
    if (sign != -1) {
        db.testReceive(req, sign, csp, (success) => {
            if(success) {
                console.log(`Received a request (css) - Test ID : ${sign} - CSP : ${csp} - Browser : ${req.query.browser}`);
            }
        });
    }
    res.sendFile("sample.css", { root: "./static" });
})

// route jpg
app.get(/\.jpg/, (req, res) => {
    let sign = parseInt(req.query.sign) || -1;
    let csp = parseInt(req.query.csp) || 0;
    if (sign != -1) {
        db.testReceive(req, sign, csp, (success) => {
            if(success) {
                console.log(`Received a request (jpg) - Test ID : ${sign} - CSP : ${csp} - Browser : ${req.query.browser}`);
            }
        });
    }
    res.sendFile("sample.jpg", { root: "./static" });
})

// route mp3
app.get(/\.mp3/, (req, res) => {
    let sign = parseInt(req.query.sign) || -1;
    let csp = parseInt(req.query.csp) || 0;
    if (sign != -1) {
        db.testReceive(req, sign, csp, (success) => {
            if(success) {
                console.log(`Received a request (mp3) - Test ID : ${sign} - CSP : ${csp} - Browser : ${req.query.browser}`);
            }
        });
    }
    res.sendFile("sample.mp3", { root: "./static" });
})

// route mp4
app.get(/\.mp4/, (req, res) => {
    let sign = parseInt(req.query.sign) || -1;
    let csp = parseInt(req.query.csp) || 0;
    if (sign != -1) {
        db.testReceive(req, sign, csp, (success) => {
            if(success) {
                console.log(`Received a request (mp4) - Test ID : ${sign} - CSP : ${csp} - Browser : ${req.query.browser}`);
            }
        });
    }
    res.sendFile("sample.mp4", { root: "./static" });
})

module.exports = app;