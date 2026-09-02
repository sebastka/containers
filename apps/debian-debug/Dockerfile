# syntax=docker/dockerfile:1@sha256:ecfaec9ed6d810b56388c508f4121597bfbba70d41a6dfeee4d8cad5f295fc32

FROM docker.io/library/debian:13@sha256:f324c7ff54321e8d9c588493a20244965938ce0aa50bbd1022d38010e9ffc4b1
ARG VERSION
ARG USER=debian

# Recommends are wanted here: this is a toolbox image, and nmap, tshark and
# dnsutils pull useful companions in that way.
# hadolint ignore=DL3015
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
CMD ["sh", "-c", "while [ ! -e /tmp/continue ]; do sleep 3; done"]
