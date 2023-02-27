const fs = require("fs")
csp_map = {}

const csp_policies = fs.readFileSync(`../../testing_csp_list.txt`, {encoding:'utf8', flag:'r'}).split("\n")
for(let i = 0; i < csp_policies.length-1; i++)
    csp_map[csp_policies[i].trim()] = i;

module.exports = {
    ports: {
        self: 8000,
        allowed_http: 8080,
        allowed_https: 8081,
        blocked_http: 8082,
        blocked_https: 8083,
    },
    db: {
        credential: {
            host: "localhost",
            user: "cspuzz",
            password: "cspuzz",
            database: "cspuzz_result"
        }
    },
    csp_set: csp_map
};
