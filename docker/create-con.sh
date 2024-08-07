#!/bin/bash

docker run --name test-he-v2 -itd --network=host --gpus all --shm-size 32g --ipc=host  -v /data/lizh/app:/opt/app  --cap-add=IPC_LOCK --device=/dev/infiniband  cluster-health:v1  