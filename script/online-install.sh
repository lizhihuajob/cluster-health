#!/bin/bash
#
set -eu

CurPath=$(cd `dirname $0`; pwd)
CurTime=`date "+%Y-%m-%d %H:%M:%S"`
SYS_INFO=`uname -r`
APPPath="/opt/eht-cluster-health/app"
APPName="cluster-health"
containerName=cluster-health-app
imaqgehub=eht.docker.hub:30443/eht-images
imageName=eht.docker.hub:30443/eht-images/cluster-health
#imageTag=24.08
clusterUrl="http://www.starmodel.top:32080/cluster-health/online"

echo "[${CurTime}] install cluster-health app start : ${SYS_INFO}"


#获取docker镜像最新tag
imageTag=$(curl -s ${clusterUrl}/images/version)
if [ -z "${imageTag}" ]; then
    echo "imageTag is empty!"
    exit
else
    echo "imageTag is v${imageTag}"
fi

#加载docker images
## 检测是否存在旧镜像，如果存在则移除
echo "check running container ... "
docker ps  | grep ${containerName} | while read line 
do 
    echo "stop old ${containerName} container"
    docker stop ${containerName}
done
echo "check exist container ..."
docker ps -a  | grep ${containerName} | while read line 
do 
    echo "remove old ${containerName} container"
    docker rm ${containerName}
done
echo "check exist image ..."
docker images --filter reference=${imageName}:${imageTag}   |grep -v REPOSITORY | while read line 
do 
    echo "exist old ${imageName}:${imageTag} image"
    #docker rmi ${imageName}:${imageTag}
done

#下载镜像
echo "pull image from hub ..."
docker pull ${imageName}:${imageTag}

docker images --filter reference=${imageName} | grep -v REPOSITORY|  awk '$2 == "<none>" {print $3}' | while read line 
do 
    IMAGE_ID=${line}
    docker ps |grep -v REPOSITORY| grep ${IMAGE_ID} | awk '{print $1}' | while read container_id
    do 
       echo "stop container: ${container_id}"
       docker stop ${container_id}
    done    
    docker ps -a | grep -v REPOSITORY| grep ${IMAGE_ID} | awk '{print $1}' | while read container_id
    do 
       echo "remove container: ${container_id}"
       docker rm ${container_id}
    done
    docker rmi ${IMAGE_ID}
done

#部署cluster-health 到opt 目录下
echo "deploy cluster-health to ${APPPath} ..."
remoteverson=$(curl -s ${clusterUrl}/code/version)
if [ -z "${remoteverson}" ]; then
    echo "code version is empty!"
    exit
else
    echo "code version is v${remoteverson}"
fi

mkdir -p ${CurPath}/update-tmp

#部署cluster-health 到opt 目录下
if tesf -f ${CurPath}/update-tmp/${APPName}-code-${remoteverson}.tar.gz;then
    rm -rf ${CurPath}/update-tmp/${APPName}-code-${remoteverson}.tar.gz
fi

wget -O ${CurPath}/update-tmp/${APPName}-code-${remoteverson}.tar.gz ${clusterUrl}/code/v${remoteverson}/${APPName}-code.tar.gz
if  test -d ${CurPath}/update-tmp/${APPName}-code-${remoteverson}; then
    echo "remove old ${APPPath}/${APPName}"
    rm -rf ${CurPath}/update-tmp/${APPName}-code-${remoteverson}  
fi
mkdir -p ${CurPath}/update-tmp/${APPName}-code-${remoteverson}
#cp -r ${CurPath}/code/* ${APPPath}/
tar -zxvf ${CurPath}/update-tmp/${APPName}-code-${remoteverson}.tar.gz -C ${CurPath}/update-tmp/${APPName}-code-${remoteverson}

if [ -f ${CurPath}/update-tmp/${APPName}-code-${remoteverson}/${APPName}-code/install.sh ]; then
    echo "exec install.sh ..."
    cd ${CurPath}/update-tmp/${APPName}-code-${remoteverson}/${APPName}-code
    chmod +x install.sh
    ./install.sh
    cd ${CurPath}
else
    echo "install.sh is not exist!"
fi
if test -f ${APPPath}/${APPName}/init.sh; then
    chmod +x ${APPPath}/${APPName}/init.sh
    ${APPPath}/${APPName}/init.sh
fi

#创建容器
echo "create container ${containerName} ..."
docker run --name ${containerName} -itd --network=host --gpus all --shm-size 32g --ipc=host  -v ${APPPath}:/opt/app  --privileged --device=/dev/infiniband  ${imageName}:${imageTag}

sleep 5
docker ps

#修改ssh权限
#docker exec -i cluster-health-app chmod 600 /root/.ssh/id_rsa
rm -rf  ${CurPath}/update-tmp
CurTime=`date "+%Y-%m-%d %H:%M:%S"`

echo "[${CurTime}] install cluster-health app done : ${SYS_INFO}"