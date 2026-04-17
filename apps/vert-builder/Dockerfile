# syntax=docker/dockerfile:1

FROM oven/bun:1.3.12-alpine
ARG VERSION
RUN apk add --no-cache git

USER 65534:65533
WORKDIR /app
RUN git clone --branch main --depth 1 https://github.com/VERT-sh/VERT.git . \
    && bun install

ARG PUB_ENV=production \
    PUB_DISABLE_FAILURE_BLOCKS=false
ENV PUB_ENV=${PUB_ENV} \
    PUB_HOSTNAME=localhost:5173 \
    PUB_PLAUSIBLE_URL='' \
    PUB_VERTD_URL=https://vertd.vert.sh \
    PUB_DISABLE_ALL_EXTERNAL_REQUESTS=true \
    PUB_DONATION_URL=https://donations.vert.sh \
    PUB_STRIPE_KEY=pk_live_51RDVmAGSxPVad6bQwzVNnbc28nlmzA30krLWk1fefCMpUPiSRPkavMMbGqa8A3lUaOCMlsUEVy2CWDYg0ip3aPpL00ZJlsMkf2 \
    PUB_DISABLE_FAILURE_BLOCKS=${PUB_DISABLE_FAILURE_BLOCKS}

CMD ["bun", "run", "build"]
