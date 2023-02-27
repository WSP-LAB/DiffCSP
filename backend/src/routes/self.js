const express = require('express');
const db = require("../src/db");
const fs = require("fs");
const config = require('../config');
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
	let aa = req.query.csp || "";
    if(aa != "empty")
	    res.set("Content-Security-Policy", aa);

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

// route tests
app.get("/test/:test_name", (req, res) => {

    let test_name = req.params.test_name;
    let browser = req.query.browser;
    let data = ''
    // console.log(browser);
    try {
        data = fs.readFileSync(`./test/${test_name}.html`,
                {encoding:'utf8', flag:'r'});
    } catch(err) {
        console.log(err);
	    res.status(404).send('not found');
    }
    
	let csp = req.query.csp || "";
    
    if(csp.includes('가')) {
        let responseMessage = `HTTP/1.1 200 OK
Content-Type: text/html
Content-Security-Policy: `;
        responseMessage += csp;
        responseMessage += "\n\n";
        responseMessage += data.replace(/\$\$\$\?/g, `?browser=${browser}&csp=${config.csp_set[csp]}&`);

        console.log(`Received a test - Test : ${test_name} - CSP : ${config.csp_set[csp]} - Browser : ${browser}`);
        res.socket.end(responseMessage);
        
    }
    else { 

        if(csp != "empty") {
            res.set("Content-Security-Policy", csp);
            
        
            // normalize hashes in CSP into an unified and combined form
            csp_directive_value = csp.split(';');
            csp = "";
            for (v in csp_directive_value.slice(0,-1)) {
                let sha_exist = false;
                let directive_value = csp_directive_value[v];
                let value = directive_value.trim().split(" ");
                for (e in value) {
                    if (value[e].includes('sha256') && !sha_exist) {
                        csp += "'sha256-HASH' ";
                        sha_exist = true;
                    }    
                    else if (value[e].includes('sha256') && sha_exist)
                        continue;
                    else if (value[e].includes('connect-src'))
                        csp = csp.trim() + value[e] + " ";
                    else
                        csp += value[e] + " ";
                }        
                csp = csp.trim() + "; ";
            }
            csp = csp.trim();
        }
        
        if (test_name.includes('status')) {
                res.status(parseInt(test_name.split('_')[3]));  
        }
        
        // if (req.query.statuscode) {
         //   res.status(req.query.statuscode)
        //}
        

        console.log(`Received a test - Test : ${test_name} - CSP : ${config.csp_set[csp]} - Browser : ${browser}`);
        res.set("Content-Type", "text/html");    
        res.send(data.replace(/\$\$\$\?/g, `?browser=${browser}&csp=${config.csp_set[csp]}&`));
    }


})

// route script (console.log) receiver
app.get("/script_receive", (req, res) => {
    let sign = parseInt(req.query.sign) || -1;
	let csp = parseInt(req.query.csp) || 0;
    if (sign != -1) {
        db.testReceive(req, sign, csp, (success) => {
            if(success) {
                console.log(`Received a request script - Test ID : ${sign} - CSP : ${csp} - Browser : ${req.query.browser}`);
            }
        });
    }
    res.send("done");
});

// route CSP end receiver
app.get("/csp_finish", (req, res) => {
    let csp = req.query.csp || "";
    let browser = req.query.browser; //one of 'Chrome', 'Firefox', 'Safari', or 'Edge'
    
    if(csp != "empty") {
        // normalize hashes in CSP into an unified and combined form
        csp_directive_value = csp.split(';');
        csp = "";
        for (v in csp_directive_value.slice(0,-1)) {
            let sha_exist = false;
            let directive_value = csp_directive_value[v];
            let value = directive_value.trim().split(" ");
            for (e in value) {
                if (value[e].includes('sha256') && !sha_exist) {
                    csp += "'sha256-HASH' ";
                    sha_exist = true;
                }    
                else if (value[e].includes('sha256') && sha_exist)
                    continue;
                else if (value[e].includes('connect-src'))
                    csp = csp.trim() + value[e] + " ";
                else
                    csp += value[e] + " ";
            }        
            csp = csp.trim() + "; ";
        }
        csp = csp.trim();
    }

    try { 
        csp_id = config.csp_set[csp];
        db.testDone(csp_id, browser, (success) => {
            if(success) {
                console.log(`CSP[${csp_id}]: ${csp} done for ${browser}`);
            }
        })
        res.send("done");
    }
    catch(err) {
        res.send("error");
    }  
});

module.exports = app;
