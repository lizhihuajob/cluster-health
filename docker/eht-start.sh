#!/bin/bash

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

#清空known_hosts
cat /dev/null > /root/.ssh/known_hosts


if test -f /opt/app/bin/eht-init.sh; then
    chmod +x /opt/app/bin/eht-init.sh
    /opt/app/bin/eht-init.sh
fi

tail -f /dev/null