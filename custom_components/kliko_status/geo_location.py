"""Geolocation platform for the Kliko Status integration."""

from __future__ import annotations

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KlikoConfigEntry
from .const import ATTR_CONTAINER_NUMBER, ATTR_DISTRICT, DOMAIN
from .entity import KlikoEntity, _float_or_none


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KlikoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kliko geolocation entities."""
    async_add_entities(
        KlikoGeoLocation(entry, container_number)
        for container_number in entry.runtime_data.coordinator.container_numbers
        if _has_coordinates(entry, container_number)
    )


def _has_coordinates(entry: KlikoConfigEntry, container_number: str) -> bool:
    """Return true if the selected container has usable coordinates."""
    container = entry.runtime_data.coordinator.data.get(container_number, {})
    address = container.get("address")
    if not isinstance(address, dict):
        return False
    return (
        _float_or_none(address.get("latitude")) is not None
        and _float_or_none(address.get("longitude")) is not None
    )


class KlikoGeoLocation(KlikoEntity, GeolocationEvent):
    """Representation of a selected waste container location."""

    _attr_icon = "mdi:map-marker"
    _attr_translation_key = "location"

    def __init__(self, entry: KlikoConfigEntry, container_number: str) -> None:
        """Initialize the geolocation entity."""
        super().__init__(entry, container_number)
        self._attr_unique_id = f"{self._container_number.casefold()}_location"
        self._attr_source = DOMAIN
        self._update_location_attributes()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_location_attributes()
        super()._handle_coordinator_update()

    def _update_location_attributes(self) -> None:
        """Update Home Assistant geolocation attributes from container data."""
        self._attr_latitude = _float_or_none(self.address_data.get("latitude"))
        self._attr_longitude = _float_or_none(self.address_data.get("longitude"))
        attributes = {ATTR_CONTAINER_NUMBER: self._container_number}
        if district := self.address_data.get("district"):
            attributes[ATTR_DISTRICT] = str(district)
        self._attr_extra_state_attributes = attributes
