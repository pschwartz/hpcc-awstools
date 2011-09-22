#!/bin/bash
# filename: remote-hpcc-init.sh
username=$1
key=$2
nodes=$3
cmd=$4
EXPECTEDARGS=4
if [ $# -ne $EXPECTEDARGS ]; then
echo "USAGE:./remote-hpcc-init.sh <username> <key> <node list> <cmd>"
exit
fi

for server in `cat $nodes`; do
        echo "Server: $server"
        /usr/bin/ssh -i $key $username@$server -o StrictHostKeyChecking=no -C "sudo service hpcc-init $cmd"
done


