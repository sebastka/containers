# syntax=docker/dockerfile:1

FROM oven/bun:1.3.14-alpine AS builder
ARG VERSION

USER 65534:65533
WORKDIR /app

ARG PUB_ENV=production \
    PUB_HOSTNAME=localhost:5173 \
    PUB_PLAUSIBLE_URL='' \
    PUB_VERTD_URL=https://vertd.vert.sh \
    PUB_DISABLE_ALL_EXTERNAL_REQUESTS=true \
    PUB_DONATION_URL=https://donations.vert.sh \
    PUB_STRIPE_KEY=pk_live_51RDVmAGSxPVad6bQwzVNnbc28nlmzA30krLWk1fefCMpUPiSRPkavMMbGqa8A3lUaOCMlsUEVy2CWDYg0ip3aPpL00ZJlsMkf2 \
    PUB_DISABLE_FAILURE_BLOCKS=false
ENV PUB_ENV=${PUB_ENV} \
    PUB_HOSTNAME=${PUB_HOSTNAME} \
    PUB_PLAUSIBLE_URL=${PUB_PLAUSIBLE_URL} \
    PUB_VERTD_URL=${PUB_VERTD_URL} \
    PUB_DISABLE_ALL_EXTERNAL_REQUESTS=${PUB_DISABLE_ALL_EXTERNAL_REQUESTS} \
    PUB_DONATION_URL=${PUB_DONATION_URL} \
    PUB_STRIPE_KEY=${PUB_STRIPE_KEY} \
    PUB_DISABLE_FAILURE_BLOCKS=${PUB_DISABLE_FAILURE_BLOCKS}

RUN mkdir /tmp/vert \
    && wget -O - https://github.com/VERT-sh/VERT/archive/refs/heads/main.tar.gz \
        | tar -xzf - --strip-components=1 -C /tmp/vert \
    && (cd /tmp/vert && bun install) \
    && (cd /tmp/vert && bun run build)

FROM nginxinc/nginx-unprivileged:1.30.0-alpine-slim
COPY --from=builder /tmp/vert/build /app
