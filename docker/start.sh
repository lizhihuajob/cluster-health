#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

# Check if PORT is set, otherwise set default value
if [ -z "${PORT:-}" ]; then
            PORT=16802
fi

# Check if PASS is set, otherwise set default value
if [ -z "${PASS:-}" ]; then
            PASS=1234.com
fi

# change the sshd port
sed -i "s/16802/$PORT/" /etc/ssh/sshd_config
#echo " StrictHostKeyChecking no" >> /etc/ssh/ssh_config

# start sshd
service ssh restart


# change the root password
echo "root:$PASS" | chpasswd

tail -f /dev/null


#docker run --name test-he-ssh -itd --network=host --gpus all --shm-size 32g --ipc=host -v /data/lizh/app:/opt/app  --cap-add=IPC_LOCK --device=/dev/infiniband  cluster-health:v2