#!/bin/bash
 
db=YOUR_DB
user=YOUR_USER
pass=YOUR_PASS
 
for table in $(mysql -u$user -p$pass $db -Be "SHOW tables" | sed 1d); do
  echo "exporting $table.."
  mysql -u$user -p$pass $db -e "SELECT * FROM $table" | sed 's/\t/","/g;s/^/"/;s/$/"/;' > export/$table.csv
done
