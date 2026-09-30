"""Momentary controls for Wopet Local."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_CONTROL_PORT,
    CONF_CONTROL_TOKEN,
    CONF_STREAM_NAME,
    DEFAULT_CONTROL_PORT,
)
from .control import WopetControlClient


@dataclass(frozen=True, kw_only=True)
class WopetButtonDescription(ButtonEntityDescription):
    """Describe a Wopet momentary action."""

    action: str


BUTTONS = (
    WopetButtonDescription(
        key="pan_left", name="Pan Left", icon="mdi:pan-left", action="pan_left"
    ),
    WopetButtonDescription(
        key="pan_right", name="Pan Right", icon="mdi:pan-right", action="pan_right"
    ),
    WopetButtonDescription(
        key="dispense_treat",
        name="Dispense Treat",
        icon="mdi:bone",
        action="dispense_treat",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Wopet momentary control buttons."""
    token = str(entry.options.get(CONF_CONTROL_TOKEN, ""))
    port = int(entry.options.get(CONF_CONTROL_PORT, DEFAULT_CONTROL_PORT))
    client = WopetControlClient(
        hass,
        entry.options.get(CONF_HOST, entry.data[CONF_HOST]),
        port,
        token,
        entry.options.get(CONF_STREAM_NAME, entry.data[CONF_STREAM_NAME]),
    )
    async_add_entities(
        WopetButton(entry, description, client, bool(token))
        for description in BUTTONS
    )


class WopetButton(ButtonEntity):
    """A single, non-repeating Wopet control action."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        description: WopetButtonDescription,
        client: WopetControlClient,
        configured: bool,
    ) -> None:
        self.entity_description = description
        self._client = client
        self._attr_available = configured
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {("wopet_local", entry.unique_id or entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Wopet",
            "model": "Guardian Plus D100",
        }

    async def async_press(self) -> None:
        """Send exactly one action; the treat button never repeats automatically."""
        await self._client.async_execute(self.entity_description.action)
