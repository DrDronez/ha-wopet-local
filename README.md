# Wopet Local for Home Assistant

Experimental, local video access for supported Wopet cameras in Home Assistant.

> [!WARNING]
> This is an early interoperability project. The only validated combination is
> the Wopet Guardian Plus D100 running firmware `40.23.6.5`. It is not affiliated
> with or endorsed by Wopet or ThroughTek. Use it only with devices and accounts
> you own.

The project has two installable pieces:

1. **Wopet Local Bridge**, a Home Assistant app (formerly add-on) that connects
   to the camera with a pure-Python TUTK/Kalay client and publishes a local RTSP
   stream through go2rtc.
2. **Wopet Local**, a HACS custom integration that creates a normal Home
   Assistant camera entity for that RTSP stream.

No proprietary TUTK native library is included or required. Camera credentials
are entered in the private Home Assistant app configuration and are never part
of this repository.

## Install the bridge

The bridge must be installed before the HACS integration.

1. In Home Assistant, open **Settings → Apps → App store**.
2. Open the repository menu, choose **Repositories**, and add:

   ```text
   https://github.com/DrDronez/ha-wopet-local
   ```

3. Install **Wopet Local Bridge**.
4. Open its **Configuration** tab and enter your camera's LAN IP, TUTK device
   UID, device username, and device password.
5. Start the app and enable its watchdog.
6. Confirm the log reports that go2rtc is listening. Do not post bridge logs
   publicly until you have checked them for private network information.

Complete bridge instructions, credential guidance, and troubleshooting are in
[Bridge setup](docs/BRIDGE_SETUP.md).

## Install the HACS integration

This repository is intentionally not listed in HACS's default catalog during
the alpha period.

1. In HACS, open the three-dot menu and select **Custom repositories**.
2. Add `https://github.com/DrDronez/ha-wopet-local` as type **Integration**.
3. Search for **Wopet Local**, install it, and restart Home Assistant.
4. Open **Settings → Devices & services → Add integration → Wopet Local**.
5. Enter the hostname or IP address of your Home Assistant host, RTSP port
   `8554`, and stream name `wopet`.

See [HACS setup](docs/HACS_SETUP.md) for screenshots-free, step-by-step details.

## Supported features

| Feature | Status |
| --- | --- |
| Direct LAN authentication | Validated |
| HEVC/H.265 video | Validated experimentally |
| RTSP restream | Alpha |
| Home Assistant camera entity | Alpha |
| Audio | Planned |
| PTZ | Planned |
| Quality selection | Planned |
| Two-way talk | Planned |
| Treat dispensing | Deliberately deferred |

## Security

- Never commit app options, PCAP files, credentials, real device identifiers,
  or private IP addresses.
- Diagnostics and bug reports must be scrubbed before publication.
- The Wopet mobile app has been observed using plain HTTP for account bootstrap
  traffic. This project therefore starts with local device credentials rather
  than asking for a Wopet account password.

Please read [SECURITY.md](SECURITY.md) before reporting a vulnerability.

## Development

The bridge currently targets `amd64`, matching HAOS on x86-64. The transport is
adapted from the MIT-licensed `cuboai-tutk` pure-Python implementation; see
[third-party notices](THIRD_PARTY_NOTICES.md).

```bash
python -m pip install -r requirements-dev.txt
pytest
ruff check .
```

## License

MIT. See [LICENSE](LICENSE).
