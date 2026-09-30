"""Client for the authenticated Wopet bridge control API."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from urllib.parse import quote

from aiohttp import ClientError, ClientTimeout
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession


class WopetControlClient:
    """Send one-shot controls to the bridge without exposing camera credentials."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        token: str,
        stream_name: str,
    ) -> None:
        self._session = async_get_clientsession(hass)
        self._url = f"http://{host}:{port}/control"
        self._health_url = f"http://{host}:{port}/health"
        self._prime_url = (
            f"http://{host}:1985/api/frame.jpeg?src={quote(stream_name, safe='')}"
        )
        self._headers = {"Authorization": f"Bearer {token}"}

    async def _is_ready(self) -> bool:
        try:
            async with self._session.get(
                self._health_url,
                headers=self._headers,
                timeout=ClientTimeout(total=2),
            ) as response:
                return response.status == 200
        except (ClientError, TimeoutError):
            return False

    async def _prime_stream(self) -> None:
        """Ask go2rtc for a frame so its lazy exec producer starts."""
        with suppress(ClientError, TimeoutError):
            async with self._session.get(
                self._prime_url,
                timeout=ClientTimeout(total=20),
            ) as response:
                await response.read()

    async def _ensure_ready(self) -> None:
        if await self._is_ready():
            return

        prime_task = asyncio.create_task(self._prime_stream())
        try:
            for _attempt in range(30):
                await asyncio.sleep(0.5)
                if await self._is_ready():
                    return
        finally:
            if not prime_task.done():
                prime_task.cancel()
            with suppress(asyncio.CancelledError):
                await prime_task
        raise HomeAssistantError("Wopet camera stream did not become ready for controls")

    async def async_execute(self, action: str) -> None:
        """Prime the stream, then transmit the physical action exactly once."""
        await self._ensure_ready()
        try:
            async with self._session.post(
                self._url,
                json={"action": action},
                headers=self._headers,
                timeout=ClientTimeout(total=5),
            ) as response:
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as exc:
            # Do not retry an action after transmission. The camera may have applied
            # it even when its response was lost; retrying a treat could dispense twice.
            raise HomeAssistantError("Unable to reach the Wopet control bridge") from exc

        if response.status != 200 or not payload.get("ok"):
            error = payload.get("error", "camera command failed")
            raise HomeAssistantError(f"Wopet control failed: {error}")
