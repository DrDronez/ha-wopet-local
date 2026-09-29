# Wopet Local Bridge

This app must be installed and running before configuring the Wopet Local HACS
integration.

Enter the camera's LAN IP and its TUTK device credentials in the Configuration
tab. All credential fields are treated as passwords by the Home Assistant app
UI. They are read directly from `/data/options.json`; they are not placed in
command-line arguments, generated go2rtc configuration, or normal logs.

After startup, the default stream is available at:

```text
rtsp://HOME_ASSISTANT_HOST:8554/wopet
```

The app's **Open Web UI** button opens the protected go2rtc diagnostics page.
Do not expose ports 8554 or 1984 to the internet.

For complete installation, credential, network, and troubleshooting guidance,
see https://github.com/DrDronez/ha-wopet-local/blob/main/docs/BRIDGE_SETUP.md

