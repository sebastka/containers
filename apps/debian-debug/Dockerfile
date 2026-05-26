# syntax=docker/dockerfile:1@sha256:87999aa3d42bdc6bea60565083ee17e86d1f3339802f543c0d03998580f9cb89

FROM docker.io/library/debian:trixie-20260518@sha256:4ae67669760b807c19f23902a3fd7c121a6a70cf2ae709035674b23e712e4d62
ARG VERSION
ARG USER=debian

RUN printf -- 'alias ll="ls -alh"\n' >>/etc/profile && \
    \
    apt-get update && \
    apt-get install -y \
        vim nano \
        rsync duf htop screen \
        xz-utils procps \
        mariadb-client postgresql-client \
        iputils-ping net-tools tcpdump nmap tshark \
        curl wget inetutils-telnet dnsutils ldnsutils \
        openssh-client ldap-utils \
        && \
    rm -rf /var/lib/apt/lists/* && \
    \
    useradd -m ${USER}

USER ${USER}
WORKDIR /home/${USER}
CMD ["sleep", "infinity"]
