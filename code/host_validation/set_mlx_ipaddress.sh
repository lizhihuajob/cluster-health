#!/bin/bash
# 
#  set_mlx_ipaddress.sh
#
set -eu
CurPath=$(cd `dirname $0`; pwd)

mlx_name=$1
mlx_ip=$2
mlx_mask=$3

#echo "set $mlx_name ipaddress $mlx_ip"

devname=$( /opt/app/bin/ibdev2netdev |grep ${mlx_name} |awk '{print$5}')
ifconfig ${devname} ${mlx_ip} netmask ${mlx_mask} up

#ifconfig $devname