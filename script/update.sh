#!/bin/bash
# version : 24.09.001  
# update cluster-health app
set -eu

CurPath=$(cd `dirname $0`; pwd)
CurTime=`date "+%Y-%m-%d %H:%M:%S"`
SYS_INFO=`uname -r`
APPPath="/opt/eht-cluster-health/app"
containerName=cluster-health-app
imageName=eht.docker.hub:30443/eht-images/cluster-health
imageTag=24.08
appName="cluster-health"
#从终端读取要更新的应用名称
echo -en "please input the app name to update(default:${appName}):"
read appNameInput
if [ "${appNameInput}" != "" ]; then
    appName=${appNameInput}
fi

clusterUrl="http://www.starmodel.top:32080/${appName}/online"

if ! test -d ${APPPath}; then
    mkdir -p ${APPPath}
fi

#
#获取docker镜像最新tag
echo "update images start ..."
latestImageTag=$(curl -s ${clusterUrl}/images/version)
if [ -z "${latestImageTag}" ]; then
    latestImageTag="24.08"
else
    echo "latest image tag is v${latestImageTag}"
fi
#停止正在运行的容器，并移除
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

echo "pull image from hub ..."
docker pull ${imageName}:${latestImageTag}

docker images --filter reference=${imageName}:${latestImageTag}   |grep -v REPOSITORY | while read line 
do 
    echo "pull lastest image tag: ${latestImageTag} successful! "
    echo "${latestImageTag}" > ${APPPath}/image-version
done

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

echo "update images done  ,lastest image tag is ${latestImageTag}"

echo "update ${appName} app start ..."

#获取本地版本信息
localverson="24.08"
if test -f ${APPPath}/${appName}/version; then
    localverson=$(cat ${APPPath}/${appName}/version)
fi

# 检查远端版本文件是否存在
status_code=$(curl -s -o /dev/null -w "%{http_code}" ${clusterUrl}/code/version)
if [ "${status_code}" -eq 200 ]; then  
    echo "check remote version file successful!"  
else  
    echo "check remote version file fail!"
    exit 1
fi

#获取远端版本信息
remoteverson=$(curl -s ${clusterUrl}/code/version)
if [ "${remoteverson}" == "${localverson}" ]; then
    echo "version ${localverson} is latest"
else
    mkdir -p ${CurPath}/update-tmp
    #部署cluster-health 到opt 目录下
    if tesf -f ${CurPath}/update-tmp/${appName}-code-${remoteverson}.tar.gz;then
        rm -rf ${CurPath}/update-tmp/${appName}-code-${remoteverson}.tar.gz
    fi

    echo "deploy ${appName} to ${APPPath} ..."
    wget -O ${CurPath}/update-tmp/${appName}-code-${remoteverson}.tar.gz ${clusterUrl}/code/v${remoteverson}/${appName}-code.tar.gz
    if  test -d ${CurPath}/update-tmp/${appName}-code-${remoteverson}; then
        echo "remove old ${APPPath}/${appName}"
        rm -rf ${CurPath}/update-tmp/${appName}-code-${remoteverson}  
    fi
    mkdir -p ${CurPath}/update-tmp/${appName}-code-${remoteverson}
    #cp -r ${CurPath}/code/* ${APPPath}/
    tar -zxvf ${CurPath}/update-tmp/${appName}-code-${remoteverson}.tar.gz -C ${CurPath}/update-tmp/${appName}-code-${remoteverson}

    if [ -f ${CurPath}/update-tmp/${appName}-code-${remoteverson}/${appName}-code/install.sh ]; then
        echo "exec install.sh ..."
        cd ${CurPath}/update-tmp/${appName}-code-${remoteverson}/${appName}-code
        chmod +x install.sh
        ./install.sh
        cd ${CurPath}
    else
        echo "install.sh is not exist!"
    fi
    if test -f ${APPPath}/${appName}/init.sh; then
        chmod +x ${APPPath}/${appName}/init.sh
        ${APPPath}/${appName}/init.sh
    fi
    #清理临时文件
    rm -rf  ${CurPath}/update-tmp
fi

#
#创建容器
imageTag=`cat ${APPPath}/image-version`
echo "create container ${containerName} ... image tag is ${imageTag}"
docker run --name ${containerName} -itd --network=host --gpus all --shm-size 32g --ipc=host  -v ${APPPath}:/opt/app  --privileged --device=/dev/infiniband  ${imageName}:${imageTag}

sleep 5
docker ps

#修改ssh权限
docker exec -i cluster-health-app chmod 600 /root/.ssh/id_rsa


echo "install cluster-health app done"
