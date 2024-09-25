#!/bin/bash
#清除构建缓存
docker builder prune

echo "build start "
#开始构建镜像
docker build -t eht.docker.hub:30443/eht-images/cluster-health:24.10 .

echo "build done"