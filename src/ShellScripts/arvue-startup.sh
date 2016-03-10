#!/bin/bash
##############################################################################
# This script launches one EC2 instance using provided AWS credentials and
# security key parameters. The key-pair can be any key-pair created using the
# ec2-add-keypair command or by using the AWS web interface.
#
# The EC2 machine image used (ami-fb9ca98f) does not contain all the required
# tools by default. Therefore, some things are downloaded and installed semi-
# manually.
#
# The EC2 instance is started in a security group called "arvuemaster" which
# should be created beforehand. The arvuemaster-group should probably have
# ports 80 and 22 open for incoming traffic.
##############################################################################

# Check arguments count
if [ "$#" -ne 6 ]
then
    echo "Usage: $0 <AWSAccessKey> <AWSSecretKey> <S3RepoAWSAccessKey> <S3RepoAWSSecretKey> <keypair name> <absolute path to key>"
    exit
fi 

# Setup variables
AKEY=$1
SKEY=$2
RAKEY=$3
RSKEY=$4
KEYPAIRNAME=$5
KEYPAIR=$6
AMI="ami-fb9ca98f" # From alestic.com

# Launch master instance
echo "Launching master instance..."
MASTER=`java -jar EC2Manager/bin/EC2Manager.jar launch a=$AKEY s=$SKEY i=$AMI t=m1.small k=$KEYPAIRNAME g=arvuemaster | awk '{print $3}'`
#echo $MASTER

# Give the instance some time to boot
echo "Waiting 60s for the instance to boot..."
sleep 60

# Setup assumed filesystem
#ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "mkdir /tmp/arvue" > /dev/null 2>&1

# Install Java
echo "Installing Java..."
ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "sudo apt-get -y update" > /dev/null 2>&1
ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "sudo apt-get -y install openjdk-6-jre-headless" > /dev/null 2>&1

# Install subversion
echo "Installing subversion..."
ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "sudo apt-get -y install subversion" > /dev/null 2>&1

# Install haproxy
echo "Installing haproxy..."
ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "sudo apt-get -y install haproxy" > /dev/null 2>&1

# Download master tools
echo "Downloading ArvueMaster-1.0-SNAPSHOT-jar-with-dependencies.jar"
ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "wget http://users.abo.fi/bbyholm/ArvueMaster-1.0-SNAPSHOT-jar-with-dependencies.jar" > /dev/null 2>&1

# Download entertainment server stuff
echo "Downloading EntertainmentServer-1.0-SNAPSHOT-jar-with-dependencies.jar"
ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "wget http://users.abo.fi/bbyholm/EntertainmentServer-1.0-SNAPSHOT-jar-with-dependencies.jar" > /dev/null 2>&1

# Download webserver to masterinstance
echo "downloading webserver to master instance..."
ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "svn co http://dev.vaadin.com/svn/incubator/Arvue/ArvueConfiguration" > /dev/null 2>&1

# Start Entertainment Server on port 6666
echo "Starting Entertainment Server..."
ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "nohup java -jar EntertainmentServer-1.0-SNAPSHOT-jar-with-dependencies.jar > entertainment.out 2> entertainment.err < /dev/null &" > /dev/null 2>&1

echo "starting webserver on master instance..."
ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "nohup java -jar ArvueConfiguration/WebServerLite.jar ArvueConfiguration/webserver/ 8099 > web.out 2> web.err < /dev/null &" > /dev/null 2>&1

# Start ArvueMaster
echo "Starting ArvueMaster..."
ssh -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$MASTER "nohup java -DaccessKey=$RAKEY -DprivateKey=$RSKEY -DAWSAccessKey=$AKEY -DAWSPrivateKey=$SKEY -jar ArvueMaster-1.0-SNAPSHOT-jar-with-dependencies.jar > master.out 2> master.err < /dev/null &" > /dev/null 2>&1

# Give ArvueMaster some time to start
sleep 10



echo "Arvue is up and running at $MASTER"
