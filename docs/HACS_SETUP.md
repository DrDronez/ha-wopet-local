# HACS integration setup

Install and start the [Wopet Local Bridge](BRIDGE_SETUP.md) first.

## Add the unlisted repository

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu and select **Custom repositories**.
3. Enter:

   ```text
   https://github.com/DrDronez/ha-wopet-local
   ```

4. Select category **Integration** and choose **Add**.
5. Search for **Wopet Local** and install it.
6. Restart Home Assistant when HACS requests it.

This project is public so HACS can download it, but it has not been submitted
to HACS's default catalog. Add it as a custom repository using the steps above.

## Add the integration

1. Open **Settings → Devices & services**.
2. Select **Add integration** and search for **Wopet Local**.
3. Enter:

   - **Bridge host:** the IP address or resolvable hostname of your Home
     Assistant host. On HAOS, use the host's LAN address, not `127.0.0.1`,
     because Home Assistant Core runs in a separate container;
   - **RTSP port:** the port selected in the bridge configuration (`8554` by default);
   - **Stream name:** `wopet` unless changed in the bridge configuration;
   - **Camera name:** the friendly name to display in Home Assistant.

4. Open the Wopet Local integration's **Configure** dialog. You can correct
   the bridge host, RTSP port, or stream name there without removing the
   integration, and enter:

   - **Control port:** the bridge control port (`1986` by default);
   - **Control token:** the same private random value saved in the bridge app.

The integration creates momentary Pan Left, Pan Right, and Dispense Treat
button entities. Each button press sends one action. Treat dispensing does not
repeat automatically.

The setup flow checks that the RTSP port is reachable before creating the
camera entity. It never asks for or stores camera credentials.

## Dashboard

After setup, add the created `camera` entity and any desired control buttons to
the dashboard. Home Assistant consumes the RTSP URL through its stream
integration. If experimental listen audio is enabled in the bridge, unmute the
camera player to hear it.

## Removing the project

Remove the Wopet Local integration first, then uninstall the bridge app. HACS
and the Home Assistant App Store repository entries may be removed afterward.
