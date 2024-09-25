#!/bin/bash

CurPath=$(cd `dirname $0`; pwd)
Time=`date +%Y%m%d_%H%M%S`

#输入版本号,不换行。echo 不换行
echo -en "\033[32mplease input version number:\033[0m"
read version
if [ -z "$version" ]; then
    echo -e "\033[31mversion number is empty!\033[0m"
    exit
else
    echo -e "\033[32mversion number is v${version}\033[0m"
fi

#清理可能存在的旧文件
if test -d ${CurPath}/release/cluster-health-v${version}; then
    echo "[${Time}] release cluster-health-v${version} exist! remove it"
    rm -rf ${CurPath}/release/cluster-health-v${version}
fi

#create release dir
mkdir -p ${CurPath}/release/cluster-health-v${version}

#copy images
echo "copy images start ..."
mkdir -p ${CurPath}/release/cluster-health-v${version}/images
cp -r ${CurPath}/images/* ${CurPath}/release/cluster-health-v${version}/images/
echo "copy images done"

#copy install.sh
echo "copy install.sh start ..."
cp ${CurPath}/script/install.sh ${CurPath}/release/cluster-health-v${version}/install.sh
echo "copy install.sh done"


