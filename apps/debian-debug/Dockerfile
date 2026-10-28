# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

FROM docker.io/library/debian:13@sha256:8c4733a92aacd0bcff3779eadc35a4a5147f36cb20a5fcb56504cbc740212259
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
CMD ["sh", "-c", "trap 'exit 0' TERM INT; while [ ! -e /tmp/continue ]; do sleep 3 & wait $!; done"]
