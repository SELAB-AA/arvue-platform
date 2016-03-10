#!/bin/bash

# Check arguments count
if [ "$#" -ne 2 ]
then
    echo "Usage: $0 <AWSAccessKey> <AWSSecurityKey>"
    exit
fi 

# Setup variables
AKEY=$1
SKEY=$2

# Terminate master instance
echo "Terminating master instance..."
java -jar EC2Manager/bin/EC2Manager.jar terminate a=$AKEY s=$SKEY g=arvuemaster

# Terminate app servers
echo "Terminating app servers..."
java -jar EC2Manager/bin/EC2Manager.jar terminate a=$AKEY s=$SKEY g=arvue

