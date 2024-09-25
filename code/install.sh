#!/bin/bash
# 
# install cluster-health code to /opt/eht-cluster-health/app
#
set -eu

CurPath=$(cd `dirname $0`; pwd)
CurTime=`date "+%Y-%m-%d %H:%M:%S"`
SYS_INFO=`uname -r`
APPPath="/opt/eht-cluster-health/app"
appName="cluster-health"

echo "[${CurTime}] install cluster-health code start ..."

# 检查目标目录是否存在，不存在则创建
if ! test -d ${APPPath}/${appName}; then
    mkdir -p ${APPPath}/${appName}
    echo "create ${APPPath}/${appName} success!"
fi

cat ${CurPath}/applist | while read line
do
    echo "install ${line} start ..."
    cd ${CurPath}/${line}
    chmod +x install.sh
    ./install.sh
    cd ${CurPath}
    echo "install ${line} done "
done

cat ${CurPath}/version > ${APPPath}/${appName}/version
cat ${CurPath}/requirements.txt > ${APPPath}/${appName}/requirements.txt
cat ${CurPath}/init.sh > ${APPPath}/${appName}/init.sh

CurTime=`date "+%Y-%m-%d %H:%M:%S"`
echo "[${CurTime}] install cluster-health code done ..."