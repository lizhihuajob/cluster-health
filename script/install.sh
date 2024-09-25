#!/bin/bash
# 
# docker images 通过离线方式导入。cluster-health 代码通过在线方式下载
#
set -eu

CurPath=$(cd `dirname $0`; pwd)
CurTime=`date "+%Y-%m-%d %H:%M:%S"`
SYS_INFO=`uname -r`
APPPath="/opt/eht-cluster-health/app"
containerName=cluster-health-app
imaqgehub=eht.docker.hub:30443/eht-images
imageName=eht.docker.hub:30443/eht-images/cluster-health
imageTag=24.08
clusterUrl="http://www.starmodel.top:32080/cluster-health/online/v24.08"

echo "[${Time}] install cluster-health app start : ${SYS_INFO}"

#检查安装文件是否完整
if !  test -f ${CurPath}/images/md5info.txt; then
    echo "[${Time}] images md5info.txt not exist!"
    exit
fi
if !  test -f ${CurPath}/images/cluster-health-v${imageTag}.tar.gz; then
    echo "[${Time}] images cluster-health-v${imageTag}.tar.gz not exist!"
    exit
fi

images_md5sum=$(cat ${CurPath}/images/md5info.txt)
md5info=$(md5sum ${CurPath}/images/cluster-health-v${imageTag}.tar.gz|awk -F " " '{print$1}' )
if [ "${images_md5sum}" != "${md5info}" ]; then
    echo "[${Time}] images md5sum not match!"
    exit
fi

#加载docker images
## 检测是否存在旧镜像，如果存在则移除
docker ps  | grep ${containerName} | while read line 
do 
    echo "[${Time}] stop old ${containerName} container"
    docker stop ${containerName}
done
docker ps -a  | grep ${containerName} | while read line 
do 
    echo "[${Time}] remove old ${containerName} container"
    docker rm ${containerName}
done
docker images --filter reference=${imageName}   |grep -v REPOSITORY | while read line 
do 
    echo "[${Time}] remove old ${imageName}:${imageTag} image"
    docker rmi ${imageName}:${imageTag}
done


tar -zxvf ${CurPath}/images/cluster-health-v${imageTag}.tar.gz -C ${CurPath}/images
if ! test -f ${CurPath}/images/cluster-health-v${imageTag}.tar; then
    echo "[${Time}] cluster-health image not exist!"
    exit
fi
docker load -i ${CurPath}/images/cluster-health-v${imageTag}.tar

if docker images | grep -q "cluster-health"; then
    echo "[${Time}] cluster-health image load success!"
else
    echo "[${Time}] cluster-health image load failed!"
    exit
fi


#部署cluster-health 到opt 目录下
echo "deploy cluster-health to ${APPPath} ..."
wget -O ${CurPath}/cluster-health-code-${imageTag}.tar.gz ${clusterUrl}/cluster-health-code.tar.gz
if  test -d ${APPPath}; then
    rm -rf ${APPPath}
fi
mkdir -p ${APPPath}
#cp -r ${CurPath}/code/* ${APPPath}/
tar -zxvf ${CurPath}/cluster-health-code-${imageTag}.tar.gz -C ${APPPath}
if test -f ${APPPath}/cluster-health/init.sh; then
    chmod +x ${APPPath}/cluster-health/init.sh
    ${APPPath}/cluster-health/init.sh
fi

#创建容器
docker run --name ${containerName} -itd --network=host --gpus all --shm-size 32g --ipc=host  -v ${APPPath}:/opt/app  --privileged --device=/dev/infiniband  ${imageName}:${imageTag}
sleep 5
docker ps

#修改ssh权限
docker exec -i cluster-health-app chmod 600 /root/.ssh/id_rsa

echo "[${Time}] install cluster-health app done : ${SYS_INFO}"