#!/bin/bash
# filename: pushconfig.sh
username=$1
key=$2
nodes=$3
file=$4
to=$5
EXPECTEDARGS=5
if [ $# -ne $EXPECTEDARGS ]; then
echo "USAGE:./push.sh <username> <key> <node list> <filename to be pushed> <location to push to>"
exit
fi

for server in `cat $nodes`; do
    /usr/bin/scp -i $key $file $username@$server:~
	/usr/bin/ssh -i $key $username@$server  -C "sudo cp $file $to"
done

