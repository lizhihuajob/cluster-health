FROM nvcr.io/nvidia/pytorch:24.04-py3

WORKDIR /

# change the download source of apt, comment it out if you are abroad
COPY sources.list /etc/apt/sources.list
RUN apt-get update && apt-get install -y openssh-server vim  net-tools telnet lsof sudo sshpass sysstat perftest iproute2
 
#1 install python3
COPY requirements.txt /requirements.txt
RUN pip3 install --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r /requirements.txt

#ssh install
COPY  ssh/sshd_config /etc/ssh/sshd_config
COPY  ssh/ssh_config  /etc/ssh/ssh_config
#RUN  ssh-keygen -t rsa -f ~/.ssh/id_rsa -P '' 
#RUN  cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys 
#RUN  chmod 600 /root/.ssh/authorized_keys
COPY  ssh/authorized_keys  /root/.ssh/authorized_keys
COPY  ssh/id_rsa  /root/.ssh/id_rsa
COPY  ssh/id_rsa.pub  /root/.ssh/id_rsa.pub
RUN   chmod 600  /root/.ssh/id_rsa

#sys init
#COPY 80-eht-init.sh /opt/nvidia/entrypoint.d/80-eht-init.sh
COPY environment /etc/environment
COPY eht-start.sh /opt/eht-start.sh
RUN  chmod +x /opt/eht-start.sh

#在目录/opt/nvidia/entrypoint.d 添加shell脚本，进行相关的初始化操作
#ENTRYPOINT ["/start.sh"]
CMD ["/opt/eht-start.sh"]
