"""The Kliko Container Manager integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import KlikoDataUpdateCoordinator
from .const import (
    CONF_CARD_NUMBER,
    CONF_CLIENT,
    CONF_CONTAINER_NUMBER,
    CONF_CONTAINER_NUMBERS,
    CONF_STREET_NUMBER,
    CONF_STREET_NUMBER_ADDITION,
    CONF_ZIP_CODE,
    DOMAIN,
)

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


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old single-container config entries."""
    if entry.version == 1 and CONF_CONTAINER_NUMBERS not in entry.data:
        data = {**entry.data}
        container_number = data.get(CONF_CONTAINER_NUMBER)
        if container_number is not None:
            data[CONF_CONTAINER_NUMBERS] = [str(container_number)]

        hass.config_entries.async_update_entry(
            entry,
            data=data,
            unique_id=_entry_unique_id(data),
            version=2,
        )
        return True

    return True


async def async_unload_entry(hass: HomeAssistant, entry: KlikoConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _entry_unique_id(data: dict) -> str | None:
    """Return the login-level unique ID for a config entry."""
    client = data.get(CONF_CLIENT)
    if not client:
        return None

    unique_login = data.get(CONF_CARD_NUMBER) or (
        f"{data.get(CONF_ZIP_CODE)}_{data.get(CONF_STREET_NUMBER)}_"
        f"{data.get(CONF_STREET_NUMBER_ADDITION, '')}"
    )
    return f"{client}_{unique_login}"
