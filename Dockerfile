FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV container=docker

# systemd + Python + 基础工具
# 容器模式使用 ansible_connection=docker 直接管理容器，不再内置 sshd/root 免密登录。
RUN apt-get update && apt-get install -y \
    systemd \
    systemd-sysv \
    python3 \
    python3-pip \
    sudo \
    ca-certificates \
    curl \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# 精简 systemd，移除无关 unit
RUN cd /lib/systemd/system/sysinit.target.wants/ && \
    ls | grep -v systemd-tmpfiles-setup | xargs rm -f && \
    rm -f /lib/systemd/system/multi-user.target.wants/* && \
    rm -f /etc/systemd/system/*.wants/* && \
    rm -f /lib/systemd/system/local-fs.target.wants/* && \
    rm -f /lib/systemd/system/sockets.target.wants/*udev* && \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl* && \
    rm -f /lib/systemd/system/basic.target.wants/* && \
    rm -f /lib/systemd/system/anaconda.target.wants/* && \
    rm -f /lib/systemd/system/plymouth* && \
    rm -f /lib/systemd/system/systemd-update-utmp*

VOLUME ["/sys/fs/cgroup", "/tmp", "/run", "/run/lock", "/var/log"]

STOPSIGNAL SIGRTMIN+3

CMD ["/sbin/init"]
