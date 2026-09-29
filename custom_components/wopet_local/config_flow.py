"""Config flow for Wopet Local."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import (
    CONF_RTSP_PORT,
    CONF_STREAM_NAME,
    DEFAULT_RTSP_PORT,
    DEFAULT_STREAM_NAME,
    DOMAIN,
)


async def _port_is_open(host: str, port: int) -> bool:
    """Return whether the configured RTSP endpoint accepts a TCP connection."""
    try:
        _reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
    except (TimeoutError, OSError):
        return False
    writer.close()
    await writer.wait_closed()
    return True


class WopetLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Wopet Local config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure a Wopet Local bridge."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_RTSP_PORT]
            stream_name = user_input[CONF_STREAM_NAME].strip().strip("/")
            unique_id = f"{host.lower()}:{port}/{stream_name.lower()}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            if not await _port_is_open(host, port):
                errors["base"] = "cannot_connect"
            else:
                data = {**user_input, CONF_HOST: host, CONF_STREAM_NAME: stream_name}
                return self.async_create_entry(title=user_input[CONF_NAME], data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Wopet Camera"): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_RTSP_PORT, default=DEFAULT_RTSP_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Required(CONF_STREAM_NAME, default=DEFAULT_STREAM_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
