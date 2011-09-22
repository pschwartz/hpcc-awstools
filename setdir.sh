#!/bin/bash
# filename: setdir.sh
username=$1
key=$2
nodes=$3
EXPECTEDARGS=3
if [ $# -ne $EXPECTEDARGS ]; then
echo "USAGE:./setdir.sh <username> <key> <node list>"
exit
fi

for server in `cat $nodes`; do
	/usr/bin/ssh -i $key $username@$server -o StrictHostKeyChecking=no -C "sudo mkdir -p /mnt/var/lib/LexisNexis"
	/usr/bin/ssh -i $key $username@$server -o StrictHostKeyChecking=no -C "sudo mkdir -p /mnt/var/log/LexisNexis"
    /usr/bin/ssh -i $key $username@$server -o StrictHostKeyChecking=no -C "sudo chown -R ubuntu:ubuntu /mnt/var"
done


