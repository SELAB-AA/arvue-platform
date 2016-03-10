#!/bin/bash
if [ "$#" -lt 2 ]
then
    echo "Usage: $0 <Key> <Server> ..."
    exit
fi 

# Setup variables
KEYPAIR=$1

i=0

while [ $# -ne 1 ]; do
SERVERS[((i++))]=$2
shift
done

i=1

for SERVER in  ${SERVERS[*]}
do
	scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR ubuntu@$SERVER:scalereport.csv scalereport$i.csv
	scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR ubuntu@$SERVER:scalingtest.out scalingtest$i.out
	scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR ubuntu@$SERVER:scalingtest.err scalereport$i.err
	((i++))
done
