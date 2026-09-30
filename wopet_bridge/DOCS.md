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

Generate a long random **control token** and enter it in both this app and the
Wopet Local integration's Configure dialog. The integration uses the
authenticated control port for the momentary Pan Left, Pan Right, and Dispense
Treat buttons. A treat press sends exactly one dispense request.

Enable **Include camera audio** to publish the camera's AAC listen track with
the video. This changes the bridge pipe from raw HEVC to MPEG-TS and remains
experimental; turn it back off if a client cannot play the combined stream.

The app's **Open Web UI** button opens the protected go2rtc diagnostics page.

If the camera drops a session or temporarily refuses a reconnect, the bridge
waits for a complete HEVC keyframe before handing data to go2rtc, keeps the
go2rtc media pipe open, and applies a persistent 60-second-to-10-minute
exponential cooldown if the session ends. The cooldown survives go2rtc source
respawns so the camera cannot be pushed into a rapid-attempt lockout.
Repeated failures back off to a maximum of five minutes so the camera is not
trapped in its rapid-connection rate limit.

After the opening VPS/keyframe establishes the stream, malformed or incomplete
HEVC access units are discarded. Playback resynchronizes at the next keyframe
instead of allowing a damaged NAL unit to restart go2rtc.
Do not expose the selected RTSP port, control port, or diagnostics port `1985`
to the internet.

For complete installation, credential, network, and troubleshooting guidance,
see https://github.com/DrDronez/ha-wopet-local/blob/main/docs/BRIDGE_SETUP.md
