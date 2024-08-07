#!/bin/bash

docker ps

docker stop  test-he-v2
sleep 1
docker rm test-he-v2
sleep 1
docker rmi cluster-health:v1
docker ps
docker images