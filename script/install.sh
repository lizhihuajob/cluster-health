#!/bin/bash

CurPath=$(cd `dirname $0`; pwd)
Time=`date +%Y%m%d_%H%M%S`
SYS_INFO=`uname -r`
APPPath="/opt/eht-cluster-health"

echo "install cluster-health app start : ${Time} ${SYS_INFO}"

#检查安装文件是否完整
if !    test -f ${CurPath}/images/md5sum.txt; then
    echo "[${Time}] images md5sum.txt not exist!"
    exit
fi
if !    test -f ${CurPath}/images/cluster-health-v1.tar.gz; then
    echo "[${Time}] images cluster-health.tar not exist!"
    exit
fi

images_md5sum=$(cat ${CurPath}/images/md5sum.txt)
md5info=$(md5sum ${CurPath}/images/cluster-health-v1.tar.gz)
if [ "$images_md5sum" != "$md5info" ]; then
    echo "[${Time}] images md5sum not match!"
    exit
fi

#加载docker images
## 检测是否存在旧镜像，如果存在则移除
if docker images | grep -q "cluster-health"; then
    echo "[${Time}] cluster-health image exist! remove it"
    docker rmi cluster-health
fi

tar -zxvf ${CurPath}/images/cluster-health-v1.tar.gz -C images
docker load -i ${CurPath}/images/cluster-health-v1.tar

if docker images | grep -q "cluster-health"; then
    echo "[${Time}] cluster-health image load success!"
else
    echo "[${Time}] cluster-health image load failed!"
    exit
fi


#部署cluster-health 到opt 目录下
if  test -d ${APPPath}; then
    rm -rf ${APPPath}
fi
mkdir -p ${APPPath}
tar -zxvf cluster-health-code.tar.gz -C ${APPPath}


#创建容器
docker run --name cluster-health-app -itd --network=host --gpus all --shm-size 32g --ipc=host  -v ${APPPath}:/opt/app  --cap-add=IPC_LOCK --device=/dev/infiniband  cluster-health:v1  


echo "install cluster-health app done : ${Time} ${SYS_INFO}"