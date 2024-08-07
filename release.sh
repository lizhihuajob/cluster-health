#!/bin/bash

CurPath=$(cd `dirname $0`; pwd)
Time=`date +%Y%m%d_%H%M%S`

#输入版本号
echo -e "\033[32mplease input version number:\033[0m"
read version
if [ -z "$version" ]; then
    echo -e "\033[31mversion number is empty!\033[0m"
    exit
else
    echo -e "\033[32mversion number is $version\033[0m"
fi

