FROM ghcr.io/home-assistant/amd64-base-python:3.13-alpine3.22

ARG BUILD_VERSION=dev
ARG BUILD_ARCH=amd64

LABEL \
    io.hass.name="Wopet Local Bridge" \
    io.hass.description="Local TUTK/Kalay to RTSP bridge for supported Wopet cameras" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}"

RUN wget -q -T 30 -t 5 \
        -O /usr/local/bin/go2rtc \
        https://github.com/AlexxIT/go2rtc/releases/download/v1.9.14/go2rtc_linux_amd64 \
    && echo "32d616af226bd731678ffde328b94cfb94e30339bfefc469cfb76323144615a6  /usr/local/bin/go2rtc" \
        | sha256sum -c - \
    && chmod 0755 /usr/local/bin/go2rtc

COPY rootfs /
COPY wopet /app/wopet
COPY vendor /app/vendor

RUN chmod 0755 /etc/services.d/wopet/run /app/wopet/wopet_stream.py
