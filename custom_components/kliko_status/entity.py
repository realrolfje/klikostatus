"""Base entity for the Kliko Container Manager integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import KlikoConfigEntry
from .const import (
    ATTR_CONTAINER_NUMBER,
    ATTR_DISTRICT,
    CLIENTS,
    CONF_CLIENT,
    CONF_SOURCE,
    DOMAIN,
    SOURCE_KLIKO_MANAGER,
)
from .coordinator import KlikoDataUpdateCoordinator


class KlikoEntity(CoordinatorEntity[KlikoDataUpdateCoordinator]):
    """Base entity for Kliko container entities."""

    _attr_has_entity_name = True

    def __init__(self, entry: KlikoConfigEntry, container_number: str) -> None:
        """Initialize the entity."""
        super().__init__(entry.runtime_data.coordinator)
        self._entry = entry
        self._container_number = container_number
        source = self.integration_source
        client_name = self.client_name
        manufacturer = (
            "Kliko Container Manager"
            if source == SOURCE_KLIKO_MANAGER
            else client_name
        )
        device_name = (
            f"Kliko {self._container_number}"
            if source == SOURCE_KLIKO_MANAGER
            else f"{client_name} {self._container_number}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._container_number.casefold())},
            manufacturer=manufacturer,
            name=device_name,
        )

    @property
    def container_data(self) -> dict[str, Any]:
        """Return data for this entity's container."""
        return self.coordinator.data.get(self._container_number, {})

    @property
    def client_name(self) -> str:
        """Return the configured client display name."""
        return CLIENTS[self._entry.data[CONF_CLIENT]]["name"]

    @property
    def integration_source(self) -> str:
        """Return the configured data source."""
        return self._entry.data.get(CONF_SOURCE, SOURCE_KLIKO_MANAGER)

    @property
    def address_data(self) -> dict[str, Any]:
        """Return address data for this entity's container."""
        address = self.container_data.get("address")
        if not isinstance(address, dict):
            return {}
        return address

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return common entity attributes."""
        attributes: dict[str, str] = {
            ATTR_CONTAINER_NUMBER: self._container_number
        }

        district = self.address_data.get("district")
        if district:
            attributes[ATTR_DISTRICT] = str(district)
        return attributes


def _float_or_none(value: object) -> float | None:
    """Return a float value when possible."""
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return None
