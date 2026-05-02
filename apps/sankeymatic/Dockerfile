# syntax=docker/dockerfile:1

FROM alpine/git:v2.52.0 AS builder
ARG VERSION
USER 65534:65533

RUN git -C /tmp clone \
    --depth 1 \
    --branch main \
    https://github.com/nowthis/sankeymatic.git

FROM nginxinc/nginx-unprivileged:1.30.0-alpine-slim
COPY --from=builder /tmp/sankeymatic/build /app
