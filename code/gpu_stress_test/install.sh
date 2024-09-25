#!/bin/bash
# 
# install cluster-health code to /opt/eht-cluster-health/app
#
set -eu

CurPath=$(cd `dirname $0`; pwd)
CurTime=`date "+%Y-%m-%d %H:%M:%S"`
SYS_INFO=`uname -r`
APPPath="/opt/eht-cluster-health/app/cluster-health"
appName="gpu_stress_test"

echo "[${CurTime}] install ${appName} code start ..."

# 移除旧的文件
if test -d ${APPPath}/${appName}; then
    ls  ${APPPath}/${appName} |grep -v json|while read line
    do
        rm -rf ${APPPath}/${appName}/${line}
    done
fi

if ! test -d  ${APPPath}/${appName}; then
    mkdir -p ${APPPath}/${appName}
fi

#添加新文件
ls ${CurPath} |grep -v install.sh | while read line
do
    echo "copy ${line} to ${APPPath}/${appName}"
    cp -r ${CurPath}/${line} ${APPPath}/${appName}/
done



CurTime=`date "+%Y-%m-%d %H:%M:%S"`
echo "[${CurTime}] install ${appName} code done ..."
