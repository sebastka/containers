ARG VERSION=latest
FROM docker.io/crowdsecurity/crowdsec:${VERSION}
RUN addgroup -g 1000 crowdsec && \
    adduser -u 1000 -G crowdsec -D crowdsec && \
    chgrp crowdsec /etc && \
    chmod g+w /etc && \
    chown -R crowdsec:crowdsec \
        /var/lib/crowdsec \
        /staging/etc/crowdsec \
        /staging/var/lib/crowdsec

USER 1000:1000
