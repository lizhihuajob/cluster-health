#!/bin/bash
# 
# docker images 通过离线方式导入。cluster-health 代码通过在线方式下载
#
set -eu

CurPath=$(cd `dirname $0`; pwd)
CurTime=`date "+%Y-%m-%d %H:%M:%S"`
SYS_INFO=`uname -r`
APPPath="/opt/eht-cluster-health/app"

#将ibdev2netdev的结果信息，保存为json文件
function ibdev2netdev_json()
{
    ibdev_json_file=$1

    ibdev2netdev_info=$(ibdev2netdev |awk -F " " '{print"\""$1"\":\""$5"\""}')
    
    echo "{" > ${ibdev_json_file}
    #在每行的输出后面添加逗号，最后一行不添加
    last_item="mlx5_bond_0"
    for i in ${ibdev2netdev_info}
    do
       last_item=$i
    done
    #echo $last_item
    for i in ${ibdev2netdev_info}
    do
        if [ "${i}" == "${last_item}" ]; then
            echo  ${i} >> ${ibdev_json_file}
        else
            echo  ${i}, >> ${ibdev_json_file}
        fi
    done
    #去掉最后一行的逗号
    
    echo "}" >> ${ibdev_json_file}

    cat ${ibdev_json_file}
}

#复制IB相关命令到指定目录
function copy_ib_cmd()
{
    #定义一个指令列表
    ib_cmd_list="ibdev2netdev ibstat ibstatus"
    ib_cmd_dir=${APPPath}/bin
    if test -d ${ib_cmd_dir}; then
        echo "remove old ${ib_cmd_dir}"
        rm -rf ${ib_cmd_dir}
    fi
    mkdir -p ${ib_cmd_dir}

    for i in ${ib_cmd_list}
    do
        #获取指令的绝对路径
        i_path=$(which ${i})
        echo "copy ${i} to ${ib_cmd_dir}"
        cp ${i_path} ${ib_cmd_dir}
    done


}

#补充缺失的命令
copy_ib_cmd

#生成ibdev2netdev的json文件
#ibdev2netdev_json  ${CurPath}/host_validation/ibdev2netdev_info.json

