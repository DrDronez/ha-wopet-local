"""Camera platform for Wopet Local."""

from __future__ import annotations

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_RTSP_PORT, CONF_STREAM_NAME


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the configured Wopet camera entity."""
    async_add_entities([WopetLocalCamera(entry)])


class WopetLocalCamera(Camera):
    """A camera published by the Wopet Local Bridge."""

    _attr_brand = "Wopet"
    _attr_model = "Guardian Plus D100"
    _attr_supported_features = CameraEntityFeature.STREAM
    _attr_use_stream_for_stills = True

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__()
        self._attr_name = entry.data[CONF_NAME]
        self._attr_unique_id = entry.unique_id or entry.entry_id
        self._host = entry.data[CONF_HOST]
        self._port = entry.data[CONF_RTSP_PORT]
        self._stream_name = entry.data[CONF_STREAM_NAME]

    async def stream_source(self) -> str:
        """Return the local bridge RTSP source."""
        return f"rtsp://{self._host}:{self._port}/{self._stream_name}"
