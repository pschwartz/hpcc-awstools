#!/bin/bash
# filename: getdir.sh
username=$1
key=$2
nodes=$3
EXPECTEDARGS=3
if [ $# -ne $EXPECTEDARGS ]; then
echo "USAGE:./getdir.sh <username> <key> <node list>"
exit
fi

for server in `cat $nodes`; do
	echo "server: ${server}"
	/usr/bin/ssh -i $key $username@$server -o StrictHostKeyChecking=no -C "sudo df -h | grep /dev/sdb"
done


