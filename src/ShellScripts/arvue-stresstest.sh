#!/bin/bash
if [ "$#" -ne 7 ]
then
    echo "Usage: $0 <AWSAccessKey> <AWSSecretKey> <S3RepoAWSAccessKey> <S3RepoAWSSecretKey> <keypair name> <absolute path to key> <target url>"
    exit
fi 

# Setup variables
AKEY=$1
SKEY=$2
RAKEY=$3
RSKEY=$4
KEYPAIRNAME=$5
KEYPAIR=$6
TARGET=$7
AMI="ami-fb9ca98f" # From alestic.com

# Launch instances
echo "Launching instances..."
TESTER1=`java -jar EC2Manager/bin/EC2Manager.jar launch a=$AKEY s=$SKEY i=$AMI t=m1.small k=$KEYPAIRNAME g=arvuemaster | awk '{print $3}'`
TESTER2=`java -jar EC2Manager/bin/EC2Manager.jar launch a=$AKEY s=$SKEY i=$AMI t=m1.small k=$KEYPAIRNAME g=arvuemaster | awk '{print $3}'`
TESTER3=`java -jar EC2Manager/bin/EC2Manager.jar launch a=$AKEY s=$SKEY i=$AMI t=m1.small k=$KEYPAIRNAME g=arvuemaster | awk '{print $3}'`
TESTER4=`java -jar EC2Manager/bin/EC2Manager.jar launch a=$AKEY s=$SKEY i=$AMI t=m1.small k=$KEYPAIRNAME g=arvuemaster | awk '{print $3}'`
TESTER5=`java -jar EC2Manager/bin/EC2Manager.jar launch a=$AKEY s=$SKEY i=$AMI t=m1.small k=$KEYPAIRNAME g=arvuemaster | awk '{print $3}'`

# Give the instances some time to boot
echo "Waiting 100s for the instances to boot..."
sleep 100

# Install Java
echo "Installing Java..."
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER1 "sudo apt-get -y update" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER1 "sudo apt-get -y install openjdk-6-jre-headless" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER2 "sudo apt-get -y update" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER2 "sudo apt-get -y install openjdk-6-jre-headless" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER3 "sudo apt-get -y update" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER3 "sudo apt-get -y install openjdk-6-jre-headless" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER4 "sudo apt-get -y update" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER4 "sudo apt-get -y install openjdk-6-jre-headless" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER5 "sudo apt-get -y update" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER5 "sudo apt-get -y install openjdk-6-jre-headless" > /dev/null 2>&1

# Download ScalingTest
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER1 "wget http://users.abo.fi/bbyholm/ScalingTest-1.0-SNAPSHOT-jar-with-dependencies.jar" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER2 "wget http://users.abo.fi/bbyholm/ScalingTest-1.0-SNAPSHOT-jar-with-dependencies.jar" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER3 "wget http://users.abo.fi/bbyholm/ScalingTest-1.0-SNAPSHOT-jar-with-dependencies.jar" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER4 "wget http://users.abo.fi/bbyholm/ScalingTest-1.0-SNAPSHOT-jar-with-dependencies.jar" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER5 "wget http://users.abo.fi/bbyholm/ScalingTest-1.0-SNAPSHOT-jar-with-dependencies.jar" > /dev/null 2>&1

# Run ScalingTest
echo "Running ScalingTest"
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER1 "nohup java -jar ScalingTest-1.0-SNAPSHOT-jar-with-dependencies.jar $TARGET > scalingtest.out 2> scalingtest.err < /dev/null &" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER2 "nohup java -jar ScalingTest-1.0-SNAPSHOT-jar-with-dependencies.jar $TARGET > scalingtest.out 2> scalingtest.err < /dev/null &" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER3 "nohup java -jar ScalingTest-1.0-SNAPSHOT-jar-with-dependencies.jar $TARGET > scalingtest.out 2> scalingtest.err < /dev/null &" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER4 "nohup java -jar ScalingTest-1.0-SNAPSHOT-jar-with-dependencies.jar $TARGET > scalingtest.out 2> scalingtest.err < /dev/null &" > /dev/null 2>&1
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $KEYPAIR -o StrictHostKeyChecking=no ubuntu@$TESTER5 "nohup java -jar ScalingTest-1.0-SNAPSHOT-jar-with-dependencies.jar $TARGET > scalingtest.out 2> scalingtest.err < /dev/null &" > /dev/null 2>&1

echo "ScalingTest running at $TESTER1"
echo "ScalingTest running at $TESTER2"
echo "ScalingTest running at $TESTER3"
echo "ScalingTest running at $TESTER4"
echo "ScalingTest running at $TESTER5"
