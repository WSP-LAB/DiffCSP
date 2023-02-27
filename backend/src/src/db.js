const mysql  = require("mysql");
const config = require("../config").db;

var pool = mysql.createPool({
    host: config.credential.host,
    user: config.credential.user,
    password: config.credential.password,
    database: config.credential.database,
    connectionLimit: 50
}, {debug: true})

var testReceive = (req, test_id, csp, cb) => {
    let user_agent = req.get("User-Agent");
    
    let ua = req.query.browser;
    
    pool.getConnection((err, conn) => {
        if(err) {
            console.warn(`Error while getting connection - Test ID : ${test_id}`);
            cb(false);
            return;
        }
        conn.query(`INSERT IGNORE  INTO \`result_csp_${csp}\` (test_sign, browser) VALUES (${test_id}, "${ua}");`, (err) => {
            if(err) {
                console.warn(`Error while inserting result (${csp})- Test ID : ${test_id}`);
                console.warn(err);
                cb(false);
                return;
            }
            cb(true);
        });
        conn.release();
    });
};

var testDone = (csp_id, browser, cb) => {
    pool.getConnection((err, conn) => {
        if(err) {
            console.warn(`Error while getting connection - csp/browser : ${csp_id}/${browser}`);
            cb(false);
            return;
        }
        
        conn.query(`INSERT IGNORE INTO CSP_STATUS (csp_id, ${browser}) VALUES (${csp_id}, TRUE) ON DUPLICATE KEY UPDATE ${browser}=TRUE`, (err) => {
            if(err) {
                console.warn(`Error while inserting status browser: ${browser}, csp_id: ${csp_id}`);
                console.warn(err);
                cb(false);
                return;
            }
            cb(true);
        });
        conn.release();
    });
}

module.exports = {testReceive, testDone};
