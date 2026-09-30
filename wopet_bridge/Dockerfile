FROM golang:1.24-alpine AS go2rtc-builder

ARG GO2RTC_VERSION=v1.9.14
ARG GO2RTC_COMMIT=b5948cfb25404cc5cb37b166ecaa2dca20b11d4b

RUN apk add --no-cache git \
    && git clone --filter=blob:none --no-checkout https://github.com/AlexxIT/go2rtc.git /src/go2rtc \
    && cd /src/go2rtc \
    && git checkout "${GO2RTC_COMMIT}" \
    && test "$(git describe --tags --exact-match)" = "${GO2RTC_VERSION}"

COPY patches/go2rtc-pcma-mpegts.patch /tmp/go2rtc-pcma-mpegts.patch

RUN cd /src/go2rtc \
    && git apply --check /tmp/go2rtc-pcma-mpegts.patch \
    && git apply /tmp/go2rtc-pcma-mpegts.patch \
    && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
        -trimpath -ldflags="-s -w" -o /out/go2rtc .

FROM ghcr.io/home-assistant/amd64-base-python:3.13-alpine3.22

ARG BUILD_VERSION=dev
ARG BUILD_ARCH=amd64

LABEL \
    io.hass.name="Wopet Local Bridge" \
    io.hass.description="Local TUTK/Kalay to RTSP bridge for supported Wopet cameras" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}"

COPY --from=go2rtc-builder /out/go2rtc /usr/local/bin/go2rtc

RUN chmod 0755 /usr/local/bin/go2rtc

COPY rootfs /
COPY wopet /app/wopet
COPY vendor /app/vendor

RUN chmod 0755 /etc/services.d/wopet/run /app/wopet/wopet_stream.py
