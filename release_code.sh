#!/bin/bash

CurPath=$(cd `dirname $0`; pwd)
Time=`date +%Y%m%d_%H%M%S`
version="24.09.001"

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
if test -d ${CurPath}/release/cluster-health-code-v${version}; then
    echo "[${Time}] release cluster-health-code-v${version} exist! remove it"
    rm -rf ${CurPath}/release/cluster-health-code-v${version}
fi

#create release dir
mkdir -p ${CurPath}/release/cluster-health-code-v${version}/cluster-health-code

#copy code
echo "copy code start ..."
cp -r ${CurPath}/code/* ${CurPath}/release/cluster-health-code-v${version}/cluster-health-code/
#cp -r ${CurPath}/script/update.sh ${CurPath}/release/cluster-health-code-v${version}/cluster-health-code/
echo "${version}" > ${CurPath}/release/cluster-health-code-v${version}/cluster-health-code/version
echo "copy code done"

#将发布代码打包为tar.gz
echo "tar.gz start ..."
cd ${CurPath}/release/cluster-health-code-v${version}/
tar -zcvf cluster-health-code.tar.gz cluster-health-code
md5info=$(md5sum cluster-health-code.tar.gz|awk -F " " '{print$1}' )

#使用tee 将md5info信息，添加到checksum文件中

cat <<EOF | tee  checksum.txt > /dev/null
MD5=${md5info}
version=${version}
EOF


echo "tar.gz done"

cd ${CurPath}





