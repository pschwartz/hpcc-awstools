#!/bin/bash
# filename: getlogs.sh
username=$1
key=$2
nodes=$3
EXPECTEDARGS=3
if [ $# -ne $EXPECTEDARGS ]; then
echo "USAGE:./getlogs.sh <username> <key> <node list>"
exit
fi
logdir="log-`date "+%F-%H-%M-%S"`"
mkdir ${logdir}
for server in `cat $nodes`; do
	echo "server: ${server}"
	mkdir ${logdir}/${server}
	/usr/bin/scp -i $key -r $username@$server:/mnt/var/log/* ${logdir}/${server}/
done
tar -zcvf ${logdir}.tar.gz ${logdir}/*
rm -rf ${logdir}
