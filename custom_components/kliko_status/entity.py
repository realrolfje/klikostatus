"""Base entity for the Kliko Container Manager integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import KlikoConfigEntry
from .const import (
    ATTR_CONTAINER_NUMBER,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    DOMAIN,
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
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._container_number.casefold())},
            manufacturer="Kliko Container Manager",
            name=f"Kliko {self._container_number}",
        )

    @property
    def container_data(self) -> dict[str, Any]:
        """Return data for this entity's container."""
        return self.coordinator.data.get(self._container_number, {})

    @property
    def extra_state_attributes(self) -> dict[str, str | float]:
        """Return common entity attributes."""
        attributes: dict[str, str | float] = {
            ATTR_CONTAINER_NUMBER: self._container_number
        }
        address = self.container_data.get("address")
        if not isinstance(address, dict):
            return attributes

        latitude = _float_or_none(address.get("latitude"))
        longitude = _float_or_none(address.get("longitude"))
        if latitude is not None:
            attributes[ATTR_LATITUDE] = latitude
        if longitude is not None:
            attributes[ATTR_LONGITUDE] = longitude
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
