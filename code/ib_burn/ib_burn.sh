#!/bin/bash
set -e
mkdir -p ./ib_burn_logs
echo "stage 0; chunk 0 / 4; servers"
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_8 --duration 1800 --port 40004 &> ./ib_burn_logs/hgx-h800-006-mlx5_3-hgx-h800-006-mlx5_8-server.log &
sleep 15
echo "stage 0; chunk 0 / 4; writers"
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_3 --duration 1800 --port 40004 hgx-h800-006 &> ./ib_burn_logs/hgx-h800-006-mlx5_3-hgx-h800-006-mlx5_8-writer.log &
sleep 1
echo "stage 0; chunk 1 / 4; servers"
ssh root@10.100.200.4 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_0 --duration 1800 --port 40000 &> ./ib_burn_logs/hgx-h800-004-mlx5_5-hgx-h800-004-mlx5_0-server.log &
ssh root@10.100.200.1 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_4 --duration 1800 --port 40002 &> ./ib_burn_logs/hgx-h800-006-mlx5_8-hgx-h800-001-mlx5_4-server.log &
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_0 --duration 1800 --port 40000 &> ./ib_burn_logs/hgx-h800-004-mlx5_8-hgx-h800-006-mlx5_0-server.log &
ssh root@10.100.200.4 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_4 --duration 1800 --port 40002 &> ./ib_burn_logs/hgx-h800-006-mlx5_5-hgx-h800-004-mlx5_4-server.log &
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_4 --duration 1800 --port 40002 &> ./ib_burn_logs/hgx-h800-001-mlx5_5-hgx-h800-006-mlx5_4-server.log &
sleep 15
echo "stage 0; chunk 1 / 4; writers"
ssh root@10.100.200.4 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_5 --duration 1800 --port 40000 hgx-h800-004 &> ./ib_burn_logs/hgx-h800-004-mlx5_5-hgx-h800-004-mlx5_0-writer.log &
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_8 --duration 1800 --port 40002 hgx-h800-001 &> ./ib_burn_logs/hgx-h800-006-mlx5_8-hgx-h800-001-mlx5_4-writer.log &
ssh root@10.100.200.4 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_8 --duration 1800 --port 40000 hgx-h800-006 &> ./ib_burn_logs/hgx-h800-004-mlx5_8-hgx-h800-006-mlx5_0-writer.log &
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_5 --duration 1800 --port 40002 hgx-h800-004 &> ./ib_burn_logs/hgx-h800-006-mlx5_5-hgx-h800-004-mlx5_4-writer.log &
ssh root@10.100.200.1 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_5 --duration 1800 --port 40002 hgx-h800-006 &> ./ib_burn_logs/hgx-h800-001-mlx5_5-hgx-h800-006-mlx5_4-writer.log &
sleep 1
echo "stage 0; chunk 2 / 4; servers"
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_5 --duration 1800 --port 40003 &> ./ib_burn_logs/hgx-h800-006-mlx5_0-hgx-h800-006-mlx5_5-server.log &
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_8 --duration 1800 --port 40004 &> ./ib_burn_logs/hgx-h800-001-mlx5_0-hgx-h800-006-mlx5_8-server.log &
ssh root@10.100.200.1 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_8 --duration 1800 --port 40004 &> ./ib_burn_logs/hgx-h800-006-mlx5_4-hgx-h800-001-mlx5_8-server.log &
ssh root@10.100.200.4 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_8 --duration 1800 --port 40004 &> ./ib_burn_logs/hgx-h800-004-mlx5_0-hgx-h800-004-mlx5_8-server.log &
ssh root@10.100.200.4 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_5 --duration 1800 --port 40003 &> ./ib_burn_logs/hgx-h800-001-mlx5_4-hgx-h800-004-mlx5_5-server.log &
sleep 15
echo "stage 0; chunk 2 / 4; writers"
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_0 --duration 1800 --port 40003 hgx-h800-006 &> ./ib_burn_logs/hgx-h800-006-mlx5_0-hgx-h800-006-mlx5_5-writer.log &
ssh root@10.100.200.1 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_0 --duration 1800 --port 40004 hgx-h800-006 &> ./ib_burn_logs/hgx-h800-001-mlx5_0-hgx-h800-006-mlx5_8-writer.log &
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_4 --duration 1800 --port 40004 hgx-h800-001 &> ./ib_burn_logs/hgx-h800-006-mlx5_4-hgx-h800-001-mlx5_8-writer.log &
ssh root@10.100.200.4 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_0 --duration 1800 --port 40004 hgx-h800-004 &> ./ib_burn_logs/hgx-h800-004-mlx5_0-hgx-h800-004-mlx5_8-writer.log &
ssh root@10.100.200.1 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_4 --duration 1800 --port 40003 hgx-h800-004 &> ./ib_burn_logs/hgx-h800-001-mlx5_4-hgx-h800-004-mlx5_5-writer.log &
sleep 1
echo "stage 0; chunk 3 / 4; servers"
ssh root@10.100.200.6 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_3 --duration 1800 --port 40001 &> ./ib_burn_logs/hgx-h800-004-mlx5_0-hgx-h800-006-mlx5_3-server.log &
sleep 15
echo "stage 0; chunk 3 / 4; writers"
ssh root@10.100.200.4 timeout 1826 stdbuf -oL -eL ib_write_bw --CPU-freq --report_gbits --ib-dev=mlx5_0 --duration 1800 --port 40001 hgx-h800-006 &> ./ib_burn_logs/hgx-h800-004-mlx5_0-hgx-h800-006-mlx5_3-writer.log &
sleep 1
echo "stage 0; awaiting"
wait
echo "stage 0; finished"
