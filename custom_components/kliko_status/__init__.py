"""The Kliko Container Manager integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import KlikoDataUpdateCoordinator
from .const import DOMAIN

PLATFORMS: tuple[Platform, ...] = (Platform.BINARY_SENSOR, Platform.SENSOR)


@dataclass
class KlikoRuntimeData:
    """Runtime data for a Kliko config entry."""

    coordinator: KlikoDataUpdateCoordinator


type KlikoConfigEntry = ConfigEntry[KlikoRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: KlikoConfigEntry) -> bool:
    """Set up Kliko Container Manager from a config entry."""
    coordinator = KlikoDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = KlikoRuntimeData(coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KlikoConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
