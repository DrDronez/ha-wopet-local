# Wopet Local Bridge

This app must be installed and running before configuring the Wopet Local HACS
integration.

Enter the camera's LAN IP and its TUTK device credentials in the Configuration
tab. All credential fields are treated as passwords by the Home Assistant app
UI. They are read directly from `/data/options.json`; they are not placed in
command-line arguments, generated go2rtc configuration, or normal logs.

Choose an unused **RTSP port** in the Configuration tab. The app uses host
networking because the camera's UDP session handshake does not survive container
NAT. After startup, the stream is available at:

```text
rtsp://HOME_ASSISTANT_HOST:RTSP_PORT/wopet
```

The app's **Open Web UI** button opens the protected go2rtc diagnostics page.
Do not expose the selected RTSP port or port 1984 to the internet.

For complete installation, credential, network, and troubleshooting guidance,
see https://github.com/DrDronez/ha-wopet-local/blob/main/docs/BRIDGE_SETUP.md
